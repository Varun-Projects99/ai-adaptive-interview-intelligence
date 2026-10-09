"""
search_public_kaggle.py — Search accessible Kaggle phone datasets
InterviewIQ Part 1 V2
"""

from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()

    results = api.dataset_list(search="mobile phone")
    print(f"Found {len(results)} datasets for 'mobile phone':\n")

    valid_datasets = []

    for ds in results[:20]:
        ref = ds.ref
        title = ds.title
        try:
            files = api.dataset_list_files(ref).files
            print(f"[ACCESSIBLE] {ref} | Title: {title} | Files count: {len(files)}")
            for f in files[:5]:
                print(f"   - {f.name}")
            valid_datasets.append((ref, title, len(files)))
        except Exception as e:
            print(f"[FORBIDDEN/SKIP] {ref}: {e}")

if __name__ == "__main__":
    main()
