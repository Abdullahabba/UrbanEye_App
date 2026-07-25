import random
import streamlit as st
from utils.metadata import get_user_metadata
from utils.helpers import initialize_mock_history, generate_tracking_id
from views.map_view import render_map_page
from report.report_tracker import render_report_tracker

from components.single_image import render_single_image_mode
from components.batch_processing import render_batch_processing_mode
from components.video_stream import render_video_stream_mode
from components.live_camera import render_live_camera_mode
from components.dispatch_panel import render_dispatch_panel

# Report Module Import Fallback
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

def render_dashboard_page():
    initialize_mock_history()
    user_details = get_user_metadata()

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
        current_view = st.radio(
            "Go To View:", 
            [
                "🔍 AI Visual Detection Engine", 
                "🔎 Public Hazard Tracker", 
                "🗺️ Interactive Map"
            ], 
            key="main_navigation"
        )
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
        else:
            manual_lat = 31.5204 + (random.random() * 0.005)
            manual_lon = 74.3587 + (random.random() * 0.005)
            manual_loc_name = f"Auto-GPS Location (Sector 4 - Lat: {manual_lat:.4f})"
            st.info(f"📡 GPS Locked Successfully! Coords: `{manual_lat:.4f}, {manual_lon:.4f}`")

        st.divider()

        # ROUTING TO MODULAR COMPONENTS
        if input_mode == "🖼️ Single Image":
            render_single_image_mode(conf_threshold)
        elif input_mode == "📂 Batch Processing":
            render_batch_processing_mode(conf_threshold)
        elif input_mode == "🎥 Video Stream":
            render_video_stream_mode(conf_threshold)
        elif input_mode == "📸 Live Camera":
            render_live_camera_mode(conf_threshold)

        # DISPATCH & REPORTING PANEL
        render_dispatch_panel(st.session_state["current_tracking_id"], manual_loc_name, user_details, create_pdf_report)

    elif current_view == "🔎 Public Hazard Tracker":
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
