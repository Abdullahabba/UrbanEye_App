import streamlit as st
import cv2
import numpy as np
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

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

def render_live_camera_mode(conf_threshold=0.15, user_details=None, create_pdf_report_func=None, *args, **kwargs):
    st.markdown("### 📸 Live Camera Capture & Detection")
    st.markdown("💡 **Camera open karein, tasweer capture karein—AI foran hazard detect kar ke neechay Dispatch Panel unlock kar dega.**")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None

    conf_threshold = st.slider("Confidence Threshold", 0.05, 0.90, conf_threshold, 0.05, key="live_cam_conf_slider")

    # Native, 100% reliable camera input (Never freezes or blocks)
    camera_file = st.camera_input("Take a photo of the hazard", key="urbaneye_native_camera_input")

    if camera_file is not None:
        # Convert uploaded image bytes to OpenCV / PIL format
        bytes_data = camera_file.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Run YOLO Detection
        proc_img, counts = run_detection(pil_img, conf_threshold)

        # Bounding box plotting logic
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
        
        if isinstance(proc_img, np.ndarray):
            if len(proc_img.shape) == 3 and proc_img.shape[2] == 3:
                proc_img = cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB)
            final_img = Image.fromarray(proc_img)
        elif isinstance(proc_img, Image.Image):
            final_img = proc_img
        else:
            final_img = pil_img

        tracking_id = generate_tracking_id()
        assessment = calculate_priority_score(counts)

        st.session_state["captured_result"] = {
            "tracking_id": tracking_id,
            "counts": counts,
            "processed_img": final_img,
            "assessment": assessment
        }
        st.session_state["counts"] = counts
        st.session_state["processed_img"] = final_img
        st.rerun()

    # Display captured result and dispatch panel if available
    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        
        st.image(res["processed_img"], caption="Detected Hazard Result with Bounding Boxes", use_container_width=True)

        from components.dispatch_panel import render_dispatch_panel
        
        render_dispatch_panel(
            tracking_id=res["tracking_id"],
            manual_loc_name="Live Camera Feed Location",
            user_details=user_details,
            create_pdf_report_func=create_pdf_report_func
        )
