import streamlit as st
import cv2
import av
import numpy as np
import time
from PIL import Image
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from models.detector import run_detection
from utils.helpers import generate_tracking_id

# Robust multi-STUN servers for live video feed
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun.stunprotocol.org:3478"]}
        ]
    }
)

def plot_boxes_on_image(img, conf):
    """Robust helper to plot bounding boxes in the main Streamlit thread (identical to snapshot mode)."""
    proc_img, counts = run_detection(img, conf)
    
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
        final_img = img
        
    return final_img, counts

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
            # Background thread sirf counts check karta hai speed ke liye
            _, counts = run_detection(pil_img, self.conf_threshold)
            
            if counts and len(counts) > 0:
                self.detected = True
                # Raw frame save kar lete hain taake main thread mein safe plotting ho sakay
                tracking_id = generate_tracking_id()
                self.result_data = {
                    "tracking_id": tracking_id,
                    "raw_img": pil_img,
                    "counts": counts,
                }
        except Exception as e:
            print(f"Inference Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(conf_threshold):
    st.markdown("### 🎥 Municipal Hazard Detection Portal")
    
    detection_mode = st.radio(
        "Select Detection Mode:",
        ["📸 Snapshot Capture (Error-Free)", "⚡ Live Video Feed (Real-Time Stream)"],
        horizontal=True,
        key="camera_mode_selector"
    )

    st.markdown("---")

    if "conf_threshold" not in st.session_state:
        st.session_state["conf_threshold"] = conf_threshold
    
    current_conf = st.slider(
        "Confidence Threshold", 0.05, 0.90, st.session_state["conf_threshold"], 0.05, key="global_conf_slider"
    )
    st.session_state["conf_threshold"] = current_conf

    # ==================== MODE 1: SNAPSHOT CAPTURE ====================
    if "Snapshot Capture" in detection_mode:
        st.markdown("#### 📸 Field Camera Snapshot Mode")
        cam_photo = st.camera_input("Take Live Photo from Camera", key="native_camera_input")
        
        if cam_photo and st.button("🔍 Analyze Field Snapshot", key="btn_snapshot_analyze"):
            img = Image.open(cam_photo)
            with st.spinner("Analyzing Camera Capture..."):
                final_img, counts = plot_boxes_on_image(img, current_conf)
                
                st.session_state.update({
                    "processed_img": final_img,
                    "counts": counts,
                    "current_tracking_id": generate_tracking_id()
                })
        
        if "processed_img" in st.session_state and st.session_state["processed_img"] is not None:
            img_to_show = st.session_state["processed_img"]
            if isinstance(img_to_show, np.ndarray):
                if len(img_to_show.shape) == 3 and img_to_show.shape[2] == 3:
                    img_to_show = cv2.cvtColor(img_to_show, cv2.COLOR_BGR2RGB)
                img_to_show = Image.fromarray(img_to_show)
                
            st.image(img_to_show, caption="Snapshot AI Analysis Result", use_container_width=True)

            if st.button("🔄 Clear Snapshot", key="reset_snapshot_btn"):
                st.session_state.pop("processed_img", None)
                st.session_state["counts"] = {}
                st.rerun()

    # ==================== MODE 2: LIVE VIDEO FEED ====================
    else:
        st.markdown("#### ⚡ Live Video Feed Auto-Stop Mode")

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
            st.session_state["current_tracking_id"] = res["tracking_id"]
            
            st.image(res["processed_img"], caption="Live Auto-Stop Detection Result", use_container_width=True)

            if st.button("🔄 Reset Live Feed", key="reset_live_capture_btn"):
                st.session_state["captured_result"] = None
                st.session_state["counts"] = {}
                st.session_state.pop("processed_img", None)
                current_transformer.detected = False
                current_transformer.result_data = None
                st.rerun()
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

            # Jab background thread hazard detect kar le, toh main thread mein plotting run karo
            if current_transformer.detected and current_transformer.result_data:
                res = current_transformer.result_data
                with st.spinner("Processing detected hazard frame..."):
                    final_img, counts = plot_boxes_on_image(res["raw_img"], current_conf)
                
                st.session_state["captured_result"] = {
                    "tracking_id": res["tracking_id"],
                    "counts": counts,
                    "processed_img": final_img
                }
                st.session_state["counts"] = counts
                st.session_state["processed_img"] = final_img
                st.session_state["current_tracking_id"] = res["tracking_id"]
                st.rerun()

            if ctx.state.playing:
                time.sleep(0.3)
                st.rerun()
