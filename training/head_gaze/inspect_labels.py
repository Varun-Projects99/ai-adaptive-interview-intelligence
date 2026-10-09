"""
inspect_labels.py — Inspect annotation contents
InterviewIQ Part 3
"""

import os
import glob

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")

    all_txt = glob.glob(os.path.join(dataset_dir, "**", "*.txt"), recursive=True)
    all_yaml = glob.glob(os.path.join(dataset_dir, "**", "*.yaml"), recursive=True)
    all_json = glob.glob(os.path.join(dataset_dir, "**", "*.json"), recursive=True)

    print(f"Total txt files: {len(all_txt)}")
    print(f"Total yaml files: {len(all_yaml)}")
    print(f"Total json files: {len(all_json)}")

    if all_yaml:
        print("\n--- YAML File Content ---")
        with open(all_yaml[0], 'r') as f:
            print(f.read())

    if all_txt:
        print("\n--- Sample TXT File 1 ---")
        with open(all_txt[0], 'r') as f:
            print(f.read()[:500])

        print("\n--- Sample TXT File 2 ---")
        if len(all_txt) > 1:
            with open(all_txt[1], 'r') as f:
                print(f.read()[:500])

if __name__ == "__main__":
    main()
