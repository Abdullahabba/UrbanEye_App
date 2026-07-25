import random
import tempfile
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# Core Detector Import
from models.detector import run_detection

# Email Utility Import
try:
    from utils.email_sender import send_email_with_pdf
except ImportError:
    from utils.email_sender import send_email_alert as send_email_with_pdf

# -----------------------------------------------------------------------------
# 📑 INTEGRATED REPORT FOLDER & UTILITY IMPORTS
# -----------------------------------------------------------------------------
create_pdf_report = None

try:
    from report.pdf_generator import create_pdf_report
except ModuleNotFoundError:
    try:
        from reports.pdf_generator import create_pdf_report
    except ModuleNotFoundError:
        try:
            from report.generator import create_pdf_report
        except ModuleNotFoundError:
            try:
                from reports.generator import create_pdf_report
            except ModuleNotFoundError:
                try:
                    from utils.pdf_sender import create_pdf_report
                except ModuleNotFoundError:
                    try:
                        from utils.pdf_generator import create_pdf_report
                    except ModuleNotFoundError:

                        def create_pdf_report(*args, **kwargs):
                            st.error(
                                "⚠️ Report Module Missing! Please verify your 'report' folder structure."
                            )
                            return b""


# Optional Plotly handling
try:
    import plotly.express as px

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def generate_tracking_id():
    """Generates a unique tracking ID for the reporting citizen."""
    return f"UE-2026-{random.randint(1000, 9999)}"


def get_user_metadata():
    """Extract user metadata safely from Streamlit Session."""
    user = st.session_state.get("user", None)
    details = {
        "email": (
            user.email
            if user and hasattr(user, "email")
            else "officer@urbaneye.ai"
        ),
        "username": "Inspector Ahmed",
        "phone": "+92 300 1234567",
        "address": "Lahore Urban Sector 4",
    }
    if user and hasattr(user, "user_metadata") and user.user_metadata:
        meta = user.user_metadata
        details["username"] = meta.get("username", "Inspector Ahmed")
        details["phone"] = meta.get("phone", "N/A")
        details["address"] = meta.get("address", "Lahore Urban Sector 4")
    return details


def calculate_severity_and_sla(counts: dict) -> tuple[str, str, str]:
    """Calculates hazard severity index and SLA response target."""
    total_objects = sum(counts.values())
    if total_objects == 0:
        return "LOW", "#28a745", "48 Hours"

    has_critical = any(
        k.lower() in ["fallen tree", "open manhole", "fire hazard"]
        for k in counts.keys()
    )
    potholes = sum(v for k, v in counts.items() if "pothole" in k.lower())

    if total_objects >= 5 or has_critical or potholes >= 3:
        return "CRITICAL", "#dc3545", "4 Hours (Immediate)"
    elif total_objects >= 2:
        return "MEDIUM", "#ffc107", "12 Hours"
    else:
        return "LOW", "#28a745", "24 Hours"


def initialize_mock_history():
    """Initializes rich dummy incident ledger history with Tracking IDs."""
    if "incident_ledger" not in st.session_state:
        st.session_state["incident_ledger"] = pd.DataFrame(
            [
                {
                    "Tracking ID": "UE-2026-1001",
                    "Hazard": "Pothole",
                    "Severity": "CRITICAL",
                    "SLA Target": "4 Hours",
                    "Status": "In Progress",
                    "Assigned Dept": "Road Maintenance Dept",
                    "Latitude": 31.5204,
                    "Longitude": 74.3587,
                    "Timestamp": "2026-07-23 08:15",
                },
                {
                    "Tracking ID": "UE-2026-1002",
                    "Hazard": "Garbage Dump",
                    "Severity": "MEDIUM",
                    "SLA Target": "12 Hours",
                    "Status": "Pending",
                    "Assigned Dept": "Waste Management Dept",
                    "Latitude": 31.5100,
                    "Longitude": 74.3400,
                    "Timestamp": "2026-07-23 11:30",
                },
                {
                    "Tracking ID": "UE-2026-1003",
                    "Hazard": "Fallen Tree",
                    "Severity": "CRITICAL",
                    "SLA Target": "4 Hours",
                    "Status": "Resolved",
                    "Assigned Dept": "Parks & Horticulture Authority",
                    "Latitude": 31.5300,
                    "Longitude": 74.3600,
                    "Timestamp": "2026-07-22 09:00",
                },
            ]
        )


# -----------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -----------------------------------------------------------------------------
def render_dashboard_page():
    initialize_mock_history()
    user_details = get_user_metadata()
    df_ledger = st.session_state["incident_ledger"]

    # =========================================================================
    # 🎛️ SIDEBAR CONTROL CENTER
    # =========================================================================
    with st.sidebar:
        st.title("👁️ UrbanEye AI")
        st.caption("Smart City Operations Command")

        st.divider()

        # 👤 Officer Profile
        st.markdown(f"**👤 Officer:** {user_details['username']}")
        st.markdown(f"**📍 Sector:** {user_details['address']}")
        st.caption("🟢 System Status: **Online & Synced**")

        st.divider()

        # 🎯 MAIN NAVIGATION MENU
        st.subheader("🧭 Navigation Menu")
        current_view = st.radio(
            "Go To View:",
            [
                "🏠 Executive Command Overview",
                "🔍 AI Visual Detection Engine",
                "🔎 Public Hazard Tracker",
                "🗺️ GIS Live Incident Map",
                "📊 City Analytics & BI",
                "📋 Master Incident Ledger",
                "📄 City Reports Generator",
                "✅ Fix Verification (Before/After)",
            ],
            key="main_navigation",
        )

        st.divider()

        # ⚙️ AI DETECTION INPUT CONTROLS
        if current_view == "🔍 AI Visual Detection Engine":
            st.subheader("⚙️ Detector Settings")
            conf_threshold = st.slider(
                "YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05
            )

            st.subheader("📷 Input Media Source")
            input_mode = st.radio(
                "Select Source Type:",
                [
                    "🖼️ Single Image",
                    "📂 Batch Processing",
                    "🎥 Video Stream",
                    "📸 Live Camera",
                ],
                key="input_source_mode",
            )
        else:
            conf_threshold = 0.45
            input_mode = "🖼️ Single Image"

        # 🔍 GLOBAL FILTERS
        if current_view in [
            "🏠 Executive Command Overview",
            "🗺️ GIS Live Incident Map",
            "📊 City Analytics & BI",
            "📋 Master Incident Ledger",
            "📄 City Reports Generator",
        ]:
            st.subheader("🌪️ Global Data Filters")
            filter_status = st.multiselect(
                "Filter Status:",
                ["Pending", "In Progress", "Resolved"],
                default=["Pending", "In Progress", "Resolved"],
            )
            filter_severity = st.multiselect(
                "Filter Severity:",
                ["LOW", "MEDIUM", "CRITICAL"],
                default=["LOW", "MEDIUM", "CRITICAL"],
            )

            filtered_ledger = df_ledger[
                (df_ledger["Status"].isin(filter_status))
                & (df_ledger["Severity"].isin(filter_severity))
            ]
        else:
            filtered_ledger = df_ledger

    # =========================================================================
    # MAIN AREA CONTENT
    # =========================================================================

    # -------------------------------------------------------------------------
    # VIEW 1: EXECUTIVE COMMAND OVERVIEW
    # -------------------------------------------------------------------------
    if current_view == "🏠 Executive Command Overview":
        st.title("🏠 Executive Command Center")
        st.caption("Real-time City Metrics & Emergency Overview")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Reported", len(filtered_ledger))
        c2.metric(
            "Pending Action",
            len(filtered_ledger[filtered_ledger["Status"] == "Pending"]),
        )
        c3.metric(
            "Critical SLA Hazards",
            len(filtered_ledger[filtered_ledger["Severity"] == "CRITICAL"]),
        )
        c4.metric(
            "SLA Resolution Rate",
            f"{int((len(filtered_ledger[filtered_ledger['Status'] == 'Resolved']) / max(len(filtered_ledger), 1)) * 100)}%",
        )

        st.divider()

        col_left, col_right = st.columns([3, 2])
        with col_left:
            st.subheader("📍 Active GIS Hazard Map")
            map_data = filtered_ledger[["Latitude", "Longitude"]].rename(
                columns={"Latitude": "lat", "Longitude": "lon"}
            )
            st.map(map_data, zoom=11)

        with col_right:
            st.subheader("🚨 Critical Priority Queue")
            critical_df = filtered_ledger[
                filtered_ledger["Severity"] == "CRITICAL"
            ]
            if not critical_df.empty:
                for idx, row in critical_df.iterrows():
                    st.error(
                        f"**{row['Tracking ID']}** | {row['Hazard']}\n\n⏱️ **SLA:** {row['SLA Target']} | 📌 **Status:** {row['Status']}"
                    )
            else:
                st.success("🎉 No active Critical Hazards pending!")

    # -------------------------------------------------------------------------
    # VIEW 2: AI VISUAL DETECTION ENGINE
    # -------------------------------------------------------------------------
    elif current_view == "🔍 AI Visual Detection Engine":
        st.title("🔍 AI Inspection Engine")
        st.caption(
            f"Active Mode: **{input_mode}** | YOLO Confidence Threshold: `{conf_threshold}`"
        )

        processed_img = None

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

        # MODE 1: SINGLE IMAGE
        if input_mode == "🖼️ Single Image":
            st.markdown("### 🖼️ Single Image Inspection")
            uploaded_file = st.file_uploader(
                "Upload Hazard Snapshot",
                type=["jpg", "jpeg", "png"],
                key="single_image_upload",
            )
            if uploaded_file:
                img = Image.open(uploaded_file)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(
                        img, caption="Original Input", use_container_width=True
                    )

                if st.button("🔍 Run AI Detection", key="btn_single"):
                    with st.spinner("Analyzing with YOLO Model..."):
                        processed_img, current_counts = run_detection(
                            img, conf_threshold
                        )
                        st.session_state["processed_img"] = processed_img
                        st.session_state["counts"] = current_counts
                        st.session_state["current_tracking_id"] = (
                            generate_tracking_id()
                        )

                if "processed_img" in st.session_state:
                    with c2:
                        st.image(
                            st.session_state["processed_img"],
                            caption="YOLO AI Detection Result",
                            use_container_width=True,
                        )

        # MODE 2: BATCH PROCESSING
        elif input_mode == "📂 Batch Processing":
            st.markdown("### 📂 Batch Image Processing")
            uploaded_files = st.file_uploader(
                "Upload Multiple Hazard Images",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="batch_image_upload",
            )
            if uploaded_files and st.button(
                "🚀 Process All Batch Images", key="btn_batch"
            ):
                batch_summary = {}
                cols = st.columns(min(len(uploaded_files), 3))

                for idx, file in enumerate(uploaded_files):
                    img = Image.open(file)
                    p_img, counts = run_detection(img, conf_threshold)
                    with cols[idx % 3]:
                        st.image(
                            p_img,
                            caption=f"Image {idx+1}",
                            use_container_width=True,
                        )
                    for k, v in counts.items():
                        batch_summary[k] = batch_summary.get(k, 0) + v

                st.session_state["counts"] = batch_summary
                st.session_state["current_tracking_id"] = (
                    generate_tracking_id()
                )
                st.success(
                    f"✅ Batch processing complete for {len(uploaded_files)} images!"
                )

        # MODE 3: VIDEO STREAM
        elif input_mode == "🎥 Video Stream":
            st.markdown("### 🎥 Video Stream Inspection")
            uploaded_video = st.file_uploader(
                "Upload CCTV or Drone Footage",
                type=["mp4", "avi", "mov"],
                key="video_upload",
            )
            if uploaded_video and st.button(
                "🎥 Start Video Analysis", key="btn_video"
            ):
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_video.read())

                cap = cv2.VideoCapture(tfile.name)
                st_frame = st.empty()
                v_counts = {}
                last_frame = None

                with st.spinner("Processing Video Stream Frame by Frame..."):
                    frame_count = 0
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break

                        frame_count += 1
                        if frame_count % 3 != 0:
                            continue

                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(frame_rgb)
                        proc_frame, counts = run_detection(
                            pil_img, conf_threshold
                        )
                        last_frame = proc_frame

                        st_frame.image(
                            proc_frame,
                            caption=f"Live Frame Analysis (Frame {frame_count})",
                            use_container_width=True,
                        )

                        for k, v in counts.items():
                            v_counts[k] = v_counts.get(k, 0) + v

                cap.release()
                st.session_state["counts"] = v_counts
                st.session_state["current_tracking_id"] = (
                    generate_tracking_id()
                )
                if last_frame:
                    st.session_state["processed_img"] = last_frame
                st.success(
                    "✅ Video Stream Analysis Completed Successfully!"
                )

        # MODE 4: LIVE CAMERA
        elif input_mode == "📸 Live Camera":
            st.markdown("### 📸 Field Camera Live Capture")
            cam_photo = st.camera_input(
                "Take Live Photo from Camera", key="camera_input"
            )

            if cam_photo and st.button(
                "🔍 Analyze Field Snapshot", key="btn_cam"
            ):
                img = Image.open(cam_photo)
                with st.spinner("Analyzing Camera Capture..."):
                    proc_img, counts = run_detection(img, conf_threshold)
                    st.session_state["processed_img"] = proc_img
                    st.session_state["counts"] = counts
                    st.session_state["current_tracking_id"] = (
                        generate_tracking_id()
                    )

            if "processed_img" in st.session_state:
                st.image(
                    st.session_state["processed_img"],
                    caption="Live Camera AI Result",
                    use_container_width=True,
                )

        # DISPATCH & REPORTING SECTION
        if "counts" in st.session_state and st.session_state["counts"]:
            st.divider()

            tracking_id = st.session_state["current_tracking_id"]
            st.info(
                f"🎫 **Your Unique Report Tracking ID:** `{tracking_id}` (Save this ID to track status later!)"
            )

            st.subheader("🚨 Inspection Breakdown & Urgent Dispatch")

            (
                severity_label,
                color_code,
                sla_target,
            ) = calculate_severity_and_sla(st.session_state["counts"])

            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write("### Detected Hazards Summary:")
                for hz, count in st.session_state["counts"].items():
                    st.write(f"- **{hz.title()}**: {count} instance(s)")

            with col_b:
                st.markdown(
                    f"""
                    <div style="background-color: {color_code}; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                        <h4 style="margin:0;">SEVERITY INDEX</h4>
                        <h2 style="margin:0;">{severity_label}</h2>
                        <p style="margin:0; font-size:12px;">SLA Target: {sla_target}</p>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

            st.write("")
            col_inp1, col_inp2 = st.columns(2)
            with col_inp1:
                title = st.text_input(
                    "Incident Title",
                    "Municipal Hazard Alert",
                    key="dispatch_title",
                )
            with col_inp2:
                dept_email = st.selectbox(
                    "Target Department Email",
                    [
                        "road_maintenance@city.gov",
                        "waste_management@city.gov",
                        "urban_planning@city.gov",
                        "civic_support@city.gov",
                    ],
                    key="dispatch_dept",
                )

            summary_text = f"Tracking ID: {tracking_id}\nUrbanEye AI Summary:\n" + "\n".join(
                [
                    f"- {k.title()}: {v}"
                    for k, v in st.session_state["counts"].items()
                ]
            )
            p_img = st.session_state.get("processed_img", None)

            pdf_bytes = create_pdf_report(
                title=f"{title} (ID: {tracking_id})",
                user_details=user_details,
                summary_text=summary_text,
                detected_image=p_img,
            )

            btn1, btn2, btn3 = st.columns(3)
            with btn1:
                if pdf_bytes:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"Report_{tracking_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_dl_pdf",
                    )
            with btn2:
                if st.button(
                    "📩 Send Email Alert",
                    use_container_width=True,
                    key="btn_send_email",
                ):
                    with st.spinner("Sending Email Alert..."):
                        try:
                            ok, msg = send_email_with_pdf(
                                sender_email=user_details["email"],
                                target_department_email=dept_email,
                                pdf_bytes=pdf_bytes,
                                title=f"{title} [{tracking_id}]",
                                user_details=user_details,
                                counts=st.session_state["counts"],
                            )
                            if ok:
                                st.success(f"✅ {msg}")
                            else:
                                st.error(f"❌ {msg}")
                        except Exception as e:
                            st.error(f"❌ Failed to send email: {e}")
            with btn3:
                if st.button(
                    "💾 Submit & Log to Master Ledger",
                    use_container_width=True,
                    key="btn_save_ledger",
                ):
                    primary_hazard = (
                        list(st.session_state["counts"].keys())[0].title()
                        if st.session_state["counts"]
                        else "General Hazard"
                    )
                    new_row = pd.DataFrame(
                        [
                            {
                                "Tracking ID": tracking_id,
                                "Hazard": primary_hazard,
                                "Severity": severity_label,
                                "SLA Target": sla_target,
                                "Status": "Pending",
                                "Assigned Dept": dept_email.split("@")[0]
                                .replace("_", " ")
                                .title(),
                                "Latitude": 31.5204
                                + (np.random.randn() * 0.01),
                                "Longitude": 74.3587
                                + (np.random.randn() * 0.01),
                                "Timestamp": pd.Timestamp.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                ),
                            }
                        ]
                    )
                    st.session_state["incident_ledger"] = pd.concat(
                        [df_ledger, new_row], ignore_index=True
                    )
                    st.success(
                        f"✅ Incident submitted successfully! Tracking ID: **{tracking_id}**"
                    )

    # -------------------------------------------------------------------------
    # VIEW 3: PUBLIC HAZARD TRACKER
    # -------------------------------------------------------------------------
    elif current_view == "🔎 Public Hazard Tracker":
        st.title("🔎 Citizen Hazard Tracker")
        st.caption(
            "Enter your unique Tracking ID to view real-time resolution status"
        )

        search_id = st.text_input(
            "Enter Tracking ID (e.g., UE-2026-1001):",
            value="",
            placeholder="UE-2026-XXXX",
        ).strip()

        if search_id:
            match = df_ledger[
                df_ledger["Tracking ID"].str.upper() == search_id.upper()
            ]

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
                st.markdown(f"**🕒 Reported Time:** {record['Timestamp']}")

            else:
                st.error(f"❌ No record found matching Tracking ID: `{search_id}`. Please check and try again.")

    # -------------------------------------------------------------------------
    # VIEW 4: GIS LIVE INCIDENT MAP
    # -------------------------------------------------------------------------
    elif current_view == "🗺️ GIS Live Incident Map":
        st.title("🗺️ Interactive GIS City Map")
        st.caption("Live geographical plotting based on active filters")

        map_data = filtered_ledger[["Latitude", "Longitude"]].rename(
            columns={"Latitude": "lat", "Longitude": "lon"}
        )
        st.map(map_data, zoom=12)

        st.subheader("Filtered Location Registry")
        st.dataframe(filtered_ledger, use_container_width=True)

    # -------------------------------------------------------------------------
    # VIEW 5: CITY ANALYTICS & BI
    # -------------------------------------------------------------------------
    elif current_view == "📊 City Analytics & BI":
        st.title("📊 Business Intelligence & Trend Analytics")

        c_a1, c_a2 = st.columns(2)
        if HAS_PLOTLY:
            with c_a1:
                fig1 = px.bar(
                    filtered_ledger,
                    x="Hazard",
                    color="Severity",
                    title="Incidents by Category & Severity",
                    color_discrete_map={
                        "CRITICAL": "#dc3545",
                        "MEDIUM": "#ffc107",
                        "LOW": "#28a745",
                    },
                )
                st.plotly_chart(fig1, use_container_width=True)

            with c_a2:
                fig2 = px.pie(
                    filtered_ledger,
                    names="Status",
                    title="Incident Resolution Status",
                    hole=0.4,
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            with c_a1:
                st.bar_chart(filtered_ledger["Hazard"].value_counts())
            with c_a2:
                st.bar_chart(filtered_ledger["Status"].value_counts())

    # -------------------------------------------------------------------------
    # VIEW 6: MASTER INCIDENT LEDGER
    # -------------------------------------------------------------------------
    elif current_view == "📋 Master Incident Ledger":
        st.title("📋 City Incident Master Ledger")
        st.caption("Central Database of all recorded municipal violations")

        st.dataframe(filtered_ledger, use_container_width=True)

        csv_data = filtered_ledger.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Filtered Ledger to CSV",
            data=csv_data,
            file_name="UrbanEye_Ledger_Export.csv",
            mime="text/csv",
            key="btn_export_csv",
        )

    # -------------------------------------------------------------------------
    # VIEW 7: CITY REPORTS GENERATOR
    # -------------------------------------------------------------------------
    elif current_view == "📄 City Reports Generator":
        st.title("📄 Executive City Reports Hub")
        st.caption("Generate, view summaries, and export municipal reports")

        r_col1, r_col2 = st.columns([2, 1])

        with r_col1:
            report_type = st.selectbox(
                "Select Report Type:",
                [
                    "📊 Executive Summary Report",
                    "🚨 Critical SLA Violations Audit",
                    "🧹 Hazard Category Distribution",
                    "📋 Complete Incident Master Log",
                ],
            )
            report_notes = st.text_area(
                "Officer Remarks / Directives:",
                "All critical hazards must be prioritized within the 4-hour SLA window.",
                height=100,
            )

        with r_col2:
            st.markdown("### Report Summary")
            st.metric("Total Records", len(filtered_ledger))
            st.metric(
                "Critical Hazards",
                len(
                    filtered_ledger[filtered_ledger["Severity"] == "CRITICAL"]
                ),
            )
            st.metric(
                "Pending Actions",
                len(filtered_ledger[filtered_ledger["Status"] == "Pending"]),
            )

        st.divider()
        st.subheader("📋 Report Data Preview")
        st.dataframe(filtered_ledger, use_container_width=True)

        st.divider()

        rep_summary_text = (
            f"UrbanEye AI Executive Report ({report_type.split(' ')[1]})\n\n"
            f"Officer: {user_details['username']} ({user_details['address']})\n"
            f"Total Incidents Recorded: {len(filtered_ledger)}\n"
            f"Pending: {len(filtered_ledger[filtered_ledger['Status'] == 'Pending'])}\n"
            f"Critical: {len(filtered_ledger[filtered_ledger['Severity'] == 'CRITICAL'])}\n\n"
            f"Officer Directives:\n{report_notes}"
        )

        gen_pdf_bytes = create_pdf_report(
            title=report_type.replace("📊 ", "")
            .replace("🚨 ", "")
            .replace("🧹 ", "")
            .replace("📋 ", ""),
            user_details=user_details,
            summary_text=rep_summary_text,
            detected_image=None,
        )

        b1, b2 = st.columns(2)
        with b1:
            if gen_pdf_bytes:
                st.download_button(
                    label="📥 Export Full PDF Report",
                    data=gen_pdf_bytes,
                    file_name="UrbanEye_Executive_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_gen_pdf_rep",
                )
            else:
                st.warning("PDF generation utility unavailable.")

        with b2:
            rep_csv = filtered_ledger.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Report Data (CSV)",
                data=rep_csv,
                file_name="UrbanEye_Report_Data.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_gen_csv_rep",
            )

    # -------------------------------------------------------------------------
    # VIEW 8: FIX VERIFICATION (BEFORE / AFTER)
    # -------------------------------------------------------------------------
    elif current_view == "✅ Fix Verification (Before/After)":
        st.title("✅ Municipal Fix Verification Engine")
        st.caption(
            "Upload 'After Fix' evidence to resolve active pending incidents"
        )

        pending_incidents = df_ledger[df_ledger["Status"] != "Resolved"]

        if pending_incidents.empty:
            st.success("🎉 All incidents have been verified and resolved!")
        else:
            selected_inc_id = st.selectbox(
                "Select Tracking ID to Verify & Close:",
                pending_incidents["Tracking ID"].tolist(),
                key="select_pending_id",
            )

            inc_details = pending_incidents[
                pending_incidents["Tracking ID"] == selected_inc_id
            ].iloc[0]

            st.info(
                f"**Selected:** {inc_details['Tracking ID']} | **Hazard:** {inc_details['Hazard']} | **Current Status:** `{inc_details['Status']}`"
            )

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📷 Original Hazard (Before)")
                st.warning("Original inspection evidence logged in database.")

            with c2:
                st.subheader("📸 Upload Fix Evidence (After)")
                after_file = st.file_uploader(
                    "Upload Repair Photo",
                    type=["jpg", "png"],
                    key="after_repair_upload",
                )
                if after_file:
                    st.image(
                        Image.open(after_file),
                        caption="After Repair Evidence",
                        use_container_width=True,
                    )

            if after_file and st.button(
                "🟢 Mark as Resolved & Verify", key="btn_verify_fix"
            ):
                st.session_state["incident_ledger"].loc[
                    st.session_state["incident_ledger"]["Tracking ID"]
                    == selected_inc_id,
                    "Status",
                ] = "Resolved"
                st.success(
                    f"✅ Incident {selected_inc_id} status updated to RESOLVED!"
                )
                st.balloons()
