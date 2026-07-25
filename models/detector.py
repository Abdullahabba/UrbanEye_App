import random
import string
import numpy as np
from PIL import Image
import streamlit as st
from ultralytics import YOLO
from database.supabase_client import supabase


# -----------------------------------------------------------------------------
# 1. MODEL LOADING (WITH CACHING FOR FAST PERFORMANCE)
# -----------------------------------------------------------------------------
@st.cache_resource
def load_yolo_model(model_path="models/best.pt"):
    """YOLO model ko load karta hai (cached so it doesn't reload every time)."""
    try:
        return YOLO(model_path)
    except Exception:
        return YOLO("yolov8n.pt")


# -----------------------------------------------------------------------------
# 2. RUN DETECTION
# -----------------------------------------------------------------------------
def run_detection(image: Image.Image, conf_threshold=0.50):
    """Image par detection run karta hai higher confidence threshold ke sath."""
    model = load_yolo_model()

    # Image ko numpy array mein convert karna
    img_array = np.array(image)

    # Detection run karna
    results = model(img_array, conf=conf_threshold, iou=0.45, imgsz=640)
    res = results[0]

    # Processed Image (Bounding boxes ke sath)
    res_plotted = res.plot()
    processed_img = Image.fromarray(res_plotted)

    # Object Counts calculate karna
    counts = {}
    for box in res.boxes:
        cls_id = int(box.cls[0])
        class_name = model.names[cls_id]
        counts[class_name] = counts.get(class_name, 0) + 1

    return processed_img, counts


# -----------------------------------------------------------------------------
# 3. TRACKING ID GENERATOR
# -----------------------------------------------------------------------------
def generate_tracking_id():
    """Generates a unique tracking code like UE-48291."""
    random_digits = "".join(random.choices(string.digits, k=5))
    return f"UE-{random_digits}"


# -----------------------------------------------------------------------------
# 4. SAVE REPORT TO SUPABASE (UPDATED WITH GEO-TAGGING)
# -----------------------------------------------------------------------------
def save_detection_report(user_id, counts, location, description="", latitude=None, longitude=None):
    """Detection results ko Supabase 'reports' table me coordinates ke sath submit karta hai."""
    if not counts:
        issue_summary = "General Civic Defect"
    else:
        # Detected objects se string banana (e.g., "Pothole x 2, Garbage x 1")
        issue_summary = ", ".join([f"{k} x {v}" for k, v in counts.items()])

    tracking_id = generate_tracking_id()

    data = {
        "tracking_id": tracking_id,
        "user_id": user_id,
        "issue_type": issue_summary,
        "location": location.strip() if location else "Location not specified",
        "description": description.strip(),
        "status": "Pending",
        "latitude": latitude,   # Map view ke liye zaroori
        "longitude": longitude, # Map view ke liye zaroori
    }

    response = supabase.table("reports").insert(data).execute()
    return tracking_id, response
