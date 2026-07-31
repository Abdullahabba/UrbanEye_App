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


# ==========================================================
# Report Module Import Fallback
# ==========================================================

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
        module = __import__(
            mod[0],
            fromlist=[mod[1]]
        )

        create_pdf_report = getattr(
            module,
            mod[1]
        )

        break

    except (
        ModuleNotFoundError,
        AttributeError
    ):
        continue



# ==========================================================
# Load External CSS
# ==========================================================

def load_css():

    try:

        with open(
            "style.css",
            "r",
            encoding="utf-8"
        ) as f:

            st.markdown(
                f"""
                <style>
                {f.read()}
                </style>
                """,
                unsafe_allow_html=True
            )

    except FileNotFoundError:

        pass



# ==========================================================
# Premium UI Helpers
# ==========================================================

def render_header(user_details):

    username = user_details.get(
        "username",
        "Officer"
    )

    st.markdown(
        f"""
        <div class="hero-card">

            <div class="hero-content">

                <h1>
                    👁️ UrbanEye AI
                    Command Center
                </h1>

                <p>
                    Smart City Detection &
                    Automated Hazard Response System
                </p>

                <span class="status-badge">
                    🟢 System Online |
                    Officer: {username}
                </span>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )



def render_section(title, subtitle=""):

    st.markdown(
        f"""
        <div class="section-title">

            <h2>
                {title}
            </h2>

            <p>
                {subtitle}
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )



# ==========================================================
# Dashboard Page
# ==========================================================

def render_dashboard_page():

    load_css()


    initialize_mock_history()


    user_details = get_user_metadata()



    # Initialize captured images

    if "captured_images" not in st.session_state:

        st.session_state["captured_images"] = []



    # ======================================================
    # SIDEBAR
    # ======================================================

    with st.sidebar:


        st.markdown(
            """
            <div class="sidebar-logo">

                <h1>
                    👁️ UrbanEye AI
                </h1>

                <p>
                    Smart City Intelligence
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


        st.divider()



        st.markdown(
            f"""
            <div class="user-panel">

                👤
                <b>Officer</b>

                <br>

                {user_details['username']}

                <br><br>

                🟢
                System Status:
                Online & Synced

            </div>
            """,
            unsafe_allow_html=True
        )


        st.divider()



        st.subheader(
            "🧭 Navigation Menu"
        )


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


            st.subheader(
                "⚙️ Detector Settings"
            )


            conf_threshold = st.slider(

                "YOLO Confidence Threshold",

                0.1,

                1.0,

                0.45,

                step=0.05

            )


            st.subheader(
                "📷 Input Media Source"
            )


            input_mode = st.radio(

                "Select Source Type:",

                [
                    "🖼️ Single Image",
                    "📂 Batch Processing",
                    "🎥 Video Stream",
                    "📸 Live Camera"
                ],

                key="input_source_mode"

            )


        else:

            conf_threshold = 0.45

            input_mode = "🖼️ Single Image"



    # ======================================================
    # MAIN AREA
    # ======================================================


    render_header(
        user_details
    )
    
    # ======================================================
    # AI VISUAL DETECTION ENGINE
    # ======================================================

    if current_view == "🔍 AI Visual Detection Engine":


        render_section(
            "🔍 AI Inspection Engine",
            f"Active Mode: {input_mode} | YOLO Confidence: {conf_threshold}"
        )


        if "current_tracking_id" not in st.session_state:

            st.session_state["current_tracking_id"] = generate_tracking_id()



        st.markdown(
            """
            <div class="feature-card">

                <h3>
                    🤖 AI Vision Processing
                </h3>

                <p>
                    Upload media and analyze hazards
                    using intelligent YOLO detection.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )



        # ==================================================
        # COMPONENT ROUTING
        # ==================================================

        if input_mode == "🖼️ Single Image":

            render_single_image_mode(
                conf_threshold
            )


        elif input_mode == "📂 Batch Processing":

            render_batch_processing_mode(
                conf_threshold
            )


        elif input_mode == "🎥 Video Stream":

            render_video_stream_mode(
                conf_threshold
            )


        elif input_mode == "📸 Live Camera":

            render_live_camera_mode(
                conf_threshold
            )



        # ==================================================
        # DISPATCH SECTION
        # ==================================================

        st.markdown(
            """
            <div class="feature-card dispatch-title">

                <h3>
                    📤 Dispatch & Verification Center
                </h3>

                <p>
                    Verify incidents, generate reports,
                    and synchronize with authorities.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )



        all_evidence_images = st.session_state.get(
            "captured_images",
            []
        )



        if (
            not all_evidence_images
            and "processed_img" in st.session_state
        ):

            all_evidence_images = [
                st.session_state["processed_img"]
            ]



        manual_loc_name = user_details.get(
            "address",
            "Iqbal Sector, Block AA, Lahore"
        )



        render_dispatch_panel(

            st.session_state["current_tracking_id"],

            manual_loc_name,

            user_details,

            create_pdf_report

        )



    # ======================================================
    # PUBLIC HAZARD TRACKER
    # ======================================================

    elif current_view == "🔎 Public Hazard Tracker":


        render_section(

            "🔎 Public Hazard Tracker",

            "Monitor synchronized municipal hazard reports."

        )


        st.markdown(
            """
            <div class="info-banner">

                📡 Live Incident Monitoring Dashboard

            </div>
            """,
            unsafe_allow_html=True
        )


        render_report_tracker()



    # ======================================================
    # INTERACTIVE MAP
    # ======================================================

    elif current_view == "🗺️ Interactive Map":


        render_section(

            "🗺️ Interactive Map & Geo Tracking",

            "Visualize reported incidents across locations."

        )


        st.markdown(
            """
            <div class="info-banner">

                📍 Geographic Hazard Intelligence System

            </div>
            """,
            unsafe_allow_html=True
        )


        render_map_page()
        
# ==========================================================
# Application Entry Point
# ==========================================================

if __name__ == "__main__":

    render_dashboard_page()
