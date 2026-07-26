import tempfile
import cv2
import numpy as np
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id
import streamlit as st

def render_video_stream_mode(conf_threshold):
    st.markdown("### 🎥 Video Stream Inspection")
    uploaded_video = st.file_uploader("Upload CCTV or Drone Footage", type=["mp4", "avi", "mov"], key="video_upload")
    
    if uploaded_video and st.button("🎥 Start Video Analysis", key="btn_video"):
        # Initialize captured images list if not present
        if "captured_images" not in st.session_state:
            st.session_state["captured_images"] = []
        else:
            # Purani images clear karna chahein taake nayi video ki fresh images aayein
            st.session_state["captured_images"] = []

        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())
        cap = cv2.VideoCapture(tfile.name)
        st_frame = st.empty()
        v_counts, last_frame, frame_count = {}, None, 0

        with st.spinner("Processing Video Stream Frame by Frame..."):
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: 
                    break
                frame_count += 1
                if frame_count % 3 != 0: 
                    continue
                
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                proc_frame, counts = run_detection(pil_img, conf_threshold)
                last_frame = proc_frame
                st_frame.image(proc_frame, caption=f"Live Frame (Frame {frame_count})", use_container_width=True)
                
                for k, v in counts.items():
                    v_counts[k] = v_counts.get(k, 0) + v

                # 🚨 STRIKING FIX: Sirf wahi frame save hoga jahan actual detections/issues milein!
                total_detected_objects = sum(counts.values()) if isinstance(counts, dict) else 0
                if total_detected_objects > 0:
                    # Convert processed frame (PIL or numpy) to numpy array if needed for storage
                    if isinstance(proc_frame, Image.Image):
                        frame_to_store = np.array(proc_frame)
                    else:
                        frame_to_store = proc_frame
                    
                    # Avoid exact duplicate continuous frames
                    if len(st.session_state["captured_images"]) == 0 or not np.array_equal(st.session_state["captured_images"][-1], frame_to_store):
                        st.session_state["captured_images"].append(frame_to_store)

        cap.release()
        st.session_state.update({
            "counts": v_counts, 
            "current_tracking_id": generate_tracking_id()
        })
        if last_frame is not None: 
            st.session_state["processed_img"] = last_frame
            
        st.success(f"✅ Video Stream Analysis Completed! Captured {len(st.session_state['captured_images'])} frames containing hazards.")
