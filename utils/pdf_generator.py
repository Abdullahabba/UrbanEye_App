import os
import tempfile
from fpdf import FPDF
from PIL import Image


def sanitize_text(text: str) -> str:
    """Non-Latin1 characters ko replace karta hai taake PDF crash na ho."""
    if not text:
        return "N/A"
    text = str(text).replace("•", "-")
    return text.encode("latin-1", "replace").decode("latin-1")


class ProfessionalPDF(FPDF):

    def header(self):
        # 🎨 Top Dark Navy Banner
        self.set_fill_color(24, 43, 73)  # Dark Navy Blue
        self.rect(0, 0, 210, 20, "F")

        # Header Title Text
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(10, 5)
        self.cell(
            0,
            10,
            "URBAN EYE AI - MUNICIPAL HAZARD INSPECTION REPORT",
            align="C",
        )
        self.ln(18)

    def footer(self):
        # Bottom Footer Page Numbering
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | Confidential - UrbanEye AI Automated Verification System",
            align="C",
        )


def create_pdf_report(
    title: str,
    user_details: dict,
    summary_text: str,
    detected_image: Image.Image = None,
) -> bytes:
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Inputs Sanitize karna
    safe_title = sanitize_text(title)
    safe_summary = sanitize_text(summary_text)

    u_name = sanitize_text(user_details.get("username", "N/A"))
    u_email = sanitize_text(user_details.get("email", "N/A"))
    u_phone = sanitize_text(user_details.get("phone", "N/A"))
    u_address = sanitize_text(user_details.get("address", "N/A"))

    # ---------------------------------------------------------
    # SECTION 1: REPORTER & INCIDENT DETAILS (CARD BOX)
    # ---------------------------------------------------------
    pdf.set_draw_color(210, 215, 220)
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 25, 190, 42, "DF")  # Light gray box background

    # Incident Title
    pdf.set_xy(15, 28)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, f"Report Title: {safe_title}")
    pdf.ln(8)

    # 2-Column User Info Layout
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)

    # Row 1
    pdf.set_x(15)
    pdf.cell(90, 5, f"Reported By: {u_name}")
    pdf.cell(90, 5, f"Phone: {u_phone}")
    pdf.ln(6)

    # Row 2
    pdf.set_x(15)
    pdf.cell(90, 5, f"Email: {u_email}")
    pdf.cell(90, 5, f"Location / Dept: {u_address}")
    pdf.ln(12)

    # ---------------------------------------------------------
    # SECTION 2: AI VISUAL EVIDENCE (EMBEDDED IMAGE)
    # ---------------------------------------------------------
    if detected_image:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(24, 43, 73)
        pdf.cell(0, 6, "Visual Inspection Evidence (AI Detection Grid):")
        pdf.ln(8)

        # Temporary Image File Banana
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            if detected_image.mode in ("RGBA", "P"):
                img_to_save = detected_image.convert("RGB")
            else:
                img_to_save = detected_image

            img_to_save.save(tmp.name, format="PNG")
            tmp_path = tmp.name

        # PDF ke center mein image insert karna (Width=140mm)
        pdf.image(tmp_path, x=35, w=140)
        pdf.ln(8)

        # Temporary file cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # ---------------------------------------------------------
    # SECTION 3: DETECTION BREAKDOWN & LOGS
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "AI Analysis Breakdown & Summary:")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, safe_summary)

    return bytes(pdf.output())
