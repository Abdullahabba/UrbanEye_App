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

# 🌌 Page Configuration - Clean Command Center
st.set_page_config(
    page_title="UrbanEye AI — Municipal Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ⚡ Advanced Glassmorphism & Mobile-Responsive CSS Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;700&display=swap');

    .stApp {
        background-color: #07090e;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    /* Cyber Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1f2937;
    }

    /* Glassmorphic Command Cards */
    .command-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 15px;
    }

    /* Hero Command Banner */
    .cyber-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid #38bdf8;
        padding: 22px 26px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15);
    }

    /* Custom Buttons - Touch Friendly */
    .stButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 10px 16px;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0ea5e9 0%, #3b82f6 100%);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }

    /* 📱 MOBILE RESPONSIVE MEDIA QUERIES */
    @media (max-width: 768px) {
        .cyber-banner {
            padding: 16px 18px;
            margin-bottom: 15px;
        }
        .cyber-banner h1 {
            font-size: 20px !important;
        }
        .cyber-banner p {
            font-size: 12px !important;
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

    # 🛡️ SIDEBAR COMMAND CENTER
    with st.sidebar:
        st.markdown("### 👁️ URBANEYE // SECURE")
        st.caption("Autonomous Municipal Intelligence")
        st.divider()
        
        st.markdown(f"**👤 Operative:** `{user_details['username']}`")
        st.markdown(f"**📍 Sector Zone:** `{user_details['address']}`")
        st.markdown("🟢 **Status:** `Online`")
        st.divider()

        st.subheader("🌐 Navigation Core")
        current_view = st.radio(
            "Select Subsystem:", 
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
            st.subheader("⚙️ Neural Parameters")
            conf_threshold = st.slider("YOLO Confidence Threshold", 0.1, 1.0, 0.45, step=0.05)
            st.subheader("📡 Input Channel Matrix")
            input_mode = st.radio("Select Feed Source:", ["🖼️ Single Image", "📂 Batch Processing", "🎥 Video Stream", "📸 Live Camera"], key="input_source_mode", label_visibility="collapsed")
        else:
            conf_threshold, input_mode = 0.45, "🖼️ Single Image"

    # 🖥️ MAIN COMMAND WINDOW
    if current_view == "🔍 AI Visual Detection Engine":
        
        # Clean Cyber Banner
        st.markdown("""
            <div class="cyber-banner">
                <h1 style="margin:0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">🔍 AI Visual Detection & Dispatch Hub</h1>
                <p style="margin:5px 0 0 0; color: #94a3b8; font-size: 13px;">Real-time municipal hazard inspection and automated report generation.</p>
            </div>
        """, unsafe_allow_html=True)

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

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
            <div class="cyber-banner">
                <h1 style="margin:0; font-size: 24px; font-weight: 700;">🔎 Public Hazard Ledger & Audit Trail</h1>
                <p style="margin:5px 0 0 0; color: #94a3b8; font-size: 13px;">Review event logs, verification states, and department routing history.</p>
            </div>
        """, unsafe_allow_html=True)
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        st.markdown("""
            <div class="cyber-banner">
                <h1 style="margin:0; font-size: 24px; font-weight: 700;">🗺️ Geo-Spatial Threat Heatmap</h1>
                <p style="margin:5px 0 0 0; color: #94a3b8; font-size: 13px;">Live satellite grid overlay tracking infrastructure status.</p>
            </div>
        """, unsafe_allow_html=True)
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
