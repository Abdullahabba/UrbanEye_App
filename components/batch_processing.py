import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_batch_processing_mode(conf_threshold):
    st.markdown("### 📂 Batch Image Processing")
    uploaded_files = st.file_uploader("Upload Multiple Hazard Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="batch_image_upload")
    if uploaded_files and st.button("🚀 Process All Batch Images", key="btn_batch"):
        batch_summary = {}
        cols = st.columns(min(len(uploaded_files), 3))
        for idx, file in enumerate(uploaded_files):
            img = Image.open(file)
            p_img, counts = run_detection(img, conf_threshold)
            with cols[idx % 3]:
                st.image(p_img, caption=f"Image {idx+1}", use_container_width=True)
            for k, v in counts.items():
                batch_summary[k] = batch_summary.get(k, 0) + v
        st.session_state.update({
            "counts": batch_summary, 
            "current_tracking_id": generate_tracking_id()
        })
        st.success(f"✅ Batch processing complete for {len(uploaded_files)} images!")
