import streamlit as st
import cv2
import av
import numpy as np
import time
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id

# Safe fallback for priority engine
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
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
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
        
        # Performance optimization: No heavy image processing here to keep FPS high
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        try:
            # Inference directly on raw frame for speed
            proc_img, counts = run_detection(pil_img, self.conf_threshold)
            
            if counts and len(counts) > 0:
                self.detected = True
                
                # Plotting logic for result image
                try:
                    from ultralytics.engine.results import Results
                    if isinstance(proc_img, Results):
                        proc_img = proc_img.plot()
                except: pass
                    
                if isinstance(proc_img, list) and len(proc_img) > 0:
                    try: proc_img = proc_img[0].plot()
                    except: pass
                
                if isinstance(proc_img, np.ndarray):
                    final_img = Image.fromarray(cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB))
                else:
                    final_img = pil_img
                
                tracking_id = generate_tracking_id()
                self.result_data = {
                    "tracking_id": tracking_id,
                    "counts": counts,
                    "processed_img": final_img,
                    "assessment": calculate_priority_score(counts)
                }
        except Exception as e:
            print(f"Inference Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(conf_threshold=0.15, user_details=None, create_pdf_report_func=None, *args, **kwargs):
    st.markdown("### ⚡ Live AI Detection (Fast Mode)")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None

    if "conf_threshold" not in st.session_state:
        st.session_state["conf_threshold"] = conf_threshold
    
    st.session_state["conf_threshold"] = st.slider("Confidence Threshold", 0.05, 0.90, st.session_state["conf_threshold"], 0.05)

    if "auto_stop_transformer_instance" not in st.session_state:
        st.session_state["auto_stop_transformer_instance"] = AutoStopTransformer()
    
    current_transformer = st.session_state["auto_stop_transformer_instance"]
    current_transformer.conf_threshold = st.session_state["conf_threshold"]

    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        st.image(res["processed_img"], caption="Detection Result", use_container_width=True)

        if st.button("🔄 Reset / Capture Another"):
            st.session_state["captured_result"] = None
            current_transformer.detected = False
            current_transformer.result_data = None
            st.rerun()

        from components.dispatch_panel import render_dispatch_panel
        render_dispatch_panel(res["tracking_id"], "Live Feed", user_details, create_pdf_report_func)
    else:
        # Optimized constraints: 640x480 is best for real-time detection
        ctx = webrtc_streamer(
            key="auto-stop-streamer-clean",
            video_processor_factory=lambda: current_transformer,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={
                "video": {"width": 640, "height": 480}, 
                "audio": False
            },
            async_processing=True,
        )

        if current_transformer.detected and current_transformer.result_data:
            st.session_state["captured_result"] = current_transformer.result_data
            st.rerun()

        if ctx.state.playing:
            time.sleep(0.3)
            st.rerun()
