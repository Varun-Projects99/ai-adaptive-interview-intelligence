"""
download_h5_dataset.py — Download MPIIGaze Dataset from Kaggle API
InterviewIQ Part 3
"""

import os
import sys
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")
    os.makedirs(dataset_dir, exist_ok=True)

    api = KaggleApi()
    api.authenticate()

    slug = "michaelzaki4/mpiigaze-dataset"
    print(f"Downloading Kaggle dataset: {slug}...", flush=True)
    api.dataset_download_files(slug, path=dataset_dir, unzip=True)
    print(f"[SUCCESS] Downloaded dataset {slug} into {dataset_dir}!", flush=True)

    print("\nFiles in dataset directory:", flush=True)
    for f in os.listdir(dataset_dir):
        fpath = os.path.join(dataset_dir, f)
        is_dir = os.path.isdir(fpath)
        size = "<DIR>" if is_dir else f"{round(os.path.getsize(fpath)/1024/1024, 2)} MB"
        print(f" - {f} ({size})", flush=True)

if __name__ == "__main__":
    main()
