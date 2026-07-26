import streamlit as st
import streamlit.components.v1 as components
from utils.metadata import get_user_metadata
from utils.helpers import initialize_mock_history, generate_tracking_id
from views.map_view import render_map_page
from report.report_tracker import render_report_tracker

from components.single_image import render_single_image_mode
from components.batch_processing import render_batch_processing_mode
from components.video_stream import render_video_stream_mode
from components.live_camera import render_live_camera_mode
from components.dispatch_panel import render_dispatch_panel

# 🌌 Page Configuration
st.set_page_config(
    page_title="UrbanEye AI — Enterprise Command",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ⚡ Extreme Custom UI Injection (Tailwind + Custom Glassmorphic CSS + JS Animations)
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');

    .stApp {
        background: #030712;
        color: #f3f4f6;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Hide Default Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}

    /* Custom SaaS Navbar Component */
    .saas-nav {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
    }

    /* High-End Glass Card */
    .saas-card {
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.6) 0%, rgba(3, 7, 18, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .saas-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 15px 40px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
    }

    /* Glowing Status Badge */
    .glow-dot {
        height: 8px;
        width: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 12px #22c55e;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    /* Custom Input & Button Overrides */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 12px 24px;
        width: 100%;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }

    .stRadio > div {
        background: rgba(17, 24, 39, 0.5);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
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

    # 🚀 Custom SaaS Header Navigation Bar
    st.markdown(f"""
        <div class="saas-nav">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 10px; border-radius: 12px; font-size: 20px;">⚡</div>
                <div>
                    <h3 style="margin: 0; font-size: 18px; font-weight: 700; letter-spacing: -0.5px;">UrbanEye AI <span style="color: #3b82f6; font-size: 12px; border: 1px solid #3b82f6; padding: 2px 6px; border-radius: 6px; margin-left: 8px;">ENTERPRISE v2.5</span></h3>
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">Autonomous Municipal Surveillance & Dispatch Core</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 20px; font-size: 13px;">
                <div>👤 <span style="color: #f3f4f6; font-weight: 600;">{user_details['username']}</span></div>
                <div>📍 <span style="color: #9ca3af;">{user_details['address']}</span></div>
                <div style="display: flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); padding: 4px 10px; border-radius: 20px;">
                    <span class="glow-dot"></span>
                    <span style="color: #4ade80; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;">ONLINE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 🎛️ Sleek Control Dock (Tabs / Selectors)
    col_nav1, col_nav2 = st.columns([3, 1])
    with col_nav1:
        current_view = st.radio(
            "Navigation Core",
            ["🔍 AI Visual Detection Engine", "🔎 Public Hazard Tracker", "🗺️ Interactive Map"],
            key="main_navigation",
            horizontal=True,
            label_visibility="collapsed"
        )
    with col_nav2:
        if current_view == "🔍 AI Visual Detection Engine":
            conf_threshold = st.slider("YOLO Confidence", 0.1, 1.0, 0.45, step=0.05, label_visibility="collapsed")
        else:
            conf_threshold = 0.45

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # 🖥️ MAIN VIEW ROUTING
    if current_view == "🔍 AIVisual Detection Engine" or current_view == "🔍 AI Visual Detection Engine":
        
        # Sub-feed selection inside a card layout
        input_mode = st.radio(
            "Input Channel",
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
