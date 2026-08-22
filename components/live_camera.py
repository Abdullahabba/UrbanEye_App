import time
import av
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

from models.detector import run_detection
from utils.helpers import generate_tracking_id

# Extended STUN servers for fail-proof WebRTC connections
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302", "stun:stun3.l.google.com:19302"]},
            {"urls": ["stun:stun.stunprotocol.org:3478"]},
        ]
    }
)


class AutoStopTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = 0.35
        self.frame_counter = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img_bgr = frame.to_ndarray(format="bgr24")

        if self.detected:
            return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")

        # High resolution par processing smooth rakhne ke liye alternate frames
        self.frame_counter += 1
        if self.frame_counter % 2 != 0:
            return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")

        try:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            proc_img, counts = run_detection(pil_img, self.conf_threshold)

            if counts and len(counts) > 0:
                self.detected = True
                tracking_id = generate_tracking_id()

                self.result_data = {
                    "tracking_id": tracking_id,
                    "counts": counts,
                    "processed_img": proc_img,
                }
        except Exception as e:
            print(f"Inference Error in Stream: {e}")

        return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")


def render_live_camera_mode(conf_threshold):
    st.markdown("### 🎥 Municipal Hazard Detection Portal")

    detection_mode = st.radio(
        "Select Detection Mode:",
        ["📸 Snapshot Capture (Error-Free)", "⚡ Live Video Feed (Real-Time Stream)"],
        horizontal=True,
        key="camera_mode_selector",
    )

    st.markdown("---")

    if "conf_threshold" not in st.session_state:
        st.session_state["conf_threshold"] = conf_threshold

    current_conf = st.slider(
        "Confidence Threshold",
        0.05,
        0.90,
        st.session_state["conf_threshold"],
        0.05,
        key="global_conf_slider",
    )
    st.session_state["conf_threshold"] = current_conf

    # ==================== MODE 1: SNAPSHOT CAPTURE ====================
    if "Snapshot Capture" in detection_mode:
        st.markdown("#### 📸 Field Camera Snapshot Mode")
        cam_photo = st.camera_input("Take Live Photo from Camera", key="native_camera_input")

        if cam_photo and st.button("🔍 Analyze Field Snapshot", key="btn_snapshot_analyze"):
            img = Image.open(cam_photo)
            with st.spinner("Analyzing Camera Capture..."):
                proc_img, counts = run_detection(img, current_conf)

                st.session_state.update(
                    {
                        "processed_img": proc_img,
                        "counts": counts,
                        "current_tracking_id": generate_tracking_id(),
                    }
                )

        if "processed_img" in st.session_state and st.session_state["processed_img"] is not None:
            st.image(
                st.session_state["processed_img"],
                caption="Snapshot AI Analysis Result",
                use_container_width=True,
            )

            if st.button("🔄 Clear Snapshot", key="reset_snapshot_btn"):
                st.session_state.pop("processed_img", None)
                st.session_state["counts"] = {}
                st.rerun()

    # ==================== MODE 2: LIVE VIDEO FEED ====================
    else:
        st.markdown("#### ⚡ Live Video Feed Auto-Stop Mode")

        if "captured_result" not in st.session_state:
            st.session_state["captured_result"] = None

        if st.session_state["captured_result"] is not None:
            res = st.session_state["captured_result"]
            st.session_state["counts"] = res["counts"]
            st.session_state["processed_img"] = res["processed_img"]
            st.session_state["current_tracking_id"] = res["tracking_id"]

            st.image(
                res["processed_img"],
                caption=f"✅ Hazard Detected ({res['tracking_id']})",
                use_container_width=True,
            )

            if st.button("🔄 Reset Live Feed", key="reset_live_capture_btn"):
                st.session_state["captured_result"] = None
                st.session_state["counts"] = {}
                st.session_state.pop("processed_img", None)
                st.rerun()
        else:
            ctx = webrtc_streamer(
                key="auto-stop-streamer-maxres",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=AutoStopTransformer,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={
                    "video": {
                        "width": {"ideal": 1920, "max": 3840},
                        "height": {"ideal": 1080, "max": 2160},
                        "frameRate": {"ideal": 30},
                    },
                    "audio": False,
                },
                async_processing=True,
            )

            if ctx.video_processor:
                ctx.video_processor.conf_threshold = current_conf

                if ctx.video_processor.detected and ctx.video_processor.result_data:
                    st.session_state["captured_result"] = ctx.video_processor.result_data
                    st.rerun()

            if ctx.state.playing:
                time.sleep(0.2)
                st.rerun()
