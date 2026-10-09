"""
download_kaggle_dataset.py — Direct Kaggle API dataset downloader
InterviewIQ AI Adaptive Interview Intelligence System (Part 3)
"""

import os
import sys
import zipfile
import h5py

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")
    os.makedirs(dataset_dir, exist_ok=True)

    print("=== InterviewIQ Part 3: Kaggle Dataset Downloader ===")
    print(f"Target Directory: {dataset_dir}")

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("[OK] Kaggle API authenticated successfully.")
    except Exception as e:
        print(f"[ERROR] Kaggle API authentication failed: {e}")
        sys.exit(1)

    # 1. Attempt competition download first (mp18-eye-gaze-estimation)
    downloaded = False
    print("\nAttempting Kaggle competition download: mp18-eye-gaze-estimation...")
    try:
        api.competition_download_files("mp18-eye-gaze-estimation", path=dataset_dir)
        print("[SUCCESS] Downloaded competition mp18-eye-gaze-estimation zip!")
        downloaded = True
    except Exception as e:
        print(f"[INFO] Competition download note: {e}")

    # 2. Search & Download Kaggle datasets if competition zip is not available
    if not downloaded:
        print("\nAttempting Kaggle dataset download for MPIIGaze...")
        slugs = [
            "vatsalshah1/mpiigaze",
            "prajwal8/mpiigaze",
            "ritsuka/mpiigaze",
            "gauravdutta/mpiigaze-dataset"
        ]
        for slug in slugs:
            try:
                print(f"Trying Kaggle dataset slug: {slug}...")
                api.dataset_download_files(slug, path=dataset_dir, unzip=True)
                print(f"[SUCCESS] Downloaded Kaggle dataset: {slug}")
                downloaded = True
                break
            except Exception as e:
                print(f"Slug {slug} note: {e}")

    # Unzip any zip files in dataset_dir
    for f in os.listdir(dataset_dir):
        if f.endswith(".zip"):
            zpath = os.path.join(dataset_dir, f)
            print(f"Extracting zip archive: {zpath}...")
            with zipfile.ZipFile(zpath, 'r') as z:
                z.extractall(dataset_dir)
            print("[SUCCESS] Extraction complete.")

    # Check for downloaded dataset files (e.g. .h5, .mat, or subdirectories)
    files = os.listdir(dataset_dir)
    print(f"\nDownloaded dataset directory contents ({len(files)} files/folders):")
    for f in files[:15]:
        fpath = os.path.join(dataset_dir, f)
        size = os.path.getsize(fpath) if os.path.isfile(fpath) else "<DIR>"
        print(f" - {f}: {size}")

if __name__ == "__main__":
    main()
