"""
download_mpii_clean.py — Download clean MPIIGaze dataset from Kaggle
InterviewIQ Part 3
"""

import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")
os.makedirs(dataset_dir, exist_ok=True)

# Remove partial zip files
for item in os.listdir(dataset_dir):
    if item.endswith(".kaggle-partial") or (item.endswith(".zip") and item.startswith("mpiigaze")):
        try:
            os.remove(os.path.join(dataset_dir, item))
            print(f"Removed partial file: {item}")
        except Exception as e:
            pass

api = KaggleApi()
api.authenticate()

# Try downloading aiepbug/mpiigaze or scishadymayez/7p-mpiigaze or nabhanzahid/mpiigaze
slugs = [
    "aiepbug/mpiigaze",
    "scishadymayez/7p-mpiigaze",
    "nabhanzahid/mpiigaze",
    "michaelzaki4/mpiigaze-dataset"
]

downloaded_slug = None
for slug in slugs:
    try:
        print(f"Downloading Kaggle dataset: {slug}...", flush=True)
        api.dataset_download_files(slug, path=dataset_dir, unzip=True)
        print(f"[SUCCESS] Downloaded dataset: {slug}", flush=True)
        downloaded_slug = slug
        break
    except Exception as e:
        print(f"Slug {slug} error: {e}", flush=True)

print(f"\nFinal dataset folder contents in {dataset_dir}:", flush=True)
for f in os.listdir(dataset_dir):
    fpath = os.path.join(dataset_dir, f)
    is_dir = os.path.isdir(fpath)
    size = f"<DIR>" if is_dir else f"{round(os.path.getsize(fpath)/1024/1024, 2)} MB"
    print(f" - {f} ({size})", flush=True)
