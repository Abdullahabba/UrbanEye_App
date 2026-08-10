import streamlit as st
import cv2
import av
import numpy as np
import time
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id

# Optimize RTC with higher bitrate for better quality
RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}],
    "iceTransportPolicy": "relay"
})

class AutoStopTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = 0.25 # Thora barha diya taake false detection kam ho
        self.frame_count = 0
        self.skip_frames = 5  # <--- MAGIC KEY: Har 5th frame process karega

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        if self.detected:
            return frame
        
        self.frame_count += 1
        img = frame.to_ndarray(format="bgr24")
        
        # Sirf har 5th frame process karo taake video smooth rahe
        if self.frame_count % self.skip_frames != 0:
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            proc_img, counts = run_detection(pil_img, self.conf_threshold)
            
            if counts and len(counts) > 0:
                self.detected = True
                
                # Plotting logic
                if hasattr(proc_img, 'plot'):
                    proc_img = proc_img.plot()
                elif isinstance(proc_img, list) and len(proc_img) > 0:
                    proc_img = proc_img[0].plot()
                
                if isinstance(proc_img, np.ndarray):
                    final_img = Image.fromarray(cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB))
                else:
                    final_img = pil_img
                
                self.result_data = {
                    "tracking_id": generate_tracking_id(),
                    "counts": counts,
                    "processed_img": final_img,
                }
        except Exception as e:
            print(f"Detection Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(conf_threshold=0.15, user_details=None, create_pdf_report_func=None):
    st.markdown("### ⚡ Real-Time Fast Detection")
    
    # Session state persistency
    if "captured_result" not in st.session_state: st.session_state["captured_result"] = None
    if "auto_stop_transformer" not in st.session_state:
        st.session_state["auto_stop_transformer"] = AutoStopTransformer()
    
    transformer = st.session_state["auto_stop_transformer"]
    transformer.conf_threshold = st.slider("Confidence", 0.05, 0.90, 0.25, 0.05)

    if st.session_state["captured_result"]:
        res = st.session_state["captured_result"]
        st.image(res["processed_img"], use_container_width=True)
        
        if st.button("🔄 Reset Camera"):
            st.session_state["captured_result"] = None
            transformer.detected = False
            st.rerun()
            
        from components.dispatch_panel import render_dispatch_panel
        render_dispatch_panel(res["tracking_id"], "Live Feed", user_details, create_pdf_report_func)
    else:
        # Optimization: Fixed 640x480 with balanced constraints
        webrtc_streamer(
            key="live-fast-feed",
            video_processor_factory=lambda: transformer,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={
                "video": {"width": 640, "height": 480, "frameRate": 30},
                "audio": False
            },
            async_processing=True,
        )

        if transformer.detected and transformer.result_data:
            st.session_state["captured_result"] = transformer.result_data
            st.rerun()
