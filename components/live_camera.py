import streamlit as st
import cv2
import numpy as np
from models.detector import run_detection
from utils.helpers import generate_tracking_id

def render_live_camera_mode(conf_threshold=0.3):
    st.markdown("### 🚗 UrbanEye AI - Live Camera & Dashcam Capture")
    st.info("Freezing aur low resolution ke maslay ko khatam karne ke liye high-quality snapshot mode active hai. Tasveer capture karein aur foran AI result dekhein!")

    # Streamlit ka native camera input jo kabhi freeze nahi hota aur HD result deta hai
    camera_file = st.camera_input("Apne mobile ya laptop camera se live shot lein")

    if camera_file is not None:
        # Uploaded file bytes ko OpenCV image (NumPy array) mein convert karna
        bytes_data = camera_file.getvalue()
        np_arr = np.frombuffer(bytes_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is not None:
            with st.spinner("🔍 AI model hazards detect kar raha hai..."):
                # YOLO detection run karna set confidence (0.3) ke sath
                detection_result = run_detection(img, conf_threshold=conf_threshold)
                
                if isinstance(detection_result, tuple):
                    processed_img = detection_result[0]
                else:
                    processed_img = detection_result

                # YOLO Results object ya list ko handle karna
                if hasattr(processed_img, "plot"):
                    processed_img = processed_img.plot()
                elif isinstance(processed_img, list) and len(processed_img) > 0:
                    if hasattr(processed_img[0], "plot"):
                        processed_img = processed_img[0].plot()
                    else:
                        processed_img = processed_img[0]
                
                if isinstance(processed_img, np.ndarray):
                    # OpenCV BGR ko Streamlit ke liye RGB mein convert karna taake colors bilkul theek dikhein
                    rgb_output = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
                    
                    st.success("✅ Detection Successful!")
                    st.image(rgb_output, channels="RGB", caption="AI Analyzed Snapshot", use_container_width=True)
                    
                    # Session state mein save karna taake report ya dispatch panel mein use ho sakay
                    st.session_state["processed_img"] = processed_img
                    if "captured_images" in st.session_state:
                        if processed_img not in st.session_state["captured_images"]:
                            st.session_state["captured_images"].append(processed_img)
                else:
                    st.error("❌ AI processing mein koi masla aaya hai. Dobara try karein.")
        else:
            st.warning("Camera frame read nahi ho saka. Baraye meharbani dobara picture lein.")
