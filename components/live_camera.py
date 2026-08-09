import streamlit as st
import cv2
import numpy as np
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

def extract_img_and_counts(result):
    """Smart helper function jo kisi bhi type ke YOLO output se Image aur Counts extract kar leta hai."""
    processed_img = None
    counts = {}

    def resolve_img(item):
        if item is None:
            return None
        # 1. Direct NumPy Array
        if isinstance(item, np.ndarray):
            return item
        # 2. PIL Image Object
        if hasattr(item, "convert") and hasattr(item, "size"):
            return np.array(item)
        # 3. YOLO Results Object
        if hasattr(item, "plot"):
            try:
                p = item.plot()
                if isinstance(p, np.ndarray):
                    return p
            except Exception:
                pass
        # 4. List / Tuple of Results
        if isinstance(item, (list, tuple)) and len(item) > 0:
            return resolve_img(item[0])
        return None

    if isinstance(result, (tuple, list)):
        for element in result:
            if isinstance(element, dict):
                counts = element
            else:
                img_candidate = resolve_img(element)
                if img_candidate is not None and processed_img is None:
                    processed_img = img_candidate
    else:
        if isinstance(result, dict):
            counts = result
        else:
            processed_img = resolve_img(result)

    return processed_img, counts

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🚗 UrbanEye AI - Smart Capture & Supabase Sync")
    st.info("💡 Camera se hazard ki tasveer lein. Smart Extractor automatically output parse kar ke Supabase par push karega!")

    camera_file = st.camera_input("Apne camera se hazard ki tasveer lein")

    if camera_file is not None:
        bytes_data = camera_file.getvalue()
        np_arr = np.frombuffer(bytes_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is not None:
            with st.spinner("🔍 AI model analyze kar raha hai..."):
                try:
                    # Run YOLO detection
                    try:
                        detection_result = run_detection(img, conf_threshold=conf_threshold)
                    except TypeError:
                        detection_result = run_detection(img)

                    # Extract image and counts using smart resolver
                    processed_img, counts = extract_img_and_counts(detection_result)

                    if processed_img is not None and isinstance(processed_img, np.ndarray):
                        # Convert BGR to RGB for correct Streamlit color rendering
                        if len(processed_img.shape) == 3 and processed_img.shape[2] == 3:
                            rgb_output = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                        else:
                            rgb_output = processed_img

                        st.success("✅ Detection Successful & Synced!")
                        st.image(rgb_output, caption="AI Analyzed Hazard Result", use_container_width=True)

                        if counts:
                            st.write("📊 **Detected Counts:**", counts)

                        # --- AUTOMATIC SUPABASE PUSH ---
                        total_detected = sum(counts.values()) if isinstance(counts, dict) and len(counts) > 0 else 1
                        
                        if total_detected > 0:
                            tracking_id = generate_tracking_id()
                            supabase.table("reports").insert({
                                "tracking_id": tracking_id,
                                "counts": str(counts) if counts else "Hazard Detected",
                                "status": "Auto-Synced Snapshot"
                            }).execute()
                            st.toast("🚀 Data successfully pushed to Supabase database!", icon="🔥")
                    else:
                        st.error("❌ Output tuple se valid image extract nahi ho saki.")
                        st.write("🔍 **Raw Return Structure (Debug):**", detection_result)
                except Exception as e:
                    st.error(f"❌ Error during AI detection: {e}")
        else:
            st.warning("Camera frame read nahi ho saka.")
