"""
download_7p.py — Download 7p-mpiigaze Kaggle dataset
InterviewIQ Part 3
"""

import os
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")
os.makedirs(dataset_dir, exist_ok=True)

api = KaggleApi()
api.authenticate()

slug = "scishadymayez/7p-mpiigaze"
print(f"Downloading Kaggle dataset: {slug}...", flush=True)
api.dataset_download_files(slug, path=dataset_dir, unzip=True)
print(f"[SUCCESS] Downloaded dataset: {slug}", flush=True)

print("\nFiles in dataset directory:", flush=True)
for f in os.listdir(dataset_dir):
    fpath = os.path.join(dataset_dir, f)
    size = "<DIR>" if os.path.isdir(fpath) else f"{round(os.path.getsize(fpath)/1024/1024, 2)} MB"
    print(f" - {f} ({size})", flush=True)
