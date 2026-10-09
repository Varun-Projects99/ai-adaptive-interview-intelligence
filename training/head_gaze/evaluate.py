"""
evaluate.py — Evaluation script for Head Pose + Eye Gaze model
InterviewIQ AI Adaptive Interview Intelligence System (Part 3)
"""

import os
import sys
import json
import time
import math
import numpy as np
import torch

from prepare_dataset import get_train_val_test_splits, HeadGazeDataset
from train import HeadGazeEstimatorNet
from direction_mapper import DirectionMapper

def compute_classification_metrics(y_true, y_pred, labels=["LEFT", "CENTER", "RIGHT", "UP", "DOWN"]):
    """
    Computes Precision, Recall, and F1 score per class and overall accuracy.
    """
    metrics = {}
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = round(correct / max(1, len(y_true)), 4)

    for cls in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)

        prec = round(tp / max(1, tp + fp), 4)
        rec = round(tp / max(1, tp + fn), 4)
        f1 = round(2 * prec * rec / max(1e-5, prec + rec), 4)

        metrics[cls] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": sum(1 for t in y_true if t == cls)
        }

    return accuracy, metrics

def evaluate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    dataset_dir = os.path.join(script_dir, "dataset")
    model_path = os.path.join(project_root, "models", "head_gaze_detector", "best_model.pt")
    metrics_out = os.path.join(project_root, "models", "head_gaze_detector", "metrics.json")

    print("=" * 60)
    print("  InterviewIQ — Head Pose & Eye Gaze Model Evaluation")
    print("=" * 60)

    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found at: {model_path}")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load Model
    model = HeadGazeEstimatorNet().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # Load Test Split
    _, _, test_samples = get_train_val_test_splits(dataset_dir, seed=42)
    if not test_samples:
        print("[ERROR] Test set is empty!")
        return

    test_ds = HeadGazeDataset(test_samples)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=1, shuffle=False)

    mapper = DirectionMapper()

    head_p_errors, head_y_errors = [], []
    gaze_p_errors, gaze_y_errors = [], []

    head_true_dirs, head_pred_dirs = [], []
    gaze_true_dirs, gaze_pred_dirs = [], []

    start_time = time.time()
    with torch.no_grad():
        for img_tensor, targets in test_loader:
            img_tensor = img_tensor.to(device)
            preds = model(img_tensor).cpu().numpy()[0]
            tgts = targets.numpy()[0]

            # [head_p, head_y, gaze_p, gaze_y] in radians
            hp_pred, hy_pred, gp_pred, gy_pred = preds
            hp_tgt, hy_tgt, gp_tgt, gy_tgt = tgts

            # MAE in degrees
            head_p_errors.append(abs(math.degrees(hp_pred - hp_tgt)))
            head_y_errors.append(abs(math.degrees(hy_pred - hy_tgt)))
            gaze_p_errors.append(abs(math.degrees(gp_pred - gp_tgt)))
            gaze_y_errors.append(abs(math.degrees(gy_pred - gy_tgt)))

            # Directional Classification
            head_true_dirs.append(mapper.map_head_direction(hp_tgt, hy_tgt))
            head_pred_dirs.append(mapper.map_head_direction(hp_pred, hy_pred))

            gaze_true_dirs.append(mapper.map_gaze_direction(gp_tgt, gy_tgt))
            gaze_pred_dirs.append(mapper.map_gaze_direction(gp_pred, gy_pred))

    total_eval_time = time.time() - start_time
    fps = round(len(test_samples) / max(1e-5, total_eval_time), 2)

    # MAE Metrics (Degrees)
    head_yaw_mae = round(float(np.mean(head_y_errors)), 2)
    head_pitch_mae = round(float(np.mean(head_p_errors)), 2)
    gaze_yaw_mae = round(float(np.mean(gaze_y_errors)), 2)
    gaze_pitch_mae = round(float(np.mean(gaze_p_errors)), 2)

    # Directional Classification Metrics
    head_acc, head_class_metrics = compute_classification_metrics(head_true_dirs, head_pred_dirs)
    gaze_acc, gaze_class_metrics = compute_classification_metrics(gaze_true_dirs, gaze_pred_dirs)

    head_macro_f1 = round(float(np.mean([head_class_metrics[k]["f1"] for k in head_class_metrics])), 4)
    gaze_macro_f1 = round(float(np.mean([gaze_class_metrics[k]["f1"] for k in gaze_class_metrics])), 4)

    print("\n=== REGRESSION METRICS (Degrees) ===")
    print(f"Head Yaw MAE:   {head_yaw_mae}°")
    print(f"Head Pitch MAE: {head_pitch_mae}°")
    print(f"Gaze Yaw MAE:   {gaze_yaw_mae}°")
    print(f"Gaze Pitch MAE: {gaze_pitch_mae}°")

    print("\n=== DIRECTIONAL CLASSIFICATION METRICS ===")
    print(f"Head Direction Accuracy: {head_acc} (Macro F1: {head_macro_f1})")
    print(f"Gaze Direction Accuracy: {gaze_acc} (Macro F1: {gaze_macro_f1})")
    print(f"Inference Speed:         {fps} FPS")

    metrics_data = {
        "num_test_samples": len(test_samples),
        "regression": {
            "head_yaw_mae_deg": head_yaw_mae,
            "head_pitch_mae_deg": head_pitch_mae,
            "gaze_yaw_mae_deg": gaze_yaw_mae,
            "gaze_pitch_mae_deg": gaze_pitch_mae
        },
        "directional_classification": {
            "head_accuracy": head_acc,
            "head_macro_f1": head_macro_f1,
            "head_per_class": head_class_metrics,
            "gaze_accuracy": gaze_acc,
            "gaze_macro_f1": gaze_macro_f1,
            "gaze_per_class": gaze_class_metrics
        },
        "performance": {
            "inference_fps": fps,
            "latency_ms": round(1000.0 / fps, 2)
        }
    }

    with open(metrics_out, "w") as f:
        json.dump(metrics_data, f, indent=4)

    print(f"\n[SUCCESS] Exported test metrics to: {metrics_out}")
    return metrics_data

if __name__ == "__main__":
    evaluate()
