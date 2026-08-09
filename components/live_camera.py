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
        # Fixed optimal threshold for instant detection without needing slider interaction
        self.conf_threshold = 0.15

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        if self.detected:
            return frame
        
        img = frame.to_ndarray(format="bgr24")
        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            # Run detection with fixed threshold
            proc_img, counts = run_detection(pil_img, self.conf_threshold)
            
            # Check if any valid hazard count is detected
            if counts and isinstance(counts, dict) and len(counts) > 0:
                # Ensure at least one count is greater than 0
                has_hazard = any(v is not None and v > 0 for v in counts.values())
                if has_hazard:
                    self.detected = True
                    
                    # Bounding box plotting logic
                    try:
                        from ultralytics.engine.results import Results
                        if isinstance(proc_img, Results):
                            proc_img = proc_img.plot()
                    except ImportError:
                        pass
                        
                    if isinstance(proc_img, list) and len(proc_img) > 0:
                        try:
                            proc_img = proc_img[0].plot()
                        except:
                            pass
                    
                    if isinstance(proc_img, np.ndarray):
                        if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                            proc_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB)
                        final_img = Image.fromarray(proc_img)
                    elif isinstance(proc_img, Image.Image):
                        final_img = proc_img
                    else:
                        final_img = Image.fromarray(img)
                        
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
    st.markdown("### 📸 Instant Auto-Stop AI Detection")
    st.markdown("💡 **Camera start karein—baghair kisi button ya slider ke live feed par automatic detection shuru ho gi aur hazard aate hi foran result aa jaye ga!**")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None
    if "synced_to_db" not in st.session_state:
        st.session_state["synced_to_db"] = False

    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        
        img_to_show = res["processed_img"]
        st.image(img_to_show, caption="Detected Hazard Result with Bounding Boxes", use_container_width=True)

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
        ctx = webrtc_streamer(
            key="auto-stop-streamer-v2",
            video_processor_factory=AutoStopTransformer,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
            async_processing=True,
        )

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
