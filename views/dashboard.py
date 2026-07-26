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

# 🎨 Page Configuration & Professional Theme Setup
st.set_page_config(
    page_title="UrbanEye AI - Smart City Command Center",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🌐 Custom CSS for Professional SaaS UI Styling
st.markdown("""
    <style>
    /* Main Background & Font */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Professional Cards / Containers */
    .metric-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    
    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 25px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Buttons Customization */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    
    /* Hide default streamlit branding footer for clean look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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

    # Initialize captured images list for multi-image PDF reports
    if "captured_images" not in st.session_state:
        st.session_state["captured_images"] = []

    # 🧭 SIDEBAR CONTROL CENTER
    with st.sidebar:
        st.markdown("### 👁️ UrbanEye AI")
        st.caption("Municipal Intelligence & Command System")
        st.divider()
        
        # Officer Profile Card in Sidebar
        st.markdown(f"**👤 Officer:** `{user_details['username']}`")
        st.markdown(f"**📍 Jurisdiction:** `{user_details['address']}`")
        st.markdown("🟢 Status: **Online & Encrypted**")
        st.divider()

        st.subheader("🚀 Navigation")
        current_view = st.radio(
            "Select Module:", 
            [
                "🔍 AI Visual Detection Engine", 
                "🔎 Public Hazard Tracker", 
                "🗺️ Interactive Map"
            ], 
            key="main_navigation",
            label_visibility="collapsed"
        )
        st.divider()

        if current_view == "🔍 AI Visual Detection Engine":
            st.subheader("⚙️ Engine Parameters")
            conf_threshold = st.slider("YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05)
            st.subheader("📷 Input Channel")
            input_mode = st.radio("Select Source Type:", ["🖼️ Single Image", "📂 Batch Processing", "🎥 Video Stream", "📸 Live Camera"], key="input_source_mode", label_visibility="collapsed")
        else:
            conf_threshold, input_mode = 0.45, "🖼️ Single Image"

    # 🖥️ MAIN CONTENT AREA
    if current_view == "🔍 AI Visual Detection Engine":
        
        # Professional Hero Banner
        st.markdown("""
            <div class="hero-banner">
                <h1 style="margin:0; font-size: 26px; font-weight: 700;">🔍 AI Urban Inspection & Dispatch Hub</h1>
                <p style="margin:5px 0 0 0; color: #94a3b8; font-size: 14px;">Real-time computer vision threat assessment and automated municipal dispatching.</p>
            </div>
        """, unsafe_allow_html=True)

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

        # Top Executive Metrics Bar
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Tracking ID", st.session_state["current_tracking_id"])
        with col_m2:
            st.metric("Active Model", "YOLOv8 Municipal")
        with col_m3:
            st.metric("SLA Target", "12 Hours")
        with col_m4:
            st.metric("Cloud Sync", "Supabase Live")

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

        # Base default location fallback from officer user metadata
        default_manual_loc = user_details.get("address", "Iqbal Sector, Block AA, Lahore")

        # DISPATCH & REPORTING PANEL
        render_dispatch_panel(
            st.session_state["current_tracking_id"], 
            default_manual_loc, 
            user_details, 
            create_pdf_report
        )

    elif current_view == "🔎 Public Hazard Tracker":
        st.markdown("""
            <div class="hero-banner">
                <h1 style="margin:0; font-size: 26px; font-weight: 700;">🔎 Public Hazard Ledger & Tracker</h1>
                <p style="margin:5px 0 0 0; color: #94a3b8; font-size: 14px;">Monitor status updates, assigned departments, and resolution timelines.</p>
            </div>
        """, unsafe_allow_html=True)
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        st.markdown("""
            <div class="hero-banner">
                <h1 style="margin:0; font-size: 26px; font-weight: 700;">🗺️ Smart City Incident Heatmap</h1>
                <p style="margin:5px 0 0 0; color: #94a3b8; font-size: 14px;">Geo-spatial visualization of reported municipal issues across sectors.</p>
            </div>
        """, unsafe_allow_html=True)
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
