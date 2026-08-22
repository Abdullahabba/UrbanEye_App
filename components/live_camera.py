import time
import av
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

from models.detector import run_detection
from utils.helpers import generate_tracking_id

# Fixed Global Confidence Threshold
FIXED_CONFIDENCE_THRESHOLD = 0.65

RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302", "stun:stun3.l.google.com:19302"]},
            {"urls": ["stun:global.stun.twilio.com:3478"]},
            {
                "urls": ["turn:openrelay.metered.ca:80", "turn:openrelay.metered.ca:443"],
                "username": "openrelay",
                "credential": "openrelay",
            },
        ]
    }
)


class FastDirectTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = FIXED_CONFIDENCE_THRESHOLD
        self.last_check_time = 0.0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img_bgr = frame.to_ndarray(format="bgr24")

        # Agar detect ho chuka hai toh raw frame pass-through
        if self.detected:
            return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")

        current_time = time.time()

        # Har 0.15 second baad fast OpenCV resize ke sath detection
        if current_time - self.last_check_time >= 0.15:
            self.last_check_time = current_time
            try:
                # Fast 640x640 downscale solely for YOLO model input (Takes 1-2ms)
                small_bgr = cv2.resize(img_bgr, (640, 640), interpolation=cv2.INTER_NEAREST)
                img_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)

                # Direct OpenVINO Detection Call
                proc_small, counts = run_detection(pil_img, self.conf_threshold)

                if counts and len(counts) > 0:
                    # Hazard milne par Full HD original frame par detection run karke process save kar lein
                    full_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    full_pil = Image.fromarray(full_rgb)
                    proc_full, full_counts = run_detection(full_pil, self.conf_threshold)

                    self.detected = True
                    self.result_data = {
                        "tracking_id": generate_tracking_id(),
                        "counts": full_counts,
                        "processed_img": proc_full,
                    }
            except Exception as e:
                print(f"❌ Detection Engine Error: {e}")

        # Always return full native resolution HD frame to WebRTC player
        return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")


def render_live_camera_mode(conf_threshold=FIXED_CONFIDENCE_THRESHOLD):
    st.markdown(
        """
        <style>
        div[data-testid="stWebRtc"] video {
            width: 100% !important;
            height: auto !important;
            max-height: 80vh !important;
            object-fit: contain !important;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎥 Municipal Hazard Detection Portal")

    detection_mode = st.radio(
        "Select Detection Mode:",
        ["📸 Snapshot Capture (Error-Free)", "⚡ Live Video Feed (Real-Time Stream)"],
        horizontal=True,
        key="camera_mode_selector",
    )

    st.markdown("---")

    # ==================== MODE 1: SNAPSHOT CAPTURE ====================
    if "Snapshot Capture" in detection_mode:
        st.markdown("#### 📸 Field Camera Snapshot Mode")
        cam_photo = st.camera_input("Take Live Photo from Camera", key="native_camera_input")

        if cam_photo and st.button("🔍 Analyze Field Snapshot", key="btn_snapshot_analyze"):
            img = Image.open(cam_photo)
            with st.spinner("Analyzing Camera Capture..."):
                proc_img, counts = run_detection(img, FIXED_CONFIDENCE_THRESHOLD)

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
                caption="Snapshot AI Analysis Result (Conf: 0.65)",
                use_container_width=True,
            )

            if st.button("🔄 Clear Snapshot", key="reset_snapshot_btn"):
                st.session_state.pop("processed_img", None)
                st.session_state["counts"] = {}
                st.rerun()

    # ==================== MODE 2: LIVE VIDEO FEED ====================
    else:
        st.markdown("#### ⚡ Real-Time Live Detection Stream (Conf: 0.65)")

        if "captured_result" not in st.session_state:
            st.session_state["captured_result"] = None

        if st.session_state["captured_result"] is not None:
            res = st.session_state["captured_result"]
            st.session_state["counts"] = res["counts"]
            st.session_state["processed_img"] = res["processed_img"]
            st.session_state["current_tracking_id"] = res["tracking_id"]

            st.image(
                res["processed_img"],
                caption=f"✅ Hazard Detected ({res['tracking_id']}) - Conf: 0.65",
                use_container_width=True,
            )

            if st.button("🔄 Reset Live Feed", key="reset_live_capture_btn"):
                st.session_state["captured_result"] = None
                st.session_state["counts"] = {}
                st.session_state.pop("processed_img", None)
                st.rerun()
        else:
            ctx = webrtc_streamer(
                key="direct-fast-engine-v1",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=FastDirectTransformer,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={
                    "video": {
                        "width": {"ideal": 1920, "max": 3840},
                        "height": {"ideal": 1080, "max": 2160},
                        "frameRate": {"ideal": 30, "max": 60},
                    },
                    "audio": False,
                },
                async_processing=True,
            )

            # Polling to trigger Streamlit rerun immediately upon detection
            if ctx.video_processor:
                if ctx.video_processor.detected and ctx.video_processor.result_data:
                    st.session_state["captured_result"] = ctx.video_processor.result_data
                    st.rerun()

            # Active UI Polling Loop
            if ctx.state.playing and st.session_state["captured_result"] is None:
                time.sleep(0.1)
                st.rerun()
