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

# Multiple robust STUN servers for connection stability
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

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🚗 UrbanEye AI - HD Live Auto-Detection & Supabase Sync")
    st.info("🔥 Live stream ab HD resolution par active hai. Snapshot ki tarah ab live stream par bhi hazards detect honge aur background mein Supabase sync hoga!")

    class HDNonBlockingVideoTransformer(VideoTransformerBase):
        def __init__(self):
            self.latest_frame = None
            self.annotated_frame = None
            self.lock = threading.Lock()
            self.running = True
            self.last_db_push_time = 0

            # Background thread for AI processing without freezing live stream
            self.thread = threading.Thread(target=self._ai_worker, daemon=True)
            self.thread.start()

        def _ai_worker(self):
            while self.running:
                frame_to_process = None
                with self.lock:
                    if self.latest_frame is not None:
                        frame_to_process = self.latest_frame.copy()
                        self.latest_frame = None  # Consume frame

                if frame_to_process is not None:
                    try:
                        # Run YOLO detection with confidence threshold
                        try:
                            detection_result = run_detection(frame_to_process, conf_threshold=conf_threshold)
                        except TypeError:
                            detection_result = run_detection(frame_to_process)
                        
                        processed_img = None
                        counts = {}

                        if isinstance(detection_result, tuple):
                            processed_img = detection_result[0]
                            if len(detection_result) > 1 and isinstance(detection_result[1], dict):
                                counts = detection_result[1]
                        else:
                            processed_img = detection_result

                        # Handle Ultralytics YOLO Results object or list
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

                            # Automatic Supabase sync if hazard detected
                            total_detected = sum(counts.values()) if isinstance(counts, dict) and len(counts) > 0 else 0
                            
                            if total_detected > 0:
                                curr_time = time.time()
                                if curr_time - self.last_db_push_time > 12:  # 12 seconds cooldown
                                    self.last_db_push_time = curr_time
                                    try:
                                        tracking_id = generate_tracking_id()
                                        supabase.table("reports").insert({
                                            "tracking_id": tracking_id,
                                            "counts": str(counts),
                                            "status": "Auto-Synced Live HD"
                                        }).execute()
                                        print(f"Successfully auto-synced live detection to Supabase: {counts}")
                                    except Exception as db_err:
                                        print(f"Supabase Sync Error: {db_err}")
                    except Exception as e:
                        print(f"AI Live Worker Error: {e}")
                else:
                    time.sleep(0.01)

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            
            with self.lock:
                self.latest_frame = img
                current_output = self.annotated_frame if self.annotated_frame is not None else img

            return av.VideoFrame.from_ndarray(current_output, format="bgr24")

        def __del__(self):
            self.running = False

    # WebRTC Streamer configured with HD resolution for crystal clear YOLO detections
    webrtc_streamer(
        key="urbaneye-hd-live-stream",
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=HDNonBlockingVideoTransformer,
        media_stream_constraints={
            "video": {
                "facingMode": "environment",
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
                "frameRate": {"ideal": 20}
            }, 
            "audio": False
        },
        async_processing=True,
    )
