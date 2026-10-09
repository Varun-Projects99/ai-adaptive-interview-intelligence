"""
split_dataset.py — Dataset Splitter (80% Train, 10% Val, 10% Test)
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
import sys
import glob
import shutil
import numpy as np

def split_dataset():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yolo_dir = os.path.join(script_dir, "yolo_v2_dataset")

    images = glob.glob(os.path.join(yolo_dir, "images", "*.*"))
    print(f"Total available images for splitting: {len(images)}")

    if not images:
        print(f"[ERROR] No images found in {yolo_dir}/images!")
        return

    np.random.seed(42)
    np.random.shuffle(images)

    n_total = len(images)
    n_train = int(n_total * 0.80)
    n_val = int(n_total * 0.10)

    train_imgs = images[:n_train]
    val_imgs = images[n_train:n_train + n_val]
    test_imgs = images[n_train + n_val:]

    print(f"Split Ratios (Total: {n_total}):")
    print(f" - Train (80%) : {len(train_imgs)} images")
    print(f" - Val   (10%) : {len(val_imgs)} images")
    print(f" - Test  (10%) : {len(test_imgs)} images")

    out_dataset_dir = os.path.join(script_dir, "dataset_v2_split")

    for split_name, img_list in [("train", train_imgs), ("val", val_imgs), ("test", test_imgs)]:
        img_out = os.path.join(out_dataset_dir, "images", split_name)
        lbl_out = os.path.join(out_dataset_dir, "labels", split_name)
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)

        for img_path in img_list:
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            lbl_path = os.path.join(yolo_dir, "labels", f"{base_name}.txt")

            shutil.copy(img_path, os.path.join(img_out, os.path.basename(img_path)))
            if os.path.exists(lbl_path):
                shutil.copy(lbl_path, os.path.join(lbl_out, f"{base_name}.txt"))

    # Generate data_v2.yaml
    data_yaml_p = os.path.join(script_dir, "data_v2.yaml")
    yaml_content = f"""path: {out_dataset_dir.replace('\\', '/')}
train: images/train
val: images/val
test: images/test

names:
  0: mobile_phone
"""
    with open(data_yaml_p, "w") as f:
        f.write(yaml_content)

    print(f"\n[SUCCESS] Generated dataset YAML configuration at: {data_yaml_p}")

if __name__ == "__main__":
    split_dataset()
