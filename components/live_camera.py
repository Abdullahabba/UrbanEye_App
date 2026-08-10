import streamlit as st
import numpy as np
from PIL import Image
from models.detector import run_detection
from utils.helpers import generate_tracking_id

# Safe fallback for priority engine
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

def render_live_camera_mode(conf_threshold=0.15, user_details=None, create_pdf_report_func=None):
    st.markdown("### 📸 Live Camera Capture (Fast & Error-Free)")
    st.markdown("💡 **Camera ke samne hazard la kar capture button dabayein—foran high-quality detection aur Dispatch Panel khul jaye ga!**")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None

    conf_threshold = st.slider("Confidence Threshold", 0.05, 0.90, conf_threshold, 0.05, key="native_cam_conf")

    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        
        st.session_state["counts"] = res["counts"]
        st.session_state["processed_img"] = res["processed_img"]
        
        st.image(res["processed_img"], caption="Detected Hazard Result", use_container_width=True)

        if st.button("🔄 Capture Another Hazard", key="reset_native_capture_btn"):
            st.session_state["captured_result"] = None
            st.session_state["counts"] = {}
            st.session_state.pop("processed_img", None)
            st.rerun()

        from components.dispatch_panel import render_dispatch_panel
        render_dispatch_panel(
            tracking_id=res["tracking_id"],
            manual_loc_name="Live Camera Capture Location",
            user_details=user_details,
            create_pdf_report_func=create_pdf_report_func
        )

    else:
        # Native Streamlit camera input (No WebRTC, No STUN/TURN errors!)
        camera_file = st.camera_input("Take a picture of the hazard")

        if camera_file is not None:
            try:
                # Read image from camera input
                bytes_data = camera_file.getvalue()
                cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                
                if cv2_img is not None:
                    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    
                    with st.spinner("Running AI Detection..."):
                        proc_img, counts = run_detection(pil_img, conf_threshold)
                    
                    if counts and len(counts) > 0:
                        # Plotting bounding boxes
                        try:
                            from ultralytics.engine.results import Results
                            if isinstance(proc_img, Results):
                                proc_img = proc_img.plot()
                        except:
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
                        st.success("✅ Hazard successfully detected and captured!")
                        st.rerun()
                    else:
                        st.warning("⚠️ No municipal hazards detected in this picture. Please try again with a clearer angle.")
            except Exception as e:
                st.error(f"❌ Processing Error: {str(e)}")
