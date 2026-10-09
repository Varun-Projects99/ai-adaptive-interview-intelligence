"""
download_kaggle_dataset.py — Download Kaggle Human Faces Object Detection Dataset
InterviewIQ AI Adaptive Interview Intelligence System (Part 2)
"""

import os
import sys
import kaggle

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")
    os.makedirs(dataset_dir, exist_ok=True)

    dataset_slug = "sbaghbidi/human-faces-object-detection"

    print("=" * 60)
    print("  Downloading Kaggle Face Detection Dataset")
    print(f"  Dataset Slug: {dataset_slug}")
    print("=" * 60)

    try:
        kaggle.api.authenticate()
        print("[KAGGLE] Authenticated successfully.")

        print("[KAGGLE] Starting download...")
        kaggle.api.dataset_download_files(
            dataset_slug,
            path=dataset_dir,
            unzip=True
        )

        print("[KAGGLE] Dataset downloaded and extracted successfully!")

        items = os.listdir(dataset_dir)
        print(f"[KAGGLE] Items in {dataset_dir}: {items}")

    except Exception as e:
        print(f"[ERROR] Failed to download Kaggle dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
