"""
search_kaggle_gaze.py — Search Kaggle datasets for MPIIGaze files
InterviewIQ Part 3
"""

from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()

    results = api.dataset_list(search="MPIIGaze")
    print(f"Found {len(results)} datasets matching 'MPIIGaze':\n")
    for ds in results:
        print(f"Ref: {ds.ref}")
        print(f"Title: {ds.title}")
        print(f"URL: https://www.kaggle.com/datasets/{ds.ref}")
        try:
            files = api.dataset_list_files(ds.ref).files
            print(f"Files count: {len(files)}")
            for f in files[:5]:
                print(f"  - {f.name} ({f.size} bytes)")
        except Exception as e:
            print(f"Files list error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    main()
