"""
extract_h5.py — Extract HDF5 files from mpiigaze.zip
InterviewIQ Part 3
"""

import os
import zipfile

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")
    zip_path = os.path.join(dataset_dir, "mpiigaze.zip")

    if not os.path.exists(zip_path):
        print(f"[ERROR] Zip file not found at {zip_path}")
        return

    print(f"Opening zip archive: {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        all_files = z.namelist()
        print(f"Total entries in zip: {len(all_files)}")

        # Find .h5, .mat, or subject folder files
        target_files = [f for f in all_files if f.endswith('.h5') or f.endswith('.mat') or 'p0' in f or 'p1' in f]
        print(f"Found {len(target_files)} target dataset files/folders.")
        for f in target_files[:15]:
            print(f" - {f}")

        # Extract all files into dataset_dir/mpii_raw
        raw_out = os.path.join(dataset_dir, "mpii_raw")
        os.makedirs(raw_out, exist_ok=True)
        print(f"Extracting all files into {raw_out}...")
        z.extractall(raw_out)
        print("[SUCCESS] Extracted dataset archive!")

if __name__ == "__main__":
    main()
