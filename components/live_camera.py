import streamlit as st
import cv2
import av
import numpy as np
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

try:
    from utils.priority_engine import calculate_priority_score
except Exception:
    def calculate_priority_score(counts):
        return {
            "priority_score": 65,
            "severity": "Medium",
            "assigned_dept": "Municipal Operations",
            "sla_target": "24 Hours"
        }

# Multiple STUN servers taake network connection timeout na ho
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302", "stun:stun.stunprotocol.org:3478"]}
        ]
    }
)

class AutoStopTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = 0.15

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        if self.detected:
            return frame
        
        img = frame.to_ndarray(format="bgr24")
        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            proc_img, counts = run_detection(pil_img, self.conf_threshold)
            
            if counts and len(counts) > 0:
                self.detected = True
                
                from ultralytics.engine.results import Results
                if isinstance(proc_img, Results):
                    proc_img = proc_img.plot()
                elif isinstance(proc_img, list) and len(proc_img) > 0:
                    try:
                        proc_img = proc_img[0].plot()
                    except:
                        pass
                
                if isinstance(proc_img, np.ndarray):
                    final_img = proc_img
                else:
                    final_img = img
                    
                tracking_id = generate_tracking_id()
                assessment = calculate_priority_score(counts)
                
                hazard_list = [f"{str(k).capitalize()} ({v})" for k, v in counts.items() if v is not None]
                main_hazard = ", ".join(hazard_list) if hazard_list else "Municipal Hazard"
                
                self.result_data = {
                    "tracking_id": tracking_id,
                    "counts": counts,
                    "processed_img": final_img,
                    "assessment": assessment,
                    "main_hazard": main_hazard
                }
        except Exception as e:
            print(f"Auto-Stop Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(conf_threshold=0.15, *args, **kwargs):
    st.markdown("### 📸 Auto-Stop AI Detection & Instant Result")
    st.markdown("💡 **Jaise hi hazard detect hoga, camera stop ho kar foran result aur Supabase sync dikha dega!**")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None
    if "synced_to_db" not in st.session_state:
        st.session_state["synced_to_db"] = False

    conf_threshold = st.slider("Confidence Threshold", 0.05, 0.90, conf_threshold, 0.05, key="auto_stop_conf")

    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        
        img_to_show = res["processed_img"]
        if isinstance(img_to_show, np.ndarray):
            if len(img_to_show.shape) == 3 and img_to_show.shape[2] == 3:
                img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_BGR2RGB)
            img_to_show = Image.fromarray(img_to_show)
            
        st.image(img_to_show, caption="Detected Hazard Result (Auto-Captured)", use_container_width=True)

        with st.container(border=True):
            st.markdown(f"**🏷️ Tracking ID:** `{res['tracking_id']}`")
            summary_bullets = "".join([f"- **{str(k).capitalize()}**: {v}\n" for k, v in res['counts'].items() if v is not None])
            st.markdown("**📋 Detected Items:**")
            st.markdown(summary_bullets if summary_bullets else "- Hazard Detected")
            
            assessment = res['assessment']
            st.markdown(f"**⚡ Priority Score:** {assessment.get('priority_score')}/100 | **Severity:** {assessment.get('severity')}")
            st.markdown(f"**🏢 Assigned Dept:** {assessment.get('assigned_dept')} | **⏱️ SLA:** {assessment.get('sla_target')}")

        if st.session_state.get("synced_to_db", False):
            st.success("✅ Data kamyabi ke sath automatically Supabase mein save ho gaya hai!")

        if st.button("🔄 Dobara Scanning Shuru Karein", use_container_width=True):
            st.session_state["captured_result"] = None
            st.session_state["synced_to_db"] = False
            st.rerun()

    else:
        st.info("ℹ️ Agar connection mein der lage, to page ko aik bar refresh (F5) kar lein.")
        
        ctx = webrtc_streamer(
            key="auto-stop-streamer",
            video_processor_factory=AutoStopTransformer,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
            async_processing=True,
        )

        if ctx.video_processor:
            ctx.video_processor.conf_threshold = conf_threshold

        if ctx.video_processor and ctx.video_processor.detected and ctx.video_processor.result_data:
            res = ctx.video_processor.result_data
            st.session_state["captured_result"] = res
            
            try:
                payload = {
                    "tracking_id": res["tracking_id"],
                    "hazard": res["main_hazard"],
                    "issue_type": res["main_hazard"],
                    "severity": f"{res['assessment']['severity']} ({res['assessment']['priority_score']}/100)",
                    "status": "Active / Dispatched",
                    "location_name": "Live Auto-Stop Camera",
                    "latitude": 31.5204,
                    "longitude": 74.3587,
                    "assigned_dept": res['assessment']['assigned_dept'],
                    "sla_target": res['assessment']['sla_target']
                }
                supabase.table("reports").insert(payload).execute()
                st.session_state["synced_to_db"] = True
            except Exception as db_err:
                print(f"Supabase Error: {db_err}")
                st.session_state["synced_to_db"] = False
            
            st.rerun()
