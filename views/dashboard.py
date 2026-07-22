from PIL import Image
import streamlit as st
from models.detector import run_detection
from utils.email_sender import send_email_with_pdf
from utils.pdf_generator import create_pdf_report


def render_dashboard_page():
    user = st.session_state.get("user", None)
    user_email = user.email if user else "guest_user@urbaneye.ai"

    st.title("👁️ UrbanEye AI - Incident Dashboard")
    st.write(f"Logged in as: **{user_email}**")

    # Image Upload Section
    uploaded_file = st.file_uploader(
        "Upload Incident Image", type=["jpg", "png", "jpeg"]
    )

    if uploaded_file:
        image = Image.open(uploaded_file)

        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Uploaded Image", use_container_width=True)

        if st.button("🔍 Run AI Detection", use_container_width=True):
            with st.spinner("Processing image via YOLO..."):
                processed_img, counts = run_detection(image)
                st.session_state["processed_img"] = processed_img
                st.session_state["counts"] = counts

        if "processed_img" in st.session_state:
            with col2:
                st.image(
                    st.session_state["processed_img"],
                    caption="Detection Results",
                    use_container_width=True,
                )

            st.success("✅ Detections complete!")
            st.write("**Detected Objects:**", st.session_state["counts"])

            st.divider()

            # Incident Reporting Form
            st.subheader("🚨 Report Incident to Authorities")

            title = st.text_input("Incident Title", "Unauthorized Activity Detected")
            dept_email = st.selectbox(
                "Target Department Email",
                [
                    "traffic@city.gov",
                    "urban.planning@city.gov",
                    "police@city.gov",
                ],
            )

            if st.button(
                "📩 Generate & Send Email Report", use_container_width=True
            ):
                with st.spinner("Generating PDF & Sending Email..."):
                    summary_text = f"Detections Count:\n{st.session_state['counts']}\n\nLocation: Sector A Urban Grid"

                    # 1. Generate PDF Bytes
                    pdf_bytes = create_pdf_report(title, user_email, summary_text)

                    # 2. Send Email
                    success, msg = send_email_with_pdf(
                        sender_email=user_email,
                        target_department_email=dept_email,
                        pdf_bytes=pdf_bytes,
                        title=title,
                    )

                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
