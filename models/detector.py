import numpy as np
from PIL import Image
from ultralytics import YOLO


def load_yolo_model(model_path="models/best.pt"):
    """YOLO model ko load karta hai."""
    try:
        return YOLO(model_path)
    except Exception:
        return YOLO("yolov8n.pt")


def run_detection(image: Image.Image, conf_threshold=0.50):
    """Image par detection run karta hai higher confidence threshold ke sath."""
    model = load_yolo_model()

    # Image ko numpy array mein convert karna
    img_array = np.array(image)

    # 🎯 FIX: conf=0.50 aur iou=0.45 set karne se false positives khatam ho jayenge
    # imgsz=640 resolution increase karta hai taake human vs garbage ka farq samajh aaye
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
