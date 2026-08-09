import streamlit as st
import cv2
import numpy as np
from models.detector import run_detection
from utils.helpers import generate_tracking_id
from database.supabase_client import supabase

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🚗 UrbanEye AI - HD Smart Capture & Supabase Sync")
    st.info("💡 Snapshot lein. AI model hazard detect karega, screen par saaf box banay ga, aur data khud ba khud Supabase par sync ho jaye ga!")

    # Streamlit native camera input (100% stable, no freezing, high resolution)
    camera_file = st.camera_input("Apne camera se hazard ki tasveer lein")

    if camera_file is not None:
        bytes_data = camera_file.getvalue()
        np_arr = np.frombuffer(bytes_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is not None:
            with st.spinner("🔍 AI model analyze kar raha hai..."):
                try:
                    # Run YOLO detection
                    detection_result = run_detection(img, conf_threshold=conf_threshold)
                    
                    # --- UNIVERSAL SAFE PARSER (Har tarah ke output ko handle karega) ---
                    processed_img = None
                    counts = {}

                    # 1. Tuple check (e.g., (image, counts))
                    if isinstance(detection_result, tuple):
                        if len(detection_result) > 0:
                            processed_img = detection_result[0]
                        if len(detection_result) > 1 and isinstance(detection_result[1], dict):
                            counts = detection_result[1]
                    else:
                        processed_img = detection_result

                    # 2. Ultralytics YOLO Results object check
                    if hasattr(processed_img, "plot"):
                        try:
                            processed_img = processed_img.plot()
                        except Exception:
                            pass

                    # 3. List of Results check
                    elif isinstance(processed_img, list) and len(processed_img) > 0:
                        first_item = processed_img[0]
                        if hasattr(first_item, "plot"):
                            try:
                                processed_img = first_item.plot()
                            except Exception:
                                processed_img = first_item
                        else:
                            processed_img = first_item

                    # Final validation check
                    if isinstance(processed_img, np.ndarray):
                        # OpenCV BGR ko RGB mein convert karna taake colors bilkul theek dikhein
                        rgb_output = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                        
                        st.success("✅ Detection Successful & Synced!")
                        st.image(rgb_output, channels="RGB", caption="AI Analyzed Hazard Result", use_container_width=True)
                        
                        # Display detected counts if available
                        if counts:
                            st.write("📊 **Detected Counts:**", counts)
                        
                        # --- AUTOMATIC SUPABASE PUSH ---
                        total_detected = sum(counts.values()) if isinstance(counts, dict) and len(counts) > 0 else 1
                        
                        if total_detected > 0:
                            tracking_id = generate_tracking_id()
                            supabase.table("reports").insert({
                                "tracking_id": tracking_id,
                                "counts": str(counts) if counts else "Detected",
                                "status": "Auto-Synced Snapshot"
                            }).execute()
                            st.toast("🚀 Data successfully pushed to Supabase database!", icon="🔥")
                    else:
                        st.error(f"❌ AI model ne valid image return nahi ki. Output type: {type(detection_result)}")
                except Exception as e:
                    st.error(f"❌ Error during AI detection or database sync: {e}")
        else:
            st.warning("Camera frame read nahi ho saka. Baraye meharbani dobara picture lein.")
