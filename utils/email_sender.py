import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email_with_pdf(sender_email, target_department_email, pdf_bytes, title):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = st.secrets.get("SMTP_USER", "your_system_email@gmail.com")
    SMTP_PASS = st.secrets.get("SMTP_PASS", "your_app_password")

    msg = MIMEMultipart()
    msg['From'] = f"Urban Eye AI <{SMTP_USER}>"
    msg['To'] = target_department_email
    msg['Reply-To'] = sender_email
    msg['Subject'] = f"🚨 URGENT INCIDENT REPORT: {title}"

    body = f"""
    Respected Authority / Department,

    An incident report has been generated via Urban Eye AI Platform.

    • Reported By User Email: {sender_email}
    • Incident Title: {title}
    
    Please find attached the official PDF Report containing AI Detection evidence.

    Regards,
    Urban Eye AI Incident System
    """
    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="Incident_Report_{title}.pdf"')
    msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True, "Report email sent successfully!"
    except Exception as e:
        return False, f"Email sending failed: {e}"