"""
evaluate.py — Evaluation script for fine-tuned YOLO11n face detector
InterviewIQ AI Adaptive Interview Intelligence System - Part 2
"""

import os
import json
import time
import torch
from ultralytics import YOLO


def evaluate_face_detector():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    model_path = os.path.join(project_root, "models", "face_detector", "best.pt")
    data_yaml = os.path.join(script_dir, "data_kaggle.yaml")
    metrics_out = os.path.join(project_root, "models", "face_detector", "metrics.json")

    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found at: {model_path}")
        return

    print(f"=== Evaluating Face Detector Model ===")
    print(f"Model Path: {model_path}")
    print(f"Data YAML: {data_yaml}")

    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"Using Device: {device}")

    model = YOLO(model_path)

    # 1. Run Ultralytics evaluation on test split
    print("\nRunning YOLO test set evaluation...")
    results = model.val(data=data_yaml, split='test', imgsz=416, device=device, verbose=False)

    precision = round(float(results.box.mp), 4)
    recall = round(float(results.box.mr), 4)
    map50 = round(float(results.box.map50), 4)
    map50_95 = round(float(results.box.map), 4)

    # 2. Benchmark Inference FPS on test set images
    test_img_dir = os.path.join(script_dir, "dataset", "images", "test")
    test_images = [os.path.join(test_img_dir, f) for f in os.listdir(test_img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    fps = 0.0
    if test_images:
        print(f"Benchmarking inference speed over {len(test_images)} test images...")
        # Warmup
        for _ in range(5):
            model(test_images[0], imgsz=416, verbose=False)

        start_time = time.time()
        for img_p in test_images:
            model(img_p, imgsz=416, verbose=False)
        total_time = time.time() - start_time
        fps = round(len(test_images) / total_time, 2)
    else:
        fps = round(1000.0 / float(results.speed['inference']), 2) if 'inference' in results.speed else 0.0

    print("\n=== FINAL TEST METRICS ===")
    print(f"Precision:   {precision}")
    print(f"Recall:      {recall}")
    print(f"mAP50:       {map50}")
    print(f"mAP50-95:    {map50_95}")
    print(f"Inference FPS: {fps}")

    metrics_data = {
        "precision": precision,
        "recall": recall,
        "map50": map50,
        "map50_95": map50_95,
        "inference_fps": fps,
        "dataset": "sbaghbidi/human-faces-object-detection (Kaggle)",
        "num_test_images": len(test_images)
    }

    os.makedirs(os.path.dirname(metrics_out), exist_ok=True)
    with open(metrics_out, "w") as f:
        json.dump(metrics_data, f, indent=4)

    print(f"\nMetrics exported successfully to: {metrics_out}")
    return metrics_data


if __name__ == "__main__":
    evaluate_face_detector()
