import streamlit as st
import av
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from ultralytics import YOLO

def render_live_camera_page(model):
    st.subheader("🔴 Live Urban Hazard Stream (Real-Time AI Detection)")
    st.markdown("Camera open karein, YOLO model khud ba khud real-time frames par hazards detect karta rahega.")

    # Define video transformer class for continuous YOLO inference
    class YOLOVideoTransformer:
        def __init__(self):
            self.model = model

        def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
            # Convert video frame to numpy array (OpenCV format)
            img = frame.to_ndarray(format="bgr24")
            
            # Run YOLO inference on the live frame
            results = self.model(img, conf=0.4)
            
            # Get annotated image with bounding boxes
            annotated_img = results[0].plot()
            
            # Extract counts for live analytics if needed
            boxes = results[0].boxes
            current_counts = {}
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                current_counts[cls_name] = current_counts.get(cls_name, 0) + 1
            
            # Save latest counts to session state safely
            st.session_state["counts"] = current_counts
            st.session_state["processed_img"] = annotated_img

            # Return processed frame back to the WebRTC stream
            return av.VideoFrame.from_ndarray(annotated_img, format="bgr24")

    # Start the WebRTC streamer
    webrtc_streamer(
        key="urbaneye-live-stream",
        video_transformer_factory=YOLOVideoTransformer,
        rtc_configuration=RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        ),
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True
    )
