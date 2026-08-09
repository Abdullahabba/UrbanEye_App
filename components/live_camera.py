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
    st.markdown("### 🚗 UrbanEye AI - Live Auto-Detection & Supabase Sync")
    st.info("Live stream active hai. Database sync ab background thread mein ho rahi hai taake camera bilkul freeze na ho.")

    class VideoTransformer(VideoTransformerBase):
        def __init__(self):
            self.frame_count = 0
            self.last_processed_img = None
            self.last_db_push_time = 0  # Cooldown timer

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            self.frame_count += 1
            
            # Frame Skipping: Har 8th frame par AI run hoga taake performance smooth rahay
            if self.frame_count % 8 == 0:
                try:
                    detection_result = run_detection(img, conf_threshold=conf_threshold)
                    
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
                        self.last_processed_img = processed_img
                        
                        total_detected = sum(counts.values()) if isinstance(counts, dict) else 1
                        
                        if total_detected > 0:
                            current_time = time.time()
                            # Har 15 seconds mein aik baar background mein Supabase sync hoga
                            if current_time - self.last_db_push_time > 15:
                                self.last_db_push_time = current_time
                                
                                # Background thread taake live video freeze na ho
                                def background_supabase_sync(c_data):
                                    try:
                                        tracking_id = generate_tracking_id()
                                        supabase.table("reports").insert({
                                            "tracking_id": tracking_id,
                                            "counts": str(c_data),
                                            "status": "Auto-Synced Live"
                                        }).execute()
                                    except Exception as db_err:
                                        pass

                                threading.Thread(target=background_supabase_sync, args=(counts,), daemon=True).start()
                    else:
                        if self.last_processed_img is None:
                            self.last_processed_img = img
                except Exception as e:
                    if self.last_processed_img is None:
                        self.last_processed_img = img

            output_img = self.last_processed_img if self.last_processed_img is not None else img
            return av.VideoFrame.from_ndarray(output_img, format="bgr24")

    # WebRTC Streamer with lightweight constraints to prevent any freezing
    webrtc_streamer(
        key="urbaneye-bulletproof-dashcam",
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=VideoTransformer,
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
