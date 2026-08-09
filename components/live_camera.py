import streamlit as st
import av
import cv2
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id

# WebRTC configuration (STUN servers for connection stability)
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

def render_live_camera_mode(conf_threshold=0.7):
    st.markdown("### 🚗 UrbanEye AI - Dashcam Live Stream Mode")
    st.info("Live video streaming active hai. AI automatic 70% confidence par issues detect kar raha hai.")

    # Frame processor class jo har video frame ko pakar kar YOLO model chalayegi
    class VideoTransformer(VideoTransformerBase):
        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            
            # Yahan 70% confidence (0.7) fix kar diya hai ya passed threshold use hoga
            processed_img, counts = run_detection(img, conf_threshold=0.7)
            
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
            
            # Agar processed image ndarray hai toh wapas VideoFrame mein badal dein
            if not isinstance(processed_img, np.ndarray):
                processed_img = img # Fallback agar format match na ho
                
            return av.VideoFrame.from_ndarray(processed_img, format="bgr24")

    # WebRTC Streamer component jo browser ka camera direct on kar dega bina kisi button ke
    webrtc_streamer(
        key="urbaneye-dashcam",
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=VideoTransformer,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True,
    )
