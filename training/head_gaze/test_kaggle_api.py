"""
test_kaggle_api.py — Direct Kaggle API wrapper
InterviewIQ Part 3
"""

import os
import sys

def main():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("[SUCCESS] Kaggle API authenticated successfully!")
    except Exception as e:
        print(f"[ERROR] Kaggle API authentication failed: {e}")
        return

    # 1. Search competition datasets
    print("\n--- Searching Competition mp18-eye-gaze-estimation ---")
    try:
        files = api.competition_list_files("mp18-eye-gaze-estimation")
        print(f"Found {len(files)} competition files:")
        for f in files:
            print(f" - {f.name}")
    except Exception as e:
        print(f"Competition check note: {e}")

    # 2. Search datasets with query 'mpiigaze'
    print("\n--- Searching Kaggle Datasets for 'mpiigaze' ---")
    try:
        ds_list = api.dataset_list(search="mpiigaze")
        print(f"Found {len(ds_list)} dataset results:")
        for ds in ds_list[:10]:
            print(f" - {ds.ref} (Title: {ds.title})")
    except Exception as e:
        print(f"Dataset search note: {e}")

    # 3. Search datasets with query 'eye gaze'
    print("\n--- Searching Kaggle Datasets for 'eye gaze' ---")
    try:
        ds_list2 = api.dataset_list(search="eye gaze")
        print(f"Found {len(ds_list2)} dataset results:")
        for ds in ds_list2[:10]:
            print(f" - {ds.ref} (Title: {ds.title})")
    except Exception as e:
        print(f"Dataset search note: {e}")

if __name__ == "__main__":
    main()
