import streamlit as st
import av
import cv2
import numpy as np
import time
import threading
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

# Multiple robust STUN servers for instant connection stability
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
            {"urls": ["stun:stun.services.mozilla.com"]}
        ]
    }
)

def render_live_camera_mode(conf_threshold=0.3):
    st.markdown("### 🚗 UrbanEye AI - Non-Blocking Live Stream")
    st.info("Live stream ko non-blocking background architecture par shift kar diya gaya hai taake camera bilkul freeze na ho.")

    class NonBlockingVideoTransformer(VideoTransformerBase):
        def __init__(self):
            self.latest_frame = None
            self.annotated_frame = None
            self.lock = threading.Lock()
            self.running = True
            self.last_db_push_time = 0

            # Alag background thread start karna taake video stream block na ho
            self.thread = threading.Thread(target=self._ai_worker, daemon=True)
            self.thread.start()

        def _ai_worker(self):
            while self.running:
                frame_to_process = None
                with self.lock:
                    if self.latest_frame is not None:
                        frame_to_process = self.latest_frame.copy()
                        self.latest_frame = None  # Frame consume ho gaya

                if frame_to_process is not None:
                    try:
                        detection_result = run_detection(frame_to_process, conf_threshold=conf_threshold)
                        
                        if isinstance(detection_result, tuple):
                            processed_img, counts = detection_result
                        else:
                            processed_img = detection_result
                            counts = {}

                        if hasattr(processed_img, "plot"):
                            processed_img = processed_img.plot()
                        elif isinstance(processed_img, list) and len(processed_img) > 0:
                            if hasattr(processed_img[0], "plot"):
                                processed_img = processed_img[0].plot()
                            else:
                                processed_img = processed_img[0]

                        if isinstance(processed_img, np.ndarray):
                            with self.lock:
                                self.annotated_frame = processed_img

                            # Background Supabase sync check
                            total_detected = sum(counts.values()) if isinstance(counts, dict) else 1
                            if total_detected > 0:
                                curr_time = time.time()
                                if curr_time - self.last_db_push_time > 15:
                                    self.last_db_push_time = curr_time
                                    try:
                                        tracking_id = generate_tracking_id()
                                        supabase.table("reports").insert({
                                            "tracking_id": tracking_id,
                                            "counts": str(counts),
                                            "status": "Auto-Synced Live"
                                        }).execute()
                                    except Exception as db_err:
                                        pass
                    except Exception as e:
                        pass
                else:
                    time.sleep(0.01)

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            
            # Non-blocking frame passing
            with self.lock:
                self.latest_frame = img
                current_output = self.annotated_frame if self.annotated_frame is not None else img

            return av.VideoFrame.from_ndarray(current_output, format="bgr24")

        def __del__(self):
            self.running = False

    # WebRTC Streamer with lightweight constraints
    webrtc_streamer(
        key="urbaneye-nonblocking-dashcam",
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=NonBlockingVideoTransformer,
        media_stream_constraints={
            "video": {
                "facingMode": "environment",
                "width": {"ideal": 640},
                "height": {"ideal": 360},
                "frameRate": {"ideal": 15}
            }, 
            "audio": False
        },
        async_processing=True,
    )
