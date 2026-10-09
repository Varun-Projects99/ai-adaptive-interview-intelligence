# Mobile Phone Object Detection Training Pipeline — InterviewIQ

This module contains the training and evaluation scripts for fine-tuning a lightweight YOLO object detector on mobile phone datasets.

## Directory Structure

```
training/phone_detection/
├── dataset/            # Dataset images and YOLO format labels (git-ignored)
├── data.yaml           # Dataset configuration file
├── prepare_dataset.py  # Script to download/prepare datasets
├── train.py            # Model training script
├── evaluate.py         # Model benchmarking and evaluation script
└── README.md
```

## How to Prepare Dataset

1. Download a YOLO-format dataset for mobile phone detection (e.g. from Roboflow Public Datasets or COCO).
2. Extract images to `dataset/images/train`, `dataset/images/val` and labels to `dataset/labels/train`, `dataset/labels/val`.
3. Run dataset preparation:
   ```bash
   python prepare_dataset.py
   ```

## How to Train Model

Run the fine-tuning script:
```bash
python train.py
```
This fine-tunes YOLOv8n on `data.yaml` and exports `best.pt` to `models/phone_detector/best.pt`.

## How to Evaluate Model

Run the evaluation script to measure FPS, Precision, Recall, and mAP:
```bash
python evaluate.py
```
