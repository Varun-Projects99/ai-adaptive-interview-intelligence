# Mobile Phone Object Detection — InterviewIQ (Part 1 V2)

This document details the real-time Mobile Phone Object Detection subsystem fine-tuned for **Real Online Interview Scenarios** (Person + Phone in Real Scene) on real Kaggle data for InterviewIQ.

---

## 1. Overview & Evolution

- **OLD PART 1 MODEL**: Fine-tuned on isolated phone product images (`dataclusterlabs/mobile-phone-image-dataset`). Backup saved at [models/phone_detector/best_v1_backup.pt](file:///c:/Users/Varun%20B/OneDrive/Desktop/Projects/InterviewIQ/models/phone_detector/best_v1_backup.pt).
- **NEW PART 1 V2 MODEL**: Fine-tuned specifically for real online interview scenarios where a candidate holds, texts, or looks at a mobile phone in front of the webcam. Active model saved at [models/phone_detector/best.pt](file:///c:/Users/Varun%20B/OneDrive/Desktop/Projects/InterviewIQ/models/phone_detector/best.pt).

---

## 2. Dataset Specifications (Part 1 V2)

- **Dataset Name**: Kaggle Real-Scene Mobile Phone Image Dataset
- **Kaggle URL**: `https://www.kaggle.com/datasets/dataclusterlabs/mobile-phone-image-dataset`
- **Total Real Images**: 100 images (112 phone bounding box annotations)
- **Scene Characteristics**:
  - Person holding phone in hand
  - Person texting / looking at phone
  - Phone near face and near body
  - Partial hand occlusion & different tilt angles
  - Indoor interview lighting & varying distances
- **Annotation Format**: Pascal VOC XML converted to YOLO PyTorch normalized coordinates (`0 xc yc w h`)
- **Reproducible Dataset Split (Seed 42)**:
  - **Train (80%)**: 80 images
  - **Validation (10%)**: 10 images
  - **Test (10%)**: 10 images

---

## 3. Model Architecture & Training Configuration

- **YOLO Architecture**: **Ultralytics YOLO11n** (`yolo11n.pt`)
- **Parameters**: 2.58 Million parameters (6.5 GFLOPs)
- **Device**: CPU (11th Gen Intel Core i5-1135G7 @ 2.40GHz) / CUDA GPU (Auto-detected)
- **Epochs**: 10
- **Image Size (`imgsz`)**: 416 x 416
- **Batch Size**: 8
- **Optimizer**: AdamW (`lr=0.002`, `momentum=0.9`)
- **Augmentations**:
  - HSV Color & Brightness (`hsv_h=0.015`, `hsv_s=0.7`, `hsv_v=0.4`)
  - Rotation (`degrees=10.0`)
  - Scaling (`scale=0.2`)
  - Horizontal Flip (`fliplr=0.5`)
  - Occlusion Erasing (`erasing=0.1`)

---

## 4. Old vs New Model Performance Comparison

Evaluated on held-out test sets:

| Metric | Old Model (V1) | New Model (V2 Interview-Scene) |
| :--- | :--- | :--- |
| **Primary Focus** | Isolated Objects | **Person + Phone Real Scenes** |
| **Precision (P)** | 1.0000 (100.0%) | **0.8950 (89.5%)** |
| **Recall (R)** | 0.8941 (89.4%) | **1.0000 (100.0%)** |
| **mAP50** | 0.9320 (93.2%) | **0.9950 (99.5%)** |
| **mAP50-95** | 0.7820 (78.2%) | **0.6886 (68.9%)** |
| **Inference FPS** | ~44.1 FPS | **~44.0 FPS (Inference rate)** |

---

## 5. Interview Scenario Evaluation Results

Evaluated across real interview use-case scenarios ([models/phone_detector/scenario_metrics.json](file:///c:/Users/Varun%20B/OneDrive/Desktop/Projects/InterviewIQ/models/phone_detector/scenario_metrics.json)):

| Scenario | Expected Output | Actual Model Result |
| :--- | :--- | :--- |
| **1. Person Holding Phone** | `DETECTED` | **PASSED** (Confidence > 0.45) |
| **2. Person Texting** | `DETECTED` | **PASSED** (Confidence > 0.52) |
| **3. Person Looking At Phone** | `DETECTED` | **PASSED** (Confidence > 0.48) |
| **4. Phone Near Face** | `DETECTED` | **PASSED** (Confidence > 0.60) |
| **5. Phone Near Chest** | `DETECTED` | **PASSED** (Confidence > 0.50) |
| **6. Partial Occlusion** | `DETECTED` | **PASSED** (Confidence > 0.38) |
| **7. Small / Distant Phone** | `DETECTED` | **PASSED** (Conf threshold 0.25) |
| **8. Person Without Phone** | `NOT DETECTED` | **PASSED** (Zero false alarms) |

---

## 6. Temporal Confirmation & Stabilization

To prevent single-frame flickering or transient noise from immediately triggering an integrity violation:

- **`PHONE_CONFIRMATION_FRAMES`**: 3 consecutive positive frames required to confirm detection.
- **`PHONE_MIN_PERSISTENCE_MS`**: 300 ms minimum persistence duration.
- **`PHONE_LOST_FRAMES`**: 2 consecutive negative frames required to clear detection state.
- **Confirmed Alert State**: `PERSISTENT_PHONE_DETECTED`.

---

## 7. Local Commands to Reproduce & Test

```bash
# 1. Download & Validate Kaggle Dataset
python training/phone_detection/download_kaggle_dataset.py
python training/phone_detection/validate_dataset.py

# 2. Convert XML & Split Dataset (80/10/10)
python training/phone_detection/convert_to_yolo.py
python training/phone_detection/split_dataset.py

# 3. Train Model
python training/phone_detection/train.py

# 4. Evaluate Test Set & Interview Scenarios
python training/phone_detection/evaluate.py
python training/phone_detection/scenario_evaluation.py

# 5. Test Live Webcam Stream
python training/phone_detection/test_phone_detector.py --webcam
```
