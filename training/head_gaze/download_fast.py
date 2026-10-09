import os
import sys
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")
os.makedirs(dataset_dir, exist_ok=True)

api = KaggleApi()
api.authenticate()

slugs = ["dyccccc/sub-mpiigaze", "aiepbug/mpiigaze", "scishadymayez/7p-mpiigaze"]

for slug in slugs:
    try:
        print(f"Downloading Kaggle dataset: {slug}...", flush=True)
        api.dataset_download_files(slug, path=dataset_dir, unzip=True)
        print(f"Successfully downloaded {slug}!", flush=True)
        break
    except Exception as e:
        print(f"Failed {slug}: {e}", flush=True)

print("Current dataset folder contents:", flush=True)
for f in os.listdir(dataset_dir):
    print(f" - {f}", flush=True)
