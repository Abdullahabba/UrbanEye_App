import tempfile
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# Core Modules Import
from models.detector import run_detection
from utils.email_sender import send_email_with_pdf
from utils.pdf_generator import create_pdf_report

# Optional Visualization Libraries
try:
    import plotly.express as px

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
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
    """Initializes rich dummy incident ledger history."""
    if "incident_ledger" not in st.session_state:
        st.session_state["incident_ledger"] = pd.DataFrame(
            [
                {
                    "ID": "INC-1001",
                    "Hazard": "Pothole",
                    "Severity": "CRITICAL",
                    "SLA Target": "4 Hours",
                    "Status": "In Progress",
                    "Latitude": 31.5204,
                    "Longitude": 74.3587,
                    "Timestamp": "2026-07-23 08:15",
                },
                {
                    "ID": "INC-1002",
                    "Hazard": "Garbage Dump",
                    "Severity": "MEDIUM",
                    "SLA Target": "12 Hours",
                    "Status": "Pending",
                    "Latitude": 31.5100,
                    "Longitude": 74.3400,
                    "Timestamp": "2026-07-23 11:30",
                },
                {
                    "ID": "INC-1003",
                    "Hazard": "Fallen Tree",
                    "Severity": "CRITICAL",
                    "SLA Target": "4 Hours",
                    "Status": "Resolved",
                    "Latitude": 31.5300,
                    "Longitude": 74.3600,
                    "Timestamp": "2026-07-22 09:00",
                },
                {
                    "ID": "INC-1004",
                    "Hazard": "Graffiti",
                    "Severity": "LOW",
                    "SLA Target": "48 Hours",
                    "Status": "Pending",
                    "Latitude": 31.5400,
                    "Longitude": 74.3300,
                    "Timestamp": "2026-07-24 01:45",
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

        # 👤 Officer Profile Pill
        st.markdown(f"**👤 Officer:** {user_details['username']}")
        st.markdown(f"**📍 Sector:** {user_details['address']}")
        st.caption(f"🟢 System Status: **Online & Synced**")

        st.divider()

        # 🎯 MAIN NAVIGATION MENU
        st.subheader("🧭 Command Center View")
        current_view = st.radio(
            "Go To:",
            [
                "🏠 Executive Command Overview",
                "🔍 AI Visual Detection Engine",
                "🗺️ GIS Live Incident Map",
                "📊 City Analytics & BI",
                "📋 Master Incident Ledger",
                "✅ Fix Verification (Before/After)",
            ],
            key="main_navigation",
        )

        st.divider()

        # ⚙️ AI DETECTION ENGINE CONTROLS (Only visible if Detection Engine selected)
        if current_view == "🔍 AI Visual Detection Engine":
            st.subheader("⚙️ Detector Settings")
            conf_threshold = st.slider(
                "YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05
            )
            input_mode = st.radio(
                "Select Input Source:",
                [
                    "🖼️ Single Image",
                    "📂 Batch Processing",
                    "🎥 Video Stream",
                    "📸 Live Camera",
                ],
            )
        else:
            conf_threshold = 0.45
            input_mode = "🖼️ Single Image"

        # 🔍 GLOBAL FILTERS (For Map, Analytics, and Ledger)
        if current_view in [
            "🏠 Executive Command Overview",
            "🗺️ GIS Live Incident Map",
            "📊 City Analytics & BI",
            "📋 Master Incident Ledger",
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

            # Apply Global Sidebar Filters to DataFrame
            filtered_ledger = df_ledger[
                (df_ledger["Status"].isin(filter_status))
                & (df_ledger["Severity"].isin(filter_severity))
            ]
        else:
            filtered_ledger = df_ledger

    # =========================================================================
    # MAIN AREA CONTENT (BASED ON SIDEBAR NAVIGATION)
    # =========================================================================

    # -------------------------------------------------------------------------
    # VIEW 1: EXECUTIVE COMMAND OVERVIEW
    # -------------------------------------------------------------------------
    if current_view == "🏠 Executive Command Overview":
        st.title("🏠 Executive Command Center")
        st.caption("Real-time City Metrics & High-Level Emergency Overview")

        # Top Metric Bar
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
            st.subheader("📍 Active GIS Hazard Quick Map")
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
                        f"**{row['ID']}** | {row['Hazard']}\n\n⏱️ **SLA:** {row['SLA Target']} | 📌 **Status:** {row['Status']}"
                    )
            else:
                st.success("🎉 No active Critical Hazards pending!")

    # -------------------------------------------------------------------------
    # VIEW 2: AI VISUAL DETECTION ENGINE
    # -------------------------------------------------------------------------
    elif current_view == "🔍 AI Visual Detection Engine":
        st.title("🔍 AI Inspection & Emergency Dispatch")
        st.caption(
            f"Active Detection Engine | Confidence Threshold: `{conf_threshold}`"
        )

        processed_img = None
        current_counts = {}

        # --- MODE 1: SINGLE IMAGE ---
        if input_mode == "🖼️ Single Image":
            uploaded_file = st.file_uploader(
                "Upload Field Inspection Snapshot",
                type=["jpg", "jpeg", "png"],
            )
            if uploaded_file:
                img = Image.open(uploaded_file)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(img, caption="Original Input", use_container_width=True)

                if st.button("🔍 Execute AI Inference", key="btn_single"):
                    with st.spinner("Analyzing with YOLO Model..."):
                        processed_img, current_counts = run_detection(img)
                        st.session_state["processed_img"] = processed_img
                        st.session_state["counts"] = current_counts

                if "processed_img" in st.session_state:
                    with c2:
                        st.image(
                            st.session_state["processed_img"],
                            caption="YOLO AI Detections",
                            use_container_width=True,
                        )

        # --- MODE 2: BATCH PROCESSING ---
        elif input_mode == "📂 Batch Processing":
            uploaded_files = st.file_uploader(
                "Upload Multiple Hazard Images",
                type=["jpg", "png"],
                accept_multiple_files=True,
            )
            if uploaded_files and st.button("🚀 Process Batch"):
                batch_summary = {}
                cols = st.columns(min(len(uploaded_files), 3))

                for idx, file in enumerate(uploaded_files):
                    img = Image.open(file)
                    p_img, counts = run_detection(img)
                    with cols[idx % 3]:
                        st.image(
                            p_img,
                            caption=f"Image {idx+1}",
                            use_container_width=True,
                        )
                    for k, v in counts.items():
                        batch_summary[k] = batch_summary.get(k, 0) + v

                st.session_state["counts"] = batch_summary
                st.success(f"✅ Batch of {len(uploaded_files)} images processed!")

        # --- MODE 3: VIDEO STREAM ---
        elif input_mode == "🎥 Video Stream":
            uploaded_video = st.file_uploader(
                "Upload Video Stream", type=["mp4", "avi", "mov"]
            )
            if uploaded_video and st.button("🎥 Process Stream"):
                tfile = tempfile.NamedTemporaryFile(delete=False)
                tfile.write(uploaded_video.read())
                cap = cv2.VideoCapture(tfile.name)
                st_frame = st.empty()
                v_counts = {}
                last_frame = None

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    proc_frame, counts = run_detection(pil_img)
                    last_frame = proc_frame
                    st_frame.image(
                        proc_frame,
                        caption="Live Stream Analysis",
                        use_container_width=True,
                    )
                    for k, v in counts.items():
                        v_counts[k] = v_counts.get(k, 0) + v

                cap.release()
                st.session_state["counts"] = v_counts
                if last_frame:
                    st.session_state["processed_img"] = last_frame
                st.success("✅ Video Stream Analysis Complete!")

        # --- MODE 4: LIVE CAMERA ---
        elif input_mode == "📸 Live Camera":
            cam_photo = st.camera_input("Capture Field Photo")
            if cam_photo and st.button("🔍 Analyze Snapshot"):
                img = Image.open(cam_photo)
                proc_img, counts = run_detection(img)
                st.session_state["processed_img"] = proc_img
                st.session_state["counts"] = counts
                st.image(proc_img, caption="Camera Detection", use_container_width=True)

        # ---------------------------------------------------------------------
        # DISPATCH & REPORTING SECTION
        # ---------------------------------------------------------------------
        if "counts" in st.session_state and st.session_state["counts"]:
            st.divider()
            st.subheader("🚨 Inspection Results & SLA Dispatch")

            severity_label, color_code, sla_target = calculate_severity_and_sla(
                st.session_state["counts"]
            )

            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write("### Detected Hazards:")
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

            summary_text = "UrbanEye AI Summary:\n" + "\n".join(
                [f"- {k.title()}: {v}" for k, v in st.session_state["counts"].items()]
            )
            p_img = st.session_state.get("processed_img", None)

            pdf_bytes = create_pdf_report(
                title=title,
                user_details=user_details,
                summary_text=summary_text,
                detected_image=p_img,
            )

            btn1, btn2, btn3 = st.columns(3)
            with btn1:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"Incident_{title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            with btn2:
                if st.button("📩 Send Email Alert", use_container_width=True):
                    ok, msg = send_email_with_pdf(
                        sender_email=user_details["email"],
                        target_department_email=dept_email,
                        pdf_bytes=pdf_bytes,
                        title=title,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
            with btn3:
                if st.button("💾 Log to Master Ledger", use_container_width=True):
                    new_id = f"INC-{1001 + len(df_ledger)}"
                    primary_hazard = list(st.session_state["counts"].keys())[0].title()
                    new_row = pd.DataFrame(
                        [
                            {
                                "ID": new_id,
                                "Hazard": primary_hazard,
                                "Severity": severity_label,
                                "SLA Target": sla_target,
                                "Status": "Pending",
                                "Latitude": 31.5204 + (np.random.randn() * 0.01),
                                "Longitude": 74.3587 + (np.random.randn() * 0.01),
                                "Timestamp": pd.Timestamp.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                ),
                            }
                        ]
                    )
                    st.session_state["incident_ledger"] = pd.concat(
                        [df_ledger, new_row], ignore_index=True
                    )
                    st.success(f"✅ Added {new_id} to Ledger!")

    # -------------------------------------------------------------------------
    # VIEW 3: GIS LIVE INCIDENT MAP
    # -------------------------------------------------------------------------
    elif current_view == "🗺️ GIS Live Incident Map":
        st.title("🗺️ Interactive GIS City Map")
        st.caption("Live geographical plotting based on sidebar global filters")

        map_data = filtered_ledger[["Latitude", "Longitude"]].rename(
            columns={"Latitude": "lat", "Longitude": "lon"}
        )
        st.map(map_data, zoom=12)

        st.subheader("Filtered Location Registry")
        st.dataframe(filtered_ledger, use_container_width=True)

    # -------------------------------------------------------------------------
    # VIEW 4: CITY ANALYTICS & BI
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
    # VIEW 5: MASTER INCIDENT LEDGER
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
        )

    # -------------------------------------------------------------------------
    # VIEW 6: FIX VERIFICATION (BEFORE / AFTER) - NEW FEATURE!
    # -------------------------------------------------------------------------
    elif current_view == "✅ Fix Verification (Before/After)":
        st.title("✅ Municipal Fix Verification Engine")
        st.caption("Upload 'After Fix' evidence to resolve active pending incidents")

        pending_incidents = df_ledger[df_ledger["Status"] != "Resolved"]

        if pending_incidents.empty:
            st.success("🎉 All incidents have been verified and resolved!")
        else:
            selected_inc_id = st.selectbox(
                "Select Incident to Verify & Close:",
                pending_incidents["ID"].tolist(),
            )

            inc_details = pending_incidents[
                pending_incidents["ID"] == selected_inc_id
            ].iloc[0]

            st.info(
                f"**Selected:** {inc_details['ID']} | **Hazard:** {inc_details['Hazard']} | **Current Status:** `{inc_details['Status']}`"
            )

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📷 Original Hazard (Before)")
                st.warning("Original inspection evidence attached in database.")

            with c2:
                st.subheader("📸 Upload Fix Evidence (After)")
                after_file = st.file_uploader(
                    "Upload Repair Photo", type=["jpg", "png"]
                )
                if after_file:
                    st.image(
                        Image.open(after_file),
                        caption="After Repair Evidence",
                        use_container_width=True,
                    )

            if after_file and st.button("🟢 Mark as Resolved & Verify"):
                # Update status in DataFrame
                st.session_state["incident_ledger"].loc[
                    st.session_state["incident_ledger"]["ID"] == selected_inc_id,
                    "Status",
                ] = "Resolved"
                st.success(
                    f"✅ {selected_inc_id} has been successfully verified and status changed to RESOLVED!"
                )
                st.balloons()
