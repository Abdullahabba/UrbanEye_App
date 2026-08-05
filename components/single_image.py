import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_single_image_mode(conf_threshold):
    st.markdown("### 🖼️ Single Image Inspection")
    
    uploaded_file = st.file_uploader("Upload Hazard Snapshot", type=["jpg", "jpeg", "png"], key="single_image_upload")
    
    # Clear previous results if a new file is uploaded or removed
    if uploaded_file is None:
        if "processed_img" in st.session_state:
            del st.session_state["processed_img"]
        if "counts" in st.session_state:
            del st.session_state["counts"]
        st.info("💡 Please upload an image using the uploader above to start the AI inspection.")
        return

    try:
        img = Image.open(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error opening image file: {e}")
        return

    c1, c2 = st.columns(2)
    
    with c1:
        if img is not None:
            st.image(img, caption="Original Input", use_container_width=True)

    if st.button("🔍 Run AI Detection", key="btn_single"):
        with st.spinner("Analyzing with YOLO Model..."):
            processed_img, counts = run_detection(img, conf_threshold)
            st.session_state.update({
                "processed_img": processed_img, 
                "counts": counts, 
                "current_tracking_id": generate_tracking_id()
            })

    # Safe check: Render only when the processed image is valid
    if st.session_state.get("processed_img") is not None:
        with c2:
            st.image(st.session_state["processed_img"], caption="YOLO AI Detection Result", use_container_width=True)
