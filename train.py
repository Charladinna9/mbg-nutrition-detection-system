from ultralytics import YOLO

model = YOLO("yolo11n.pt")

model.train(
    data="dataset/data.yaml",
    epochs=30,
    imgsz=640,
    batch=8,
    name="mbg_model"
)