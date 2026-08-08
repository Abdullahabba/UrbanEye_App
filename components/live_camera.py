import streamlit as st
from PIL import Image
import numpy as np
import cv2
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_live_camera_mode(conf_threshold):
    st.markdown("### 📸 Field Camera Live Capture")
    
    cam_photo = st.camera_input("Take Live Photo from Camera", key="camera_input")
    
    if cam_photo:
        img = Image.open(cam_photo)
        with st.spinner("Analyzing Camera Capture with YOLOv8..."):
            proc_img, counts, raw_detections = run_detection(img, conf_threshold)
            
            try:
                from ultralytics.engine.results import Results
                if isinstance(proc_img, Results):
                    proc_img = proc_img.plot()
            except ImportError:
                pass
                
            if isinstance(proc_img, list) and len(proc_img) > 0:
                try:
                    proc_img = proc_img[0].plot()
                except:
                    pass
            
            if isinstance(proc_img, np.ndarray):
                if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                    proc_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB)
                proc_img = Image.fromarray(proc_img)
            
            high_conf_detections = [d for d in raw_detections if d.get("confidence", 0) >= conf_threshold] if raw_detections else []
            
            tracking_id = generate_tracking_id()
            
            st.session_state.update({
                "processed_img": proc_img, 
                "counts": counts, 
                "raw_detections": high_conf_detections,
                "current_tracking_id": tracking_id
            })
            
            if high_conf_detections:
                st.success(f"🎯 Target Detected! High confidence issue(s) found. Tracking ID: {tracking_id}")
            else:
                st.info("ℹ️ No target issues found above the confidence threshold.")
          
    if "processed_img" in st.session_state and st.session_state["processed_img"] is not None:
        img_to_show = st.session_state["processed_img"]
        
        if isinstance(img_to_show, np.ndarray):
            if len(img_to_show.shape) == 3 and img_to_show.shape[2] == 3:
                img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_BGR2RGB)
            img_to_show = Image.fromarray(img_to_show)
            
        st.image(img_to_show, caption="Live Camera AI Result", use_container_width=True)
        
        if st.session_state.get("raw_detections"):
            if st.button("🚀 Proceed to Dispatch Report", type="primary", use_container_width=True):
                st.session_state["navigate_to_report"] = True
                st.rerun()
