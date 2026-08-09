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
try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

# --- 1. App State Management ---
# Hum session state use karein ge taake video stream se bahar aakar location ki details le sakein.
def initialize_session_states():
    if "live_scan_state" not in st.session_state:
        st.session_state["live_scan_state"] = "IDLE"  # IDLE, DETECTED, SYNCING
    if "live_last_counts" not in st.session_state:
        st.session_state["live_last_counts"] = {}
    if "live_last_tracking_id" not in st.session_state:
        st.session_state["live_last_tracking_id"] = None
    if "live_annotated_frame" not in st.session_state:
        st.session_state["live_annotated_frame"] = None

# --- 2. Non-Blocking Video Transformer ---
class HazardDetectionTransformer(VideoTransformerBase):
    def __init__(self):
        # Latest frame buffers
        self.latest_frame = None
        self.annotated_frame = None
        self.lock = threading.Lock()
        self.running = True
        
        # Cooldown timer taake database spamm na ho
        self.last_auto_dispatch_time = 0
        
    def _run_ai_inference(self, frame_bgr):
        try:
            # YOLO model run karein (heavy processing)
            detection_result = run_detection(frame_bgr, conf_threshold=0.25)
            
            processed_img = None
            counts = {}

            if isinstance(detection_result, tuple):
                processed_img = detection_result[0]
                if len(detection_result) > 1 and isinstance(detection_result[1], dict):
                    counts = detection_result[1]
            else:
                processed_img = detection_result

            # Ultralytics Results ko plot/ndarray mein convert karna
            if hasattr(processed_img, "plot"):
                processed_img = processed_img.plot()
            elif isinstance(processed_img, list) and len(processed_img) > 0:
                if hasattr(processed_img[0], "plot"):
                    processed_img = processed_img[0].plot()
                else:
                    processed_img = processed_img[0]
            
            if isinstance(processed_img, np.ndarray):
                # Lock current annotated frame
                with self.lock:
                    self.annotated_frame = processed_img
                    
                # --- CHECK FOR HAZARD AND AUTO-DISPATCH ---
                total_detected = sum(counts.values()) if isinstance(counts, dict) else 0
                
                if total_detected > 0:
                    # Agar pehlay se syncing mode mein nahi hai aur cooldown khatam hai
                    if st.session_state["live_scan_state"] == "IDLE":
                        current_time = time.time()
                        if current_time - self.last_auto_dispatch_time > 15: # 15 seconds cooldown
                            self.last_auto_dispatch_time = current_time
                            
                            # Update Session States to trigger Location Input Phase
                            st.session_state["live_scan_state"] = "DETECTED"
                            st.session_state["live_last_counts"] = counts
                            st.session_state["live_last_tracking_id"] = generate_tracking_id()
                            
                            # Save annotated frame for later review
                            st.session_state["live_annotated_frame"] = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                            
        except Exception as e:
            print(f"AI Worker Error: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # WebRTC recv loop runs here. Keep it fast.
        img = frame.to_ndarray(format="bgr24")
        
        # Agar IDLE hai to detection run karo (lekin sync nahi honay dena yahan)
        if st.session_state["live_scan_state"] == "IDLE":
            # AI inference ko alag thread mein chalanay ki zaroorat nahi kyunki 
            # webrtc_streamer(async_processing=True) khud aik thread pool use karta hai.
            # Lekin performance ensure karne ke liye hum har frame par nahi challayein ge.
            # (Is example mein ham directly challa rahe hain, agar freeze ho to batana).
            self._run_ai_inference(img)
            current_output = img # Initially show raw
            
            # Agar inference ne annotated frame update kar di hai, to show it
            with self.lock:
                if self.annotated_frame is not None:
                    current_output = self.annotated_frame

        else:
            # Agar DETECTED ya SYNCING mode mein hai, to video band kar dein
            # Hum black screen return karein ge taake user ko pata chalay ke 
            # system next phase mein chala gaya hai.
            current_output = np.zeros_like(img)
            
        return av.VideoFrame.from_ndarray(current_output, format="bgr24")

    def __del__(self):
        self.running = False

# --- 3. Main Render Function ---
def render_live_camera_mode(conf_threshold=None):
    initialize_session_states()
    
    st.markdown("### 🚀 UrbanEye AI - Auto-Live Scanner")
    
    # --- PHASE 1: IDLE / Scanning ---
    if st.session_state["live_scan_state"] == "IDLE":
        st.info("📡 Live scanner active hai. Samne aane wale hazards detect hon ge aur khud ba khud sync phase shuru ho jaye ga.")
        
        # STUN servers for connection
        RTC_CONFIG = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
        
        webrtc_streamer(
            key="urbaneye-auto-live",
            rtc_configuration=RTC_CONFIG,
            video_processor_factory=HazardDetectionTransformer,
            media_stream_constraints={
                "video": {"width": {"ideal": 640}, "height": {"ideal": 360}},
                "audio": False
            },
            async_processing=True,  # Must be True for smooth streaming
        )
        
    # --- PHASE 2: DETECTED (Get Location & Confirm) ---
    elif st.session_state["live_scan_state"] == "DETECTED":
        st.success("✅ Hazard detect ho gaya! Ab verification aur sync ki zaroorat hai.")
        
        tracking_id = st.session_state["live_last_tracking_id"]
        counts = st.session_state["live_last_counts"]
        
        # (Logic copied from Dispatch.py)
        with st.container(border=True):
            st.markdown(f"#### 📋 Incident Details (ID: `{tracking_id}`)")
            
            # Detections Summary
            summary_bullets = ""
            for k, v in counts.items():
                summary_bullets += f"- **{k.capitalize()}**: {v}\n"
            st.markdown("**Detected
