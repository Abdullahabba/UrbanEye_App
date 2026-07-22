import io
import os
import streamlit as st
from PIL import Image
from ultralytics import YOLO

@st.cache_resource
def load_yolo_model(model_path="models/best.pt"):
    if not os.path.exists(model_path):
        st.warning(f"⚠️ '{model_path}' nahi mila! Generic YOLOv8 model system use kar raha hai.")
        return YOLO("yolov8n.pt")
    return YOLO(model_path)

def run_ai_detection(image_bytes, model_path="models/best.pt"):
    # Load Model
    model = load_yolo_model(model_path)
    
    # Bytes to PIL Image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # YOLO Inference
    results = model(img)
    
    # Plotted image with bounding boxes
    res_plotted = results[0].plot()
    result_img = Image.fromarray(res_plotted[..., ::-1]) if len(res_plotted.shape) == 3 else Image.fromarray(res_plotted)
    
    # Convert back to Bytes
    img_byte_arr = io.BytesIO()
    result_img.save(img_byte_arr, format='JPEG')
    
    # Extraction stats
    boxes = results[0].boxes
    detections_count = len(boxes) if boxes is not None else 0
    
    stats = {
        "Detections Count": detections_count,
        "Severity": "High" if detections_count > 2 else ("Medium" if detections_count > 0 else "Low"),
        "Category": "Urban Infrastructure Violation"
    }
    
    return img_byte_arr.getvalue(), stats