"""
validate_dataset.py — Validate Kaggle Human Faces Object Detection Dataset
InterviewIQ AI Adaptive Interview Intelligence System (Part 2)
"""

import os
import glob
import pandas as pd
import cv2

def validate_dataset():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")

    csv_path = os.path.join(dataset_dir, "faces.csv")
    images_dir = os.path.join(dataset_dir, "images")

    if not os.path.exists(csv_path) or not os.path.exists(images_dir):
        print(f"[ERROR] Required dataset path missing: {csv_path} or {images_dir}")
        return False, []

    df = pd.read_csv(csv_path)

    print("=" * 60)
    print("  InterviewIQ — Kaggle Face Dataset Validation Report")
    print("=" * 60)
    print(f"Dataset CSV Entries    : {len(df)}")
    print(f"Unique Image Names     : {df['image_name'].nunique()}")

    valid_images = {}
    corrupted_count = 0
    invalid_box_count = 0

    grouped = df.groupby("image_name")

    for img_name, group in grouped:
        img_path = os.path.join(images_dir, img_name)
        if not os.path.exists(img_path):
            continue

        img = cv2.imread(img_path)
        if img is None:
            corrupted_count += 1
            continue

        h, w, c = img.shape
        valid_boxes = []

        for _, row in group.iterrows():
            x0, y0, x1, y1 = float(row['x0']), float(row['y0']), float(row['x1']), float(row['y1'])

            if x0 < 0 or y0 < 0 or x1 > w or y1 > h or x0 >= x1 or y0 >= y1:
                invalid_box_count += 1
                x0 = max(0.0, min(x0, float(w - 1)))
                y0 = max(0.0, min(y0, float(h - 1)))
                x1 = max(x0 + 1.0, min(x1, float(w)))
                y1 = max(y0 + 1.0, min(y1, float(h)))

            valid_boxes.append({
                "bbox": [x0, y0, x1, y1],
                "width": w,
                "height": h
            })

        if valid_boxes:
            valid_images[img_name] = {
                "img_path": img_path,
                "width": w,
                "height": h,
                "boxes": valid_boxes
            }

    print("-" * 60)
    print(f"Valid Validated Images      : {len(valid_images)}")
    print(f"Total Verified Face Boxes   : {sum(len(v['boxes']) for v in valid_images.values())}")
    print(f"Corrupted/Missing Images    : {corrupted_count}")
    print(f"Invalid Bounding Boxes Fixed: {invalid_box_count}")
    print("=" * 60)

    return True, valid_images

if __name__ == "__main__":
    validate_dataset()
