import streamlit as st
import pandas as pd
import traceback

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    st.divider()
    st.subheader("📤 Dispatch & Verification Panel")
    st.caption("Review incident summary, download multi-image PDF reports, or push logs to Supabase cloud.")

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

    col1, col2 = st.columns(2)

    with col1:
        # PDF Report Download Button
        if create_pdf_report_func:
            try:
                pdf_bytes = create_pdf_report_func(
                    title=f"Incident Report (ID: {tracking_id})",
                    user_details=user_details,
                    summary_text=summary_text,
                    detected_images=all_images
                )
                st.download_button(
                    label="📥 Download Multi-Image PDF Report",
                    data=pdf_bytes,
                    file_name=f"UrbanEye_Report_{tracking_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                # 🔍 DETAILED ERROR LOGGING FOR DEBUGGING
                st.error("❌ PDF Generation Error Details:")
                st.exception(e)
                print(traceback.format_exc())

    with col2:
        if st.button("🚀 Push to Supabase Cloud & Tracker", use_container_width=True):
            try:
                from database.supabase_client import supabase
                payload = {
                    "tracking_id": tracking_id,
                    "hazard": list(counts.keys())[0] if counts else "General Hazard",
                    "severity": "MEDIUM",
                    "sla_target": "12 Hours",
                    "status": "Pending",
                    "assigned_dept": "Road Maintenance",
                    "latitude": 31.5204,
                    "longitude": 74.3587,
                    "location_name": manual_loc_name,
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                if supabase:
                    supabase.table("reports").insert(payload).execute()

                if "incident_ledger" not in st.session_state:
                    st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
                
                new_row_df = pd.DataFrame([payload])
                st.session_state["incident_ledger"] = pd.concat([st.session_state["incident_ledger"], new_row_df], ignore_index=True)
                
                st.success(f"✅ Incident {tracking_id} successfully dispatched and synced!")
            except Exception as e:
                st.error("❌ Sync Error Details:")
                st.exception(e)
