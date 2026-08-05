import streamlit as st
import numpy as np
from PIL import Image

try:
    import av
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

def render_live_camera_mode(model, tracking_id, user_details, create_pdf_report_func):
    st.subheader("🔴 Live Auto-Detection & Instant Dispatch Stream")
    
    if not WEBRTC_AVAILABLE:
        st.error("❌ `streamlit-webrtc` ya `av` library install nahi hai.")
        return

    st.markdown("Live camera start karein. Jaise hi model ko koi hazard nazar ayega, woh fouri taur par capture kar ke niche report aur dispatch panel unlock kar dega!")

    # Initialize live detection flag
    if "live_hazard_detected" not in st.session_state:
        st.session_state["live_hazard_detected"] = False

    # Define video transformer class for continuous automatic YOLO inference & capture
    class YOLOVideoTransformer:
        def __init__(self):
            self.model = model

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            # Convert video frame to numpy array
            img = frame.to_ndarray(format="bgr24")
            
            # Run YOLO inference on the live frame
            results = self.model(img, conf=0.4, verbose=False)
            
            # Get annotated image with bounding boxes
            annotated_img = results[0].plot()
            
            # Extract counts for live detection check
            boxes = results[0].boxes
            current_counts = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                current_counts[cls_name] = current_counts.get(cls_name, 0) + 1
            
            # Check if any hazard is detected in the current frame
            has_hazard = any(v > 0 for v in current_counts.values())
            
            if has_hazard:
                # Automatically save counts and captured frame to session state
                st.session_state["counts"] = current_counts
                st.session_state["processed_img"] = annotated_img
                st.session_state["live_hazard_detected"] = True

            # Return processed frame back to the WebRTC stream
            return av.VideoFrame.from_ndarray(annotated_img, format="bgr24")

    # Start the WebRTC streamer
    webrtc_streamer(
        key="urbaneye-live-stream",
        video_transformer_factory=YOLOVideoTransformer,
        rtc_configuration=RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        ),
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
            },
            "audio": False
        },
        async_processing=True
    )

    # 🚀 Automatic Dispatch Panel Trigger (Appears right below camera once a hazard is caught live)
    if st.session_state.get("live_hazard_detected", False) and st.session_state.get("counts"):
        st.success("🚨 **Live Hazard Captured Successfully!** Automatic dispatch summary and report panel generated below.")
        
        # Import and render dispatch panel dynamically
        from components.dispatch_panel import render_dispatch_panel
        render_dispatch_panel(
            tracking_id=tracking_id,
            manual_loc_name="Live Camera Stream Location",
            user_details=user_details,
            create_pdf_report_func=create_pdf_report_func
        )
