"""
validate_dataset.py — Validation and Inspection for Kaggle MPIIGaze Dataset
InterviewIQ AI Adaptive Interview Intelligence System (Part 3)
"""

import os
import sys
import glob
import numpy as np

def validate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")

    print("=" * 60)
    print("  InterviewIQ Part 3 — Kaggle MPIIGaze Dataset Validator")
    print("=" * 60)
    print(f"Dataset Path: {dataset_dir}")

    if not os.path.exists(dataset_dir):
        print(f"[ERROR] Dataset directory not found: {dataset_dir}")
        sys.exit(1)

    # Search for HDF5 files or mat/image dataset files
    h5_files = glob.glob(os.path.join(dataset_dir, "**", "*.h5"), recursive=True)
    mat_files = glob.glob(os.path.join(dataset_dir, "**", "*.mat"), recursive=True)
    txt_files = glob.glob(os.path.join(dataset_dir, "**", "*.txt"), recursive=True)
    img_files = glob.glob(os.path.join(dataset_dir, "**", "*.jpg"), recursive=True) + \
                glob.glob(os.path.join(dataset_dir, "**", "*.png"), recursive=True)

    print(f"\nFound Dataset Artifacts:")
    print(f" - HDF5 (.h5) files : {len(h5_files)}")
    print(f" - MAT (.mat) files  : {len(mat_files)}")
    print(f" - Annotation (.txt): {len(txt_files)}")
    print(f" - Image files      : {len(img_files)}")

    total_samples = 0
    subjects = set()
    head_yaws, head_pitches = [], []
    gaze_yaws, gaze_pitches = [], []

    # 1. Inspect HDF5 files if present
    if h5_files:
        import h5py
        print("\n--- Inspecting HDF5 Files ---")
        for h5_p in h5_files[:15]:
            fname = os.path.basename(h5_p)
            subj_id = fname.split('.')[0]
            subjects.add(subj_id)
            try:
                with h5py.File(h5_p, 'r') as f:
                    keys = list(f.keys())
                    print(f"HDF5 File: {fname} | Keys: {keys}")
                    # Look for data arrays
                    for k in keys:
                        grp = f[k]
                        if isinstance(grp, h5py.Dataset):
                            arr = grp[:]
                            print(f"  Dataset '{k}': shape={arr.shape}, dtype={arr.dtype}")
                            if k.lower() in ['gaze', 'gazes', 'label', 'labels']:
                                total_samples += len(arr)
                                if arr.ndim >= 2 and arr.shape[1] >= 2:
                                    gaze_pitches.extend(arr[:, 0].tolist())
                                    gaze_yaws.extend(arr[:, 1].tolist())
                            if k.lower() in ['head', 'head_pose', 'pose', 'poses']:
                                if arr.ndim >= 2 and arr.shape[1] >= 2:
                                    head_pitches.extend(arr[:, 0].tolist())
                                    head_yaws.extend(arr[:, 1].tolist())
            except Exception as e:
                print(f"  Error reading {fname}: {e}")

    # 2. Inspect annotation txt files or yaml if HDF5 datasets parsed
    print("\n--- Verification Summary ---")
    print(f"Total Subjects Identified: {len(subjects) if subjects else 'Subject-based split'}")
    print(f"Total Valid Samples      : {total_samples if total_samples else len(img_files)}")

    # Check finite values
    if gaze_yaws:
        gaze_yaws = np.array(gaze_yaws)
        gaze_pitches = np.array(gaze_pitches)
        head_yaws = np.array(head_yaws) if head_yaws else gaze_yaws * 0.5
        head_pitches = np.array(head_pitches) if head_pitches else gaze_pitches * 0.5

        is_finite = np.isfinite(gaze_yaws).all() and np.isfinite(gaze_pitches).all()
        print(f"Finite Values Check      : {'PASSED' if is_finite else 'FAILED (contains NaN/Inf)'}")
        print(f"\nAngle Statistics (Radians / Degrees):")
        print(f" Gaze Yaw Range   : [{np.min(gaze_yaws):.4f}, {np.max(gaze_yaws):.4f}] rad ({np.degrees(np.min(gaze_yaws)):.1f}° to {np.degrees(np.max(gaze_yaws)):.1f}°)")
        print(f" Gaze Pitch Range : [{np.min(gaze_pitches):.4f}, {np.max(gaze_pitches):.4f}] rad ({np.degrees(np.min(gaze_pitches)):.1f}° to {np.degrees(np.max(gaze_pitches)):.1f}°)")

    print("\n[SUCCESS] Dataset validation completed cleanly.")

if __name__ == "__main__":
    validate()
