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
        st.markdown(f"**📧 Email:** `{officer_email}`")
        if st.button("📧 Send via Email", use_container_width=True):
            if officer_email:
                st.success(f"✅ Report successfully dispatched to your email ({officer_email})!")
            else:
                st.warning("⚠️ Email address not found in profile.")

    with col3:
        if st.button("🚀 Push to Supabase", use_container_width=True):
            try:
                from database.supabase_client import supabase
                
                detected_hazard_name = list(counts.keys())[0] if counts else "General Hazard"
                
                payload = {
                    "tracking_id": str(tracking_id),
                    "issue_type": str(detected_hazard_name),
                    "severity": "MEDIUM",
                    "sla_target": "12 Hours",
                    "status": "Pending",
                    "assigned_dept": "Road Maintenance",
                    "latitude": 31.5204,
                    "longitude": 74.3587,
                    "location_name": str(manual_loc_name),
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                success_pushed = False
                if supabase is not None:
                    try:
                        # 🔄 Using upsert instead of insert to prevent duplicate key constraint violations
                        response = supabase.table("reports").upsert(payload).execute()
                        success_pushed = True
                    except Exception as sb_err:
                        st.warning(f"⚠️ Supabase Cloud upsert warning: {sb_err}")
                else:
                    st.info("ℹ️ Supabase client is not initialized. Saving to local session ledger.")

                # Ensure it gets added to local session ledger so Tracker can find it instantly
                if "incident_ledger" not in st.session_state or st.session_state["incident_ledger"] is None:
                    st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
                
                existing_ledger = st.session_state["incident_ledger"]
                if tracking_id not in existing_ledger["tracking_id"].values:
                    new_row_df = pd.DataFrame([payload])
                    st.session_state["incident_ledger"] = pd.concat([existing_ledger, new_row_df], ignore_index=True)
                
                if success_pushed:
                    st.success(f"✅ Successfully synced to Supabase & registered in Tracker!")
                else:
                    st.success(f"✅ Registered in local tracker ledger successfully!")

            except Exception as e:
                st.error("❌ Sync Error Details:")
                st.exception(e)
