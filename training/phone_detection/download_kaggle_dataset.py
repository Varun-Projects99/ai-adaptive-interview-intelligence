"""
download_kaggle_dataset.py — Download Kaggle Phone Dataset for Part 1 V2
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
import sys
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

def download():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset_v2")
    os.makedirs(dataset_dir, exist_ok=True)

    print("=== InterviewIQ Part 1 V2: Kaggle Dataset Downloader ===")
    print(f"Target Directory: {dataset_dir}")

    api = KaggleApi()
    api.authenticate()
    print("[OK] Kaggle API Authenticated.")

    slugs = [
        "dataclusterlabs/mobile-phone-image-dataset",
        "alessandrasala/cell-phone-detection",
        "shashwatwork/mobile-phone-dataset",
        "dheerajperumalla/mobile-phone-detection"
    ]

    downloaded = False
    for slug in slugs:
        try:
            print(f"Attempting download for slug: {slug}...", flush=True)
            api.dataset_download_files(slug, path=dataset_dir, unzip=True)
            print(f"[SUCCESS] Downloaded Kaggle dataset: {slug}", flush=True)
            downloaded = True
            break
        except Exception as e:
            print(f"  Slug {slug} download note: {e}", flush=True)

    # Check unzipped files
    print(f"\nFiles in {dataset_dir}:", flush=True)
    for root, dirs, files in os.walk(dataset_dir):
        rel = os.path.relpath(root, dataset_dir)
        print(f" Directory: {rel} ({len(files)} files, {len(dirs)} subdirs)")
        for f in files[:5]:
            print(f"   - {f}")

if __name__ == "__main__":
    download()
