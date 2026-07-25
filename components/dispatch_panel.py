import streamlit as st
import pandas as pd
from utils.helpers import calculate_severity_and_sla

try:
    from utils.email_sender import send_email_with_pdf
except ImportError:
    from utils.email_sender import send_email_alert as send_email_with_pdf

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    if "counts" not in st.session_state or not st.session_state["counts"]:
        return

    st.divider()
    st.info(f"🎫 **Tracking ID:** `{tracking_id}` | 📍 **Location:** {manual_loc_name}")
    st.subheader("🚨 Inspection Breakdown & Urgent Dispatch")

    severity_label, color_code, sla_target = calculate_severity_and_sla(st.session_state["counts"])

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write("### Detected Hazards Summary:")
        for hz, count in st.session_state["counts"].items():
            st.write(f"- **{hz.title()}**: {count} instance(s)")
    with col_b:
        st.markdown(f"""
            <div style="background-color: {color_code}; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h4 style="margin:0;">SEVERITY INDEX</h4>
                <h2 style="margin:0;">{severity_label}</h2>
                <p style="margin:0; font-size:12px;">SLA Target: {sla_target}</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    col_inp1, col_inp2 = st.columns(2)
    with col_inp1:
        title = st.text_input("Incident Title", "Municipal Hazard Alert", key="dispatch_title")
    with col_inp2:
        dept_email = st.selectbox("Target Department Email", ["road_maintenance@city.gov", "waste_management@city.gov", "urban_planning@city.gov", "civic_support@city.gov"], key="dispatch_dept")

    summary_text = f"Tracking ID: {tracking_id}\nLocation: {manual_loc_name}\nUrbanEye AI Summary:\n" + "\n".join([f"- {k.title()}: {v}" for k, v in st.session_state["counts"].items()])
    p_img = st.session_state.get("processed_img", None)
    
    pdf_bytes = b""
    if create_pdf_report_func:
        pdf_bytes = create_pdf_report_func(title=f"{title} (ID: {tracking_id})", user_details=user_details, summary_text=summary_text, detected_image=p_img)

    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if pdf_bytes:
            st.download_button(label="📥 Download PDF Report", data=pdf_bytes, file_name=f"Report_{tracking_id}.pdf", mime="application/pdf", use_container_width=True, key="btn_dl_pdf")
    with btn2:
        if st.button("📩 Send Email Alert", use_container_width=True, key="btn_send_email"):
            with st.spinner("Sending Email Alert..."):
                try:
                    ok, msg = send_email_with_pdf(sender_email=user_details["email"], target_department_email=dept_email, pdf_bytes=pdf_bytes, title=f"{title} [{tracking_id}]", user_details=user_details, counts=st.session_state["counts"])
                    st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")
                except Exception as e:
                    st.error(f"❌ Failed to send email: {e}")
    with btn3:
        if st.button("💾 Submit & Log to Tracker", use_container_width=True, key="btn_save_ledger"):
            primary_hazard = list(st.session_state["counts"].keys())[0].title() if st.session_state["counts"] else "General Hazard"
            
            new_record = {
                "Tracking ID": tracking_id,
                "Hazard": primary_hazard,
                "Severity": severity_label,
                "SLA Target": sla_target,
                "Status": "Pending",
                "Assigned Dept": dept_email.split("@")[0].replace("_", " ").title(),
                "Latitude": 31.5204,
                "Longitude": 74.3587,
                "Location Name": manual_loc_name,
                "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            }

            # 1. Save to Session State Ledger
            new_row_df = pd.DataFrame([new_record])
            st.session_state["incident_ledger"] = pd.concat([st.session_state["incident_ledger"], new_row_df], ignore_index=True)

            # 2. Save to Supabase (Optional backup)
            try:
                from utils.supabase_client import init_supabase
                supabase = init_supabase()
                if supabase:
                    supabase.table("reports").insert(new_record).execute()
            except Exception:
                pass

            st.success(f"✅ Incident submitted successfully! Tracking ID: **{tracking_id}**")
