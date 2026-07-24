from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import streamlit as st


def send_email_with_pdf(
    sender_email: str,
    target_department_email: str,
    pdf_bytes: bytes,
    title: str,
    user_details: dict = None,
    counts: dict = None,
) -> tuple[bool, str]:
    """
    Sends an automated incident report email with PDF attachment.
    Location: utils/email_sender.py
    """
    # 1. Fetch Credentials safely from Secrets
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = st.secrets.get("SMTP_USER", "Abdullahabbasi555a@gmail.com")
    SMTP_PASS = st.secrets.get("SMTP_PASS", "zlsekipjqddtvubq")

    # 2. Extract Optional User & Hazard Details
    user_details = user_details or {}
    counts = counts or {}

    officer_name = user_details.get("username", "Inspector / Officer")
    officer_phone = user_details.get("phone", "N/A")
    officer_address = user_details.get("address", "N/A")

    # Format AI Detection breakdown if available
    breakdown_text = ""
    if counts:
        breakdown_text = "\n• Detected Hazards:\n" + "\n".join(
            [f"   - {k.title()}: {v} instance(s)" for k, v in counts.items()]
        )

    # 3. Create Email Container
    msg = MIMEMultipart()
    msg["From"] = f"Urban Eye AI <{SMTP_USER}>"
    msg["To"] = target_department_email
    msg["Reply-To"] = sender_email
    msg["Subject"] = f"🚨 URGENT INCIDENT REPORT: {title}"

    # 4. Professional Email Body Text
    body = f"""Respected Authority / Department,

An automated civic hazard report has been logged and dispatched via Urban Eye AI Platform.

==================================================
📌 INCIDENT DETAILS
==================================================
• Incident Title : {title}
• Reported By    : {sender_email} ({officer_name})
• Contact Phone  : {officer_phone}
• Sector/Location: {officer_address}
{breakdown_text}

==================================================
📄 ATTACHMENT
==================================================
Please find attached the official PDF Report containing AI detection evidence and visual proofs.

Regards,
Urban Eye AI Operations Team
"""
    msg.attach(MIMEText(body, "plain"))

    # 5. Attach PDF File (Sanitized Filename)
    if pdf_bytes:
        # Replace spaces and special chars to prevent email corruption
        safe_title = "".join(c if c.isalnum() else "_" for c in title).strip("_")
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="Incident_Report_{safe_title}.pdf"',
        )
        msg.attach(part)

    # 6. Send Email via SMTP
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True, "Report email sent successfully!"
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"
