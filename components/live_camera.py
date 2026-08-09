import streamlit as st
import cv2
import av
import numpy as np
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

def render_live_camera_mode(conf_threshold=0.2):
    st.markdown("### 🔴 Real-Time Live Continuous AI Detection")
    st.markdown("💡 **Koi snapshot ya button dabane ki zaroorat nahi!** 'Start' button dabayein, camera khulte hi live video par automatic bounding boxes aur detection shuru ho jaye gi.")

    class VideoTransformer:
        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            try:
                # Convert BGR frame to RGB PIL Image for model detection
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                
                # Run AI detection with threshold
                proc_img, counts = run_detection(pil_img, conf_threshold)
                
                # Handle YOLO Results object safely
                from ultralytics.engine.results import Results
                if isinstance(proc_img, Results):
                    proc_img = proc_img.plot()
                elif isinstance(proc_img, list) and len(proc_img) > 0:
                    try:
                        proc_img = proc_img[0].plot()
                    except:
                        pass
                
                # YOLO .plot() returns BGR numpy array
                if isinstance(proc_img, np.ndarray):
                    if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                        img = proc_img
            except Exception as e:
                # Agar kisi frame par error aaye toh original frame return ho taake stream na rukey
                pass
                
            return av.VideoFrame.from_ndarray(img, format="bgr24")

    # Real-time WebRTC Streamer
    webrtc_streamer(
        key="live-ai-continuous-detection",
        video_processor_factory=VideoTransformer,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
        async_processing=True,
    )
