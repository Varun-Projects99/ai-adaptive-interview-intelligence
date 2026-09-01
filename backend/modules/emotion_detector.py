"""
Real-Time Emotion & Face Detection Module
Uses OpenCV Cascade Classifiers to detect candidate face, eye visibility, multiple faces, and low lighting.
"""

import base64
import numpy as np
import cv2
import os

LOW_LIGHT_THRESHOLD = 20.0          # Average luminance threshold (0-255)
MIN_FACE_WIDTH = 15                 # Minimum bounding box width
MIN_FACE_HEIGHT = 15                # Minimum bounding box height
MIN_FACE_AREA_RATIO = 0.001          # Minimum face area ratio

face_cascade = None
eye_cascade = None
cv2_initialized = False

def _lazy_init():
    global face_cascade, eye_cascade, cv2_initialized
    if cv2_initialized:
        return
    try:
        models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        face_path = os.path.join(models_dir, "haarcascade_frontalface_default.xml")
        eye_path = os.path.join(models_dir, "haarcascade_eye.xml")

        if not os.path.exists(face_path):
            face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.exists(eye_path):
            eye_path = cv2.data.haarcascades + "haarcascade_eye.xml"

        face_cascade = cv2.CascadeClassifier(face_path)
        eye_cascade = cv2.CascadeClassifier(eye_path)
        cv2_initialized = True
        print(f"[EmotionDetector] Face & Eye cascades loaded (Face empty: {face_cascade.empty()}, Eye empty: {eye_cascade.empty()})")
    except Exception as e:
        print(f"[EmotionDetector] OpenCV init error: {e}")
        cv2_initialized = False

EMOTION_MAP = {
    "happy":"confident","neutral":"neutral","surprise":"neutral",
    "fear":"nervous","sad":"nervous","angry":"stressed","disgust":"stressed"
}
EMOTION_SCORE = {"confident":90,"neutral":65,"nervous":35,"stressed":20}


def analyze_emotion_frame(frame_b64: str, sess: dict = None) -> dict:
    _lazy_init()
    if not cv2_initialized or face_cascade is None or face_cascade.empty():
        return _default("opencv_unavailable", "no_face")

    if not frame_b64:
        return _default("no_frame", "no_face")

    try:
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        arr   = np.frombuffer(base64.b64decode(frame_b64), np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return _default("decode_failed", "no_face")

        # 1. Calculate luminance / brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))

        # Check for extreme low light
        if brightness < 15.0:
            print(f"[FACE] Low brightness: {brightness:.2f}")
            return _default("low_light", "low_light")

        # Equalize histogram for robust contrast
        gray_eq = cv2.equalizeHist(gray)
        frame_h, frame_w = frame.shape[:2]
        frame_area = frame_h * frame_w

        # 2. Detect face candidates (equalized first, fallback to original gray)
        faces = face_cascade.detectMultiScale(
            gray_eq, 
            scaleFactor=1.08, 
            minNeighbors=2, 
            minSize=(20, 20)
        )
        if len(faces) == 0:
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.08, 
                minNeighbors=2, 
                minSize=(20, 20)
            )

        valid_faces = []
        for (x, y, w, h) in faces:
            area_ratio = (w * h) / frame_area
            if w >= MIN_FACE_WIDTH and h >= MIN_FACE_HEIGHT and area_ratio >= MIN_FACE_AREA_RATIO:
                valid_faces.append((x, y, w, h))

        valid_count = len(valid_faces)
        print(f"[FACE] brightness={brightness:.1f}, valid_count={valid_count}")

        # Case: No Face Detected
        if valid_count == 0:
            return _default("no_face", "no_face")

        # Case: Multiple Faces Detected
        if valid_count > 1:
            return _default("multiple_faces", "multiple_faces")

        # Exactly 1 Face Found! Check eyes & visibility
        x, y, w, h = valid_faces[0]
        face_roi = gray[y : y + int(h * 0.65), x : x + w]
        
        eyes = []
        if eye_cascade and not eye_cascade.empty():
            eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=1, minSize=(6, 6))
        
        eyes_visible = len(eyes) > 0

        # Check if lighting is dim
        if brightness < 28.0:
            status_state = "low_light"
            reason = "low_light"
            face_detected = False
        elif not eyes_visible:
            status_state = "eyes_not_visible"
            reason = "eyes_not_visible"
            face_detected = True
        else:
            status_state = "face_present"
            reason = "ok"
            face_detected = True

        return {
            "face_detected": face_detected,
            "status": status_state,
            "confidence": 0.90 if eyes_visible else 0.70,
            "dominant_emotion": "neutral",
            "interview_score": 75 if eyes_visible else 55,
            "emotions": {"neutral": 100.0},
            "eyes_visible": eyes_visible,
            "reason": reason
        }

    except Exception as e:
        print(f"[EmotionDetector] Error: {e}")
        return _default("error", "no_face")


def check_face_present(frame_b64: str) -> bool:
    res = analyze_emotion_frame(frame_b64)
    return res.get("face_detected", False)


def _default(reason: str, status: str) -> dict:
    return {
        "face_detected":    False,
        "status":           status,
        "confidence":       0.0,
        "dominant_emotion": "neutral",
        "interview_score":  65,
        "emotions":         {"neutral": 100.0},
        "reason":           reason
    }
