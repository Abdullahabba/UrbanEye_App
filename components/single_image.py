import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_single_image_mode(conf_threshold):
    st.markdown("### 🖼️ Single Image Inspection")
    uploaded_file = st.file_uploader("Upload Hazard Snapshot", type=["jpg", "jpeg", "png"], key="single_image_upload")
    if uploaded_file:
        img = Image.open(uploaded_file)
        c1, c2 = st.columns(2)
        with c1:
            st.image(img, caption="Original Input", use_container_width=True)
        if st.button("🔍 Run AI Detection", key="btn_single"):
            with st.spinner("Analyzing with YOLO Model..."):
                processed_img, counts = run_detection(img, conf_threshold)
                st.session_state.update({
                    "processed_img": processed_img, 
                    "counts": counts, 
                    "current_tracking_id": generate_tracking_id()
                })
        if "processed_img" in st.session_state:
            with c2:
                st.image(st.session_state["processed_img"], caption="YOLO AI Detection Result", use_container_width=True)
