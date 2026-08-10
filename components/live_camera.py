import streamlit as st
import numpy as np
from PIL import Image
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# Safe fallback for priority engine
try:
    from utils.priority_engine import calculate_priority_score
except Exception:
    def calculate_priority_score(counts):
        return {
            "priority_score": 50,
            "severity": "Medium",
            "assigned_dept": "Municipal Operations",
            "sla_target": "24 Hours"
        }

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}]}
)

class AutoStopTransformer:
    def __init__(self, model, conf_threshold):
        self.model = model
        self.conf_threshold = conf_threshold
        self.detected = False
        self.result_image = None
        self.counts = {}

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        # Agar pehle hi hazard detect ho chuka hai, toh mazeed processing rok dein (Auto-Stop)
        if self.detected:
            return av.VideoFrame.from_ndarray(self.result_image, format="bgr24")

        # YOLO Inference
        try:
            results = self.model(img, conf=self.conf_threshold, verbose=False)
            res = results[0]
            
            # Check if any detections found
            if len(res.boxes) > 0:
                self.detected = True
                
                # Plot bounding boxes on image
                res_plotted = res.plot() # BGR numpy array
                self.result_image = res_plotted
                
                # Count detected classes
                current_counts = {}
                for box in res.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = self.model.names[cls_id]
                    current_counts[cls_name] = current_counts.get(cls_name, 0) + 1
                self.counts = current_counts
                
                return av.VideoFrame.from_ndarray(res_plotted, format="bgr24")
        except Exception as e:
            print(f"Inference error in WebRTC stream: {e}")

        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(model, conf_threshold, user_details, create_pdf_report_func, render_dispatch_panel_func):
    st.markdown("### 🔴 Live Camera Auto-Detection Feed")
    st.markdown("System will automatically capture the frame and lock the stream as soon as a municipal hazard is detected.")

    # Session state initialization for live capture tracking
    if "live_detected_state" not in st.session_state:
        st.session_state["live_detected_state"] = False

    # WebRTC Streamer Integration
    webrtc_ctx = webrtc_streamer(
        key="urbaneye_live_camera",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=lambda: AutoStopTransformer(model, conf_threshold),
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # Check if video processor has detected a hazard
    if webrtc_ctx.video_processor:
        if webrtc_ctx.video_processor.detected and not st.session_state["live_detected_state"]:
            st.session_state["live_detected_state"] = True
            
            # Save detected counts and captured frame to main session state
            st.session_state["counts"] = webrtc_ctx.video_processor.counts
            
            if webrtc_ctx.video_processor.result_image is not None:
                # Convert BGR numpy array to PIL Image
                rgb_img = cv2_to_pil(webrtc_ctx.video_processor.result_image)
                st.session_state["processed_img"] = rgb_img
                st.session_state["captured_images"] = [rgb_img]
            
            # Generate unique tracking ID for this live capture
            import random
            st.session_state["active_live_tracking_id"] = f"LIVE-{random.randint(10000, 99999)}"
            st.rerun()

    # Agar hazard detect ho chuka hai, toh live stream rok kar direct Dispatch Panel ko call karein
    if st.session_state.get("live_detected_state", False):
        st.success("🎯 **Hazard Automatically Captured from Live Stream!**")
        
        tracking_id = st.session_state.get("active_live_tracking_id", "LIVE-99999")
        
        # Call the unified Dispatch Panel component
        render_dispatch_panel_func(
            tracking_id=tracking_id,
            manual_loc_name="Live Camera Stream Location",
            user_details=user_details,
            create_pdf_report_func=create_pdf_report_func
        )

def cv2_to_pil(cv2_img):
    import cv2
    rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_img)
