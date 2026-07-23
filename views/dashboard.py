import tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from models.detector import run_detection
from utils.email_sender import send_email_with_pdf
from utils.pdf_generator import create_pdf_report


def render_dashboard_page():
    # ---------------------------------------------------------
    # USER METADATA EXTRACTION (Supabase Session Se)
    # ---------------------------------------------------------
    user = st.session_state.get("user", None)
    user_details = {
        "email": (
            user.email
            if user and hasattr(user, "email")
            else "guest_user@urbaneye.ai"
        ),
        "username": "N/A",
        "phone": "N/A",
        "address": "N/A",
    }

    if user and hasattr(user, "user_metadata") and user.user_metadata:
        meta = user.user_metadata
        user_details["username"] = meta.get("username", "N/A")
        user_details["phone"] = meta.get("phone", "N/A")
        user_details["address"] = meta.get("address", "N/A")

    # Header Display
    st.title("👁️ UrbanEye AI - Municipal Incident Detector")
    st.caption(
        "AI Detection System for Potholes, Garbage, Graffiti & Fallen Trees"
    )

    if user_details["username"] != "N/A":
        st.write(
            f"Logged in as: **{user_details['username']}** (`{user_details['email']}`)"
        )
    else:
        st.write(f"Logged in as: **{user_details['email']}**")

    # ---------------------------------------------------------
    # 3 MAIN INPUT TABS (Image, Video, Live Camera)
    # ---------------------------------------------------------
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
                st.image(
                    image, caption="Uploaded Image", use_container_width=True
                )

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
                "🎥 Process Video Stream",
                use_container_width=True,
                key="btn_video",
            ):
                cap = cv2.VideoCapture(tfile.name)
                st_frame = st.empty()
                video_counts = {}
                last_proc_frame = None

                st.info("Processing video frames in real-time...")
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # BGR se RGB convert karke YOLO run karna
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    proc_frame, counts = run_detection(pil_img)
                    last_proc_frame = proc_frame

                    # Live Frame Display
                    st_frame.image(
                        proc_frame,
                        caption="AI Video Feed",
                        use_container_width=True,
                    )

                    # Counts accumulate karna
                    for k, v in counts.items():
                        video_counts[k] = video_counts.get(k, 0) + v

                cap.release()
                st.session_state["counts"] = video_counts
                if last_proc_frame:
                    st.session_state["processed_img"] = (
                        last_proc_frame  # Save last frame for PDF
                    )
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
    # REPORTING, DOWNLOAD & EMAIL DISPATCH SECTION
    # ---------------------------------------------------------
    if "counts" in st.session_state and st.session_state["counts"]:
        st.divider()
        st.subheader("🚨 Incident Report Actions")

        st.write("### 📊 Detected Issues Summary:")
        for hazard, count in st.session_state["counts"].items():
            st.write(f"- **{hazard.title()}**: {count} instance(s)")

        col_a, col_b = st.columns(2)
        with col_a:
            title = st.text_input(
                "Incident Title",
                "Municipal Hazard Report (Automated)",
                key="incident_title",
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
                key="target_dept",
            )

        # Summary text formatting (Hyphens used to avoid Unicode FPDF errors)
        summary_text = "UrbanEye AI Detection Summary:\n" + "\n".join(
            [f"- {k.title()}: {v}" for k, v in st.session_state["counts"].items()]
        )

        # Detected Image retrieval
        proc_img = st.session_state.get("processed_img", None)

        # Generate PDF Bytes
        pdf_bytes = create_pdf_report(
            title=title,
            user_details=user_details,
            summary_text=summary_text,
            detected_image=proc_img,
        )

        st.write("")
        col_btn1, col_btn2 = st.columns(2)

        # 📥 Button 1: Download PDF Report
        with col_btn1:
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Incident_Report_{title.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_download_pdf",
            )

        # 📩 Button 2: Dispatch Email to Department
        with col_btn2:
            if st.button(
                "📩 Send Email to Authority",
                use_container_width=True,
                key="btn_send_email",
            ):
                with st.spinner("Dispatching Email with PDF attachment..."):
                    success, msg = send_email_with_pdf(
                        sender_email=user_details["email"],
                        target_department_email=dept_email,
                        pdf_bytes=pdf_bytes,
                        title=title,
                    )

                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
