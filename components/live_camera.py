import streamlit as st
import numpy as np
from PIL import Image

try:
    import av
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

def render_live_camera_mode(model_or_conf=None):
    st.subheader("🔴 Live Auto-Detection & Instant Dispatch Stream")
    
    if not WEBRTC_AVAILABLE:
        st.error("❌ `streamlit-webrtc` ya `av` library install nahi hai. Baraye meharbani `requirements.txt` check karein.")
        return

    # Safely fetch model from arguments or session state
    model = st.session_state.get("yolo_model", None)
    if model is None and hasattr(model_or_conf, "predict"):
        model = model_or_conf
    elif model is None:
        model = st.session_state.get("model", None)

    tracking_id = st.session_state.get("current_tracking_id", "TRK-9999")
    user_details = st.session_state.get("user", {"email": "officer@urbaneye.ai"})
    
    # PDF report function import safety
    try:
        from utils.pdf_generator import create_pdf_report as create_pdf_report_func
    except ImportError:
        create_pdf_report_func = None

    st.markdown("Live camera start karein. Jaise hi model ko koi hazard nazar ayega, woh fouri taur par capture kar ke niche report aur dispatch panel unlock kar dega!")

    # Initialize live detection flag
    if "live_hazard_detected" not in st.session_state:
        st.session_state["live_hazard_detected"] = False

    # Define video transformer class for continuous automatic YOLO inference & capture
    class YOLOVideoTransformer:
        def __init__(self, yolo_model):
            self.model = yolo_model

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            img = frame.to_ndarray(format="bgr24")
            if self.model is None:
                return frame
            
            # Run YOLO inference on the live frame
            results = self.model(img, conf=0.4, verbose=False)
            annotated_img = results[0].plot()
            
            # Extract counts for live detection check
            boxes = results[0].boxes
            current_counts = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                current_counts[cls_name] = current_counts.get(cls_name, 0) + 1
            
            has_hazard = any(v > 0 for v in current_counts.values())
            
            if has_hazard:
                st.session_state["counts"] = current_counts
                st.session_state["processed_img"] = annotated_img
                st.session_state["live_hazard_detected"] = True

            return av.VideoFrame.from_ndarray(annotated_img, format="bgr24")

    # Start the WebRTC streamer with Metered.ca TURN & Forced Relay Policy
    webrtc_streamer(
        key="urbaneye-live-stream",
        video_transformer_factory=lambda: YOLOVideoTransformer(model),
        rtc_configuration=RTCConfiguration(
            {
                "iceServers": [
                    {
                        "urls": [
                            "turn:global.relay.metered.ca:443",
                            "turn:global.relay.metered.ca:443?transport=tcp"
                        ],
                        "username": "dec13fdaf07c16be9aa5a658",
                        "credential": "oeVKjF/Q0BMt13lM"
                    }
                ],
                "iceTransportPolicy": "relay"  # Forces connection through TURN, eliminating timeout/connection errors
            }
        ),
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280, "max": 1920},
                "height": {"ideal": 720, "max": 1080},
            },
            "audio": False
        },
        async_processing=True
    )

    # 🚀 Automatic Dispatch Panel Trigger (Appears right below camera once a hazard is caught live)
    if st.session_state.get("live_hazard_detected", False) and st.session_state.get("counts"):
        st.success("🚨 **Live Hazard Captured Successfully!** Automatic dispatch summary and report panel generated below.")
        
        from components.dispatch_panel import render_dispatch_panel
        render_dispatch_panel(
            tracking_id=tracking_id,
            manual_loc_name="Live Camera Stream Location",
            user_details=user_details,
            create_pdf_report_func=create_pdf_report_func
        )
