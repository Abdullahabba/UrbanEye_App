import tempfile
import cv2
import numpy as np
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id
import streamlit as st
import pandas as pd

def render_video_stream_mode(conf_threshold):
    st.markdown("### 🎥 Video Stream Inspection")
    uploaded_video = st.file_uploader("Upload CCTV or Drone Footage", type=["mp4", "avi", "mov"], key="video_upload")
    
    if uploaded_video and st.button("🎥 Start Video Analysis", key="btn_video"):
        # Fresh captured images list & tracking ID
        st.session_state["captured_images"] = []
        tracking_id = generate_tracking_id()
        st.session_state["current_tracking_id"] = tracking_id

        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())
        cap = cv2.VideoCapture(tfile.name)
        st_frame = st.empty()
        v_counts, last_frame, frame_count = {}, None, 0

        with st.spinner("Processing Video Stream Frame by Frame..."):
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: 
                    break
                frame_count += 1
                
                # Har 5th frame process karein
                if frame_count % 5 != 0: 
                    continue
                
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                proc_frame, counts = run_detection(pil_img, conf_threshold)
                last_frame = proc_frame
                st_frame.image(proc_frame, caption=f"Live Frame (Frame {frame_count})", use_container_width=True)
                
                # Counts tallying
                if isinstance(counts, dict):
                    for k, v in counts.items():
                        v_counts[k] = v_counts.get(k, 0) + v

                # Frame capture storage
                if isinstance(proc_frame, Image.Image):
                    frame_to_store = np.array(proc_frame)
                else:
                    frame_to_store = proc_frame
                
                if len(st.session_state["captured_images"]) < 6:
                    st.session_state["captured_images"].append(frame_to_store)

        cap.release()
        
        # Save counts and tracking ID to session state
        st.session_state.update({
            "counts": v_counts, 
            "current_tracking_id": tracking_id
        })
        
        if last_frame is not None: 
            st.session_state["processed_img"] = last_frame

        # Payload definition
        detected_hazard_name = list(v_counts.keys())[0] if v_counts else "Video Stream Hazard"
        payload = {
            "tracking_id": tracking_id,
            "issue_type": str(detected_hazard_name),
            "severity": "HIGH" if v_counts else "MEDIUM",
            "sla_target": "12 Hours",
            "status": "Pending Dispatch",
            "assigned_dept": "Road & Infrastructure",
            "latitude": 31.5204,
            "longitude": 74.3587,
            "location_name": "CCTV / Drone Surveillance Feed",
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
        }

        # 🛡️ ROBUST LEDGER INITIALIZATION & SAFE CHECK
        if "incident_ledger" not in st.session_state or not isinstance(st.session_state["incident_ledger"], pd.DataFrame):
            st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
        
        existing_ledger = st.session_state["incident_ledger"]
        
        # Check if 'tracking_id' column exists to prevent KeyError
        if "tracking_id" not in existing_ledger.columns:
            st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
            existing_ledger = st.session_state["incident_ledger"]

        # Safely append if tracking_id doesn't already exist
        if tracking_id not in existing_ledger["tracking_id"].values:
            new_row_df = pd.DataFrame([payload])
            st.session_state["incident_ledger"] = pd.concat([existing_ledger, new_row_df], ignore_index=True)

        st.success(f"✅ Video Analysis Completed! Tracking ID `{tracking_id}` registered successfully.")
