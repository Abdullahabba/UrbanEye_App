import streamlit as st
import numpy as np
from PIL import Image

def render_live_camera_mode(model_or_conf=None):
    st.subheader("📸 Instant Snapshot AI Detection & Dispatch")
    st.markdown("Live WebRTC connection issues se bachne ke liye yeh snapshot mode sab se stable aur fast hai. Tasweer capture karein, model foran hazard detect kar ke report generate kar dega!")

    # Smart Model Finder
    model = None
    if hasattr(model_or_conf, "predict"):
        model = model_or_conf
    if model is None:
        for key, value in st.session_state.items():
            if hasattr(value, "predict"):
                model = value
                break
    if model is None:
        try:
            from ultralytics import YOLO
            for weight in ["best.pt", "yolov8n.pt", "model.pt"]:
                try:
                    model = YOLO(weight)
                    break
                except Exception:
                    continue
        except ImportError:
            pass

    if model is None:
        st.error("⚠️ YOLO model load nahi mila. Baraye meharbani model weights file check karein.")
        return

    tracking_id = st.session_state.get("current_tracking_id", "TRK-9999")
    user_details = st.session_state.get("user", {"email": "officer@urbaneye.ai"})
    
    try:
        from utils.pdf_generator import create_pdf_report as create_pdf_report_func
    except ImportError:
        create_pdf_report_func = None

    # Built-in Streamlit Camera Input
    img_file_buffer = st.camera_input("Apne device ka camera use kar ke tasweer capture karein")

    if img_file_buffer is not None:
        image = Image.open(img_file_buffer)
        img_array = np.array(image)

        with st.spinner("🔍 AI Model hazards detect kar raha hai..."):
            results = model(img_array, conf=0.25, verbose=False)
            annotated_img = results[0].plot()

            # Extract counts for dispatch
            boxes = results[0].boxes
            current_counts = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                current_counts[cls_name] = current_counts.get(cls_name, 0) + 1

            st.session_state["counts"] = current_counts
            st.session_state["processed_img"] = annotated_img

        # Display the processed image using compatible use_column_width parameter
        st.image(annotated_img, channels="BGR", caption="Processed Hazard Detection", use_column_width=True)

        if current_counts:
            st.success("🚨 **Hazard Detected Successfully!** Instant dispatch summary and report panel generated below.")
            
            from components.dispatch_panel import render_dispatch_panel
            render_dispatch_panel(
                tracking_id=tracking_id,
                manual_loc_name="Snapshot Camera Location",
                user_details=user_details,
                create_pdf_report_func=create_pdf_report_func
            )
        else:
            st.info("ℹ️ Is tasweer mein koi hazard detect nahi hua. Mazeed behtar angle se aik aur snapshot lein.")
