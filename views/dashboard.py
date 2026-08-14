import os
import random
import streamlit as st

# Safe imports with fallback definitions to prevent any startup crash
try:
    from utils.metadata import get_user_metadata
except Exception:
    def get_user_metadata():
        return {
            "username": "Officer Ahmed",
            "email": "officer@urbaneye.ai",
            "phone": "+92 300 1234567",
            "address": "Iqbal Sector, Block AA, Lahore"
        }

try:
    from utils.helpers import initialize_mock_history, generate_tracking_id
except Exception:
    def initialize_mock_history():
        pass

    def generate_tracking_id():
        return "URB-2026-001"

try:
    from views.map_view import render_map_page
except Exception:
    def render_map_page():
        st.warning("Map view component unavailable.")

try:
    from report.report_tracker import render_report_tracker
except Exception:
    def render_report_tracker():
        st.warning("Report tracker component unavailable.")

try:
    from views.profile_view import render_profile_page
except Exception:
    def render_profile_page(ud):
        st.warning("Profile view component unavailable.")

try:
    from components.single_image import render_single_image_mode
except Exception:
    def render_single_image_mode(th):
        st.warning("Single image mode unavailable.")

try:
    from components.batch_processing import render_batch_processing_mode
except Exception:
    def render_batch_processing_mode(th):
        st.warning("Batch processing unavailable.")

try:
    from components.video_stream import render_video_stream_mode
except Exception:
    def render_video_stream_mode(th):
        st.warning("Video stream unavailable.")

try:
    from components.live_camera import render_live_camera_mode
except Exception:
    def render_live_camera_mode(th):
        st.warning("Live camera unavailable.")

try:
    from components.dispatch_panel import render_dispatch_panel
except Exception:
    def render_dispatch_panel(tid, loc, ud, pdf_fn):
        st.warning("Dispatch panel unavailable.")


# ==========================================================
# PDF REPORT GENERATOR
# ==========================================================

def create_pdf_report(
    title: str,
    user_details: dict = None,
    summary_text: str = "",
    detected_images=None,
) -> bytes:

    try:
        from fpdf import FPDF
        import numpy as np
        from PIL import Image
        import tempfile

        class ProfessionalPDF(FPDF):

            def header(self):
                self.set_fill_color(24, 43, 73)
                self.rect(0, 0, 210, 22, "F")

                self.set_fill_color(0, 168, 204)
                self.rect(0, 22, 210, 2, "F")

                self.set_text_color(255, 255, 255)
                self.set_font("Helvetica", "B", 12)
                self.set_xy(10, 6)

                self.cell(
                    0,
                    10,
                    "URBAN EYE AI - MUNICIPAL HAZARD INSPECTION REPORT",
                    align="C"
                )

                self.ln(20)

            def footer(self):
                self.set_y(-15)
                self.set_draw_color(210, 215, 220)
                self.line(10, self.get_y(), 200, self.get_y())

                self.set_font("Helvetica", "I", 8)
                self.set_text_color(128, 128, 128)

                self.cell(
                    0,
                    10,
                    f"Page {self.page_no()} | Confidential - UrbanEye AI Automated Verification System",
                    align="C"
                )

            def section_heading(self, title: str):
                self.ln(4)

                self.set_fill_color(230, 238, 248)
                self.set_text_color(24, 43, 73)
                self.set_font("Helvetica", "B", 10)

                self.cell(
                    0,
                    7,
                    f"  {title}",
                    0,
                    1,
                    "L",
                    fill=True
                )

                self.ln(3)

        pdf = ProfessionalPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        if (
            not user_details
            or not isinstance(user_details, dict)
            or not user_details.get("username")
        ):
            try:
                user_details = get_user_metadata()
            except Exception:
                user_details = {}

        def sanitize(text):
            if not text:
                return "N/A"

            return (
                str(text)
                .replace("•", "-")
                .encode("latin-1", "replace")
                .decode("latin-1")
            )

        safe_title = sanitize(title)
        safe_summary = sanitize(summary_text)

        u_name = sanitize(
            user_details.get("username", "Inspector Ahmed")
        )

        u_email = sanitize(
            user_details.get("email", "officer@urbaneye.ai")
        )

        u_phone = sanitize(
            user_details.get("phone", "+92 300 1234567")
        )

        u_address = sanitize(
            user_details.get("address", "Lahore Urban Sector 4")
        )

        # SECTION 1
        pdf.section_heading("1. INCIDENT & OFFICER METADATA")

        pdf.set_draw_color(210, 215, 220)
        pdf.set_fill_color(248, 249, 250)

        box_y = pdf.get_y()

        pdf.rect(
            10,
            box_y,
            190,
            32,
            "DF"
        )

        pdf.set_xy(14, box_y + 4)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(24, 43, 73)

        pdf.cell(
            0,
            6,
            f"Report Title: {safe_title}"
        )

        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(60, 60, 60)

        pdf.set_xy(14, box_y + 12)

        pdf.cell(
            95,
            5,
            f"Reported By: {u_name}"
        )

        pdf.cell(
            85,
            5,
            f"Phone: {u_phone}"
        )

        pdf.set_xy(14, box_y + 19)

        pdf.cell(
            95,
            5,
            f"Email: {u_email}"
        )

        pdf.cell(
            85,
            5,
            f"Location / Dept: {u_address}"
        )

        pdf.set_y(box_y + 36)

        # SECTION 2
        if detected_images:

            if not isinstance(detected_images, list):
                detected_images = [detected_images]

            pdf.section_heading(
                f"2. VISUAL INSPECTION EVIDENCE ({len(detected_images)} AI SNAPSHOTS)"
            )

            for idx, img in enumerate(detected_images):

                if img is None:
                    continue

                if isinstance(img, np.ndarray):
                    img_pil = Image.fromarray(img)

                elif isinstance(img, Image.Image):
                    img_pil = img

                else:
                    continue

                if img_pil.mode in ("RGBA", "P"):
                    img_to_save = img_pil.convert("RGB")
                else:
                    img_to_save = img_pil

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".png"
                ) as tmp:

                    img_to_save.save(
                        tmp.name,
                        format="PNG"
                    )

                    tmp_path = tmp.name

                pdf.ln(2)

                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(100, 100, 100)

                pdf.cell(
                    0,
                    5,
                    f"Evidence Snapshot #{idx + 1}",
                    ln=True
                )

                pdf.image(
                    tmp_path,
                    x=(210 - 130) / 2,
                    w=130
                )

                pdf.ln(6)

                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        # SECTION 3
        pdf.section_heading(
            "3. AI ANALYSIS BREAKDOWN & SUMMARY"
        )

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)

        pdf.ln(2)
        pdf.set_x(14)

        pdf.multi_cell(
            182,
            6,
            safe_summary
        )

        pdf.ln(4)

        pdf_output = pdf.output(dest="S")

        if isinstance(pdf_output, str):
            return pdf_output.encode("latin-1")

        elif isinstance(pdf_output, bytearray):
            return bytes(pdf_output)

        elif isinstance(pdf_output, bytes):
            return pdf_output

        return bytes(pdf_output)

    except Exception as e:

        from fpdf import FPDF

        fallback_pdf = FPDF()
        fallback_pdf.add_page()
        fallback_pdf.set_font("Helvetica", size=10)

        fallback_pdf.cell(
            0,
            10,
            f"Report Generated via Fallback Buffer. Error: {str(e)}"
        )

        out = fallback_pdf.output(dest="S")

        if isinstance(out, str):
            return out.encode("latin-1")

        return bytes(out)


# ==========================================================
# CSS
# ==========================================================

def load_css():

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    css_path = os.path.join(
        BASE_DIR,
        "style.css"
    )

    try:

        with open(
            css_path,
            "r",
            encoding="utf-8"
        ) as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

    except FileNotFoundError:
        pass


# ==========================================================
# RESET INPUT MODE
# ==========================================================

def handle_input_mode_change():

    st.session_state["counts"] = {}

    st.session_state.pop(
        "processed_img",
        None
    )

    st.session_state["captured_images"] = []

    st.session_state.pop(
        "current_tracking_id",
        None
    )

    st.session_state["stream_active"] = False


# ==========================================================
# LOGOUT
# ==========================================================

def logout_user():

    # Clear login/session information
    for key in [
        "user",
        "user_profile",
        "logged_in_email",
        "reset_verified",
        "reset_target_user_id",
        "reset_matched_email",
        "main_navigation",
        "input_source_mode",
        "current_tracking_id",
        "captured_images",
        "processed_img",
        "counts",
        "stream_active",
    ]:
        st.session_state.pop(key, None)

    # Clear URL query parameters
    try:
        st.query_params.clear()
    except Exception:
        pass

    # Redirect to login page
    st.switch_page("auth/login.py")


# ==========================================================
# DASHBOARD
# ==========================================================

def render_dashboard_page():

    load_css()

    initialize_mock_history()

    user_details = get_user_metadata()

    if "captured_images" not in st.session_state:
        st.session_state["captured_images"] = []

    # Keep only latest 3 images
    if len(st.session_state["captured_images"]) > 3:

        st.session_state["captured_images"] = (
            st.session_state["captured_images"][-3:]
        )

    if "counts" not in st.session_state:
        st.session_state["counts"] = {}

    # ======================================================
    # SIDEBAR
    # NEW ORDER ONLY
    # ======================================================

    with st.sidebar:

        st.divider()

        # --------------------------------------------------
        # 2. USERNAME
        # --------------------------------------------------

        st.markdown(
            f"**👤 Officer:** "
            f"{user_details.get('username', 'Officer')}"
        )

        # --------------------------------------------------
        # 3. SYSTEM STATUS
        # --------------------------------------------------

        st.caption(
            "🟢 System Status: **Online & Synced**"
        )

        st.divider()

        # --------------------------------------------------
        # 4. INPUT MEDIA SOURCE
        # --------------------------------------------------

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
            key="input_source_mode",
            on_change=handle_input_mode_change
        )

        # --------------------------------------------------
        # 5. DETECTOR SETTINGS
        # --------------------------------------------------

        if True:

            st.subheader(
                "⚙️ Detector Settings"
            )

            conf_threshold = st.slider(
                "YOLO Confidence Threshold",
                0.1,
                1.0,
                0.45,
                step=0.05,
                key="dashboard_yolo_conf_slider"
            )

        st.divider()

        # --------------------------------------------------
        # 6. NAVIGATION MENU
        # --------------------------------------------------

        st.subheader(
            "🧭 Navigation Menu"
        )

        current_view = st.radio(
            "Go To View:",
            [
                "🔍 AI Visual Detection Engine",
                "🔎 Public Hazard Tracker",
                "🗺️ Interactive Map",
                "👤 My Profile & Reports"
            ],
            key="main_navigation"
        )

        st.divider()

        # --------------------------------------------------
        # 7. LOGOUT
        # --------------------------------------------------

        st.subheader("🔐 Account")

        if st.button(
            "🚪 Logout",
            use_container_width=True,
            key="logout_button"
        ):
            logout_user()

    # ======================================================
    # MAIN CONTENT
    # ======================================================

    if current_view == "🔍 AI Visual Detection Engine":

        st.title(
            "🔍 AI Inspection Engine"
        )

        st.caption(
            f"Active Mode: **{input_mode}** | "
            f"YOLO Confidence Threshold: "
            f"`{conf_threshold}`"
        )

        if (
            "current_tracking_id" not in st.session_state
            or not st.session_state["current_tracking_id"]
        ):

            st.session_state[
                "current_tracking_id"
            ] = generate_tracking_id()

        st.divider()

        # --------------------------------------------------
        # DETECTION MODES
        # --------------------------------------------------

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

        # --------------------------------------------------
        # EVIDENCE
        # --------------------------------------------------

        all_evidence_images = (
            st.session_state.get(
                "captured_images",
                []
            )
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

        # --------------------------------------------------
        # DISPATCH PANEL
        # --------------------------------------------------

        render_dispatch_panel(
            st.session_state[
                "current_tracking_id"
            ],
            manual_loc_name,
            user_details,
            create_pdf_report
        )

    # ======================================================
    # PUBLIC HAZARD TRACKER
    # ======================================================

    elif current_view == "🔎 Public Hazard Tracker":

        render_report_tracker()

    # ======================================================
    # INTERACTIVE MAP
    # ======================================================

    elif current_view == "🗺️ Interactive Map":

        render_map_page()

    # ======================================================
    # PROFILE
    # ======================================================

    elif current_view == "👤 My Profile & Reports":

        render_profile_page(
            user_details
        )


# ==========================================================
# RUN DASHBOARD
# ==========================================================

if __name__ == "__main__":
    render_dashboard_page()
