import streamlit as st
from database.supabase_client import get_supabase_client
from models.detector import run_ai_detection
from utils.pdf_generator import generate_pdf_report
from utils.email_sender import send_email_with_pdf

def render_dashboard_ui():
    supabase = get_supabase_client()
    user = st.session_state.user

    st.sidebar.markdown("### 👤 User Info")
    st.sidebar.code(user.email)

    if st.sidebar.button("🚪 Log Out"):
        if supabase:
            supabase.auth.sign_out()
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()

    st.title("👁️ Urban Eye AI - Inspection Dashboard")

    tab1, tab2 = st.tabs(["📸 Image AI Analysis", "📩 Department PDF Dispatch"])

    # TAB 1: UPLOAD & DETECT
    with tab1:
        st.subheader("1. Upload Incident Image")
        uploaded_file = st.file_uploader("Choose image file (JPG, PNG)", type=["jpg", "jpeg", "png"])

        if uploaded_file:
            bytes_data = uploaded_file.read()
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Original Image**")
                st.image(bytes_data, use_container_width=True)

            if st.button("🚀 Run AI Detection Analysis"):
                with st.spinner("YOLO Model (`best.pt`) analyzing image..."):
                    proc_img_bytes, stats = run_ai_detection(bytes_data, model_path="models/best.pt")
                    st.session_state.processed_image = proc_img_bytes
                    st.session_state.detection_stats = stats

            if st.session_state.get("processed_image"):
                with col_b:
                    st.markdown("**AI Detection Result**")
                    st.image(st.session_state.processed_image, use_container_width=True)
                
                st.success("✅ AI Detection Completed!")
                st.json(st.session_state.detection_stats)

    # TAB 2: GENERATE & EMAIL REPORT
    with tab2:
        st.subheader("2. Generate & Send Incident Report")

        if not st.session_state.get("processed_image"):
            st.warning("⚠️ Please complete AI Analysis in Tab 1 first.")
        else:
            with st.form("report_form"):
                title = st.text_input("Incident Title", value="Traffic Hazard / Road Violation")
                location = st.text_input("Location / City Zone", value="Main Boulevard, Sector A")
                target_email = st.text_input("Target Department Email", value="department_authority@gov.pk")
                notes = st.text_area("Additional Details / Evidence Description")
                
                submit_btn = st.form_submit_button("📄 Generate & Dispatch Report")

            if submit_btn:
                with st.spinner("Generating PDF & Sending Email..."):
                    pdf_data = generate_pdf_report(
                        user.email, title, location, notes, 
                        st.session_state.processed_image, 
                        st.session_state.detection_stats
                    )
                    
                    st.download_button(
                        label="⬇️ Download PDF Copy Directly",
                        data=pdf_data,
                        file_name=f"Report_{title}.pdf",
                        mime="application/pdf"
                    )

                    success, msg = send_email_with_pdf(user.email, target_email, pdf_data, title)
                    if success:
                        st.balloons()
                        st.success(f"🎉 {msg}")
                    else:
                        st.info(f"PDF generated! Email status: {msg}")