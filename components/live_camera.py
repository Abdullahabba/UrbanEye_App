import av
import cv2
import gc
import numpy as np
import threading
from queue import Queue, Empty
import streamlit as st
from PIL import Image
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

# Fixed Global Confidence Threshold
FIXED_CONFIDENCE_THRESHOLD = 0.70

# Multi-STUN & TURN Relays with Optimized Buffer
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


class LeakFreePerformanceTransformer:
    def __init__(self):
        self.detected = False
        self.result_data = None
        self.conf_threshold = FIXED_CONFIDENCE_THRESHOLD
        
        # Lock Frame Queue to size 1 with auto-purge
        self.frame_queue = Queue(maxsize=1)
        self.lock = threading.Lock()
        
        # Async Worker Control
        self.stopped = False
        self.worker_thread = threading.Thread(target=self._ai_worker_loop, daemon=True)
        self.worker_thread.start()

    def _ai_worker_loop(self):
        """Dedicated Inference Thread with Explicit Garbage Collection"""
        while not self.stopped:
            try:
                img_bgr = self.frame_queue.get(timeout=0.1)
            except Empty:
                continue

            if self.detected:
                del img_bgr
                continue

            try:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)

                from models.detector import run_detection
                from utils.helpers import generate_tracking_id

                proc_img, counts = run_detection(pil_img, self.conf_threshold)

                if counts and len(counts) > 0:
                    with self.lock:
                        self.detected = True
                        tracking_id = generate_tracking_id()
                        self.result_data = {
                            "tracking_id": tracking_id,
                            "counts": counts,
                            "processed_img": proc_img,
                        }
            except Exception as e:
                print(f"Inference Engine Error: {e}")
            finally:
                # Force Memory Release
                del img_bgr
                gc.collect()

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Zero-Copy Passthrough for Constant 1080p/4K Crisp Quality"""
        img_bgr = frame.to_ndarray(format="bgr24")

        if not self.detected and not self.frame_queue.full():
            try:
                self.frame_queue.put_nowait(img_bgr)
            except Exception:
                pass

        return av.VideoFrame.from_ndarray(img_bgr, format="bgr24")

    def stop(self):
        self.stopped = True


def render_live_camera_mode(conf_threshold=FIXED_CONFIDENCE_THRESHOLD):
    # CSS to force sharp pixel rendering and prevent canvas downscaling
    st.markdown(
        """
        <style>
        div[data-testid="stWebRtc"] video {
            width: 100% !important;
            height: auto !important;
            max-height: 80vh !important;
            object-fit: contain !important;
            image-rendering: crisp-edges !important;
            image-rendering: -webkit-optimize-contrast !important;
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
            from models.detector import run_detection
            from utils.helpers import generate_tracking_id

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
                caption="Snapshot AI Analysis Result (Fixed Conf: 0.70)",
                use_container_width=True,
            )

            if st.button("🔄 Clear Snapshot", key="reset_snapshot_btn"):
                st.session_state.pop("processed_img", None)
                st.session_state["counts"] = {}
                st.rerun()

    # ==================== MODE 2: LIVE VIDEO FEED ====================
    else:
        st.markdown("#### ⚡ Ultra-HD Fixed Quality Live Stream")

        if "captured_result" not in st.session_state:
            st.session_state["captured_result"] = None

        if st.session_state["captured_result"] is not None:
            res = st.session_state["captured_result"]
            st.session_state["counts"] = res["counts"]
            st.session_state["processed_img"] = res["processed_img"]
            st.session_state["current_tracking_id"] = res["tracking_id"]

            st.image(
                res["processed_img"],
                caption=f"✅ Hazard Detected ({res['tracking_id']}) - Conf: 0.70",
                use_container_width=True,
            )

            if st.button("🔄 Reset Live Feed", key="reset_live_capture_btn"):
                st.session_state["captured_result"] = None
                st.session_state["counts"] = {}
                st.session_state.pop("processed_img", None)
                st.rerun()
        else:
            ctx = webrtc_streamer(
                key="extreme-engine-fixed-quality",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=LeakFreePerformanceTransformer,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={
                    "video": {
                        "width": {"ideal": 1920, "max": 3840},
                        "height": {"ideal": 1080, "max": 2160},
                        "frameRate": {"ideal": 30, "max": 60},
                        "degradationPreference": "maintain-resolution",  # Prevents quality drop
                    },
                    "audio": False,
                },
                async_processing=True,
            )

            # Polling mechanism replacing st.rerun() infinite loop
            if ctx.video_processor and ctx.video_processor.detected:
                if ctx.video_processor.result_data:
                    st.session_state["captured_result"] = ctx.video_processor.result_data
                    st.rerun()
