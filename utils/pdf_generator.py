import os
import tempfile
import numpy as np
from PIL import Image
from fpdf import FPDF
from utils.metadata import get_user_metadata  # Metadata function import

def sanitize_text(text: str) -> str:
    """Non-Latin1 characters ko replace karta hai taake PDF crash na ho."""
    if not text:
        return "N/A"
    text = str(text).replace("•", "-")
    return text.encode("latin-1", "replace").decode("latin-1")

class ProfessionalPDF(FPDF):

    def header(self):
        # 🎨 Top Dark Navy Banner with Accent Line
        self.set_fill_color(24, 43, 73)  # Dark Navy Blue
        self.rect(0, 0, 210, 22, "F")
        self.set_fill_color(0, 168, 204)  # Cyan Accent Line
        self.rect(0, 22, 210, 2, "F")

        # Header Title Text
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.set_xy(10, 6)
        self.cell(
            0,
            10,
            "URBAN EYE AI - MUNICIPAL HAZARD INSPECTION REPORT",
            align="C",
        )
        self.ln(20)

    def footer(self):
        # Bottom Footer Page Numbering with Thin Separator Line
        self.set_y(-15)
        self.set_draw_color(210, 215, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | Confidential - UrbanEye AI Automated Verification System",
            align="C",
        )

    def section_heading(self, title: str):
        """Styled Section Banner Header"""
        self.ln(4)
        self.set_fill_color(230, 238, 248)  # Light soft blue background
        self.set_text_color(24, 43, 73)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  {title}", 0, 1, "L", fill=True)
        self.ln(3)

def create_pdf_report(
    title: str,
    user_details: dict = None,  
    summary_text: str = "",
    detected_images=None,  # Support lists, numpy arrays, or single images
) -> bytes:
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Agar user_details na milein ya adhoori hon, toh metadata function se fresh fetch karein
    if not user_details or not isinstance(user_details, dict) or not user_details.get("username"):
        user_details = get_user_metadata()

    # Inputs Sanitize karna
    safe_title = sanitize_text(title)
    safe_summary = sanitize_text(summary_text)

    u_name = sanitize_text(user_details.get("username", "Inspector Ahmed"))
    u_email = sanitize_text(user_details.get("email", "officer@urbaneye.ai"))
    u_phone = sanitize_text(user_details.get("phone", "+92 300 1234567"))
    u_address = sanitize_text(user_details.get("address", "Lahore Urban Sector 4"))

    # ---------------------------------------------------------
    # SECTION 1: REPORTER & INCIDENT DETAILS (MODERN CARD BOX)
    # ---------------------------------------------------------
    pdf.section_heading("1. INCIDENT & OFFICER METADATA")

    pdf.set_draw_color(210, 215, 220)
    pdf.set_fill_color(248, 249, 250)
    
    box_y = pdf.get_y()
    pdf.rect(10, box_y, 190, 32, "DF")

    pdf.set_xy(14, box_y + 4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, f"Report Title: {safe_title}")
    
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(60, 60, 60)

    # Row 1 Metadata
    pdf.set_xy(14, box_y + 12)
    pdf.cell(95, 5, f"Reported By: {u_name}")
    pdf.cell(85, 5, f"Phone: {u_phone}")

    # Row 2 Metadata
    pdf.set_xy(14, box_y + 19)
    pdf.cell(95, 5, f"Email: {u_email}")
    pdf.cell(85, 5, f"Location / Dept: {u_address}")

    pdf.set_y(box_y + 36)

    # ---------------------------------------------------------
    # SECTION 2: AI VISUAL EVIDENCE (MULTI-IMAGE SUPPORT)
    # ---------------------------------------------------------
    if detected_images:
        # Agar single image pass ho jaye toh usay list mein convert kar dein
        if not isinstance(detected_images, list):
            detected_images = [detected_images]

        pdf.section_heading(f"2. VISUAL INSPECTION EVIDENCE ({len(detected_images)} AI SNAPSHOTS)")

        for idx, img in enumerate(detected_images):
            if img is None:
                continue

            # Convert numpy array or PIL Image correctly
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

            # Temporary Image File Banana
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img_to_save.save(tmp.name, format="PNG")
                tmp_path = tmp.name

            # Snapshot Label & Centered Image Embedding
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Evidence Snapshot #{idx + 1}", ln=True)

            image_x = (210 - 130) / 2  # Centering 130mm width image
            pdf.image(tmp_path, x=image_x, w=130)
            pdf.ln(6)

            # Temporary file cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ---------------------------------------------------------
    # SECTION 3: DETECTION BREAKDOWN & LOGS
    # ---------------------------------------------------------
    pdf.section_heading("3. AI ANALYSIS BREAKDOWN & SUMMARY")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    
    summary_y = pdf.get_y()
    pdf.set_fill_color(252, 253, 255)
    pdf.set_draw_color(225, 230, 238)
    
    pdf.set_xy(10, summary_y)
    pdf.ln(2)
    pdf.set_x(14)
    pdf.multi_cell(182, 6, safe_summary)
    pdf.ln(4)

    # Fixed output conversion to bytes safely
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode("latin-1")
    return bytes(pdf_output)
