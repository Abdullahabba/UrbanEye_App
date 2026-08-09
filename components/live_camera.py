import streamlit as st
import cv2
import av
import numpy as np
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

try:
    from utils.priority_engine import calculate_priority_score
except Exception:
    def calculate_priority_score(counts):
        return {
            "priority_score": 65,
            "severity": "Medium",
            "assigned_dept": "Municipal Operations",
            "sla_target": "24 Hours"
        }

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

def render_live_camera_mode(conf_threshold=0.15):
    st.markdown("### 🔴 Real-Time Live Continuous AI Detection")
    st.markdown("💡 **Koi snapshot ya button dabane ki zaroorat nahi!** Camera start karein, live video feed par foran bounding boxes aur detection shuru ho jaye gi.")

    # Confidence Threshold Slider (Default: 0.15)
    conf_threshold = st.slider("Confidence Threshold", 0.05, 0.90, 0.15, 0.05, key="live_conf_slider")

    class VideoTransformer:
        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            try:
                # Convert BGR frame to RGB PIL Image for model detection
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                
                # Run AI detection with threshold 0.15
                proc_img, counts = run_detection(pil_img, conf_threshold)
                
                # Save counts to session state safely for live UI updates
                if counts:
                    st.session_state["live_detected_counts"] = counts
                
                # Handle YOLO Results object safely
                from ultralytics.engine.results import Results
                if isinstance(proc_img, Results):
                    proc_img = proc_img.plot()
                elif isinstance(proc_img, list) and len(proc_img) > 0:
                    try:
                        proc_img = proc_img[0].plot()
                    except:
                        pass
                
                # YOLO .plot() returns BGR numpy array with drawn bounding boxes
                if isinstance(proc_img, np.ndarray):
                    if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                        img = proc_img
            except Exception as e:
                print(f"WebRTC Detection Error: {e}")
                
            return av.VideoFrame.from_ndarray(img, format="bgr24")

    # Real-time WebRTC Streamer (No snapshot required)
    webrtc_streamer(
        key="live-ai-continuous-detection",
        video_processor_factory=VideoTransformer,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
        async_processing=True,
    )

    # Live UI Section for Detected Results below the video feed
    st.markdown("---")
    st.markdown("### 📋 Live Detection Dashboard")
    
    if "live_detected_counts" in st.session_state and st.session_state["live_detected_counts"]:
        counts = st.session_state["live_detected_counts"]
        
        summary_bullets = "".join([f"- **{str(k).capitalize()}**: {v}\n" for k, v in counts.items() if v is not None])
        st.markdown(summary_bullets)
        
        # Optional quick sync button if user wants to save current detected frame state to Supabase
        if st.button("💾 Save Current Hazard to Database", use_container_width=True):
            tracking_id = generate_tracking_id()
            assessment = calculate_priority_score(counts)
            score = assessment["priority_score"]
            severity = assessment["severity"]
            dept = assessment["assigned_dept"]
            sla = assessment["sla_target"]

            hazard_list = [f"{str(k).capitalize()} ({v})" for k, v in counts.items() if v is not None]
            main_hazard = ", ".join(hazard_list) if hazard_list else "Municipal Hazard"

            try:
                payload = {
                    "tracking_id": tracking_id,
                    "hazard": main_hazard,
                    "issue_type": main_hazard,
                    "severity": f"{severity} ({score}/100)",
                    "status": "Active / Dispatched",
                    "location_name": "Live Camera Feed",
                    "latitude": 31.5204,
                    "longitude": 74.3587,
                    "assigned_dept": dept,
                    "sla_target": sla
                }
                supabase.table("reports").insert(payload).execute()
                st.success(f"✅ Successfully saved! Tracking ID: `{tracking_id}`")
            except Exception as db_err:
                st.error(f"❌ Supabase Error: {db_err}")
    else:
        st.info("🔍 Camera ke samne hazard layein—detection foran screen par nazar aye gi.")
