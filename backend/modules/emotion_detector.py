"""
Real-Time Emotion Detection Module
Uses FER + OpenCV to detect emotions from base64 webcam frames.
"""

import base64, numpy as np, cv2
from fer import FER

try:
    detector = FER(mtcnn=True)
    print("[EmotionDetector] MTCNN ready.")
except:
    detector = FER(mtcnn=False)
    print("[EmotionDetector] Fallback ready.")

EMOTION_MAP = {
    "happy":"confident","neutral":"neutral","surprise":"neutral",
    "fear":"nervous","sad":"nervous","angry":"stressed","disgust":"stressed"
}
EMOTION_SCORE = {"confident":90,"neutral":65,"nervous":35,"stressed":20}


def analyze_emotion_frame(frame_b64: str) -> dict:
    if not frame_b64:
        return _default("no_frame")
    try:
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        arr   = np.frombuffer(base64.b64decode(frame_b64), np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return _default("decode_failed")

        frame   = cv2.resize(frame, (640, 480))
        results = detector.detect_emotions(frame)
        if not results:
            return _default("no_face")

        emotions     = results[0]["emotions"]
        dominant_raw = max(emotions, key=emotions.get)
        mapped       = EMOTION_MAP.get(dominant_raw, "neutral")

        # Aggregate mapped scores
        mapped_scores = {}
        for k, v in emotions.items():
            cat = EMOTION_MAP.get(k, "neutral")
            mapped_scores[cat] = round(mapped_scores.get(cat, 0) + v * 100, 1)

        return {
            "face_detected":    True,
            "dominant_emotion": mapped,
            "raw_emotion":      dominant_raw,
            "raw_confidence":   round(emotions[dominant_raw] * 100, 1),
            "interview_score":  EMOTION_SCORE[mapped],
            "emotions":         mapped_scores
        }
    except Exception as e:
        print(f"[EmotionDetector] {e}")
        return _default("error")


def check_face_present(frame_b64: str) -> bool:
    try:
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        arr   = np.frombuffer(base64.b64decode(frame_b64), np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return len(detector.detect_emotions(cv2.resize(frame, (320, 240)))) > 0
    except:
        return False


def _default(reason: str) -> dict:
    return {"face_detected":False,"dominant_emotion":"neutral","raw_emotion":"neutral",
            "raw_confidence":0.0,"interview_score":65,
            "emotions":{"neutral":100.0},"reason":reason}
