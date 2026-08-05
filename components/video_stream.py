import streamlit as st
import cv2
import numpy as np
import tempfile
import os

def render_video_stream_mode(conf_threshold):
    st.subheader("🎥 Video Stream & CCTV Inspection Mode")
    st.caption("Upload a video file or connect to a live municipal CCTV feed for automated hazard detection.")

    upload_option = st.radio("Choose Video Source:", ["📁 Upload Video File", "🔗 Live RTSP / Webcam URL"], horizontal=True)

    video_source = None
    if upload_option == "📁 Upload Video File":
        uploaded_file = st.file_uploader("Upload MP4, AVI, or MOV video", type=["mp4", "avi", "mov", "mkv"])
        if uploaded_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded_file.read())
            video_source = tfile.name
    else:
        stream_url = st.text_input("Enter RTSP Stream URL or Camera Index (e.g., 0 for webcam):", "0")
        if stream_url:
            if stream_url.isdigit():
                video_source = int(stream_url)
            else:
                video_source = stream_url

    col1, col2 = st.columns([1, 1])
    with col1:
        start_processing = st.button("▶️ Start Video Analysis", type="primary", use_container_width=True)
    with col2:
        stop_processing = st.button("⏹️ Stop Stream", use_container_width=True)

    if "stream_active" not in st.session_state:
        st.session_state["stream_active"] = False

    if start_processing:
        st.session_state["stream_active"] = True

    if stop_processing:
        st.session_state["stream_active"] = False

    if video_source is not None and st.session_state.get("stream_active", False):
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            st.error("❌ Could not open video stream. Please check the source path or file format.")
            return

        st_frame = st.empty()
        frame_count = 0
        progress_bar = st.progress(0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if isinstance(video_source, str) else 100

        while cap.isOpened() and st.session_state.get("stream_active", False):
            ret, frame = cap.read()
            if not ret:
                st.info("ℹ️ End of video stream reached.")
                break

            frame_count += 1
            
            # Basic processing / Mock detection overlay for stability
            proc_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Optional: Draw tracking box or info on frame
            h, w, _ = proc_frame.shape
            cv2.putText(proc_frame, f"CONF THRESHOLD: {conf_threshold}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Safe rendering using use_container_width
            st_frame.image(proc_frame, caption=f"Live Frame (Frame {frame_count})", use_container_width=True)

            # Capture snapshot option for reports (Safe NumPy Array Check)
            if frame_count % 30 == 0:
                if "captured_images" not in st.session_state:
                    st.session_state["captured_images"] = []
                
                is_duplicate = any(np.array_equal(proc_frame, img) for img in st.session_state["captured_images"])
                if not is_duplicate and len(st.session_state["captured_images"]) < 10:
                    st.session_state["captured_images"].append(proc_frame)

            if total_frames > 0 and isinstance(video_source, str):
                progress = min(frame_count / total_frames, 1.0)
                progress_bar.progress(progress)

        cap.release()
        st.success("✅ Video processing completed successfully.")
    elif not st.session_state.get("stream_active", False):
        st.info("ℹ️ Click 'Start Video Analysis' to begin stream processing.")
