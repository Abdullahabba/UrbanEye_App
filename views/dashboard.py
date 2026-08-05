import random
import os
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

# 🛡️ Report Module Import Fallback with Built-in Safe Generator
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
    except (ModuleNotFoundError, AttributeError, ImportError):
        continue

# Agar koi bhi external module na mile, toh app ko crash hone se bachane ke liye safe fallback generator
if create_pdf_report is None:
    try:
        from fpdf import FPDF
        import numpy as np
        from PIL import Image
        import tempfile

        def create_pdf_report(title: str, user_details: dict = None, summary_text: str = "", detected_images=None) -> bytes:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Header
            pdf.set_fill_color(24, 43, 73)
            pdf.rect(0, 0, 210, 20, "F")
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_xy(10, 6)
            pdf.cell(0, 8, "URBAN EYE AI - INCIDENT REPORT", align="C")
            pdf.ln(18)

            # Title & Summary
            pdf.set_text_color(24, 43, 73)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, f"Report: {title}", ln=True)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 6, summary_text)
            pdf.ln(5)

            # Images Section
            if detected_images:
                if not isinstance(detected_images, list):
                    detected_images = [detected_images]
                
                for idx, img in enumerate(detected_images):
                    if img is None:
                        continue
                    if isinstance(img, np.ndarray):
                        img_pil = Image.fromarray(img)
                    elif isinstance(img, Image.Image):
                        img_pil = img
                    else:
                        continue

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        img_pil.convert("RGB").save(tmp.name, format="PNG")
                        tmp_path = tmp.name

                    pdf.set_font("Helvetica", "I", 9)
                    pdf.cell(0, 5, f"Evidence Snapshot #{idx + 1}", ln=True)
                    try:
                        pdf.image(tmp_path, x=40, w=130)
                        pdf.ln(5)
                    except Exception:
                        pass
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass

            pdf_output = pdf.output()
            if isinstance(pdf_output, str):
                return pdf_output.encode("latin-1")
            elif isinstance(pdf_output, bytearray):
                return bytes(pdf_output)
            return bytes(pdf_output)
    except Exception:
        def create_pdf_report(*args, **kwargs):
            return b"%PDF-1.4 Fallback PDF Buffer"

def load_css():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(BASE_DIR, "style.css")
    
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        pass
        
def render_dashboard_page():
    load_css()
    
    initialize_mock_history()
    user_details = get_user_metadata()

    if "captured_images" not in st.session_state:
        st.session_state["captured_images"] = []

    # SIDEBAR CONTROL CENTER
    with st.sidebar:
        st.title("👁️ UrbanEye AI")
        st.caption("Smart City Detection & Tracking")
        st.divider()
        st.markdown(f"**👤 Officer:** {user_details.get('username', 'Officer')}")
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
        all_evidence_images = st.session_state.get("captured_images", [])
        if not all_evidence_images and "processed_img" in st.session_state:
            all_evidence_images = [st.session_state["processed_img"]]

        manual_loc_name = user_details.get("address", "Iqbal Sector, Block AA, Lahore")

        render_dispatch_panel(
            st.session_state["current_tracking_id"], 
            manual_loc_name, 
            user_details, 
            create_pdf_report
        )

    elif current_view == "🔎 Public Hazard Tracker":
        render_report_tracker()

    elif current_view == "🗺️ Interactive Map":
        render_map_page()

if __name__ == "__main__":
    render_dashboard_page()
