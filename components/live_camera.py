import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_live_camera_mode(conf_threshold):
    st.markdown("### 📸 Field Camera Live Capture")
    cam_photo = st.camera_input("Take Live Photo from Camera", key="camera_input")
    
    if cam_photo and st.button("🔍 Analyze Field Snapshot", key="btn_cam"):
        img = Image.open(cam_photo)
        with st.spinner("Analyzing Camera Capture..."):
            proc_img, counts = run_detection(img, conf_threshold)
            st.session_state.update({
                "processed_img": proc_img, 
                "counts": counts, 
                "current_tracking_id": generate_tracking_id()
            })
            
    if "processed_img" in st.session_state:
        # use_column_width=True use kiya hai taake version mismatch error na aaye
        st.image(st.session_state["processed_img"], caption="Live Camera AI Result", use_column_width=True)
