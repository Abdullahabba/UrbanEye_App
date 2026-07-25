import random
import tempfile
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from models.detector import run_detection

try:
    from utils.email_sender import send_email_with_pdf
except ImportError:
    from utils.email_sender import send_email_alert as send_email_with_pdf

# -----------------------------------------------------------------------------
# 📑 REPORT MODULE FALLBACK IMPORTS
# -----------------------------------------------------------------------------
create_pdf_report = None
for mod in [
    ("report.pdf_generator", "create_pdf_report"),
    ("reports.pdf_generator", "create_pdf_report"),
    ("report.generator", "create_pdf_report"),
    ("reports.generator", "create_pdf_report"),
    ("utils.pdf_sender", "create_pdf_report"),
    ("utils.pdf_generator", "create_pdf_report"),
]:
    try:
        module = __import__(mod[0], fromlist=[mod[1]])
        create_pdf_report = getattr(module, mod[1])
        break
    except (ModuleNotFoundError, AttributeError):
        continue

if not create_pdf_report:
    def create_pdf_report(*args, **kwargs):
        st.error("⚠️ Report Module Missing! Please verify your 'report' folder structure.")
        return b""

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def generate_tracking_id():
    return f"UE-2026-{random.randint(1000, 9999)}"

def get_user_metadata():
    user = st.session_state.get("user", None)
    details = {
        "email": user.email if user and hasattr(user, "email") else "officer@urbaneye.ai",
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }
    if user and hasattr(user, "user_metadata") and user.user_metadata:
        meta = user.user_metadata
        details.update({
            "username": meta.get("username", details["username"]),
            "phone": meta.get("phone", details["phone"]),
            "address": meta.get("address", details["address"]),
        })
    return details

def calculate_severity_and_sla(counts: dict) -> tuple[str, str, str]:
    total_objects = sum(counts.values())
    if total_objects == 0:
        return "LOW", "#28a745", "48 Hours"

    has_critical = any(k.lower() in ["fallen tree", "open manhole", "fire hazard"] for k in counts.keys())
    potholes = sum(v for k, v in counts.items() if "pothole" in k.lower())

    if total_objects >= 5 or has_critical or potholes >= 3:
        return "CRITICAL", "#dc3545", "4 Hours (Immediate)"
    elif total_objects >= 2:
        return "MEDIUM", "#ffc107", "12 Hours"
    else:
        return "LOW", "#28a745", "24 Hours"

def initialize_mock_history():
    if "incident_ledger" not in st.session_state:
        st.session_state["incident_ledger"] = pd.DataFrame([
            {
                "Tracking ID": "UE-2026-1001", "Hazard": "Pothole", "Severity": "CRITICAL",
                "SLA Target": "4 Hours", "Status": "In Progress", "Assigned Dept": "Road Maintenance Dept",
                "Latitude": 31.5204, "Longitude": 74.3587, "Location Name": "Iqbal Sector, Block AA", "Timestamp": "2026-07-23 08:15"
            },
            {
                "Tracking ID": "UE-2026-1002", "Hazard": "Garbage Dump", "Severity": "MEDIUM",
                "SLA Target": "12 Hours", "Status": "Pending", "Assigned Dept": "Waste Management Dept",
                "Latitude": 31.5100, "Longitude": 74.3400, "Location Name": "Gulberg III Main Blvd", "Timestamp": "2026-07-23 11:30"
            },
            {
                "Tracking ID": "UE-2026-1003", "Hazard": "Fallen Tree", "Severity": "CRITICAL",
                "SLA Target": "4 Hours", "Status": "Resolved", "Assigned Dept": "Parks & Horticulture Authority",
                "Latitude": 31.5300, "Longitude": 74.3600, "Location Name": "Model Town Link Road", "Timestamp": "2026-07-22 09:00"
            }
        ])

# -----------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -----------------------------------------------------------------------------
def render_dashboard_page():
    initialize_mock_history()
    user_details = get_user_metadata()
    df_ledger = st.session_state["incident_ledger"]

    # SIDEBAR CONTROL CENTER
    with st.sidebar:
        st.title("👁️ UrbanEye AI")
        st.caption("Smart City Detection & Tracking")
        st.divider()
        st.markdown(f"**👤 Officer:** {user_details['username']}")
        st.markdown(f"**📍 Sector:** {user_details['address']}")
        st.caption("🟢 System Status: **Online & Synced**")
        st.divider()

        st.subheader("🧭 Navigation Menu")
        current_view = st.radio("Go To View:", ["🔍 AI Visual Detection Engine", "🔎 Public Hazard Tracker"], key="main_navigation")
        st.divider()

        if current_view == "🔍 AI Visual Detection Engine":
            st.subheader("⚙️ Detector Settings")
            conf_threshold = st.slider("YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05)
            st.subheader("📷 Input Media Source")
            input_mode = st.radio("Select Source Type:", ["🖼️ Single Image", "📂 Batch Processing", "🎥 Video Stream", "📸 Live Camera"], key="input_source_mode")
        else:
            conf_threshold, input_mode = 0.45, "🖼️ Single Image"

    # MAIN AREA CONTENT
    if current_view == "🔍 AI Visual Detection Engine":
        st.title("🔍 AI Inspection Engine")
        st.caption(f"Active Mode: **{input_mode}** | YOLO Confidence Threshold: `{conf_threshold}`")

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

        # LOCATION CONFIGURATION
        st.markdown("### 📍 Location Configuration")
        location_mode = st.selectbox("Location Method", ["📡 Auto GPS (Device Simulation)", "✍️ Manual Address / Sector Entry"], key="input_location_method")

        if location_mode == "✍️ Manual Address / Sector Entry":
            manual_loc_name = st.text_input("Enter Location / Street / Sector Name", value="Iqbal Sector, Block AA, Lahore", key="man_loc_name")
            manual_lat, manual_lon = 31.5204, 74.3587
        else:
            manual_lat = 31.5204 + (random.random() * 0.005)
            manual_lon = 74.3587 + (random.random() * 0.005)
            manual_loc_name = f"Auto-GPS Location (Sector 4 - Lat: {manual_lat:.4f})"
            st.info(f"📡 GPS Locked Successfully! Coords: `{manual_lat:.4f}, {manual_lon:.4f}`")

        st.divider()

        # MODE 1: SINGLE IMAGE
        if input_mode == "🖼️ Single Image":
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
                        st.session_state.update({"processed_img": processed_img, "counts": counts, "current_tracking_id": generate_tracking_id()})
                if "processed_img" in st.session_state:
                    with c2:
                        st.image(st.session_state["processed_img"], caption="YOLO AI Detection Result", use_container_width=True)

        # MODE 2: BATCH PROCESSING
        elif input_mode == "📂 Batch Processing":
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
                st.session_state.update({"counts": batch_summary, "current_tracking_id": generate_tracking_id()})
                st.success(f"✅ Batch processing complete for {len(uploaded_files)} images!")

        # MODE 3: VIDEO STREAM
        elif input_mode == "🎥 Video Stream":
            st.markdown("### 🎥 Video Stream Inspection")
            uploaded_video = st.file_uploader("Upload CCTV or Drone Footage", type=["mp4", "avi", "mov"], key="video_upload")
            if uploaded_video and st.button("🎥 Start Video Analysis", key="btn_video"):
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_video.read())
                cap = cv2.VideoCapture(tfile.name)
                st_frame = st.empty()
                v_counts, last_frame, frame_count = {}, None, 0

                with st.spinner("Processing Video Stream Frame by Frame..."):
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret: break
                        frame_count += 1
                        if frame_count % 3 != 0: continue
                        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        proc_frame, counts = run_detection(pil_img, conf_threshold)
                        last_frame = proc_frame
                        st_frame.image(proc_frame, caption=f"Live Frame (Frame {frame_count})", use_container_width=True)
                        for k, v in counts.items():
                            v_counts[k] = v_counts.get(k, 0) + v
                cap.release()
                st.session_state.update({"counts": v_counts, "current_tracking_id": generate_tracking_id()})
                if last_frame: st.session_state["processed_img"] = last_frame
                st.success("✅ Video Stream Analysis Completed Successfully!")

        # MODE 4: LIVE CAMERA
        elif input_mode == "📸 Live Camera":
            st.markdown("### 📸 Field Camera Live Capture")
            cam_photo = st.camera_input("Take Live Photo from Camera", key="camera_input")
            if cam_photo and st.button("🔍 Analyze Field Snapshot", key="btn_cam"):
                img = Image.open(cam_photo)
                with st.spinner("Analyzing Camera Capture..."):
                    proc_img, counts = run_detection(img, conf_threshold)
                    st.session_state.update({"processed_img": proc_img, "counts": counts, "current_tracking_id": generate_tracking_id()})
            if "processed_img" in st.session_state:
                st.image(st.session_state["processed_img"], caption="Live Camera AI Result", use_container_width=True)

        # DISPATCH & REPORTING SECTION
        if "counts" in st.session_state and st.session_state["counts"]:
            st.divider()
            tracking_id = st.session_state["current_tracking_id"]
            st.info(f"🎫 **Tracking ID:** `{tracking_id}` | 📍 **Location:** {manual_loc_name}")
            st.subheader("🚨 Inspection Breakdown & Urgent Dispatch")

            severity_label, color_code, sla_target = calculate_severity_and_sla(st.session_state["counts"])

            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write("### Detected Hazards Summary:")
                for hz, count in st.session_state["counts"].items():
                    st.write(f"- **{hz.title()}**: {count} instance(s)")
            with col_b:
                st.markdown(f"""
                    <div style="background-color: {color_code}; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                        <h4 style="margin:0;">SEVERITY INDEX</h4>
                        <h2 style="margin:0;">{severity_label}</h2>
                        <p style="margin:0; font-size:12px;">SLA Target: {sla_target}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.write("")
            col_inp1, col_inp2 = st.columns(2)
            with col_inp1:
                title = st.text_input("Incident Title", "Municipal Hazard Alert", key="dispatch_title")
            with col_inp2:
                dept_email = st.selectbox("Target Department Email", ["road_maintenance@city.gov", "waste_management@city.gov", "urban_planning@city.gov", "civic_support@city.gov"], key="dispatch_dept")

            summary_text = f"Tracking ID: {tracking_id}\nLocation: {manual_loc_name}\nUrbanEye AI Summary:\n" + "\n".join([f"- {k.title()}: {v}" for k, v in st.session_state["counts"].items()])
            p_img = st.session_state.get("processed_img", None)
            pdf_bytes = create_pdf_report(title=f"{title} (ID: {tracking_id})", user_details=user_details, summary_text=summary_text, detected_image=p_img)

            btn1, btn2, btn3 = st.columns(3)
            with btn1:
                if pdf_bytes:
                    st.download_button(label="📥 Download PDF Report", data=pdf_bytes, file_name=f"Report_{tracking_id}.pdf", mime="application/pdf", use_container_width=True, key="btn_dl_pdf")
            with btn2:
                if st.button("📩 Send Email Alert", use_container_width=True, key="btn_send_email"):
                    with st.spinner("Sending Email Alert..."):
                        try:
                            ok, msg = send_email_with_pdf(sender_email=user_details["email"], target_department_email=dept_email, pdf_bytes=pdf_bytes, title=f"{title} [{tracking_id}]", user_details=user_details, counts=st.session_state["counts"])
                            st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
                        except Exception as e:
                            st.error(f"❌ Failed to send email: {e}")
            with btn3:
                if st.button("💾 Submit & Log to Tracker", use_container_width=True, key="btn_save_ledger"):
                    primary_hazard = list(st.session_state["counts"].keys())[0].title() if st.session_state["counts"] else "General Hazard"
                    new_row = pd.DataFrame([{
                        "Tracking ID": tracking_id, "Hazard": primary_hazard, "Severity": severity_label,
                        "SLA Target": sla_target, "Status": "Pending", "Assigned Dept": dept_email.split("@")[0].replace("_", " ").title(),
                        "Latitude": manual_lat, "Longitude": manual_lon, "Location Name": manual_loc_name, "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    }])
                    st.session_state["incident_ledger"] = pd.concat([df_ledger, new_row], ignore_index=True)
                    st.success(f"✅ Incident submitted successfully! Tracking ID: **{tracking_id}**")

    # VIEW 2: PUBLIC HAZARD TRACKER
    elif current_view == "🔎 Public Hazard Tracker":
        st.title("🔎 Citizen Hazard Tracker")
        st.caption("Enter your unique Tracking ID to view real-time resolution status")

        search_id = st.text_input("Enter Tracking ID (e.g., UE-2026-1001):", value="", placeholder="UE-2026-XXXX").strip()
        if search_id:
            match = df_ledger[df_ledger["Tracking ID"].str.upper() == search_id.upper()]
            if not match.empty:
                record = match.iloc[0]
                st.success(f"✅ Found Report Record for `{record['Tracking ID']}`")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Hazard Type", record["Hazard"])
                m2.metric("Severity", record["Severity"])
                m3.metric("Current Status", record["Status"])
                m4.metric("SLA Resolution", record["SLA Target"])

                st.divider()
                status = record["Status"]
                st.subheader("📌 Resolution Progress Tracker")
                if status == "Pending":
                    st.progress(25)
                    st.warning("⏳ **Status: Pending** — Assigned to department. Inspection team queued.")
                elif status == "In Progress":
                    st.progress(65)
                    st.info("🛠️ **Status: In Progress** — Maintenance team dispatched to the location.")
                elif status == "Resolved":
                    st.progress(100)
                    st.success("🎉 **Status: Resolved** — Repair verified & hazard resolved successfully!")

                st.markdown(f"**🏢 Department Assigned:** {record.get('Assigned Dept', 'Municipal Services')}")
                st.markdown(f"**📍 Location Area:** {record.get('Location Name', 'N/A')}")
                st.markdown(f"**🕒 Reported Time:** {record['Timestamp']}")
            else:
                st.error(f"❌ No record found matching Tracking ID: `{search_id}`. Please check and try again.")

if __name__ == "__main__":
    render_dashboard_page()
