import random
import time
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

# 🌌 Page Configuration - Animated Enterprise Command Center
st.set_page_config(
    page_title="UrbanEye AI — Municipal Intelligence",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ⚡ Ultra-Professional CSS with Smooth Keyframe Animations & Micro-Interactions
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* 🎬 Smooth Page Entrance Animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Apply Fade-in to main structural containers */
    .block-container {
        animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Premium Sidebar with Fade */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
        animation: fadeIn 0.4s ease-out forwards;
    }

    /* Sleek Animated Header Banner */
    .app-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 24px 28px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .app-header:hover {
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 15px 30px -5px rgba(56, 189, 248, 0.1);
    }

    /* Modern Radio / Selectors */
    .stRadio > div {
        background: rgba(30, 41, 59, 0.5);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #334155;
        transition: background 0.2s ease;
    }

    /* ⚡ High-End Animated Action Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        width: 100%;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 100%, #1e40af 100%);
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.45);
        transform: translateY(-2px);
    }
    .stButton>button:active {
        transform: translateY(0px);
    }

    /* Card Containers with Hover Lift */
    .content-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.25s ease, border-color 0.25s ease;
    }
    .content-card:hover {
        border-color: #374151;
        transform: translateY(-2px);
    }

    /* Glowing Pulse Effect for Active Status */
    @keyframes pulseGlow {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.05); opacity: 1; filter: drop-shadow(0 0 8px rgba(34, 197, 94, 0.6)); }
        100% { transform: scale(0.95); opacity: 0.8; }
    }
    .pulsing-status {
        display: inline-block;
        animation: pulseGlow 2s infinite ease-in-out;
    }

    /* 📱 Mobile Responsiveness Fixes */
    @media (max-width: 768px) {
        .app-header {
            padding: 18px;
        }
        .app-header h1 {
            font-size: 20px !important;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 12px;
        }
    }

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

    if "captured_images" not in st.session_state:
        st.session_state["captured_images"] = []

    # 🧭 SIDEBAR PANEL
    with st.sidebar:
        st.markdown("### 👁️ UrbanEye AI")
        st.caption("Enterprise Municipal Core")
        st.divider()
        
        st.markdown(f"**👤 Officer:** `{user_details['username']}`")
        st.markdown(f"**📍 Sector:** `{user_details['address']}`")
        st.markdown("🟢 **Status:** <span class='pulsing-status'>`Active Session`</span>", unsafe_allow_html=True)
        st.divider()

        st.subheader("📌 Navigation")
        current_view = st.radio(
            "Select View:", 
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
            st.subheader("⚙️ Model Sensitivity")
            conf_threshold = st.slider("YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05)
            st.subheader("📁 Input Channel")
            input_mode = st.radio("Select Source:", ["🖼️ Single Image", "📂 Batch Processing", "🎥 Video Stream", "📸 Live Camera"], key="input_source_mode", label_visibility="collapsed")
        else:
            conf_threshold, input_mode = 0.45, "🖼️ Single Image"

    # 🖥️ MAIN CONTENT AREA
    if current_view == "🔍 AI Visual Detection Engine":
        
        # Animated Sleek Header Banner
        st.markdown("""
            <div class="app-header">
                <h1 style="margin:0; font-size: 24px; font-weight: 700; letter-spacing: -0.3px;">🔍 AI Visual Detection & Automated Dispatch</h1>
                <p style="margin:6px 0 0 0; color: #94a3b8; font-size: 13px;">Upload municipal infrastructure media to trigger computer vision detection and report compilation.</p>
            </div>
        """, unsafe_allow_html=True)

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

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
            <div class="app-header">
                <h1 style="margin:0; font-size: 24px; font-weight: 700;">🔎 Public Hazard Ledger</h1>
                <p style="margin:6px 0 0 0; color: #94a3b8; font-size: 13px;">Track registered municipal incidents, status updates, and department routing.</p>
            </div>
        """, unsafe_allow_html=True)
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        st.markdown("""
            <div class="app-header">
                <h1 style="margin:0; font-size: 24px; font-weight: 700;">🗺️ Geo-Spatial Incident Map</h1>
                <p style="margin:6px 0 0 0; color: #94a3b8; font-size: 13px;">Visual satellite mapping of reported hazards across regional sectors.</p>
            </div>
        """, unsafe_allow_html=True)
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
