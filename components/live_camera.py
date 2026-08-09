import streamlit as st
import av
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id

# WebRTC configuration (STUN servers for connection stability)
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

def render_live_camera_mode(conf_threshold=0.3):
    st.markdown("### 🚗 UrbanEye AI - HD Dashcam Live Stream")
    st.info("Resolution ko **HD (1280x720)** kar diya gaya hai aur freezing rokne ke liye smart frame-skipping active hai.")

    # Frame processor class jo video frames ko handle karegi
    class VideoTransformer(VideoTransformerBase):
        def __init__(self):
            self.frame_count = 0
            self.last_processed_img = None

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            self.frame_count += 1
            
            # Frame Skipping: Har 5th frame par AI run hoga taake HD video smooth chale
            if self.frame_count % 5 == 0:
                try:
                    detection_result = run_detection(img, conf_threshold=conf_threshold)
                    
                    if isinstance(detection_result, tuple):
                        processed_img = detection_result[0]
                    else:
                        processed_img = detection_result

                    if hasattr(processed_img, "plot"):
                        processed_img = processed_img.plot()
                    elif isinstance(processed_img, list) and len(processed_img) > 0:
                        if hasattr(processed_img[0], "plot"):
                            processed_img = processed_img[0].plot()
                        else:
                            processed_img = processed_img[0]
                    
                    if isinstance(processed_img, np.ndarray):
                        self.last_processed_img = processed_img
                    else:
                        if self.last_processed_img is None:
                            self.last_processed_img = img
                except Exception as e:
                    if self.last_processed_img is None:
                        self.last_processed_img = img

            # Output image return karna (agar processed nahi hai toh original HD frame dikhayein)
            output_img = self.last_processed_img if self.last_processed_img is not None else img
            
            return av.VideoFrame.from_ndarray(output_img, format="bgr24")

    # WebRTC Streamer component with HD constraints
    webrtc_streamer(
        key="urbaneye-hd-dashcam",
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=VideoTransformer,
        media_stream_constraints={
            "video": {
                "facingMode": "environment",
                "width": {"ideal": 1280, "min": 640, "max": 1920},
                "height": {"ideal": 720, "min": 480, "max": 1080},
                "frameRate": {"ideal": 30, "max": 30}
            }, 
            "audio": False
        },
        async_processing=True,
    )
