"""
train.py — Train Head Pose + Eye Gaze Estimator Neural Network
InterviewIQ AI Adaptive Interview Intelligence System (Part 3)
"""

import os
import sys
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from prepare_dataset import get_train_val_test_splits, HeadGazeDataset


class HeadGazeEstimatorNet(nn.Module):
    """
    Lightweight Convolutional Regression Network for Head Pose & Eye Gaze.
    Input: Image Patch Tensor (B, 3, 112, 112)
    Output: Regression Tensor (B, 4) -> [head_pitch, head_yaw, gaze_pitch, gaze_yaw]
    """
    def __init__(self):
        super(HeadGazeEstimatorNet, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1),  # -> 56x56
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),

            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1), # -> 28x28
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), # -> 14x14
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            nn.AdaptiveAvgPool2d((4, 4)) # -> 4x4
        )

        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 4)
        )

    def forward(self, x):
        feat = self.features(x)
        out = self.regressor(feat)
        return out


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    dataset_dir = os.path.join(script_dir, "dataset")
    output_dir = os.path.join(project_root, "models", "head_gaze_detector")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  InterviewIQ — Head Pose & Eye Gaze Model Training")
    print("=" * 60)

    torch.manual_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"Target Device: {device} ({device_name})")

    # Load splits
    train_samples, val_samples, test_samples = get_train_val_test_splits(dataset_dir, seed=42)
    if not train_samples:
        print("[ERROR] No dataset samples found. Aborting training.")
        return

    train_ds = HeadGazeDataset(train_samples)
    val_ds = HeadGazeDataset(val_samples)

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=16, shuffle=False, num_workers=0)

    model = HeadGazeEstimatorNet().to(device)
    criterion = nn.SmoothL1Loss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)

    best_val_loss = float("inf")
    model_path = os.path.join(output_dir, "best_model.pt")

    epochs = 10
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for images, targets in train_loader:
            images = images.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)

        train_loss /= len(train_ds)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, targets in val_loader:
                images = images.to(device)
                targets = targets.to(device)
                outputs = model(images)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * images.size(0)

        val_loss /= len(val_ds)

        print(f"Epoch [{epoch}/{epochs}] | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), model_path)
            print(f" -> Saved best model weights to: {model_path}")

    total_time = round(time.time() - start_time, 2)
    print(f"\n[SUCCESS] Training completed in {total_time}s!")
    print(f"Best Validation Loss: {best_val_loss:.4f}")

    # Export config
    config_path = os.path.join(output_dir, "config.json")
    config_data = {
        "architecture": "HeadGazeEstimatorNet",
        "input_shape": [3, 112, 112],
        "outputs": ["head_pitch", "head_yaw", "gaze_pitch", "gaze_yaw"],
        "device": device_name,
        "epochs": epochs,
        "batch_size": 16,
        "train_samples": len(train_samples),
        "val_samples": len(val_samples),
        "test_samples": len(test_samples),
        "training_time_sec": total_time,
        "best_val_loss": round(best_val_loss, 4)
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=4)
    print(f"Saved config to: {config_path}")

if __name__ == "__main__":
    main()
