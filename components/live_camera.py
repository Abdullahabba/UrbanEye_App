import streamlit as st
import cv2
import numpy as np
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id
import time

# Local modules ko import karne mein madad deta hai
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def render_live_camera_mode(conf_threshold=0.25):
    st.markdown("### 🤖 Desktop Webcam Auto-Detection (Continuous Feed)")
    st.warning("⚠️ PROTOTYPE NOTE: Yeh sirf desktop par kaam karega. Mobile browsers par camera access nahi hoga.")
    
    # Start/Stop buttons
    col1, col2 = st.columns(2)
    start_btn = col1.button("▶️ Start Camera", key="start_cam")
    stop_btn = col2.button("⏹️ Stop Camera", key="stop_cam")

    # Session state to manage camera loop
    if "cam_active" not in st.session_state:
        st.session_state["cam_active"] = False
    
    if start_btn:
        st.session_state["cam_active"] = True
    if stop_btn:
        st.session_state["cam_active"] = False

    # Confidence Slider
    slider_conf = st.slider("AI Confidence", 0.01, 0.90, conf_threshold, 0.01)

    # Video Feed Placeholder
    vid_placeholder = st.empty()

    # Agar camera active hai
    if st.session_state["cam_active"]:
        cap = cv2.VideoCapture(0) # 0 is usually the default webcam
        
        if not cap.isOpened():
            st.error("❌ Webcam access nahi ho raha. Check karein ke camera kisi aur app mein use na ho raha ho.")
            st.session_state["cam_active"] = False
        else:
            frame_count = 0
            # Performance boost: Process every Nth frame
            SKIP_FRAMES = 8 

            while st.session_state["cam_active"]:
                ret, frame = cap.read()
                if not ret:
                    st.warning("⚠️ Frame nahi mil raha. Camera band ho raha hai.")
                    break

                frame_count += 1
                
                # --- Processing Logic ---
                processed_img = frame # Default value
                counts = {}

                # Sirf har SKIP_FRAMES ke baad model run karein
                if frame_count % SKIP_FRAMES == 0:
                    try:
                        # OpenCV frame (BGR) ko PIL Image mein convert karein
                        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        
                        # Model Detection
                        proc_res, counts = run_detection(img_pil, slider_conf)

                        # YOLO Results object ko safely parse karein (Aap ka original logic)
                        try:
                            from ultralytics.engine.results import Results
                            if isinstance(proc_res, Results):
                                processed_img = proc_res.plot() # Returns BGR numpy array
                        except ImportError:
                            pass
                            
                        if isinstance(proc_res, list) and len(proc_res) > 0:
                            try:
                                processed_img = proc_res[0].plot() # Returns BGR numpy array
                            except:
                                pass
                        
                        # Agar model ne plot return nahi kiya (sirf raw img di), original frame use karein
                        if not isinstance(processed_img, np.ndarray):
                             processed_img = frame

                    except Exception as e:
                        st.error(f"Detection Error: {e}")
                        processed_img = frame
                        counts = {}
                
                # --- Visualization ---
                # Streamlit ko btane ke liye ke yeh BGR hai jo RGB mein convert hoga
                vid_placeholder.image(processed_img, channels="BGR", use_column_width=True)
                
                # Thora sa sleep dalein taake CPU overload na ho aur UI unresponsive na ho
                time.sleep(0.01)

            # Loop khatam hone par camerarelease karein
            cap.release()
            # Ek bar image clear kar dein taake black box nazar na aye
            vid_placeholder.empty()

    else:
        st.info("🎥 Camera shuru karne ke liye 'Start Camera' dabayein.")
