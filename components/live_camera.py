import streamlit as st
import cv2
import av
import numpy as np
import queue
import threading
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

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

# Stable STUN configuration
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]}
        ]
    }
)

class AutoStopTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = 0.50
        
        # Non-blocking queue aur Background Worker thread taake video bilkul smooth rahay
        self.frame_queue = queue.Queue(maxsize=1)
        self.worker_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.worker_thread.start()

    def _processing_loop(self):
        while not self.detected:
            try:
                img = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            try:
                # Speed boost ke liye downscaled image par detection run karein
                img_small = cv2.resize(img, (320, 320))
                img_rgb = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                
                proc_img, counts = run_detection(pil_img, self.conf_threshold)
                
                if counts and isinstance(counts, dict) and len(counts) > 0:
                    has_hazard = any(v is not None and v > 0 for v in counts.values())
                    if has_hazard:
                        self.detected = True
                        
                        # Jab hazard mil jaye toh original size par bounding box plot karein
                        full_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        full_pil = Image.fromarray(full_rgb)
                        final_proc_img, _ = run_detection(full_pil, self.conf_threshold)
                        
                        try:
                            from ultralytics.engine.results import Results
                            if isinstance(final_proc_img, Results):
                                final_proc_img = final_proc_img.plot()
                        except ImportError:
                            pass
                            
                        if isinstance(final_proc_img, list) and len(final_proc_img) > 0:
                            try:
                                final_proc_img = final_proc_img[0].plot()
                            except:
                                pass
                        
                        if isinstance(final_proc_img, np.ndarray):
                            if len(final_proc_img.shape) == 3 and final_proc_img.shape[2] == 3:
                                final_proc_img = cv2.cvtColor(final_proc_img, cv2.COLOR_BGR2RGB)
                            final_img = Image.fromarray(final_proc_img)
                        elif isinstance(final_proc_img, Image.Image):
                            final_img = final_proc_img
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
                        break
            except Exception as e:
                print(f"Background Worker Error: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        if self.detected:
            return frame
        
        img = frame.to_ndarray(format="bgr24")
        
        # Frame ko queue mein non-blocking tareeqay se phenk dein taake video thread block na ho
        if self.frame_queue.empty():
            try:
                self.frame_queue.put_nowait(img)
            except queue.Full:
                pass
            
        return frame

def render_live_camera_mode(conf_threshold=0.50, *args, **kwargs):
    st.markdown("### Auto-Stop AI Detection & Dispatch")
    st.markdown("**Start the camera—once a hazard is detected, the camera will stop automatically and the dispatch panel will unlock!**")

    # Polling to switch UI instantly when background thread triggers detection
    if st_autorefresh is not None:
        st_autorefresh(interval=2000, key="auto_detection_poll")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None
    if "synced_to_db" not in st.session_state:
        st.session_state["synced_to_db"] = False

    conf_threshold = st.slider("Confidence Threshold (Safe: 0.50+)", 0.10, 0.90, conf_threshold, 0.05, key="auto_stop_conf")

    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        
        img_to_show = res["processed_img"]
        st.image(img_to_show, caption="Detected Hazard Result with Bounding Boxes", use_container_width=True)

        with st.container(border=True):
            st.markdown(f"**Tracking ID:** `{res['tracking_id']}`")
            summary_bullets = "".join([f"- **{str(k).capitalize()}**: {v}\n" for k, v in res['counts'].items() if v is not None])
            st.markdown("**Detected Items:**")
            st.markdown(summary_bullets if summary_bullets else "- Hazard Detected")
            
            assessment = res['assessment']
            st.markdown(f"**Priority Score:** {assessment.get('priority_score')}/100 | **Severity:** {assessment.get('severity')}")
            st.markdown(f"**Assigned Dept:** {assessment.get('assigned_dept')} | **SLA Target:** {assessment.get('sla_target')}")

        if st.session_state.get("synced_to_db", False):
            st.success("Data successfully saved and synced with Supabase database automatically!")

        if st.button("Restart Scanning", use_container_width=True):
            st.session_state["captured_result"] = None
            st.session_state["counts"] = {}
            st.session_state["synced_to_db"] = False
            st.rerun()

    else:
        ctx = webrtc_streamer(
            key="auto-stop-streamer-threaded-v5",
            video_processor_factory=AutoStopTransformer,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480}
                }, 
                "audio": False
            },
            async_processing=True,
        )

        if ctx.video_processor:
            ctx.video_processor.conf_threshold = conf_threshold

        if ctx.video_processor and ctx.video_processor.detected and ctx.video_processor.result_data:
            res = ctx.video_processor.result_data
            st.session_state["captured_result"] = res
            st.session_state["counts"] = res["counts"]  
            
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
