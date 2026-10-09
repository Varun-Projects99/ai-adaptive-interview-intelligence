"""
inspect_sub_mpii.py — Inspect images and annotations in dataset
InterviewIQ Part 3
"""

import os
import glob
import cv2

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")

    img_dir = os.path.join(dataset_dir, "images", "train")
    lbl_dir = os.path.join(dataset_dir, "labels", "train")

    if not os.path.exists(img_dir):
        print(f"Image train dir not found: {img_dir}")
        return

    images = glob.glob(os.path.join(img_dir, "*.*"))
    labels = glob.glob(os.path.join(lbl_dir, "*.txt"))

    print(f"Train images count: {len(images)}")
    print(f"Train labels count: {len(labels)}")

    if images:
        sample_img_path = images[0]
        img = cv2.imread(sample_img_path)
        if img is not None:
            print(f"Sample Image: {os.path.basename(sample_img_path)} | Shape: {img.shape}")

    if labels:
        sample_lbl_path = labels[0]
        with open(sample_lbl_path, 'r') as f:
            lines = f.readlines()
        print(f"Sample Label: {os.path.basename(sample_lbl_path)} | Lines count: {len(lines)}")
        for l in lines:
            parts = [float(x) for x in l.strip().split()]
            print(f"  Class: {int(parts[0])} | BBox (cx, cy, w, h): {parts[1:]}")

if __name__ == "__main__":
    main()
