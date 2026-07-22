import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO


def load_yolo_model(model_path="models/best.pt"):
    """YOLO model ko load karta hai (fallback: yolov8n.pt agar custom weight missing ho)."""
    try:
        return YOLO(model_path)
    except Exception:
        return YOLO("yolov8n.pt")


def run_detection(image: Image.Image):
    """Image par detection run karta hai aur processed image + counts return karta hai."""
    model = load_yolo_model()

    # Image ko numpy array mein convert karna
    img_array = np.array(image)

    # YOLO Inference
    results = model(img_array)
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
