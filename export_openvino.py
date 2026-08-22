from ultralytics import YOLO

# Model load karke export karein
model = YOLO("models/best.pt")
model.export(format="openvino", imgsz=640, half=True)
