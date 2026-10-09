"""
search_kaggle_phone_scenes.py — Kaggle Search for Person + Phone Scene Datasets
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
from kaggle.api.kaggle_api_extended import KaggleApi

def search():
    api = KaggleApi()
    api.authenticate()
    print("[OK] Kaggle API Authenticated.")

    queries = [
        "phone detection",
        "mobile phone",
        "cell phone",
        "holding phone",
        "person phone",
        "phone object detection"
    ]

    found_slugs = set()

    for q in queries:
        print(f"\n--- Searching Kaggle Datasets for '{q}' ---")
        try:
            results = api.dataset_list(search=q)
            for ds in results[:10]:
                if ds.ref not in found_slugs:
                    found_slugs.add(ds.ref)
                    print(f"Slug: {ds.ref}")
                    print(f"Title: {ds.title}")
                    print(f"URL: https://www.kaggle.com/datasets/{ds.ref}")
                    print("-" * 40)
        except Exception as e:
            print(f"Search query '{q}' error: {e}")

if __name__ == "__main__":
    search()
