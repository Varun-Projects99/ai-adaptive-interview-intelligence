"""
face_detector.py — Real-Time Multi-Person Face Detector Module
InterviewIQ AI Adaptive Interview Intelligence System

Part 2: Computer Vision Integrity Monitoring Component.

Features:
- Singleton model instance (loads fine-tuned YOLO face detector ONCE).
- Accepts raw OpenCV frame (numpy uint8 array, BGR color format).
- Returns strict result schema:
    {
        "count": int,
        "faces": [
            {"confidence": float, "bbox": [x1, y1, x2, y2]},
            ...
        ],
        "has_faces": bool,
        "is_multi_face": bool
    }
- Frame skipping & performance optimization support.
- Temporal FaceDetectorStabilizer buffer to track 0, 1, 2, and 3+ faces.
"""

import os
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    _ULTRALYTICS_AVAILABLE = True
except ImportError:
    _ULTRALYTICS_AVAILABLE = False


class FaceDetector:
    """
    Singleton Face Object Detector wrapper using fine-tuned YOLO model.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FaceDetector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path=None, confidence_threshold=0.35, imgsz=320):
        if self._initialized:
            return

        self.confidence_threshold = confidence_threshold
        self.imgsz = imgsz
        self.model = None

        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, "..", "..", ".."))

        if not model_path:
            possible_paths = [
                os.path.join(project_root, "models", "face_detector", "best.pt"),
                os.path.join(project_root, "models", "yolov8n.pt"),
                "yolov8n.pt"
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    model_path = p
                    break

        print(f"[FaceDetector] Initializing model from: {model_path}")

        if _ULTRALYTICS_AVAILABLE and model_path:
            try:
                self.model = YOLO(model_path)
                print(f"[FaceDetector] Loaded Ultralytics YOLO model from {model_path}")
            except Exception as e:
                print(f"[FaceDetector] Error loading YOLO face model: {e}")
                self.model = None

        self._initialized = True

    def detect(self, frame, confidence_threshold=None, imgsz=None):
        """
        Processes an OpenCV BGR frame and returns detected faces with count and bboxes.

        :param frame: numpy.ndarray (BGR image)
        :param confidence_threshold: float override threshold
        :param imgsz: int override resolution
        :return: dict {"count": int, "faces": [{"confidence": float, "bbox": [x1,y1,x2,y2]}], "has_faces": bool, "is_multi_face": bool}
        """
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        img_size = imgsz if imgsz is not None else self.imgsz

        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return {
                "count": 0,
                "faces": [],
                "has_faces": False,
                "is_multi_face": False
            }

        detected_faces = []

        if self.model is not None:
            try:
                results = self.model(frame, imgsz=img_size, conf=conf_thresh, verbose=False)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        score = float(box.conf[0].item())
                        if score >= conf_thresh:
                            xyxy = box.xyxy[0].cpu().numpy().tolist()
                            bbox = [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])]
                            detected_faces.append({
                                "confidence": round(score, 3),
                                "bbox": bbox
                            })
            except Exception as e:
                print(f"[FaceDetector] Inference error: {e}")

        count = len(detected_faces)
        return {
            "count": count,
            "faces": detected_faces,
            "has_faces": count > 0,
            "is_multi_face": count > 1
        }


class FaceDetectorStabilizer:
    """
    Temporal confirmation stabilizer to prevent false alarms due to single-frame detection noise.
    Tracks face counts across frames and generates integrity alerts.
    """
    def __init__(self, confirm_frames=3, confidence_threshold=0.35):
        self.confirm_frames = confirm_frames
        self.confidence_threshold = confidence_threshold

        self.history = []
        self.confirmed_count = 1  # Default state assuming 1 single user
        self.status = "NORMAL_SINGLE_FACE"
        self.person_entered = False
        self.person_left = False

    def update(self, detection_result):
        """
        Updates temporal buffer with a new single-frame detection result.

        :param detection_result: dict from detect_faces(frame)
        :return: dict status with stabilized count and alert flags
        """
        raw_count = detection_result.get("count", 0)
        self.history.append(raw_count)

        if len(self.history) > self.confirm_frames:
            self.history.pop(0)

        # Confirm count if consistent across buffer
        if len(self.history) >= self.confirm_frames:
            # Use majority / mode of recent frame count history
            counts, counts_freq = np.unique(self.history, return_counts=True)
            candidate_count = int(counts[np.argmax(counts_freq)])

            previous_count = self.confirmed_count
            if candidate_count != self.confirmed_count:
                if candidate_count > self.confirmed_count:
                    self.person_entered = True
                    self.person_left = False
                else:
                    self.person_left = True
                    self.person_entered = False
                self.confirmed_count = candidate_count
            else:
                self.person_entered = False
                self.person_left = False

        # Determine integrity alert status
        if self.confirmed_count == 0:
            self.status = "NO_FACE_DETECTED"
        elif self.confirmed_count == 1:
            self.status = "NORMAL_SINGLE_FACE"
        else:
            self.status = "MULTIPLE_FACES_DETECTED"

        return {
            "confirmed_count": self.confirmed_count,
            "status": self.status,
            "person_entered": self.person_entered,
            "person_left": self.person_left,
            "raw_faces": detection_result.get("faces", [])
        }


# Global module function for direct calls
def detect_faces(frame, confidence_threshold=0.35, imgsz=320):
    detector = FaceDetector()
    return detector.detect(frame, confidence_threshold=confidence_threshold, imgsz=imgsz)
