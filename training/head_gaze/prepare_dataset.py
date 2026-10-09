"""
prepare_dataset.py — Data Preparation for Head Pose + Gaze Model
InterviewIQ AI Adaptive Interview Intelligence System (Part 3)
"""

import os
import sys
import glob
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader

class HeadGazeDataset(Dataset):
    """
    PyTorch Dataset for Head Pose & Eye Gaze Estimation.
    Input: Face/Eye image patch (3x112x112 or 3x64x64 normalized)
    Targets: [head_pitch, head_yaw, gaze_pitch, gaze_yaw] in radians
    """
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        img_path = sample["img_path"]
        targets = np.array(sample["targets"], dtype=np.float32)

        img = cv2.imread(img_path)
        if img is None:
            img = np.zeros((112, 112, 3), dtype=np.uint8)
        else:
            img = cv2.resize(img, (112, 112))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1] tensor (C, H, W)
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0

        return img_tensor, torch.from_numpy(targets)


def load_dataset_samples(dataset_dir):
    """
    Parses images and annotations from dataset directory.
    Returns list of dicts: {"img_path": str, "targets": [head_p, head_y, gaze_p, gaze_y]}
    """
    img_train_dir = os.path.join(dataset_dir, "images", "train")
    lbl_train_dir = os.path.join(dataset_dir, "labels", "train")

    if not os.path.exists(img_train_dir):
        print(f"[WARN] Image directory not found: {img_train_dir}")
        return []

    images = glob.glob(os.path.join(img_train_dir, "*.*"))
    samples = []

    np.random.seed(42)

    for img_p in images:
        base_name = os.path.splitext(os.path.basename(img_p))[0]
        lbl_p = os.path.join(lbl_train_dir, f"{base_name}.txt")

        # Extract or compute pitch/yaw from dataset labels or eye positions
        head_p, head_y = 0.0, 0.0
        gaze_p, gaze_y = 0.0, 0.0

        if os.path.exists(lbl_p):
            try:
                with open(lbl_p, 'r') as f:
                    lines = f.readlines()
                if len(lines) >= 2:
                    # Bounding box coordinates for eyes -> compute relative displacement for gaze
                    p0 = [float(x) for x in lines[0].strip().split()]
                    p1 = [float(x) for x in lines[1].strip().split()]
                    # cx displacement from image center (0.5)
                    cx_avg = (p0[1] + p1[1]) / 2.0
                    cy_avg = (p0[2] + p1[2]) / 2.0
                    
                    gaze_y = float((cx_avg - 0.5) * 1.2)  # yaw in radians
                    gaze_p = float((cy_avg - 0.5) * 1.0)  # pitch in radians
                    head_y = gaze_y * 0.7
                    head_p = gaze_p * 0.7
            except Exception as e:
                pass

        samples.append({
            "img_path": img_p,
            "targets": [head_p, head_y, gaze_p, gaze_y]
        })

    return samples


def get_train_val_test_splits(dataset_dir, seed=42):
    """
    Splits samples into Train (80%), Val (10%), Test (10%).
    """
    samples = load_dataset_samples(dataset_dir)
    if not samples:
        print("[ERROR] No samples loaded from dataset!")
        return [], [], []

    np.random.seed(seed)
    np.random.shuffle(samples)

    n_total = len(samples)
    n_train = int(n_total * 0.80)
    n_val = int(n_total * 0.10)

    train_samples = samples[:n_train]
    val_samples = samples[n_train:n_train + n_val]
    test_samples = samples[n_train + n_val:]

    print(f"Dataset Splits (Total: {n_total}):")
    print(f" - Train (80%) : {len(train_samples)} samples")
    print(f" - Val   (10%) : {len(val_samples)} samples")
    print(f" - Test  (10%) : {len(test_samples)} samples")

    return train_samples, val_samples, test_samples


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ds_dir = os.path.join(script_dir, "dataset")
    get_train_val_test_splits(ds_dir)
