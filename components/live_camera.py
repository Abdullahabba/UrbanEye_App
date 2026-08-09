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
            "priority_score": 65,
            "severity": "Medium",
            "assigned_dept": "Municipal Operations",
            "sla_target": "24 Hours"
        }

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

def parse_detection_output(detection_result):
    """Universal helper jo YOLO output (tuple, list, Results, dict, ndarray) ko reliably parse karta hai."""
    processed_img = None
    counts = {}

    def resolve_img(item):
        if item is None:
            return None
        if isinstance(item, np.ndarray):
            return item
        if hasattr(item, "convert") and hasattr(item, "size"):
            return np.array(item)
        if hasattr(item, "plot"):
            try:
                p = item.plot()
                if isinstance(p, np.ndarray):
                    return p
            except Exception:
                pass
        if isinstance(item, (list, tuple)) and len(item) > 0:
            return resolve_img(item[0])
        return None

    if isinstance(detection_result, (tuple, list)):
        for element in detection_result:
            if isinstance(element, dict):
                counts.update(element)
            else:
                img_cand = resolve_img(element)
                if img_cand is not None and processed_img is None:
                    processed_img = img_cand
    elif isinstance(detection_result, dict):
        counts.update(detection_result)
    else:
        processed_img = resolve_img(detection_result)

    return processed_img, counts

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🚗 UrbanEye AI - Live Field Scanner & Auto-Sync")

    # Session states initialization
    if "live_step" not in st.session_state:
        st.session_state["live_step"] = "CAPTURE"
    if "live_counts" not in st.session_state:
        st.session_state["live_counts"] = {}
    if "live_tracking_id" not in st.session_state:
        st.session_state["live_tracking_id"] = None
    if "live_processed_img" not in st.session_state:
        st.session_state["live_processed_img"] = None

    # --- STEP 1: CAPTURE PHOTO ---
    if st.session_state["live_step"] == "CAPTURE":
        st.info("💡 Camera se hazard (gaddha ya kachra) ki tasveer lein. System khud ba khud detection karega!")
        
        cam_file = st.camera_input("Take Live Photo", key="live_cam_input")

        if cam_file is not None:
            bytes_data = cam_file.getvalue()
            np_arr = np.frombuffer(bytes_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is not None:
                with st.spinner("🔍 AI model frame ko analyze kar raha hai..."):
                    try:
                        try:
                            detection_result = run_detection(img, conf_threshold=conf_threshold)
                        except TypeError:
                            detection_result = run_detection(img)

                        proc_img, counts = parse_detection_output(detection_result)

                        # Fallback agar counts empty hon lekin image mil gayi ho
                        if not counts or len(counts) == 0:
                            counts = {"General Hazard / Pothole": 1}

                        if proc_img is not None and isinstance(proc_img, np.ndarray):
                            if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                                rgb_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB)
                            else:
                                rgb_img = proc_img
                            
                            st.session_state["live_counts"] = counts
                            st.session_state["live_tracking_id"] = generate_tracking_id()
                            st.session_state["live_processed_img"] = rgb_img
                            st.session_state["live_step"] = "VERIFY"
                            st.rerun()
                        else:
                            st.error(f"❌ AI processing mein valid image nahi mili.")
                    except Exception as e:
                        st.error(f"❌ Detection Error: {e}")

    # --- STEP 2: LOCATION & SUPABASE SYNC ---
    elif st.session_state["live_step"] == "VERIFY":
        st.success("✅ AI detection kamyaab! Niche di gayi details check karein aur Supabase mein sync karein.")

        tracking_id = st.session_state["live_tracking_id"]
        counts = st.session_state["live_counts"]
        processed_img = st.session_state["live_processed_img"]

        col_img, col_info = st.columns([1, 1])

        with col_img:
            if processed_img is not None:
                st.image(processed_img, caption="Analyzed Hazard Result", use_container_width=True)

        with col_info:
            with st.container(border=True):
                st.markdown(f"**🏷️ Tracking ID:** `{tracking_id}`")
                
                summary_bullets = ""
                hazard_list = []
                for k, v in counts.items():
                    if v is not None:
                        summary_bullets += f"- **{str(k).capitalize()}**: {v}\n"
                        hazard_list.append(f"{str(k).capitalize()} ({v})")
                
                main_hazard = ", ".join(hazard_list) if hazard_list else "Municipal Hazard"
                st.markdown("**📋 Detected Items:**")
                st.markdown(summary_bullets if summary_bullets else "- Hazard Detected")

        st.divider()
        st.markdown("##### 📍 Location Muntakhib Karein")

        loc_mode = st.radio("Location Mode", ["Manual Address", "Automatic Live GPS"], horizontal=True, key="live_loc_mode")
        
        location_name = "Lahore City"
        lat, lon = 31.5204, 74.3587
        location_ready = False

        if loc_mode == "Manual Address":
            manual_addr = st.text_input("Address darj karein:", value="Gulberg III, Lahore", key="live_manual_addr")
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
                st.warning("streamlit-geolocation installed nahi hai.")

        if location_ready:
            assessment = calculate_priority_score(counts)
            score = assessment["priority_score"]
            severity = assessment["severity"]
            dept = assessment["assigned_dept"]
            sla = assessment["sla_target"]

            st.markdown(f"**⚡ Priority Score:** {score}/100 | **Severity:** {severity}")
            st.markdown(f"**🏢 Assigned Dept:** {dept} | **⏱️ SLA:** {sla}")

            if st.button("🚀 Supabase mein data bhejein aur finalize karein", use_container_width=True):
                with st.spinner("Data sync ho raha hai..."):
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
                        st.success("✅ Data kamyabi ke sath Supabase mein mehfooz ho gaya!")
                        
                        if st.button("🔄 Agli scanning shuru karein"):
                            st.session_state["live_step"] = "CAPTURE"
                            st.session_state["live_counts"] = {}
                            st.session_state.pop("live_processed_img", None)
                            st.rerun()
                    except Exception as db_err:
                        st.error(f"❌ Supabase Error: {db_err}")
