"""
convert_to_yolo.py — Convert Kaggle Face Bounding Boxes to YOLO Format & Split
InterviewIQ AI Adaptive Interview Intelligence System (Part 2)
"""

import os
import shutil
import random
import yaml
from validate_dataset import validate_dataset

def convert_and_split():
    success, valid_images = validate_dataset()
    if not success or not valid_images:
        print("[ERROR] Validation failed or no valid face images found.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")

    splits = ["train", "val", "test"]
    for s in splits:
        os.makedirs(os.path.join(dataset_dir, "images", s), exist_ok=True)
        os.makedirs(os.path.join(dataset_dir, "labels", s), exist_ok=True)

    items = list(valid_images.items())
    random.seed(42)
    random.shuffle(items)

    n_total = len(items)
    n_train = int(n_total * 0.8)
    n_val = int(n_total * 0.1)

    train_items = items[:n_train]
    val_items = items[n_train:n_train + n_val]
    test_items = items[n_train + n_val:]

    split_map = {
        "train": train_items,
        "val": val_items,
        "test": test_items
    }

    print("\n" + "=" * 60)
    print("  InterviewIQ — Face Dataset Conversion & Split Summary")
    print("=" * 60)
    print(f"Total Unique Images  : {n_total}")
    print(f"Train Split (80%)    : {len(train_items)}")
    print(f"Val Split (10%)      : {len(val_items)}")
    print(f"Test Split (10%)     : {len(test_items)}")

    for split_name, item_list in split_map.items():
        img_dest_dir = os.path.join(dataset_dir, "images", split_name)
        lbl_dest_dir = os.path.join(dataset_dir, "labels", split_name)

        for img_name, data in item_list:
            src_img = data["img_path"]
            base_name = os.path.splitext(img_name)[0]

            dest_img = os.path.join(img_dest_dir, img_name)
            dest_lbl = os.path.join(lbl_dest_dir, base_name + ".txt")

            # Copy image file
            shutil.copy(src_img, dest_img)

            # Write YOLO TXT label file (class_id 0, xc, yc, bw, bh normalized)
            w = data["width"]
            h = data["height"]
            yolo_lines = []

            for box in data["boxes"]:
                x0, y0, x1, y1 = box["bbox"]
                xc = ((x0 + x1) / 2.0) / w
                yc = ((y0 + y1) / 2.0) / h
                bw = (x1 - x0) / w
                bh = (y1 - y0) / h

                yolo_lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")

            with open(dest_lbl, "w") as f:
                f.writelines(yolo_lines)

    # Export data_kaggle.yaml
    abs_yaml_path = os.path.join(base_dir, "data_kaggle.yaml")
    yaml_config = {
        "path": dataset_dir.replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {0: "face"}
    }

    with open(abs_yaml_path, "w") as f:
        yaml.dump(yaml_config, f, default_flow_style=False)

    print(f"\n[SUCCESS] Conversion complete. YOLO YAML config generated at:\n{abs_yaml_path}")
    print("=" * 60)

if __name__ == "__main__":
    convert_and_split()
