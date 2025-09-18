from ultralytics import YOLO
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'data', 'manga.yaml')

model = YOLO('yolov8n.pt')  

results = model.train(
    data=data_path, 
    epochs=100,          
    imgsz=640,          
    batch=19,
    save=True,   
    device='cpu'
)

results = model.val()