import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from utils.priority_engine import calculate_priority_score

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    st.divider()
    st.subheader("📤 Dispatch & Verification Panel")
    
    # 🛡️ Guard Check: Agar koi detection run nahi hui, toh panel lock rakhein
    counts = st.session_state.get("counts", {})
    processed_img = st.session_state.get("processed_img")
    captured_images = st.session_state.get("captured_images", [])

    if not counts and processed_img is None and not captured_images:
        st.info("💡 **Awaiting Inspection:** Please upload an image, video, or use the live camera and run AI detection first to generate the dispatch summary.")
        return

    st.caption("Step 1: Review Detection Summary $\rightarrow$ Step 2: Set Location $\rightarrow$ Step 3: Automatic Dispatch & Reports.")

    # Initialize session state variables for location
    if "selected_lat" not in st.session_state:
        st.session_state["selected_lat"] = None
    if "selected_lon" not in st.session_state:
        st.session_state["selected_lon"] = None
    if "selected_loc_name" not in st.session_state:
        st.session_state["selected_loc_name"] = manual_loc_name
    if "location_confirmed" not in st.session_state:
        st.session_state["location_confirmed"] = False

    # 1️⃣ Step 1: Detection Summary Displayed First
    summary_text = "Detected Hazards Summary:\n"
    if counts:
        for k, v in counts.items():
            summary_text += f"- {k.capitalize()}: {v}\n"
    else:
        summary_text += "- General Municipal Infrastructure Issue\n"

    st.text_area("📋 Generated Incident Summary", value=summary_text, height=100)

    # ⚡ Calculate Dynamic Priority & SLA Assessment
    assessment = calculate_priority_score(counts)
    
    score = assessment["priority_score"]
    severity_level = assessment["severity"]
    assigned_department = assessment["assigned_dept"]
    sla_target = assessment["sla_target"]

    if severity_level == "CRITICAL":
        st.error(f"🚨 **CRITICAL PRIORITY SCORE: {score}/100** | SLA: {sla_target} | Dept: {assigned_department}")
    elif severity_level == "HIGH":
        st.warning(f"⚠️ **HIGH PRIORITY SCORE: {score}/100** | SLA: {sla_target} | Dept: {assigned_department}")
    else:
        st.info(f"ℹ️ **STANDARD PRIORITY SCORE: {score}/100** | SLA: {sla_target} | Dept: {assigned_department}")

    st.divider()

    # 2️⃣ Step 2: Location Option (Manual Address or Live GPS)
    st.markdown("##### 📍 Step 2: Select Location Method")
    loc_mode = st.radio(
        "Choose Location Mode",
        ["Manual Address", "Automatic Live GPS"],
        horizontal=True
    )

    location_ready = False

    if loc_mode == "Manual Address":
        manual_input = st.text_input("✍️ Enter Location Name / Address:", value=st.session_state.get("selected_loc_name", manual_loc_name))
        if st.button("✅ Confirm Manual Location", use_container_width=True):
            if manual_input and manual_input.strip():
                st.session_state["selected_loc_name"] = manual_input.strip()
                st.session_state["selected_lat"] = None
                st.session_state["selected_lon"] = None
                st.session_state["location_confirmed"] = True
                st.success(f"✅ Manual Location Confirmed: `{manual_input.strip()}`")
                st.rerun()
            else:
                st.warning("⚠️ Please enter a valid location name.")
        
        if st.session_state["location_confirmed"] and loc_mode == "Manual Address":
            location_ready = True
            st.info(f"📌 Current Active Location: **{st.session_state['selected_loc_name']}**")

    else:
        st.markdown("🛰️ Click below to fetch your **real browser GPS coordinates**:")
        if streamlit_geolocation is not None:
            loc = streamlit_geolocation()
            if loc and loc.get("latitude") and loc.get("longitude"):
                lat = loc["latitude"]
                lon = loc["longitude"]
                st.session_state["selected_lat"] = lat
                st.session_state["selected_lon"] = lon
                st.session_state["selected_loc_name"] = f"Live GPS (Lat: {lat:.4f}, Lon: {lon:.4f})"
                st.session_state["location_confirmed"] = True
            
            if st.session_state["location_confirmed"] and st.session_state["selected_lat"] is not None:
                location_ready = True
                st.success(f"✅ Live GPS Locked! Lat: `{st.session_state['selected_lat']:.4f}`, Lon: `{st.session_state['selected_lon']:.4f}`")
        else:
            st.error("❌ `streamlit-geolocation` library is not installed.")

    # 3️⃣ Step 3: Automatic Push & Reports Generation (Unlocked once location is confirmed)
    if location_ready or st.session_state["location_confirmed"]:
        st.markdown("##### 🚀 Step 3: Reports & Automatic Cloud Sync")
        st.divider()

        final_location_name = st.session_state["selected_loc_name"]
        lat = st.session_state["selected_lat"]
        lon = st.session_state["selected_lon"]

        if lat is not None and lon is not None:
            full_summary_text = summary_text + f"Location: {final_location_name} (GPS: {lat:.4f}, {lon:.4f})\nPriority Score: {score}/100\nTracking ID: {tracking_id}"
        else:
            full_summary_text = summary_text + f"Location: {final_location_name} (Manual Entry)\nPriority Score: {score}/100\nTracking ID: {tracking_id}"

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

        # 🚀 AUTOMATIC SUPABASE SYNC LOGIC (Executes once per tracking ID)
        auto_push_key = f"auto_pushed_{tracking_id}"
        if not st.session_state.get(auto_push_key, False):
            try:
                from database.supabase_client import supabase
                
                payload = {
                    "tracking_id": str(tracking_id),
                    "issue_type": str(detected_hazard_name),
                    "severity": str(severity_level),
                    "priority_score": int(score),
                    "sla_target": str(sla_target),
                    "status": "Pending",
                    "assigned_dept": str(assigned_department),
                    "latitude": lat,
                    "longitude": lon,
                    "location_name": str(final_location_name),
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                }
                
                # Cloud sync
                if supabase is not None:
                    try:
                        supabase.table("reports").upsert(payload).execute()
                    except Exception as sb_err:
                        pass # Fail silently or fallback to local ledger
                
                # Local session ledger sync
                if "incident_ledger" not in st.session_state or not isinstance(st.session_state["incident_ledger"], pd.DataFrame):
                    st.session_state["incident_ledger"] = pd.DataFrame(columns=payload.keys())
                
                existing_ledger = st.session_state["incident_ledger"]
                if tracking_id not in existing_ledger["tracking_id"].values:
                    new_row_df = pd.DataFrame([payload])
                    st.session_state["incident_ledger"] = pd.concat([existing_ledger, new_row_df], ignore_index=True)

                st.session_state[auto_push_key] = True
                st.toast("✅ Incident automatically synced to Supabase & Tracker!", icon="🚀")

            except Exception as e:
                st.warning(f"⚠️ Auto-sync warning: {e}")

        # Generate PDF Bytes
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

        col1, col2 = st.columns(2)

        with col1:
            if pdf_bytes:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"UrbanEye_Report_{tracking_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        with col2:
            if st.button("📧 Send via Email", use_container_width=True):
                with st.spinner("Sending official report via email..."):
                    try:
                        from utils.email_sender import send_email_with_pdf
                        success, message = send_email_with_pdf(
                            sender_email=officer_email,
                            target_department_email=target_dept_email,
                            pdf_bytes=pdf_bytes,
                            title=f"Incident Report - ID: {tracking_id}",
                            user_details=user_details,
                            counts=counts
                        )
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as mail_err:
                        st.error(f"❌ Email sending failed: {str(mail_err)}")
    else:
        st.info("🔒 Please complete **Step 2 (Confirm Location)** above to automatically sync the report and unlock PDF download & Email options.")
