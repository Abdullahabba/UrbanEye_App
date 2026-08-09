import streamlit as st
import cv2
import numpy as np
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

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

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🚗 UrbanEye AI - Live Field Scanner & Auto-Sync")

    # Session states initialization
    if "live_step" not in st.session_state:
        st.session_state["live_step"] = "CAPTURE"  # CAPTURE, VERIFY
    if "live_counts" not in st.session_state:
        st.session_state["live_counts"] = {}
    if "live_tracking_id" not in st.session_state:
        st.session_state["live_tracking_id"] = None
    if "live_processed_img" not in st.session_state:
        st.session_state["live_processed_img"] = None

    # --- STEP 1: CAPTURE PHOTO ---
    if st.session_state["live_step"] == "CAPTURE":
        st.info("💡 کیمرہ سے ہیزرڈ (گڈھا یا کچرا) کی تصویر لیں۔ سسٹم خودکار طور پر ڈیٹیکشن کرے گا!")
        
        cam_file = st.camera_input("Take Live Photo", key="live_cam_input")

        if cam_file is not None:
            bytes_data = cam_file.getvalue()
            np_arr = np.frombuffer(bytes_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is not None:
                with st.spinner("🔍 AI model فریم کو تجزیہ کر رہا ہے..."):
                    try:
                        detection_result = run_detection(img, conf_threshold=conf_threshold)
                        
                        proc_img = None
                        counts = {}

                        if isinstance(detection_result, tuple):
                            proc_img = detection_result[0]
                            if len(detection_result) > 1 and isinstance(detection_result[1], dict):
                                counts = detection_result[1]
                        else:
                            proc_img = detection_result

                        if hasattr(proc_img, "plot"):
                            proc_img = proc_img.plot()
                        elif isinstance(proc_img, list) and len(proc_img) > 0:
                            if hasattr(proc_img[0], "plot"):
                                proc_img = proc_img[0].plot()
                            else:
                                proc_img = proc_img[0]

                        if isinstance(proc_img, np.ndarray):
                            rgb_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB)
                            
                            # Save state and move to verification step
                            st.session_state["live_counts"] = counts
                            st.session_state["live_tracking_id"] = generate_tracking_id()
                            st.session_state["live_processed_img"] = rgb_img
                            st.session_state["live_step"] = "VERIFY"
                            st.rerun()
                        else:
                            st.error("❌ AI پردازش میں تصویر درست نہیں ملی۔ دوبارہ کوشش کریں۔")
                    except Exception as e:
                        st.error(f"❌ Detection Error: {e}")

    # --- STEP 2: LOCATION & SUPABASE SYNC ---
    elif st.session_state["live_step"] == "VERIFY":
        st.success("✅ AI ڈیٹیکشن کامیاب! اب مقام (Location) درج کریں اور ڈیٹا سپابیس میں سنک کریں۔")

        tracking_id = st.session_state["live_last_tracking_id"] = st.session_state["live_tracking_id"]
        counts = st.session_state["live_counts"]
        processed_img = st.session_state["live_processed_img"]

        col_img, col_info = st.columns([1, 1])

        with col_img:
            if processed_img is not None:
                st.image(processed_img, caption="Analyzed Hazard", use_container_width=True)

        with col_info:
            with st.container(border=True):
                st.markdown(f"**🏷️ Tracking ID:** `{tracking_id}`")
                summary_bullets = ""
                hazard_list = []
                for k, v in counts.items():
                    if v > 0:
                        summary_bullets += f"- **{k.capitalize()}**: {v}\n"
                        hazard_list.append(f"{k.capitalize()} ({v})")
                
                main_hazard = ", ".join(hazard_list) if hazard_list else "Municipal Hazard"
                st.markdown("**📋 Detected:**")
                st.markdown(summary_bullets if summary_bullets else "- No counts found")

        st.divider()
        st.markdown("##### 📍 لوکیشن منتخب کریں")

        loc_mode = st.radio("Location Mode", ["Manual Address", "Automatic Live GPS"], horizontal=True, key="live_loc_mode")
        
        location_name = "Lahore City"
        lat, lon = 31.5204, 74.3587
        location_ready = False

        if loc_mode == "Manual Address":
            manual_addr = st.text_input("ایڈریس درج کریں:", value="Gulberg III, Lahore", key="live_manual_addr")
            if manual_addr.strip():
                location_name = manual_addr.strip()
                location_ready = True
        else:
            if streamlit_geolocation is not None:
                loc = streamlit_geolocation()
                if loc and loc.get("latitude"):
                    lat = loc["latitude"]
                    lon = loc["longitude"]
                    location_name = f"Live GPS (Lat: {lat:.4f}, Lon: {lon:.4f})"
                    location_ready = True
            else:
                st.warning("streamlit-geolocation انسٹال نہیں ہے۔")

        if location_ready:
            assessment = calculate_priority_score(counts)
            score = assessment["priority_score"]
            severity = assessment["severity"]
            dept = assessment["assigned_dept"]
            sla = assessment["sla_target"]

            st.markdown(f"**⚡ Priority Score:** {score}/100 | **Severity:** {severity}")
            st.markdown(f"**🏢 Assigned Dept:** {dept} | **⏱️ SLA:** {sla}")

            if st.button("🚀 Supabase میں ڈیٹا بھیجیں اور فائنل کریں", use_container_width=True):
                with st.spinner("ڈیٹا سنک ہو رہا ہے..."):
                    try:
                        payload = {
                            "tracking_id": tracking_id,
                            "hazard": main_hazard,
                            "issue_type": main_hazard,
                            "severity": f"{severity} ({score}/100)",
                            "status": "Active / Dispatched",
                            "location_name": location_name,
                            "latitude": lat,
                            "longitude": lon,
                            "assigned_dept": dept,
                            "sla_target": sla
                        }
                        
                        supabase.table("reports").insert(payload).execute()
                        st.success("✅ ڈیٹا کامیابی کے ساتھ Supabase میں محفوظ ہو گیا!")
                        
                        if st.button("🔄 اگلی اسکیننگ شروع کریں"):
                            st.session_state["live_step"] = "CAPTURE"
                            st.session_state["live_counts"] = {}
                            st.session_state.pop("live_processed_img", None)
                            st.rerun()
                    except Exception as db_err:
                        st.error(f"❌ Supabase Error: {db_err}")
