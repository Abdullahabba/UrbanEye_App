import os
from fpdf import FPDF

def generate_pdf_report(user_email, title, location, notes, image_bytes, stats):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(0, 150, 255)
    pdf.cell(0, 12, "URBAN EYE AI - INCIDENT REPORT", ln=True, align='C')
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Automated Public Safety & Monitoring System", ln=True, align='C')
    pdf.ln(8)

    # Info
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Report Title: {title}", ln=True)
    pdf.cell(0, 8, f"Reported By User: {user_email}", ln=True)
    pdf.cell(0, 8, f"Location / Address: {location}", ln=True)
    pdf.cell(0, 8, f"Category: {stats.get('Category', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Detections Count: {stats.get('Detections Count', 0)}", ln=True)
    pdf.cell(0, 8, f"Severity Level: {stats.get('Severity', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 8, "Additional Remarks / Notes:", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, notes if notes else "N/A")
    pdf.ln(8)

    # Save temp image for PDF
    temp_img_path = "temp_report_img.jpg"
    with open(temp_img_path, "wb") as f:
        f.write(image_bytes)

    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 8, "Evidence & AI Detection Image:", ln=True)
    pdf.image(temp_img_path, x=15, w=180)

    pdf_bytes = pdf.output()
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)
        
    return pdf_bytes