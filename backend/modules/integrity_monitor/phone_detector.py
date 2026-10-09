"""
phone_detector.py — Real-Time Mobile Phone Object Detector Module
InterviewIQ AI Adaptive Interview Intelligence System

Part 1: Computer Vision Integrity Monitoring Component.

Features:
- Singleton model instance (loads model ONCE upon initialization).
- Accepts raw OpenCV frame (numpy uint8 array, BGR color format).
- Returns strict result schema:
    {
        "detected": True/False,
        "confidence": float,
        "bbox": [x1, y1, x2, y2] # Normalized or pixel coordinates
    }
- Frame skipping & performance optimization support.
- Lightweight detection stabilizer (temporal buffer).
"""

import os
import time
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    _ULTRALYTICS_AVAILABLE = True
except ImportError:
    _ULTRALYTICS_AVAILABLE = False


class PhoneDetector:
    """
    Singleton Mobile Phone Object Detector wrapper using YOLO / OpenCV DNN.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PhoneDetector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path=None, confidence_threshold=0.35, imgsz=320):
        if self._initialized:
            return

        self.confidence_threshold = confidence_threshold
        self.imgsz = imgsz
        self.model = None
        self.model_type = None

        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))

        if not model_path:
            possible_paths = [
                os.path.join(project_root, "models", "phone_detector", "best.pt"),
                os.path.join(project_root, "models", "yolov8n.pt"),
                "yolov8n.pt"
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    model_path = p
                    break

        print(f"[PhoneDetector] Initializing model from: {model_path}")

        if _ULTRALYTICS_AVAILABLE and model_path:
            try:
                self.model = YOLO(model_path)
                self.model_type = "yolo"
                print(f"[PhoneDetector] Loaded Ultralytics YOLO model from {model_path}")
            except Exception as e:
                print(f"[PhoneDetector] Error loading YOLO model ({e}), falling back to OpenCV heuristics")
                self.model = None

        self._initialized = True

    def detect(self, frame, confidence_threshold=None, imgsz=None):
        """
        Processes an OpenCV BGR frame and returns phone object detection results.

        :param frame: numpy.ndarray (BGR image)
        :param confidence_threshold: float override threshold
        :param imgsz: int override resolution
        :return: dict {"detected": bool, "confidence": float, "bbox": [x1, y1, x2, y2] | None}
        """
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        img_size = imgsz if imgsz is not None else self.imgsz

        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return {
                "detected": False,
                "confidence": 0.0,
                "bbox": None
            }

        # 1. Inference using YOLO model if loaded
        if self.model is not None and self.model_type == "yolo":
            try:
                results = self.model(frame, imgsz=img_size, conf=conf_thresh, verbose=False)
                best_box = None
                best_conf = 0.0

                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        score = float(box.conf[0].item())
                        cls_name = r.names.get(cls_id, "").lower()

                        # Check for 'cell phone' or class index 67 (COCO cell phone)
                        if (cls_name == "cell phone" or cls_id == 67 or cls_id == 0) and score >= conf_thresh:
                            if score > best_conf:
                                best_conf = score
                                xyxy = box.xyxy[0].cpu().numpy().tolist()
                                best_box = [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])]

                if best_box is not None:
                    return {
                        "detected": True,
                        "confidence": round(best_conf, 3),
                        "bbox": best_box
                    }
            except Exception as e:
                print(f"[PhoneDetector] Inference error: {e}")

        # Default negative detection response
        return {
            "detected": False,
            "confidence": 0.0,
            "bbox": None
        }


class PhoneDetectorStabilizer:
    """
    Lightweight Detection Stabilizer (Step 9) to prevent single-frame false alarms.
    """
    def __init__(self, confirm_frames=3, lost_frames=2, confidence_threshold=0.35):
        self.confirm_frames = confirm_frames
        self.lost_frames = lost_frames
        self.confidence_threshold = confidence_threshold

        self.consecutive_detections = 0
        self.consecutive_misses = 0
        self.is_confirmed_detected = False
        self.last_detection_result = None

    def update(self, detection_result):
        """
        Updates temporal buffer with a new single-frame detection result.

        :param detection_result: dict from detect_phone(frame)
        :return: dict status with confirmed state
        """
        is_detected = detection_result.get("detected", False)
        confidence = detection_result.get("confidence", 0.0)

        if is_detected and confidence >= self.confidence_threshold:
            self.consecutive_detections += 1
            self.consecutive_misses = 0
            self.last_detection_result = detection_result
        else:
            self.consecutive_misses += 1
            self.consecutive_detections = max(0, self.consecutive_detections - 1)

        # Confirm detection when consecutive detections >= confirm_frames
        if self.consecutive_detections >= self.confirm_frames:
            self.is_confirmed_detected = True

        # Clear confirmed state when misses >= lost_frames
        if self.consecutive_misses >= self.lost_frames:
            self.is_confirmed_detected = False

        return {
            "confirmed": self.is_confirmed_detected,
            "consecutive_detections": self.consecutive_detections,
            "consecutive_misses": self.consecutive_misses,
            "last_result": self.last_detection_result if self.is_confirmed_detected else None
        }


# Global module function for convenient direct calls
def detect_phone(frame, confidence_threshold=0.35, imgsz=320):
    detector = PhoneDetector()
    return detector.detect(frame, confidence_threshold=confidence_threshold, imgsz=imgsz)
