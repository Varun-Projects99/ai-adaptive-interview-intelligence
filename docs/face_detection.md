# Multi-Person Face Detection — InterviewIQ (Part 2)

This document details the real-time Multi-Person Face Detection subsystem fine-tuned on the real Kaggle Human Faces Object Detection Dataset for InterviewIQ.

---

## 1. Dataset Specifications

- **Dataset Name**: Human Faces Object Detection Dataset
- **Kaggle URL**: `https://www.kaggle.com/datasets/sbaghbidi/human-faces-object-detection`
- **Kaggle Download Command**:
  ```bash
  kaggle datasets download -d sbaghbidi/human-faces-object-detection
  ```
- **Total Unique Images**: 2,204 real images
- **Total Bounding Boxes**: 3,350 face bounding box annotations
- **Multi-Face Distribution**:
  - 1 face: 1,713 images
  - 2 faces: 218 images
  - 3+ faces: 273 images (Max: 12 faces in single frame)
- **Reproducible Split (Seed 42)**:
  - **Train (80%)**: 1,763 images
  - **Validation (10%)**: 220 images
  - **Test (10%)**: 221 images

---

## 2. Model Specifications

- **YOLO Architecture**: **YOLO11n** (`yolo11n.pt`)
- **Parameters**: 2.58 Million parameters (6.4 GFLOPs)
- **Pretrained Source**: Ultralytics Official Pretrained YOLO11 Weights (`yolo11n.pt`)
- **Fine-Tuned Status**: **YES** (Fine-tuned on 1,763 Kaggle face images)
- **Model Checkpoint Path**: [models/face_detector/best.pt](file:///c:/Users/Varun%20B/OneDrive/Desktop/Projects/InterviewIQ/models/face_detector/best.pt)

---

## 3. Training Configuration

- **Device**: CPU / GPU (Detected automatically)
- **Epochs**: 5
- **Image Size (`imgsz`)**: 416 x 416
- **Batch Size**: 16
- **Optimizer**: AdamW (lr=0.002, momentum=0.9)
- **Data Augmentations**:
  - HSV Color & Brightness (`hsv_h=0.015`, `hsv_s=0.7`, `hsv_v=0.4`)
  - Rotation (`degrees=10.0`)
  - Scaling (`scale=0.2`)
  - Horizontal Flip (`fliplr=0.5`)
  - Occlusion Erasing (`erasing=0.1`)

---

## 4. Real Test Set Performance Metrics

Evaluated on the 221 real held-out test images from Kaggle split:

| Metric | Result |
| :--- | :--- |
| **Precision (P)** | **0.8757 (87.6%)** |
| **Recall (R)** | **0.9029 (90.3%)** |
| **mAP50** | **0.9337 (93.4%)** |
| **mAP50-95** | **0.4653 (46.5%)** |
| **CPU Inference Speed** | **11.55 FPS (25.7 ms/frame)** |

---

## 5. Temporal Stabilization & Integrity Alerts

The module `FaceDetectorStabilizer` buffers detections across consecutive frames (default window N=3) to prevent single-frame flickers or false alarms:

- **Confirmed 0 faces**: Status `NO_FACE_DETECTED` (candidate left seat / webcam obscured)
- **Confirmed 1 face**: Status `NORMAL_SINGLE_FACE` (valid interview state)
- **Confirmed 2+ faces**: Status `MULTIPLE_FACES_DETECTED` (second person entered room / candidate looking at helper)
- **Transitions**: Tracks `person_entered` and `person_left` events.

---

## 6. Commands to Run Locally

1. **Download & Convert Kaggle Dataset**:
   ```bash
   python training/face_detection/download_kaggle_dataset.py
   python training/face_detection/convert_to_yolo.py
   ```
2. **Train Model**:
   ```bash
   python training/face_detection/train.py
   ```
3. **Evaluate Test Set**:
   ```bash
   python training/face_detection/evaluate.py
   ```
4. **Test Image / Webcam**:
   ```bash
   python training/face_detection/test_face_detector.py --image path/to/image.jpg
   python training/face_detection/test_face_detector.py --webcam
   ```
