import os
import sys
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")
os.makedirs(dataset_dir, exist_ok=True)

print("Initializing Kaggle API...", flush=True)
api = KaggleApi()
api.authenticate()
print("Kaggle API Authenticated.", flush=True)

print("Searching datasets for 'mpiigaze'...", flush=True)
results = api.dataset_list(search="mpiigaze")
if results:
    for r in results:
        print(f"Found dataset: {r.ref} (Title: {r.title})", flush=True)
    target_slug = results[0].ref
    print(f"Downloading dataset '{target_slug}' to '{dataset_dir}'...", flush=True)
    api.dataset_download_files(target_slug, path=dataset_dir, unzip=True)
    print("Download completed!", flush=True)
else:
    print("No mpiigaze dataset found, trying 'eye gaze'...", flush=True)
    gaze_results = api.dataset_list(search="eye gaze")
    for g in gaze_results[:5]:
        print(f"Found gaze dataset: {g.ref} (Title: {g.title})", flush=True)
    if gaze_results:
        target_slug = gaze_results[0].ref
        print(f"Downloading dataset '{target_slug}' to '{dataset_dir}'...", flush=True)
        api.dataset_download_files(target_slug, path=dataset_dir, unzip=True)
        print("Download completed!", flush=True)

print("\nFiles in dataset directory:", flush=True)
for f in os.listdir(dataset_dir):
    print(f" - {f}", flush=True)
