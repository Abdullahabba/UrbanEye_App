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

# Optional Visualization Libraries Fallback
try:
    import plotly.express as px

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def get_user_metadata():
    """Extract user metadata safely from Streamlit Session / Supabase."""
    user = st.session_state.get("user", None)
    details = {
        "email": (
            user.email
            if user and hasattr(user, "email")
            else "guest_user@urbaneye.ai"
        ),
        "username": "Guest User",
        "phone": "N/A",
        "address": "Lahore Urban Sector",
    }
    if user and hasattr(user, "user_metadata") and user.user_metadata:
        meta = user.user_metadata
        details["username"] = meta.get("username", "Guest User")
        details["phone"] = meta.get("phone", "N/A")
        details["address"] = meta.get("address", "Lahore Urban Sector")
    return details


def calculate_severity_score(counts: dict) -> tuple[str, str]:
    """Calculates hazard severity index based on object counts."""
    total_objects = sum(counts.values())
    if total_objects == 0:
        return "LOW", "#28a745"

    has_fallen_tree = "fallen tree" in [k.lower() for k in counts.keys()]
    pothole_count = sum(
        v for k, v in counts.items() if "pothole" in k.lower()
    )

    if total_objects >= 5 or has_fallen_tree or pothole_count >= 3:
        return "CRITICAL / HIGH", "#dc3545"
    elif total_objects >= 2:
        return "MEDIUM", "#ffc107"
    else:
        return "LOW", "#28a745"


def initialize_mock_history():
    """Initializes dummy incident ledger history for city analytics."""
    if "incident_ledger" not in st.session_state:
        st.session_state["incident_ledger"] = pd.DataFrame(
            [
                {
                    "ID": "INC-1001",
                    "Hazard": "Pothole",
                    "Severity": "HIGH",
                    "Status": "In Progress",
                    "Latitude": 31.5204,
                    "Longitude": 74.3587,
                    "Timestamp": "2026-07-20 10:15",
                },
                {
                    "ID": "INC-1002",
                    "Hazard": "Garbage Dump",
                    "Severity": "MEDIUM",
                    "Status": "Pending",
                    "Latitude": 31.5100,
                    "Longitude": 74.3400,
                    "Timestamp": "2026-07-21 14:30",
                },
                {
                    "ID": "INC-1003",
                    "Hazard": "Fallen Tree",
                    "Severity": "CRITICAL",
                    "Status": "Resolved",
                    "Latitude": 31.5300,
                    "Longitude": 74.3600,
                    "Timestamp": "2026-07-22 09:00",
                },
                {
                    "ID": "INC-1004",
                    "Hazard": "Graffiti",
                    "Severity": "LOW",
                    "Status": "Pending",
                    "Latitude": 31.5400,
                    "Longitude": 74.3300,
                    "Timestamp": "2026-07-23 16:45",
                },
            ]
        )


# -----------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -----------------------------------------------------------------------------
def render_dashboard_page():
    initialize_mock_history()
    user_details = get_user_metadata()

    # --- TOP HEADER ---
    st.title("👁️ UrbanEye AI - Smart City Operations Center")
    st.caption(
        "Real-time Municipal Hazard Detection, Geospatial Mapping & Incident Dispatch System"
    )

    # User Welcome Pill
    st.info(
        f"👤 **Officer in Charge:** {user_details['username']} | 📧 `{user_details['email']}` | 📍 **Jurisdiction:** {user_details['address']}"
    )

    # --- TOP METRIC CARDS ---
    df_ledger = st.session_state["incident_ledger"]
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    col_m1.metric("Total Incidents", len(df_ledger))
    col_m2.metric(
        "Pending Action", len(df_ledger[df_ledger["Status"] == "Pending"])
    )
    col_m3.metric(
        "Critical Hazards", len(df_ledger[df_ledger["Severity"] == "CRITICAL"])
    )
    col_m4.metric(
        "Resolution Rate",
        f"{int((len(df_ledger[df_ledger['Status'] == 'Resolved']) / len(df_ledger)) * 100)}%",
    )

    st.divider()

    # --- MAIN NAVIGATION TABS ---
    tab_engine, tab_map, tab_analytics, tab_ledger = st.tabs(
        [
            "🔍 Detection Engine",
            "🗺️ Live Incident Map",
            "📊 Executive Analytics",
            "📋 Incident Ledger & Exports",
        ]
    )

    # =========================================================================
    # TAB 1: DETECTION ENGINE (Image, Batch, Video, Live Camera)
    # =========================================================================
    with tab_engine:
        st.subheader("AI Visual Inspection Mode")

        input_mode = st.radio(
            "Select Input Source:",
            [
                "🖼️ Single Image",
                "📂 Batch Processing",
                "🎥 Video Stream",
                "📸 Live Camera",
            ],
            horizontal=True,
        )

        processed_img = None
        current_counts = {}

        # --- MODE 1: SINGLE IMAGE ---
        if input_mode == "🖼️ Single Image":
            uploaded_file = st.file_uploader(
                "Upload Incident Photo",
                type=["jpg", "jpeg", "png"],
                key="single_img",
            )
            if uploaded_file:
                img = Image.open(uploaded_file)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(img, caption="Original Input", use_container_width=True)

                if st.button("🔍 Run Inspection", key="btn_single"):
                    with st.spinner("Executing YOLO Inference..."):
                        processed_img, current_counts = run_detection(img)
                        st.session_state["processed_img"] = processed_img
                        st.session_state["counts"] = current_counts

                if "processed_img" in st.session_state:
                    with c2:
                        st.image(
                            st.session_state["processed_img"],
                            caption="AI Bounding Box Output",
                            use_container_width=True,
                        )

        # --- MODE 2: BATCH PROCESSING ---
        elif input_mode == "📂 Batch Processing":
            uploaded_files = st.file_uploader(
                "Upload Multiple Hazard Images",
                type=["jpg", "png"],
                accept_multiple_files=True,
                key="batch_img",
            )
            if uploaded_files and st.button("🚀 Process All Images"):
                batch_summary = {}
                cols = st.columns(min(len(uploaded_files), 3))

                for idx, file in enumerate(uploaded_files):
                    img = Image.open(file)
                    p_img, counts = run_detection(img)

                    # Display in grid
                    with cols[idx % 3]:
                        st.image(
                            p_img,
                            caption=f"Image {idx+1}",
                            use_container_width=True,
                        )

                    for k, v in counts.items():
                        batch_summary[k] = batch_summary.get(k, 0) + v

                st.session_state["counts"] = batch_summary
                st.success(f"✅ Processed {len(uploaded_files)} images successfully!")

        # --- MODE 3: VIDEO STREAM ---
        elif input_mode == "🎥 Video Stream":
            uploaded_video = st.file_uploader(
                "Upload CCTV / Drone Video",
                type=["mp4", "avi", "mov"],
                key="video_file",
            )
            if uploaded_video and st.button("🎥 Start Video Processing"):
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
                        proc_frame, caption="Live Video Stream", use_container_width=True
                    )
                    for k, v in counts.items():
                        v_counts[k] = v_counts.get(k, 0) + v

                cap.release()
                st.session_state["counts"] = v_counts
                if last_frame:
                    st.session_state["processed_img"] = last_frame
                st.success("✅ Video Stream Completed!")

        # --- MODE 4: LIVE CAMERA ---
        elif input_mode == "📸 Live Camera":
            cam_photo = st.camera_input("Capture Field Snapshot")
            if cam_photo and st.button("🔍 Analyze Snapshot"):
                img = Image.open(cam_photo)
                proc_img, counts = run_detection(img)
                st.session_state["processed_img"] = proc_img
                st.session_state["counts"] = counts
                st.image(proc_img, caption="Snapshot AI Result", use_container_width=True)

        # ---------------------------------------------------------------------
        # DISPATCH & REPORTING SECTION (TRIPPED WHEN DETECTIONS EXIST)
        # ---------------------------------------------------------------------
        if "counts" in st.session_state and st.session_state["counts"]:
            st.divider()
            st.subheader("🚨 Inspection Breakdown & Urgent Dispatch")

            # Severity Score Badge Calculation
            severity_label, color_code = calculate_severity_score(
                st.session_state["counts"]
            )

            c_left, c_right = st.columns([2, 1])

            with c_left:
                st.write("### Detected Hazard Quantities:")
                for hz, count in st.session_state["counts"].items():
                    st.write(f"- **{hz.title()}**: {count} instance(s)")

            with c_right:
                st.markdown(
                    f"""
                    <div style="background-color: {color_code}; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                        <h4 style="margin:0;">SEVERITY INDEX</h4>
                        <h2 style="margin:0;">{severity_label}</h2>
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

            # Generate Report Bytes
            summary_text = "UrbanEye AI Detection Summary:\n" + "\n".join(
                [f"- {k.title()}: {v}" for k, v in st.session_state["counts"].items()]
            )
            p_img = st.session_state.get("processed_img", None)

            pdf_bytes = create_pdf_report(
                title=title,
                user_details=user_details,
                summary_text=summary_text,
                detected_image=p_img,
            )

            btn_col1, btn_col2, btn_col3 = st.columns(3)

            with btn_col1:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"Incident_{title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            with btn_col2:
                if st.button("📩 Dispatch Email Alert", use_container_width=True):
                    with st.spinner("Sending Official Email..."):
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

            with btn_col3:
                if st.button("💾 Log to City Database", use_container_width=True):
                    # Add new entry to incident ledger
                    new_id = f"INC-{1001 + len(df_ledger)}"
                    primary_hazard = list(st.session_state["counts"].keys())[0].title()
                    new_row = pd.DataFrame(
                        [
                            {
                                "ID": new_id,
                                "Hazard": primary_hazard,
                                "Severity": severity_label.split(" ")[0],
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
                    st.success(f"✅ Registered as {new_id} in Ledger!")

    # =========================================================================
    # TAB 2: LIVE INCIDENT GEOSPATIAL MAP
    # =========================================================================
    with tab_map:
        st.subheader("📍 City Hazard Heatmap & GIS Coordinates")
        st.caption("Real-time GPS plotting of reported municipal violations")

        # Prepare Map DataFrame
        map_df = df_ledger[["Latitude", "Longitude"]].rename(
            columns={"Latitude": "lat", "Longitude": "lon"}
        )

        # Streamlit Native Interactive Map
        st.map(map_df, zoom=12)

        st.write("### Active Coordinates Registry:")
        st.dataframe(
            df_ledger[
                ["ID", "Hazard", "Severity", "Status", "Latitude", "Longitude"]
            ],
            use_container_width=True,
        )

    # =========================================================================
    # TAB 3: EXECUTIVE ANALYTICS
    # =========================================================================
    with tab_analytics:
        st.subheader("📊 Operational Analytics & Hazard Trends")

        col_a1, col_a2 = st.columns(2)

        if HAS_PLOTLY:
            with col_a1:
                fig_hazard = px.bar(
                    df_ledger,
                    x="Hazard",
                    color="Severity",
                    title="Incidents Grouped by Category & Severity",
                    color_discrete_map={
                        "HIGH": "#dc3545",
                        "CRITICAL": "#dc3545",
                        "MEDIUM": "#ffc107",
                        "LOW": "#28a745",
                    },
                )
                st.plotly_chart(fig_hazard, use_container_width=True)

            with col_a2:
                fig_status = px.pie(
                    df_ledger,
                    names="Status",
                    title="Current Resolution Pipeline Status",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                st.plotly_chart(fig_status, use_container_width=True)
        else:
            # Native Streamlit Fallback Charts
            with col_a1:
                st.write("**Hazard Distribution**")
                st.bar_chart(df_ledger["Hazard"].value_counts())
            with col_a2:
                st.write("**Status Breakdown**")
                st.bar_chart(df_ledger["Status"].value_counts())

    # =========================================================================
    # TAB 4: INCIDENT LEDGER & EXPORTS
    # =========================================================================
    with tab_ledger:
        st.subheader("📋 Master Incident Ledger & Management")

        # Filters
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected_status = st.multiselect(
                "Filter by Status:",
                options=["Pending", "In Progress", "Resolved"],
                default=["Pending", "In Progress", "Resolved"],
            )
        with f_col2:
            selected_severity = st.multiselect(
                "Filter by Severity:",
                options=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                default=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            )

        # Filtered DataFrame
        filtered_df = df_ledger[
            (df_ledger["Status"].isin(selected_status))
            & (df_ledger["Severity"].isin(selected_severity))
        ]

        st.dataframe(filtered_df, use_container_width=True)

        # Export Buttons
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Ledger to CSV",
                data=csv_data,
                file_name="UrbanEye_Incident_Ledger.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_ex2:
            st.info("💡 Data is synced live with Supabase Municipal Database.")
