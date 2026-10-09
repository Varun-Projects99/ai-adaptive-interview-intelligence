"""
prepare_dataset.py — Prepare Dataset Structure for Mobile Phone Object Detection
InterviewIQ AI Adaptive Interview Intelligence System
"""

import os
import cv2
import numpy as np

def prepare_sample_dataset():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")

    dirs = [
        os.path.join(dataset_dir, "images", "train"),
        os.path.join(dataset_dir, "images", "val"),
        os.path.join(dataset_dir, "labels", "train"),
        os.path.join(dataset_dir, "labels", "val"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    print(f"[DATASET] Prepared dataset directory structure at: {dataset_dir}")

    # Generate synthetic sample frames with phone bounding boxes for pipeline verification
    for split, count in [("train", 5), ("val", 2)]:
        img_dir = os.path.join(dataset_dir, "images", split)
        lbl_dir = os.path.join(dataset_dir, "labels", split)

        for i in range(count):
            img_name = f"sample_{i:03d}.jpg"
            lbl_name = f"sample_{i:03d}.txt"

            img_path = os.path.join(img_dir, img_name)
            lbl_path = os.path.join(lbl_dir, lbl_name)

            if not os.path.exists(img_path):
                # Create sample 320x320 image
                img = np.full((320, 320, 3), 120, dtype=np.uint8)
                # Draw a phone-like rectangle
                cv2.rectangle(img, (100, 80), (180, 240), (40, 40, 40), -1)
                cv2.rectangle(img, (110, 95), (170, 220), (200, 200, 255), -1)
                cv2.imwrite(img_path, img)

            if not os.path.exists(lbl_path):
                # Class 0 (cell phone), x_center, y_center, width, height (normalized)
                # Box: x1=100, y1=80, x2=180, y2=240 => xc=140/320=0.4375, yc=160/320=0.5, w=80/320=0.25, h=160/320=0.5
                with open(lbl_path, "w") as f:
                    f.write("0 0.4375 0.5000 0.2500 0.5000\n")

    print("[DATASET] Sample images and labels prepared successfully.")

if __name__ == "__main__":
    prepare_sample_dataset()
