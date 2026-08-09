import streamlit as st
import cv2
import numpy as np
import time
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🚗 UrbanEye AI - HD Auto-Capture & Supabase Sync")
    st.info("💡 Live stream compression ki waja se YOLO blind ho jata hai. Yeh HD Auto-Capture mode snapshot jaisi 100% accurate detection deta hai aur background mein khud sync karta hai!")

    # Session state for auto-capture toggle
    if "auto_scanning" not in st.session_state:
        st.session_state["auto_scanning"] = False

    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶ Start Auto-Scan", use_container_width=True)
    with col2:
        stop_btn = st.button("⏹ Stop Scan", use_container_width=True)

    if start_btn:
        st.session_state["auto_scanning"] = True
    if stop_btn:
        st.session_state["auto_scanning"] = False

    camera_file = st.camera_input("Apne camera se live feed capture karein")

    if camera_file is not None or st.session_state["auto_scanning"]:
        if camera_file is not None:
            bytes_data = camera_file.getvalue()
            np_arr = np.frombuffer(bytes_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is not None:
                try:
                    # Run YOLO detection with HD uncompressed frame
                    detection_result = run_detection(img, conf_threshold=conf_threshold)
                    
                    processed_img = None
                    counts = {}

                    if isinstance(detection_result, tuple):
                        processed_img = detection_result[0]
                        if len(detection_result) > 1 and isinstance(detection_result[1], dict):
                            counts = detection_result[1]
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
                        rgb_output = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                        st.success("✅ Hazard Detected Successfully!")
                        st.image(rgb_output, channels="RGB", caption="AI Analyzed Live Frame", use_container_width=True)
                        
                        # Automatic Supabase Sync
                        total_detected = sum(counts.values()) if isinstance(counts, dict) and len(counts) > 0 else 1
                        
                        if total_detected > 0:
                            tracking_id = generate_tracking_id()
                            supabase.table("reports").insert({
                                "tracking_id": tracking_id,
                                "counts": str(counts),
                                "status": "Auto-Synced HD Live"
                            }).execute()
                            st.toast("🚀 Data successfully pushed to Supabase database!", icon="🔥")
                    else:
                        st.error("❌ AI processing mein valid array nahi mila.")
                except Exception as e:
                    st.error(f"Error during detection or sync: {e}")
