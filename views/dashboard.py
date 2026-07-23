import tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.email_sender import send_email_with_pdf
from utils.pdf_generator import create_pdf_report


def render_dashboard_page():
    user = st.session_state.get("user", None)
    user_email = user.email if user else "guest_user@urbaneye.ai"

    st.title("👁️ UrbanEye AI - Municipal Incident Detector")
    st.caption("AI Detection System for Potholes, Garbage, Graffiti & Fallen Trees")
    st.write(f"Logged in as: **{user_email}**")

    # 3 Main Input Tabs
    tab_img, tab_video, tab_cam = st.tabs(
        ["🖼️ Image Upload", "🎥 Video Analysis", "📸 Live Camera"]
    )

    # ---------------------------------------------------------
    # TAB 1: IMAGE DETECTION
    # ---------------------------------------------------------
    with tab_img:
        uploaded_file = st.file_uploader(
            "Upload Incident Image",
            type=["jpg", "png", "jpeg"],
            key="img_uploader",
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)

            with col1:
                st.image(image, caption="Uploaded Image", use_container_width=True)

            if st.button(
                "🔍 Run AI Detection", use_container_width=True, key="btn_img"
            ):
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

    # ---------------------------------------------------------
    # TAB 2: VIDEO ANALYSIS
    # ---------------------------------------------------------
    with tab_video:
        uploaded_video = st.file_uploader(
            "Upload Incident Video",
            type=["mp4", "avi", "mov"],
            key="video_uploader",
        )

        if uploaded_video:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_video.read())

            if st.button(
                "🎥 Process Video Stream", use_container_width=True, key="btn_video"
            ):
                cap = cv2.VideoCapture(tfile.name)
                st_frame = st.empty()
                video_counts = {}

                st.info("Processing video frames in real-time...")
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Frame BGR se RGB convert karke detection run karna
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    proc_frame, counts = run_detection(pil_img)

                    # Screen par output frame dikhana
                    st_frame.image(
                        proc_frame, caption="AI Video Feed", use_container_width=True
                    )

                    # Object counts record karna
                    for k, v in counts.items():
                        video_counts[k] = video_counts.get(k, 0) + v

                cap.release()
                st.session_state["counts"] = video_counts
                st.success("✅ Video processing completed!")

    # ---------------------------------------------------------
    # TAB 3: LIVE CAMERA SNAPSHOT
    # ---------------------------------------------------------
    with tab_cam:
        camera_photo = st.camera_input("Take a Snapshot of the Hazard")

        if camera_photo:
            image = Image.open(camera_photo)
            if st.button(
                "🔍 Analyze Camera Snapshot",
                use_container_width=True,
                key="btn_cam",
            ):
                with st.spinner("Processing snapshot..."):
                    proc_img, counts = run_detection(image)
                    st.session_state["processed_img"] = proc_img
                    st.session_state["counts"] = counts
                    st.image(
                        proc_img,
                        caption="Detection Result",
                        use_container_width=True,
                    )

    # ---------------------------------------------------------
    # REPORTING & EMAIL SECTION
    # ---------------------------------------------------------
    if "counts" in st.session_state and st.session_state["counts"]:
        st.divider()
        st.subheader("🚨 Incident Reporting & Email Dispatch")

        st.write("### 📊 Detected Issues Summary:")
        for hazard, count in st.session_state["counts"].items():
            st.write(f"- **{hazard.title()}**: {count} instance(s)")

        col_a, col_b = st.columns(2)
        with col_a:
            title = st.text_input(
                "Incident Title", "Municipal Hazard Report (Automated)"
            )
        with col_b:
            dept_email = st.selectbox(
                "Target Department Email",
                [
                    "road_maintenance@city.gov",
                    "waste_management@city.gov",
                    "urban_planning@city.gov",
                    "civic_support@city.gov",
                ],
            )

        if st.button(
            "📩 Generate & Send Email Report", use_container_width=True
        ):
            with st.spinner("Generating PDF & Dispatching Email..."):
                # Detections ki formatted summary
                summary_text = f"UrbanEye AI Detection Summary:\n" + "\n".join(
                    [
                        f"• {k.title()}: {v}"
                        for k, v in st.session_state["counts"].items()
                    ]
                )

                # 1. Generate PDF Bytes
                pdf_bytes = create_pdf_report(title, user_email, summary_text)

                # 2. Send Email with PDF
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
