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
    st.info("Live video streaming active hai. Confidence threshold **30% (0.3)** set kar diya gaya hai.")

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
                processed_img, counts = run_detection(img, conf_threshold=conf_threshold)
                
                # Agar YOLO Results object ya list aaye toh usko plot/ndarray mein convert karna
                try:
                    from ultralytics.engine.results import Results
                    if isinstance(processed_img, Results):
                        processed_img = processed_img.plot()
                except:
                    pass
                    
                if isinstance(processed_img, list) and len(processed_img) > 0:
                    try:
                        processed_img = processed_img[0].plot()
                    except:
                        pass
                
                if isinstance(processed_img, np.ndarray):
                    self.last_processed_img = processed_img
                else:
                    self.last_processed_img = img

            # Agar processed image mojood hai toh wo dikhayein, warna direct frame
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
