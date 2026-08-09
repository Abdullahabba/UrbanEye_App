import streamlit as st
import cv2
import av
import numpy as np
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

# Multiple STUN servers for stable connection
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302", "stun:stun.stunprotocol.org:3478"]}
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
        try:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            proc_img, counts = run_detection(pil_img, self.conf_threshold)
            
            if counts and len(counts) > 0:
                self.detected = True
                
                # --- Bounding-box plotting logic ---
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
                    final_img = Image.fromarray(img)
                # -----------------------------------
                
                tracking_id = generate_tracking_id()
                assessment = calculate_priority_score(counts)
                
                self.result_data = {
                    "tracking_id": tracking_id,
                    "counts": counts,
                    "processed_img": final_img,
                    "assessment": assessment
                }
        except Exception as e:
            print(f"Auto-Stop Error: {e}")
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def render_live_camera_mode(conf_threshold=0.15, user_details=None, create_pdf_report_func=None, *args, **kwargs):
    st.markdown("### 📸 Auto-Stop AI Detection & Dispatch")
    st.markdown("💡 **Camera start karein—hazard detect hotay hi camera stop ho jaye ga aur neechay Dispatch Panel unlock ho jaye ga.**")

    if "captured_result" not in st.session_state:
        st.session_state["captured_result"] = None

    conf_threshold = st.slider("Confidence Threshold", 0.05, 0.90, conf_threshold, 0.05, key="auto_stop_conf")

    if st.session_state["captured_result"] is not None:
        res = st.session_state["captured_result"]
        
        # Session state variables set karna taake dispatch panel inhein access kar sakay
        st.session_state["counts"] = res["counts"]
        st.session_state["processed_img"] = res["processed_img"]
        
        # Display detected image with bounding boxes
        st.image(res["processed_img"], caption="Detected Hazard Result with Bounding Boxes", use_container_width=True)

        # 🚀 Dispatch Panel ko call kar diya hai (Yeh tab tak Supabase mein push nahi karega jab tak location select na ho)
        from components.dispatch_panel import render_dispatch_panel # Agar aap ke paas alag file hai toh import karein, warna function yahan available hona chahiye
        
        render_dispatch_panel(
            tracking_id=res["tracking_id"],
            manual_loc_name="Live Camera Feed Location",
            user_details=user_details,
            create_pdf_report_func=create_pdf_report_func
        )

    else:
        st.info("ℹ️ Camera live hai... Samne hazard laane par yeh khud-ba-khud capture kar lega.")
        
        ctx = webrtc_streamer(
            key="auto-stop-streamer-clean",
            video_processor_factory=AutoStopTransformer,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
            async_processing=True,
        )

        if ctx.video_processor:
            ctx.video_processor.conf_threshold = conf_threshold

        if ctx.video_processor and ctx.video_processor.detected and ctx.video_processor.result_data:
            res = ctx.video_processor.result_data
            st.session_state["captured_result"] = res
            st.session_state["counts"] = res["counts"]
            st.session_state["processed_img"] = res["processed_img"]
            
            # Note: Yahan se Supabase push code mukammal hata diya gaya hai taake bina location ke data save na ho.
            st.rerun()
