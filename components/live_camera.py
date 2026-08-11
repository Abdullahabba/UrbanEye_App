import streamlit as st
import cv2
import av
import numpy as np
import time
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
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

# Robust multi-STUN servers for live video feed
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun.stunprotocol.org:3478"]}
        ]
    }
)

class AutoStopTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = 0.15

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        if self.detected:
            return frame
        
        img = frame.to_ndarray(format="bgr24")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        try:
            proc_img, counts = run_detection(pil_img, self.conf_threshold)
            
            if counts and len(counts) > 0:
                self.detected = True
                
                try:
                    from ultralytics.engine.results import Results
                    if isinstance(proc_img, Results):
                        proc_img = proc_img.plot()
                except: pass
                    
                if isinstance(proc_img, list) and len(proc_img) > 0:
                    try: proc_img = proc_img[0].plot()
                    except: pass
                
                if isinstance(proc_img, np.ndarray):
                    final_img = Image.fromarray(cv2.cvtColor(proc_img, cv2.COLOR_BGR2RGB))
                else:
                    final_img = pil_img
                
                tracking_id = generate_tracking_id()
                self.result_data = {
                    "tracking_id": tracking_id,
                    "counts": counts,
                    "processed_img": final_img,
                    "assessment": calculate_priority_score(counts)
                }
        except Exception as e:
            print(f"Inference Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(conf_threshold=0.15, user_details=None, create_pdf_report_func=None, *args, **kwargs):
    st.markdown("### 🎥 Municipal Hazard Detection Portal")
    
    # Mode selection radio button
    detection_mode = st.radio(
        "Select Detection Mode:",
        ["📸 Snapshot Capture (Recommended / Error-Free)", "⚡ Live Video Feed (Real-Time Stream)"],
        horizontal=True,
        key="camera_mode_selector"
    )

    st.markdown("---")

    # Global Confidence Threshold Slider
    if "conf_threshold" not in st.session_state:
        st.session_state["conf_threshold"] = conf_threshold
    
    st.session_state["conf_threshold"] = st.slider(
        "Confidence Threshold", 0.05, 0.90, st.session_state["conf_threshold"], 0.05, key="global_conf_slider"
    )
    current_conf = st.session_state["conf_threshold"]

    # ==================== MODE 1: SNAPSHOT CAPTURE ====================
    if "Snapshot Capture" in detection_mode:
        st.markdown("#### 📸 Field Camera Snapshot Mode")
        st.markdown("💡 *Camera ke samne hazard la kar photo capture karein aur foran analyze karein.*")

        cam_photo = st.camera_input("Take Live Photo from Camera", key="native_camera_input")
        
        if cam_photo and st.button("🔍 Analyze Field Snapshot", key="btn_snapshot_analyze"):
            img = Image.open(cam_photo)
            with st.spinner("Analyzing Camera Capture..."):
                proc_img, counts = run_detection(img, current_conf)
                
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
                    proc_img = Image.fromarray(proc_img)
                
                st.session_state.update({
                    "snapshot_processed_img": proc_img,
                    "counts": counts,
                    "current_tracking_id": generate_tracking_id(),
                    "snapshot_assessment": calculate_priority_score(counts) if counts else None
                })
        
        if "snapshot_processed_img" in st.session_state and st.session_state["snapshot_processed_img"] is not None:
            img_to_show = st.session_state["snapshot_processed_img"]
            
            if isinstance(img_to_show, np.ndarray):
                if len(img_to_show.shape) == 3 and img_to_show.shape[2] == 3:
                    img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_BGR2RGB)
                img_to_show = Image.fromarray(img_to_show)
                
            st.image(img_to_show, caption="Snapshot AI Analysis Result", use_container_width=True)

            if st.button("🔄 Clear Snapshot & Capture Another", key="reset_snapshot_btn"):
                st.session_state.pop("snapshot_processed_img", None)
                st.session_state.pop("snapshot_assessment", None)
                st.session_state["counts"] = {}
                st.rerun()

            from components.dispatch_panel import render_dispatch_panel
            render_dispatch_panel(
                tracking_id=st.session_state.get("current_tracking_id", generate_tracking_id()),
                manual_loc_name="Snapshot Camera Location",
                user_details=user_details,
                create_pdf_report_func=create_pdf_report_func
            )

    # ==================== MODE 2: LIVE VIDEO FEED ====================
    else:
        st.markdown("#### ⚡ Live Video Feed Auto-Stop Mode")
        st.markdown("💡 *Stream start karein; jaise hi hazard samne aaye ga, AI khud-b-khud capture kar lega.*")

        if "captured_result" not in st.session_state:
            st.session_state["captured_result"] = None

        if "auto_stop_transformer_instance" not in st.session_state:
            st.session_state["auto_stop_transformer_instance"] = AutoStopTransformer()
        
        current_transformer = st.session_state["auto_stop_transformer_instance"]
        current_transformer.conf_threshold = current_conf

        if st.session_state["captured_result"] is not None:
            res = st.session_state["captured_result"]
            st.session_state["counts"] = res["counts"]
            st.session_state["processed_img"] = res["processed_img"]
            
            st.image(res["processed_img"], caption="Live Auto-Stop Detection Result", use_container_width=True)

            if st.button("🔄 Reset Live Feed", key="reset_live_capture_btn"):
                st.session_state["captured_result"] = None
                st.session_state["counts"] = {}
                st.session_state.pop("processed_img", None)
                current_transformer.detected = False
                current_transformer.result_data = None
                st.rerun()

            from components.dispatch_panel import render_dispatch_panel
            render_dispatch_panel(
                tracking_id=res["tracking_id"],
                manual_loc_name="Live Camera Stream Location",
                user_details=user_details,
                create_pdf_report_func=create_pdf_report_func
            )
        else:
            ctx = webrtc_streamer(
                key="auto-stop-streamer-unified",
                video_processor_factory=lambda: current_transformer,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={
                    "video": {"width": 640, "height": 480}, 
                    "audio": False
                },
                async_processing=True,
            )

            if current_transformer.detected and current_transformer.result_data:
                st.session_state["captured_result"] = current_transformer.result_data
                st.session_state["counts"] = current_transformer.result_data["counts"]
                st.session_state["processed_img"] = current_transformer.result_data["processed_img"]
                st.rerun()

            if ctx.state.playing:
                time.sleep(0.3)
                st.rerun()
