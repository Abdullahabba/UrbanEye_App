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
from components.ui_cards import render_cyber_header

# 🌌 Page Configuration
st.set_page_config(
    page_title="UrbanEye AI — Enterprise Command",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ⚡ Aggressive CSS Cleanup to eliminate Streamlit's default awkward padding
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #030712;
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Wipe out default Streamlit header & margins */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 96% !important;
    }

    /* Sleek Custom Radio / Tabs container */
    .stRadio > div {
        background: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(56, 189, 248, 0.15);
        backdrop-filter: blur(10px);
    }

    /* Premium Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        transition: all 0.25s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

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

    if "captured_images" not in st.session_state:
        st.session_state["captured_images"] = []

    # 🚀 Render High-End Custom SaaS Header Component
    render_cyber_header(
        title="UrbanEye AI",
        subtitle="Autonomous Municipal Surveillance & Dispatch Core",
        username=user_details['username'],
        sector=user_details['address']
    )

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # 🎛️ Navigation and Controls Bar
    col_nav, col_conf = st.columns([3, 1])
    with col_nav:
        current_view = st.radio(
            "Navigation Core",
            ["🔍 AI Visual Detection Engine", "🔎 Public Hazard Tracker", "🗺️ Interactive Map"],
            key="main_navigation",
            horizontal=True,
            label_visibility="collapsed"
        )
    with col_conf:
        if current_view == "🔍 AI Visual Detection Engine":
            conf_threshold = st.slider("YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05)
        else:
            conf_threshold = 0.45

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # 🖥️ MAIN VIEW ROUTING
    if current_view == "🔍 AI Visual Detection Engine":
        
        input_mode = st.radio(
            "Input Channel Matrix",
            ["🖼️ Single Image", "📂 Batch Processing", "🎥 Video Stream", "📸 Live Camera"],
            key="input_source_mode",
            horizontal=True
        )

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # ROUTING TO MODULAR COMPONENTS
        if input_mode == "🖼️ Single Image":
            render_single_image_mode(conf_threshold)
        elif input_mode == "📂 Batch Processing":
            render_batch_processing_mode(conf_threshold)
        elif input_mode == "🎥 Video Stream":
            render_video_stream_mode(conf_threshold)
        elif input_mode == "📸 Live Camera":
            render_live_camera_mode(conf_threshold)

        default_manual_loc = user_details.get("address", "Iqbal Sector, Block AA, Lahore")

        # DISPATCH & REPORTING PANEL
        render_dispatch_panel(
            st.session_state["current_tracking_id"], 
            default_manual_loc, 
            user_details, 
            create_pdf_report
        )

    elif current_view == "🔎 Public Hazard Tracker":
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
