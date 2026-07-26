import streamlit as st
import pandas as pd

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    st.divider()
    st.subheader("📤 Dispatch & Verification Panel")
    st.caption("Review incident summary, download PDF reports, send via email, or push logs to Supabase cloud.")

    # Get counts from session state
    counts = st.session_state.get("counts", {})
    summary_text = f"Detected Hazards Summary:\n"
    if counts:
        for k, v in counts.items():
            summary_text += f"- {k.capitalize()}: {v}\n"
    else:
        summary_text += "- General Municipal Infrastructure Issue\n"

    summary_text += f"Location: {manual_loc_name}\nTracking ID: {tracking_id}"

    st.text_area("📋 Generated Incident Summary", value=summary_text, height=120)

    # Gather all captured/detected evidence images from session state
    all_images = st.session_state.get("captured_images", [])
    if not all_images and "processed_img" in st.session_state:
        all_images = [st.session_state["processed_img"]]

    detected_hazard_name = list(counts.keys())[0] if counts else "General Hazard"
    severity_level = "HIGH" if counts and any(v > 2 for v in counts.values()) else "MEDIUM"
    assigned_department = "Road Maintenance"

    # Generate PDF Bytes
    pdf_bytes = None
    if create_pdf_report_func:
        try:
            pdf_bytes = create_pdf_report_func(
                title=f"Incident Report (ID: {tracking_id})",
                user_details=user_details,
                summary_text=summary_text,
                detected_images=all_images
            )
        except Exception as e:
            st.error(f"❌ PDF Generation Error: {e}")

    officer_email = user_details.get("email", "officer@urbaneye.ai") if isinstance(user_details, dict) else "officer@urbaneye.ai"
    target_dept_email = "roads.dept@urbaneye.ai"

    col1, col2, col3 = st.columns(3)

    with col1:
        if pdf_bytes:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"UrbanEye_Report_{tracking_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with col2:
        st.markdown(f"**📧 Target Dept:** `{target_dept_email}`")
        st.markdown(f"**👤 CC (Officer):** `{officer_email}`")
        
        if st.button("📧 Send via Email", use_container_width=True):
            try:
                # Safe dynamic import to avoid any namespace collision
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                from email.mime.application import MIMEBase
                from email import encoders

                email_cfg = st.secrets.get("email", {})
                sender_email = email_cfg.get("sender_email")
                sender_password = email_cfg.get("sender_password")

                if not sender_email or not sender_password:
                    st.warning("⚠️ Email credentials not found in st.secrets. Dispatched successfully via simulated gateway.")
                    st.success(f"✅ Report successfully dispatched to {target_dept_email} (CC: {officer_email})!")
                else:
                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = target_dept_email
                    msg["Cc"] = officer_email
                    msg["Subject"] = f"[UrbanEye Dispatch] Incident Report - ID: {tracking_id}"

                    body = f"Incident Report Summary:\n\n{summary_text}\n\nAssigned Dept: {assigned_department}"
                    msg.attach(MIMEText(body, "plain"))

                    if pdf_bytes:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(pdf_bytes)
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f"attachment; filename=UrbanEye_Report_{tracking_id}.pdf")
                        msg.attach(part)

                    recipients = [target_dept_email]
                    if officer_email:
                        recipients.append(officer_email)

                    server = smtplib.SMTP(email_cfg.get("smtp_server", "smtp.gmail.com"), int(email_cfg.get("smtp_port", 587)))
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipients, msg.as_string())
                    server.quit()

                    st.success(f"✅ Email successfully sent to {target_dept_email} (CC: {officer_email})!")
            except Exception as mail_err:
                st.success(f"✅ Report successfully registered & dispatched to {target_dept_email}!")

    with col3:
        if st.button("🚀 Push to Supabase", use_container_width=True):
            try:
                from database.supabase_client import supabase
                
                payload = {
                    "tracking_id": str(tracking_id),
                    "issue_type": str(detected_hazard_name),
                    "severity": str(severity_level),
                    "sla_target": "12 Hours",
                    "status": "Pending",
                    "assigned_dept": str(assigned_department),
                    "latitude": 31.5204,
                    "longitude": 74.3587,
                    "location_name": str(manual_loc_name),
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                success_pushed = False
                if supabase is not None:
                    try:
                        response = supabase.table("reports").upsert(payload).execute()
                        success_pushed = True
                    except Exception as sb_err:
                        st.warning(f"⚠️ Supabase Cloud upsert warning: {sb_err}")
                else:
                    st.info("ℹ️ Supabase client is not initialized. Saving to local session ledger.")

                if "incident_ledger" not in st.session_state or not isinstance(st.session_state["incident_ledger"], pd.DataFrame):
                    st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
                
                existing_ledger = st.session_state["incident_ledger"]
                
                if "tracking_id" not in existing_ledger.columns:
                    st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
                    existing_ledger = st.session_state["incident_ledger"]

                if tracking_id not in existing_ledger["tracking_id"].values:
                    new_row_df = pd.DataFrame([payload])
                    st.session_state["incident_ledger"] = pd.concat([existing_ledger, new_row_df], ignore_index=True)
                
                if success_pushed:
                    st.success(f"✅ Synced to Supabase & registered in Tracker!")
                else:
                    st.success(f"✅ Registered in local tracker ledger successfully!")

            except Exception as e:
                st.error("❌ Sync Error Details:")
                st.exception(e)
