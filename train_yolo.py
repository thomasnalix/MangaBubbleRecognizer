from ultralytics import YOLO
import os
import torch

print(f"CUDA disponible: {torch.cuda.is_available()}")
print(f"Nombre de GPU: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Nom du GPU: {torch.cuda.get_device_name(0)}")

current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'data', 'manga.yaml')

model = YOLO('yolov8n.pt')

device = '0' if torch.cuda.is_available() else 'cpu'

results = model.train(
    data=data_path,
    epochs=200,
    imgsz=640,
    batch=58,
    save=True,
    device=device,
    workers=0
)

results = model.val()
