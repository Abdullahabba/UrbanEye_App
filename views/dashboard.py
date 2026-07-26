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

# 🌌 Page Configuration - Cyber Command Center
st.set_page_config(
    page_title="UrbanEye AI — Global Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ⚡ Advanced Glassmorphism & Cyber-Dark CSS Styling
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
        padding: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Hero Command Banner */
    .cyber-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid #38bdf8;
        padding: 28px 35px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 25px;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15);
    }

    /* Emergency Live Ticker */
    .emergency-ticker {
        background: rgba(239, 68, 68, 0.15);
        border-left: 4px solid #ef4444;
        padding: 10px 15px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: #fca5a5;
        margin-bottom: 20px;
    }

    /* Futuristic Monospace Metrics */
    .mono-text {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0ea5e9 0%, #3b82f6 100%);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
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

    # 🛡️ EXTREME SIDEBAR COMMAND CENTER
    with st.sidebar:
        st.markdown("### 👁️ URBANEYE // SECURE")
        st.caption("Autonomous Municipal Intelligence")
        st.divider()
        
        st.markdown(f"**👤 Operative:** `{user_details['username']}`")
        st.markdown(f"**📍 Sector Zone:** `{user_details['address']}`")
        st.markdown("🟢 **Node Status:** `CONNECTED [0.4ms]`")
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

        st.divider()
        st.caption("⚡ Core Engine: YOLOv8-X + TensorRT\n🔒 Encryption: AES-256-GCM")

    # 🖥️ MAIN COMMAND WINDOW
    if current_view == "🔍 AI Visual Detection Engine":
        
        # Cyber Banner
        st.markdown("""
            <div class="cyber-banner">
                <h1 style="margin:0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">🛡️ AI Visual Detection & Autonomous Dispatch Core</h1>
                <p style="margin:8px 0 0 0; color: #94a3b8; font-size: 14px;">Real-time multi-hazard vector classification and encrypted municipal transmission.</p>
            </div>
        """, unsafe_allow_html=True)

        # Live Emergency Incident Ticker
        st.markdown("""
            <div class="emergency-ticker">
                🚨 <b>SYSTEM BROADCAST:</b> Active surveillance running across Sector Grid. Zero-tolerance policy engaged for high-severity structural anomalies.
            </div>
        """, unsafe_allow_html=True)

        if "current_tracking_id" not in st.session_state:
            st.session_state["current_tracking_id"] = generate_tracking_id()

        # Extreme Telemetry Bar (CPU, GPU, Latency, SLA)
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            st.metric("TRACKING ID", st.session_state["current_tracking_id"])
        with col_t2:
            st.metric("INFERENCE LATENCY", "14.2 ms", "-2.1 ms")
        with col_t3:
            st.metric("GPU MEMORY", "3.8 GB / 16 GB", "24%")
        with col_t4:
            st.metric("SLA TARGET", "12 Hours", "Guaranteed")

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
                <h1 style="margin:0; font-size: 28px; font-weight: 700;">🔎 Public Hazard Ledger & Audit Trail</h1>
                <p style="margin:8px 0 0 0; color: #94a3b8; font-size: 14px;">Immutable event logs, verification states, and department routing history.</p>
            </div>
        """, unsafe_allow_html=True)
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        st.markdown("""
            <div class="cyber-banner">
                <h1 style="margin:0; font-size: 28px; font-weight: 700;">🗺️ Geo-Spatial Threat Heatmap</h1>
                <p style="margin:8px 0 0 0; color: #94a3b8; font-size: 14px;">Live satellite grid overlay tracking infrastructure degradation metrics.</p>
            </div>
        """, unsafe_allow_html=True)
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
