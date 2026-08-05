import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from utils.priority_engine import calculate_priority_score

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    st.divider()
    st.subheader("📤 Dispatch & Verification Panel")
    
    # Check if input source mode changed to clear stale single-image/video state
    current_mode = st.session_state.get("input_source_mode", "🖼️ Single Image")
    last_active_mode = st.session_state.get("_last_active_input_mode", current_mode)

    if current_mode != last_active_mode:
        st.session_state["counts"] = {}
        st.session_state.pop("processed_img", None)
        st.session_state["captured_images"] = []
        st.session_state["_last_active_input_mode"] = current_mode
        st.rerun()

    # 🔍 DEBUG: Session state counts check karne ke liye
    counts = st.session_state.get("counts", {})
    st.write(f"🔍 **Debug Info - Current Counts:** `{counts}`")

    has_valid_detections = counts and any(v > 0 for v in counts.values())

    if not has_valid_detections:
        st.warning("⚠️ **Panel Locked:** AI model ke paas abhi koi valid detections (`counts`) nahi hain. Pehle uper 'Run AI Detection' / Start analysis button click karein taake hazards detect hon.")
        return

    st.caption("Step 1: Review Detection Summary $\rightarrow$ Step 2: Set Location $\rightarrow$ Step 3: Automatic Dispatch & Reports.")

    # Initialize session state variables for location
    if "selected_lat" not in st.session_state:
        st.session_state["selected_lat"] = None
    if "selected_lon" not in st.session_state:
        st.session_state["selected_lon"] = None
    if "selected_loc_name" not in st.session_state:
        st.session_state["selected_loc_name"] = manual_loc_name

    # 1️⃣ Step 1: Detection Summary
    summary_text = "Detected Hazards Summary:\n"
    for k, v in counts.items():
        if v > 0:
            summary_text += f"- {k.capitalize()}: {v}\n"

    st.text_area("📋 Generated Incident Summary", value=summary_text, height=100)

    # ⚡ Priority Assessment
    assessment = calculate_priority_score(counts)
    score = assessment["priority_score"]
    severity_level = assessment["severity"]
    assigned_department = assessment["assigned_dept"]
    sla_target = assessment["sla_target"]

    st.info(f"ℹ️ **PRIORITY SCORE: {score}/100** | Severity: {severity_level} | Dept: {assigned_department}")
    st.divider()

    # 2️⃣ Step 2: Location Option
    st.markdown("##### 📍 Step 2: Select Location Method")
    loc_mode = st.radio(
        "Choose Location Mode",
        ["Manual Address", "Automatic Live GPS"],
        horizontal=True,
        key="dispatch_loc_mode"
    )

    location_ready = False

    if loc_mode == "Manual Address":
        manual_input = st.text_input(
            "✍️ Enter Location Name / Address:", 
            value=st.session_state.get("selected_loc_name", manual_loc_name),
            key="manual_address_input_box"
        )
        if manual_input and manual_input.strip():
            st.session_state["selected_loc_name"] = manual_input.strip()
            st.session_state["selected_lat"] = None
            st.session_state["selected_lon"] = None
            location_ready = True
            st.success(f"✅ Active Location Set: `{manual_input.strip()}`")
        else:
            st.warning("⚠️ Please enter a valid location name.")
    else:
        st.markdown("🛰️ Click below to fetch your **real browser GPS coordinates**:")
        if streamlit_geolocation is not None:
            loc = streamlit_geolocation()
            if loc and loc.get("latitude") and loc.get("longitude"):
                st.session_state["selected_lat"] = loc["latitude"]
                st.session_state["selected_lon"] = loc["longitude"]
                st.session_state["selected_loc_name"] = f"Live GPS (Lat: {loc['latitude']:.4f}, Lon: {loc['longitude']:.4f})"
            
            if st.session_state.get("selected_lat") is not None:
                location_ready = True
                st.success(f"✅ Live GPS Locked!")
        else:
            st.error("❌ `streamlit-geolocation` library is not installed.")

    # 3️⃣ Step 3: Reports & Actions (Unlocked instantly when location is ready)
    if location_ready:
        st.markdown("##### 🚀 Step 3: Reports & Actions Unlocked")
        st.divider()

        final_location_name = st.session_state["selected_loc_name"]
        lat = st.session_state["selected_lat"]
        lon = st.session_state["selected_lon"]

        full_summary_text = summary_text + f"Location: {final_location_name}\nPriority Score: {score}/100\nTracking ID: {tracking_id}"

        raw_images = st.session_state.get("captured_images", [])
        if not raw_images and "processed_img" in st.session_state:
            raw_images = [st.session_state["processed_img"]]

        all_images = []
        for img in raw_images:
            if isinstance(img, np.ndarray):
                all_images.append(Image.fromarray(img))
            elif isinstance(img, Image.Image):
                all_images.append(img)

        # Generate PDF Bytes with fallback error display
        pdf_bytes = None
        if create_pdf_report_func:
            try:
                pdf_bytes = create_pdf_report_func(
                    title=f"Incident Report (ID: {tracking_id})",
                    user_details=user_details,
                    summary_text=full_summary_text,
                    detected_images=all_images
                )
            except Exception as e:
                st.error(f"❌ PDF Generation Crashed: {e}")

        col1, col2 = st.columns(2)

        with col1:
            if pdf_bytes:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"UrbanEye_Report_{tracking_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ PDF bytes are empty/None.")

        with col2:
            if st.button("📧 Send via Email", use_container_width=True):
                with st.spinner("Sending official report via email..."):
                    try:
                        from utils.email_sender import send_email_with_pdf
                        success, message = send_email_with_pdf(
                            sender_email=user_details.get("email", "officer@urbaneye.ai") if isinstance(user_details, dict) else "officer@urbaneye.ai",
                            target_department_email="roads.dept@urbaneye.ai",
                            pdf_bytes=pdf_bytes,
                            title=f"Incident Report - ID: {tracking_id}",
                            user_details=user_details,
                            counts=counts
                        )
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as mail_err:
                        st.error(f"❌ Email sending failed: {str(mail_err)}")
    else:
        st.info("🔒 Enter a location name above to unlock Step 3.")
