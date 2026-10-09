"""
test_search_kaggle.py
"""

from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

print("Searching datasets for 'gaze':")
datasets = api.dataset_list(search="gaze")
for ds in datasets:
    print(f"Slug: {ds.ref} | Title: {ds.title} | Size: {ds.size}")
