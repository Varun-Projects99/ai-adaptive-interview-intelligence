"""
inspect_kaggle_candidates.py — Inspect Kaggle Candidate Datasets for Person+Phone Scenes
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()
    print("[OK] Kaggle API Authenticated.")

    candidate_slugs = [
        "dataclusterlabs/mobile-phone-image-dataset",
        "shashwatwork/mobile-phone-dataset",
        "dheerajperumalla/mobile-phone-detection",
        "alessandrasala/cell-phone-detection",
        "saiprasad1/cell-phone-detection-dataset",
        "vijaykumar1/phone-detection"
    ]

    print("\n=== Inspecting Candidate Datasets ===")
    for slug in candidate_slugs:
        print(f"\nTarget Slug: {slug}")
        try:
            files = api.dataset_list_files(slug).files
            print(f" Total files: {len(files)}")
            xml_count = sum(1 for f in files if f.name.endswith('.xml'))
            txt_count = sum(1 for f in files if f.name.endswith('.txt'))
            json_count = sum(1 for f in files if f.name.endswith('.json'))
            img_count = sum(1 for f in files if f.name.endswith('.jpg') or f.name.endswith('.jpeg') or f.name.endswith('.png'))

            print(f"  - Image files (.jpg/.png): {img_count}")
            print(f"  - Pascal VOC XML (.xml)  : {xml_count}")
            print(f"  - YOLO TXT (.txt)        : {txt_count}")
            print(f"  - COCO JSON (.json)      : {json_count}")
        except Exception as e:
            print(f"  Error listing slug '{slug}': {e}")

if __name__ == "__main__":
    main()
