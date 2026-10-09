"""
train.py — Fine-tune YOLO11n on Real Interview-Scene Phone Dataset
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
import sys
import shutil
import json
import torch
from ultralytics import YOLO

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    data_yaml = os.path.join(base_dir, "data_v2.yaml")
    output_model_dir = os.path.join(project_root, "models", "phone_detector")
    os.makedirs(output_model_dir, exist_ok=True)

    # Detect hardware
    cuda_available = torch.cuda.is_available()
    device = "0" if cuda_available else "cpu"
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"

    print("=" * 60)
    print("  InterviewIQ — YOLO11n Part 1 V2 Phone Model Fine-Tuning")
    print("=" * 60)
    print(f"Dataset Config   : {data_yaml}")
    print(f"Target Hardware  : Device='{device}' ({device_name})")
    print(f"Output Directory : {output_model_dir}")

    # Load Pretrained YOLO11n Base Model
    try:
        model = YOLO("yolo11n.pt")
        model_name = "YOLO11n"
    except Exception as e:
        print(f"[INFO] YOLO11n download fallback ({e}), using yolov8n.pt")
        model = YOLO("yolov8n.pt")
        model_name = "YOLOv8n"

    print(f"[MODEL] Loaded pretrained base model: {model_name}")

    # Fine-Tune on 80 Train / 10 Val images
    results = model.train(
        data=data_yaml,
        epochs=10,
        imgsz=416 if not cuda_available else 640,
        batch=8,
        device=device,
        workers=0,
        patience=4,
        name="v2_phone_run",
        project=os.path.join(base_dir, "runs"),
        exist_ok=True,
        verbose=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        scale=0.2,
        fliplr=0.5,
        erasing=0.1
    )

    # Save best model to models/phone_detector/best_v2.pt and best.pt
    best_weights_src = os.path.join(base_dir, "runs", "v2_phone_run", "weights", "best.pt")
    v2_weights_dst = os.path.join(output_model_dir, "best_v2.pt")
    target_weights_dst = os.path.join(output_model_dir, "best.pt")

    if os.path.exists(best_weights_src):
        shutil.copy(best_weights_src, v2_weights_dst)
        shutil.copy(best_weights_src, target_weights_dst)
        print(f"\n[SUCCESS] Fine-tuned {model_name} v2 model saved to: {target_weights_dst}")
    else:
        model.save(target_weights_dst)
        print(f"\n[INFO] Model saved to: {target_weights_dst}")

    print(f"[METRICS] Training complete!")

if __name__ == "__main__":
    main()
