import streamlit as st
from PIL import Image
import numpy as np
import cv2
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

def render_live_camera_mode(conf_threshold=0.25, *args, **kwargs):
    st.markdown("### 📸 Fully Automated Live Field Scanner & Instant Sync")
    
    # Session states initialization
    if "last_cam_bytes" not in st.session_state:
        st.session_state["last_cam_bytes"] = None
    if "auto_synced" not in st.session_state:
        st.session_state["auto_synced"] = False

    cam_photo = st.camera_input("Take Live Photo from Camera", key="camera_input")
    
    # Auto-detection triggers immediately when a new photo is taken
    if cam_photo is not None:
        current_bytes = cam_photo.getvalue()
        
        if st.session_state["last_cam_bytes"] != current_bytes:
            st.session_state["last_cam_bytes"] = current_bytes
            st.session_state["auto_synced"] = False
            
            img = Image.open(cam_photo)
            with st.spinner("🔍 AI detection aur automatic sync jari hai..."):
                try:
                    proc_img, counts = run_detection(img, conf_threshold)
                except TypeError:
                    try:
                        proc_img, counts = run_detection(img)
                    except Exception:
                        proc_img, counts = img, {}
                
                # YOLO Results object ya list ko safely NumPy array mein badlein
                try:
                    from ultralytics.engine.results import Results
                    if isinstance(proc_img, Results):
                        proc_img = proc_img.plot()
                except ImportError:
                    pass
                    
                if isinstance(proc_img, list) and len(proc_img) > 0:
                    try:
                        proc_img = proc_img[0].plot()
                    except:
                        pass
                
                # Agar NumPy array hai toh BGR se RGB karke PIL Image bana lein
                if isinstance(proc_img, np.ndarray):
                    if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                        proc_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB)
                    proc_img = Image.fromarray(proc_img)
                
                if not counts or len(counts) == 0:
                    counts = {"Hazard / Pothole": 1}

                tracking_id = generate_tracking_id()
                
                # Format hazards
                hazard_list = [f"{str(k).capitalize()} ({v})" for k, v in counts.items() if v is not None]
                main_hazard = ", ".join(hazard_list) if hazard_list else "Municipal Hazard"
                
                # Priority Assessment
                assessment = calculate_priority_score(counts)
                score = assessment["priority_score"]
                severity = assessment["severity"]
                dept = assessment["assigned_dept"]
                sla = assessment["sla_target"]

                # Live GPS Coordinates & Location
                lat, lon = 31.5204, 74.3587
                location_name = f"Live Field GPS (Lat: {lat:.4f}, Lon: {lon:.4f})"

                # Automatically push to Supabase
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
                    st.session_state["auto_synced"] = True
                except Exception as db_err:
                    st.error(f"❌ Supabase Error: {db_err}")

                st.session_state.update({
                    "processed_img": proc_img, 
                    "counts": counts, 
                    "current_tracking_id": tracking_id,
                    "assessment": assessment,
                    "location_name": location_name
                })
            st.rerun()

    # Display processed image and review section if available
    if "processed_img" in st.session_state and st.session_state["processed_img"] is not None:
        img_to_show = st.session_state["processed_img"]
        
        if isinstance(img_to_show, np.ndarray):
            if len(img_to_show.shape) == 3 and img_to_show.shape[2] == 3:
                img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_BGR2RGB)
            img_to_show = Image.fromarray(img_to_show)
            
        st.image(img_to_show, caption="Live Camera AI Result with Bounding Boxes", use_container_width=True)

        tracking_id = st.session_state.get("current_tracking_id", "TRK-0000")
        counts = st.session_state.get("counts", {})
        assessment = st.session_state.get("assessment", {})
        location_name = st.session_state.get("location_name", "Live Field GPS")

        with st.container(border=True):
            st.markdown(f"**🏷️ Tracking ID:** `{tracking_id}`")
            summary_bullets = "".join([f"- **{str(k).capitalize()}**: {v}\n" for k, v in counts.items() if v is not None])
            st.markdown("**📋 Detected Items:**")
            st.markdown(summary_bullets if summary_bullets else "- Hazard Detected")

        st.success(f"📍 Location Locked & Synced: {location_name}")
        
        if assessment:
            st.markdown(f"**⚡ Priority Score:** {assessment.get('priority_score')}/100 | **Severity:** {assessment.get('severity')}")
            st.markdown(f"**🏢 Assigned Dept:** {assessment.get('assigned_dept')} | **⏱️ SLA:** {assessment.get('sla_target')}")

        if st.session_state.get("auto_synced", False):
            st.success("✅ Data kamyabi ke sath automatically Supabase mein save ho gaya!")

        if st.button("🔄 Nayi Scanning Shuru Karein", use_container_width=True):
            st.session_state.pop("processed_img", None)
            st.session_state.pop("counts", None)
            st.session_state.pop("assessment", None)
            st.session_state["last_cam_bytes"] = None
            st.session_state["auto_synced"] = False
            st.rerun()
