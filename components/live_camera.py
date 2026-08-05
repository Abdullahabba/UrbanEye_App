import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_live_camera_mode(conf_threshold):
    st.markdown("### 📸 Live Camera Capture Mode")
    st.caption("Capture a snapshot from your device camera for real-time hazard inspection.")

    camera_image = st.camera_input("Take a snapshot", key="live_camera_input")

    if camera_image is not None:
        try:
            img = Image.open(camera_image)
        except Exception as e:
            st.error(f"❌ Error loading camera image: {e}")
            return

        c1, c2 = st.columns(2)
        
        with c1:
            # FIX: use_column_width=True use kiya gaya hai
            st.image(img, caption="Captured Snapshot", use_column_width=True)

        if st.button("🔍 Run Live AI Detection", key="btn_live_cam"):
            with st.spinner("Analyzing camera frame with YOLO..."):
                processed_img, counts = run_detection(img, conf_threshold)
                tracking_id = generate_tracking_id()
                
                st.session_state.update({
                    "processed_img": processed_img,
                    "counts": counts,
                    "current_tracking_id": tracking_id
                })
                
                if isinstance(processed_img, Image.Image):
                    st.session_state["captured_images"] = [processed_img]

        # Safe check: Sirf tabhi render karein jab processed image maujood ho
        if st.session_state.get("processed_img") is not None:
            with c2:
                # FIX: use_column_width=True use kiya gaya hai
                st.image(st.session_state["processed_img"], caption="Live Camera AI Result", use_column_width=True)
    else:
        st.info("💡 Please click a picture using your camera widget above to start inspection.")
