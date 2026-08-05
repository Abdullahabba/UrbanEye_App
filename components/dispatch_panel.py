import datetime
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# Safe fallback for priority engine
try:
    from utils.priority_engine import calculate_priority_score
except Exception:
    def calculate_priority_score(counts):
        return {
            "priority_score": 50,
            "severity": "Medium",
            "assigned_dept": "Municipal Operations",
            "sla_target": "24 Hours"
        }

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

def render_dispatch_panel(tracking_id, manual_loc_name, user_details, create_pdf_report_func):
    st.divider()
    
    # Header with Instant Manual Reset Button
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.subheader("📤 Dispatch & Verification Panel")
    with col_btn:
        if st.button("🔄 Reset Panel", use_container_width=True, help="Click to clear stale counts and detections"):
            st.session_state["counts"] = {}
            st.session_state.pop("processed_img", None)
            st.session_state["captured_images"] = []
            st.rerun()
    
    # Check if input source mode changed to clear stale single-image/video state
    current_mode = st.session_state.get("input_source_mode", "🖼️ Single Image")
    last_active_mode = st.session_state.get("_last_active_input_mode", current_mode)

    if current_mode != last_active_mode:
        st.session_state["counts"] = {}
        st.session_state.pop("processed_img", None)
        st.session_state["captured_images"] = []
        st.session_state["_last_active_input_mode"] = current_mode
        st.rerun()

    # Session state counts check
    counts = st.session_state.get("counts", {})
    st.write(f"🔍 **Debug Info - Current Counts:** `{counts}`")

    has_valid_detections = counts and any(v > 0 for v in counts.values())

    if not has_valid_detections:
        st.warning("⚠️ **Panel Locked:** The AI model currently has no valid detections (`counts`). Please click 'Run AI Detection' or the start analysis button above first to detect hazards.")
        return

    # Initialize session state variables for location
    if "selected_lat" not in st.session_state:
        st.session_state["selected_lat"] = None
    if "selected_lon" not in st.session_state:
        st.session_state["selected_lon"] = None
    if "selected_loc_name" not in st.session_state:
        st.session_state["selected_loc_name"] = manual_loc_name

    st.markdown(f"### 🏷️ Incident Tracking ID: `{tracking_id}`")

    # ==========================================
    # STEP 1: LOCATION SELECTION (Pehle Location)
    # ==========================================
    st.markdown("##### 📍 Step 1: Set Incident Location First")
    loc_mode = st.radio(
        "Choose Location Mode",
        ["Manual Address", "Automatic Live GPS"],
        horizontal=True,
        key="dispatch_loc_mode"
    )

    location_ready = False

    if loc_mode == "Manual Address":
        manual_input = st.text_input(
            "✍️ Enter Location Name / Address:", 
            value=st.session_state.get("selected_loc_name", manual_loc_name),
            key="manual_address_input_box"
        )
        if manual_input and manual_input.strip():
            st.session_state["selected_loc_name"] = manual_input.strip()
            st.session_state["selected_lat"] = None
            st.session_state["selected_lon"] = None
            location_ready = True
            st.success(f"✅ Active Location Set: `{manual_input.strip()}`")
        else:
            st.warning("⚠️ Please enter a valid location name to unlock the panel.")
    else:
        st.markdown("🛰️ Click below to fetch your **real browser GPS coordinates**:")
        if streamlit_geolocation is not None:
            loc = streamlit_geolocation()
            if loc and loc.get("latitude") and loc.get("longitude"):
                st.session_state["selected_lat"] = loc["latitude"]
                st.session_state["selected_lon"] = loc["longitude"]
                st.session_state["selected_loc_name"] = f"Live GPS (Lat: {loc['latitude']:.4f}, Lon: {loc['longitude']:.4f})"
            
            if st.session_state.get("selected_lat") is not None:
                location_ready = True
                st.success(f"✅ Live GPS Locked!")
        else:
            st.error("❌ `streamlit-geolocation` library is not installed.")

    st.divider()

    # =========================================================================
    # STEP 2: REST OF THE PANEL (UNLOCKED ONLY AFTER LOCATION IS PROVIDED)
    # =========================================================================
    if not location_ready:
        st.info("🔒 **Dispatch Panel Locked:** Please provide or select a valid location above to unlock the detection summary, priority score, and dispatch actions.")
        return

    st.success("🔓 **Dispatch Panel Unlocked!** Review details below.")

    # Detection Summary
    summary_text = f"Tracking ID: {tracking_id}\nDetected Hazards Summary:\n"
    hazard_types_list = []
    for k, v in counts.items():
        if v > 0:
            summary_text += f"- {k.capitalize()}: {v}\n"
            hazard_types_list.append(f"{k.capitalize()} ({v})")
    
    main_hazard_str = ", ".join(hazard_types_list) if hazard_types_list else "Municipal Hazard"

    st.text_area("📋 Generated Incident Summary", value=summary_text, height=110)

    # Priority Assessment
    assessment = calculate_priority_score(counts)
    score = assessment["priority_score"]
    severity_level = assessment["severity"]
    assigned_department = assessment["assigned_dept"]
    sla_target = assessment["sla_target"]

    st.info(f"ℹ️ **PRIORITY SCORE: {score}/100** | Severity: {severity_level} | Dept: {assigned_department}")
    st.divider()

    final_location_name = st.session_state["selected_loc_name"]
    lat = st.session_state["selected_lat"]
    lon = st.session_state["selected_lon"]

    # Helper function to save report to Session State and Upsert to Supabase Database
    def record_report_to_history(rep_id, rep_hazard, rep_loc, rep_score, rep_sev, rep_status):
        user_email = user_details.get("email", "officer@urbaneye.ai") if isinstance(user_details, dict) else "officer@urbaneye.ai"
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # 1. Save to Session State (Instant Fallback)
        if "hazard_history" not in st.session_state:
            st.session_state["hazard_history"] = []
        
        new_entry = {
            "tracking_id": rep_id,
            "id": rep_id,
            "hazard": rep_hazard,
            "hazard_type": rep_hazard,
            "location_name": rep_loc,
            "location": rep_loc,
            "severity": f"{rep_sev} ({rep_score}/100)",
            "status": rep_status,
            "email": user_email,
            "timestamp": timestamp_str,
            "created_at": timestamp_str,
            "latitude": lat if lat is not None else 31.5204,
            "longitude": lon if lon is not None else 74.3587,
            "assigned_dept": assigned_department,
            "sla_target": sla_target
        }
        
        existing_ids = [item.get("tracking_id") or item.get("id") for item in st.session_state["hazard_history"]]
        if rep_id not in existing_ids:
            st.session_state["hazard_history"].insert(0, new_entry)

        # 2. Push / Upsert to Supabase Database with detailed feedback
        payload = {
            "tracking_id": rep_id,
            "hazard": rep_hazard,
            "severity": f"{rep_sev} ({rep_score}/100)",
            "status": rep_status,
            "location_name": rep_loc,
            "email": user_email,
            "timestamp": timestamp_str,
            "latitude": lat if lat is not None else 31.5204,
            "longitude": lon if lon is not None else 74.3587,
            "assigned_dept": assigned_department,
            "sla_target": sla_target
        }

        supabase_success = False
        error_logs = []

        try:
            from supabase import create_client
            supabase_url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
            supabase_key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                # Using upsert to handle duplicate tracking IDs safely
                response = supabase.table("reports").upsert(payload, on_conflict="tracking_id").execute()
                supabase_success = True
            else:
                error_logs.append("Supabase URL/Key missing in secrets.")
        except Exception as e1:
            error_logs.append(f"Method 1 Error: {str(e1)}")
            try:
                from database.supabase_client import supabase as sb_client
                if sb_client:
                    sb_client.table("reports").upsert(payload, on_conflict="tracking_id").execute()
                    supabase_success = True
                else:
                    error_logs.append("database.supabase_client is None.")
            except Exception as e2:
                error_logs.append(f"Method 2 Error: {str(e2)}")

        if supabase_success:
            st.success("✅ Report successfully pushed & synchronized with Supabase cloud database!")
        else:
            st.error(f"❌ Supabase Push Failed! Reasons: {' | '.join(error_logs)}")

    # Step 3: Reports & Actions
    st.markdown("##### 🚀 Step 2: Reports & Actions")
    st.divider()

    full_summary_text = summary_text + f"Location: {final_location_name}\nPriority Score: {score}/100\nTracking ID: {tracking_id}"

    raw_images = st.session_state.get("captured_images", [])
    if not raw_images and "processed_img" in st.session_state:
        raw_images = [st.session_state["processed_img"]]

    all_images = []
    for img in raw_images:
        if isinstance(img, np.ndarray):
            all_images.append(Image.fromarray(img))
        elif isinstance(img, Image.Image):
            all_images.append(img)

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
            st.error(f"❌ PDF Generation Crashed: {e}")

    col1, col2 = st.columns(2)

    with col1:
        if pdf_bytes:
            download_clicked = st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"UrbanEye_Report_{tracking_id}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            if download_clicked:
                record_report_to_history(
                    rep_id=tracking_id,
                    rep_hazard=main_hazard_str,
                    rep_loc=final_location_name,
                    rep_score=score,
                    rep_sev=severity_level,
                    rep_status="Dispatched / Saved"
                )
        else:
            st.warning("⚠️ PDF bytes are empty/None.")

    with col2:
        if st.button("📧 Send via Email", use_container_width=True):
            with st.spinner("Sending official report via email..."):
                try:
                    from utils.email_sender import send_email_with_pdf
                    success, message = send_email_with_pdf(
                        sender_email=user_details.get("email", "officer@urbaneye.ai") if isinstance(user_details, dict) else "officer@urbaneye.ai",
                        target_department_email="roads.dept@urbaneye.ai",
                        pdf_bytes=pdf_bytes,
                        title=f"Incident Report - ID: {tracking_id}",
                        user_details=user_details,
                        counts=counts
                    )
                    if success:
                        record_report_to_history(
                            rep_id=tracking_id,
                            rep_hazard=main_hazard_str,
                            rep_loc=final_location_name,
                            rep_score=score,
                            rep_sev=severity_level,
                            rep_status="Dispatched / Emailed"
                        )
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                except Exception as mail_err:
                    st.error(f"❌ Email sending failed: {str(mail_err)}")
