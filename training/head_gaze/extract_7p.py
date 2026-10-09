"""
extract_7p.py — Extract 7p-mpiigaze dataset
InterviewIQ Part 3
"""

import os
import zipfile

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")
    zip_p = os.path.join(dataset_dir, "7p-mpiigaze.zip")

    if not os.path.exists(zip_p):
        print(f"[ERROR] 7p-mpiigaze.zip not found at {zip_p}")
        return

    print(f"7p-mpiigaze.zip size: {round(os.path.getsize(zip_p)/1024/1024, 2)} MB")
    out_dir = os.path.join(dataset_dir, "mpii_7p")
    os.makedirs(out_dir, exist_ok=True)

    with zipfile.ZipFile(zip_p, 'r') as z:
        print(f"Extracting {len(z.namelist())} files into {out_dir}...")
        z.extractall(out_dir)
        print("Extraction complete!")

    print("\nExtracted folder contents:")
    for root, dirs, files in os.walk(out_dir):
        rel = os.path.relpath(root, out_dir)
        print(f" Directory: {rel} ({len(files)} files, {len(dirs)} subdirs)")
        if files[:5]:
            print(f"   Samples: {files[:5]}")

if __name__ == "__main__":
    main()
