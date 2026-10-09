"""
inspect_and_extract.py — Inspect Kaggle datasets and extract MPIIGaze files
InterviewIQ Part 3
"""

import os
import zipfile
import h5py

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")

    print("=== Inspecting Kaggle Dataset Directory ===")
    for item in os.listdir(dataset_dir):
        ipath = os.path.join(dataset_dir, item)
        if os.path.isfile(ipath):
            size_mb = round(os.path.getsize(ipath) / (1024 * 1024), 2)
            print(f"File: {item} ({size_mb} MB)")
            if item.endswith(".zip"):
                try:
                    with zipfile.ZipFile(ipath, 'r') as z:
                        namelist = z.namelist()
                        print(f"  Zip contents count: {len(namelist)} entries")
                        print(f"  Sample entries: {namelist[:5]}")
                        # Extract zip
                        extract_target = os.path.join(dataset_dir, item.replace(".zip", ""))
                        os.makedirs(extract_target, exist_ok=True)
                        print(f"  Extracting to {extract_target}...")
                        z.extractall(extract_target)
                        print(f"  Extraction finished!")
                except Exception as e:
                    print(f"  Zip read error: {e}")
        else:
            print(f"Directory: {item}")

if __name__ == "__main__":
    main()
