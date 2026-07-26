import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from utils.location_helper import get_live_location

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    st.divider()
    st.subheader("📤 Dispatch & Verification Panel")
    st.caption("Step 1: Review Detection Summary $\rightarrow$ Step 2: Set Location $\rightarrow$ Step 3: Dispatch Reports & Sync.")

    # 1️⃣ Step 1: Detection Summary Displayed First
    counts = st.session_state.get("counts", {})
    summary_text = "Detected Hazards Summary:\n"
    if counts:
        for k, v in counts.items():
            summary_text += f"- {k.capitalize()}: {v}\n"
    else:
        summary_text += "- General Municipal Infrastructure Issue\n"

    st.text_area("📋 Generated Incident Summary", value=summary_text, height=100)

    # 2️⃣ Step 2: Location Option (Manual or Auto GPS)
    st.markdown("##### 📍 Step 2: Select Location Method")
    loc_choice = st.radio(
        "Choose Location Entry Type",
        ["Manual", "Automatic GPS"],
        horizontal=True,
        label_visibility="collapsed"
    )

    lat = 31.5204
    lon = 74.3587
    final_location_name = manual_loc_name
    location_ready = False

    # Conditional location handling
    if loc_choice == "Manual":
        final_location_name = st.text_input("✍️ Enter Location Name / Address:", value=manual_loc_name)
        if final_location_name and final_location_name.strip():
            location_ready = True
            st.success(f"✅ Manual Location Set: `{final_location_name}`")
        else:
            st.warning("⚠️ Please enter a valid location name to proceed.")
    else:
        # Automatic GPS using location helper
        live_lat, live_lon = get_live_location()
        if live_lat is not None and live_lon is not None:
            lat = live_lat
            lon = live_lon
            final_location_name = f"Auto-GPS Location (Lat: {lat:.4f}, Lon: {lon:.4f})"
            st.success(f"✅ Automatic GPS Locked -> Lat: {lat:.4f}, Lon: {lon:.4f}")
            location_ready = True
        else:
            final_location_name = "Auto-GPS (Pending)"
            location_ready = False

    # 3️⃣ Step 3: Actions (PDF, Email, Supabase Push) - Unlocked ONLY after location is ready
    if location_ready:
        st.markdown("##### 🚀 Step 3: Dispatch & Reports")
        st.divider()

        # Update summary text with final location & tracking ID
        full_summary_text = summary_text + f"Location: {final_location_name} (GPS: {lat}, {lon})\nTracking ID: {tracking_id}"

        # Gather all captured/detected evidence images
        raw_images = st.session_state.get("captured_images", [])
        if not raw_images and "processed_img" in st.session_state:
            raw_images = [st.session_state["processed_img"]]

        all_images = []
        for img in raw_images:
            if isinstance(img, np.ndarray):
                all_images.append(Image.fromarray(img))
            elif isinstance(img, Image.Image):
                all_images.append(img)

        detected_hazard_name = list(counts.keys())[0] if counts else "General Hazard"
        severity_level = "HIGH" if counts and any(v > 2 for v in counts.values()) else "MEDIUM"
        assigned_department = "Road Maintenance"

        # Generate PDF Bytes with converted images
        pdf_bytes = None
        if create_pdf_report_func:
            try:
                pdf_bytes = create_pdf_report_func(
                    title=f"Incident Report (ID: {tracking_id})",
                    user_details=user_details,
                    summary_text=full_summary_text,
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
                with st.spinner("Sending official report via email..."):
                    try:
                        import smtplib
                        from email.mime.multipart import MIMEMultipart
                        from email.mime.text import MIMEText
                        from email.mime.base import MIMEBase
                        from email import encoders

                        email_cfg = st.secrets.get("email", {})
                        sender_email = email_cfg.get("sender_email") or st.secrets.get("SMTP_USER")
                        sender_password = email_cfg.get("sender_password") or st.secrets.get("SMTP_PASS")

                        if not sender_email or not sender_password:
                            st.error("❌ Email credentials not found in st.secrets (`SMTP_USER` / `SMTP_PASS`).")
                        else:
                            msg = MIMEMultipart()
                            msg["From"] = sender_email
                            msg["To"] = target_dept_email
                            msg["Cc"] = officer_email
                            msg["Subject"] = f"[UrbanEye Dispatch] Incident Report - ID: {tracking_id}"

                            body = f"Incident Report Summary:\n\n{full_summary_text}\n\nAssigned Dept: {assigned_department}"
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

                            smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
                            smtp_port = int(email_cfg.get("smtp_port", 587))

                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.sendmail(sender_email, recipients, msg.as_string())
                            server.quit()

                            st.success(f"✅ Email successfully sent to {target_dept_email} (CC: {officer_email})!")
                    except Exception as mail_err:
                        st.error(f"❌ Email sending failed: {str(mail_err)}")

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
                        "latitude": lat,
                        "longitude": lon,
                        "location_name": str(final_location_name),
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
                        st.success("✅ Synced to Supabase & registered in Tracker!")
                    else:
                        st.success("✅ Registered in local tracker ledger successfully!")

                except Exception as e:
                    st.error("❌ Sync Error Details:")
                    st.exception(e)
    else:
        st.info("🔒 Please complete **Step 2 (Enter Manual Location or Click 'Detect My Live GPS')** above to unlock PDF download, Email dispatch, and Supabase cloud sync.")
