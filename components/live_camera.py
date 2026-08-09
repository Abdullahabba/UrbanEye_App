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
    st.markdown("### 🚗 UrbanEye AI - Dashcam Live Stream Mode")
    st.info("Live video streaming active hai. Detections ko mazeed stable aur fast kar diya gaya hai.")

    # Frame processor class jo video frames ko handle karegi
    class VideoTransformer(VideoTransformerBase):
        def __init__(self):
            self.frame_count = 0
            self.last_processed_img = None

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            self.frame_count += 1
            
            # Frame Skipping: Har 3rd frame par YOLO run hoga (0.3 confidence ke sath)
            if self.frame_count % 3 == 0:
                try:
                    # run_detection se result hasil karna
                    detection_result = run_detection(img, conf_threshold=conf_threshold)
                    
                    # Agar tuple mile (jaise (image, counts)) toh pehla item uthayein
                    if isinstance(detection_result, tuple):
                        processed_img = detection_result[0]
                    else:
                        processed_img = detection_result

                    # Agar YOLO Results object ho toh .plot() call karein
                    if hasattr(processed_img, "plot"):
                        processed_img = processed_img.plot()
                    elif isinstance(processed_img, list) and len(processed_img) > 0:
                        if hasattr(processed_img[0], "plot"):
                            processed_img = processed_img[0].plot()
                        else:
                            processed_img = processed_img[0]
                    
                    # Confirm karein ke output valid numpy array hai
                    if isinstance(processed_img, np.ndarray):
                        self.last_processed_img = processed_img
                    else:
                        if self.last_processed_img is None:
                            self.last_processed_img = img
                except Exception as e:
                    # Agar koi bhi error aaye toh live feed freeze na ho, original frame chalay
                    if self.last_processed_img is None:
                        self.last_processed_img = img

            # Output image return karna
            output_img = self.last_processed_img if self.last_processed_img is not None else img
            
            return av.VideoFrame.from_ndarray(output_img, format="bgr24")

    # WebRTC Streamer component with optimized constraints
    webrtc_streamer(
        key="urbaneye-dashcam",
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=VideoTransformer,
        media_stream_constraints={
            "video": {
                "facingMode": "environment",
                "width": {"ideal": 640},
                "height": {"ideal": 480},
                "frameRate": {"ideal": 15}
            }, 
            "audio": False
        },
        async_processing=True,
    )
