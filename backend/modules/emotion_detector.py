"""
Real-Time Emotion Detection Module
Uses FER + OpenCV to detect emotions from base64 webcam frames.
Includes low-light pre-filtering, face sizing/confidence checks, and temporal smoothing.
"""

import base64
import numpy as np
import cv2
import os

# ── DETECTOR CONFIGURATION ───────────────────────────────────────────────────
LOW_LIGHT_THRESHOLD = 30.0          # Minimum average pixel luminance (0-255)
FACE_CONFIDENCE_THRESHOLD = 0.50    # Minimum normalized confidence (0.0-1.0)
MIN_FACE_WIDTH = 20                 # Minimum width of bounding box in pixels
MIN_FACE_HEIGHT = 20                # Minimum height of bounding box in pixels
MIN_FACE_AREA_RATIO = 0.003          # Minimum face bounding box area relative to frame area (0.3%)
FACE_CONFIRMATION_FRAMES = 1        # Consecutive frames to confirm FACE_PRESENT
NO_FACE_CONFIRMATION_FRAMES = 1     # Consecutive frames to confirm NO_FACE
# ─────────────────────────────────────────────────────────────────────────────

# Try importing FER lazily
fer_available = False
detector = None
face_cascade = None
cv2 = None

def _lazy_init():
    global fer_available, detector, face_cascade, cv2
    if cv2 is not None:
        return
    try:
        import cv2 as _cv2
        cv2 = _cv2
        # Load OpenCV face detector
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
    except Exception as e:
        print(f"[EmotionDetector] OpenCV/cv2 not available: {e}")
        cv2 = False
        return

    try:
        from fer import FER
        try:
            detector = FER(mtcnn=True)
            print("[EmotionDetector] MTCNN ready.")
        except:
            detector = FER(mtcnn=False)
            print("[EmotionDetector] Fallback ready.")
        fer_available = True
    except Exception as e:
        print(f"[EmotionDetector] FER/TensorFlow unavailable, falling back to OpenCV Haar Cascades: {e}")
        fer_available = False

EMOTION_MAP = {
    "happy":"confident","neutral":"neutral","surprise":"neutral",
    "fear":"nervous","sad":"nervous","angry":"stressed","disgust":"stressed"
}
EMOTION_SCORE = {"confident":90,"neutral":65,"nervous":35,"stressed":20}


def analyze_emotion_frame(frame_b64: str, sess: dict = None) -> dict:
    _lazy_init()
    if not cv2:
        return _default("opencv_unavailable", "no_face")

    if not frame_b64:
        return _default("no_frame", "no_face")

    # Initialize session temporal smoothing variables if session is provided
    if sess is not None:
        if "consecutive_face_frames" not in sess:
            sess["consecutive_face_frames"] = 0
        if "consecutive_no_face_frames" not in sess:
            sess["consecutive_no_face_frames"] = 0
        if "last_stable_state" not in sess:
            sess["last_stable_state"] = "no_face"

    try:
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        arr   = np.frombuffer(base64.b64decode(frame_b64), np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return _default("decode_failed", "no_face")

        # 1. Calculate brightness / luminance
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        
        # Logging for debugging
        print(f"[FACE] brightness={brightness:.2f}")

        # 2. Check if frame is in low light
        if brightness < LOW_LIGHT_THRESHOLD:
            print("[FACE] state=LOW_LIGHT")
            if sess is not None:
                sess["consecutive_face_frames"] = 0
                sess["consecutive_no_face_frames"] = 0
                sess["last_stable_state"] = "low_light"
            return _default("low_light", "low_light")

        # Equalize histogram to improve contrast
        gray = cv2.equalizeHist(gray)
        frame_h, frame_w = frame.shape[:2]
        frame_area = frame_h * frame_w

        valid_faces_count = 0
        best_confidence = 0.0
        best_emotion = "neutral"
        best_emotions_dict = {"neutral": 100.0}

        # 3. Detect face candidates using the available classifier
        if fer_available:
            results = detector.detect_emotions(frame)
            if results:
                for res in results:
                    box = res["box"]  # [x, y, w, h]
                    emotions = res["emotions"]
                    w, h = box[2], box[3]
                    area_ratio = (w * h) / frame_area
                    
                    confidence = 0.90
                    
                    if (confidence >= FACE_CONFIDENCE_THRESHOLD and
                        w >= MIN_FACE_WIDTH and
                        h >= MIN_FACE_HEIGHT and
                        area_ratio >= MIN_FACE_AREA_RATIO):
                        
                        valid_faces_count += 1
                        if valid_faces_count == 1:
                            best_confidence = confidence
                            dominant_raw = max(emotions, key=emotions.get)
                            best_emotion = EMOTION_MAP.get(dominant_raw, "neutral")
                            
                            best_emotions_dict = {}
                            for k, v in emotions.items():
                                cat = EMOTION_MAP.get(k, "neutral")
                                best_emotions_dict[cat] = round(best_emotions_dict.get(cat, 0) + v * 100, 1)
        else:
            # OpenCV Haar Cascade detectMultiScale3
            rects, rejectLevels, levelWeights = face_cascade.detectMultiScale3(
                gray, 
                scaleFactor=1.05, 
                minNeighbors=3, 
                minSize=(20, 20),
                outputRejectLevels=True
            )
            
            if len(rects) > 0:
                for i, (x, y, w, h) in enumerate(rects):
                    weight = levelWeights[i] if i < len(levelWeights) else 5.0
                    confidence = min(1.0, float(weight) / 4.0)
                    area_ratio = (w * h) / frame_area
                    
                    print(f"[FACE] candidate size={w}x{h}, area_ratio={area_ratio:.4f}, confidence={confidence:.2f}")

                    if (confidence >= FACE_CONFIDENCE_THRESHOLD and
                        w >= MIN_FACE_WIDTH and
                        h >= MIN_FACE_HEIGHT and
                        area_ratio >= MIN_FACE_AREA_RATIO):
                        
                        valid_faces_count += 1
                        if valid_faces_count == 1:
                            best_confidence = confidence

        # Map faces count to raw status state
        if valid_faces_count > 1:
            raw_face_detected = False
            raw_state = "multiple_faces"
        elif valid_faces_count == 1:
            raw_face_detected = True
            raw_state = "face_present"
        else:
            raw_face_detected = False
            raw_state = "no_face"

        # 4. Apply Temporal Smoothing
        stable_state = "no_face"
        if sess is not None:
            if raw_state == "face_present":
                sess["consecutive_face_frames"] += 1
                sess["consecutive_no_face_frames"] = 0
                if sess["consecutive_face_frames"] >= FACE_CONFIRMATION_FRAMES:
                    sess["last_stable_state"] = "face_present"
            elif raw_state == "multiple_faces":
                sess["consecutive_face_frames"] = 0
                sess["consecutive_no_face_frames"] = 0
                sess["last_stable_state"] = "multiple_faces"
            else:
                sess["consecutive_no_face_frames"] += 1
                sess["consecutive_face_frames"] = 0
                if sess["consecutive_no_face_frames"] >= NO_FACE_CONFIRMATION_FRAMES:
                    sess["last_stable_state"] = "no_face"
            
            stable_state = sess["last_stable_state"]
            print(f"[FACE] raw_detected={raw_face_detected}, consecutive_face={sess['consecutive_face_frames']}, consecutive_no_face={sess['consecutive_no_face_frames']}, status={stable_state.upper()}")
        else:
            stable_state = raw_state
            print(f"[FACE] stateless raw_detected={raw_face_detected}, status={stable_state.upper()}")

        # 5. Return appropriate response matching the stable state
        if stable_state == "face_present":
            print(f"[FACE] confidence={best_confidence:.2f}")
            print(f"[FACE] status=FACE_PRESENT")
            return {
                "face_detected":    True,
                "status":           "face_present",
                "confidence":       round(best_confidence, 2),
                "dominant_emotion": best_emotion,
                "interview_score":  EMOTION_SCORE.get(best_emotion, 65),
                "emotions":         best_emotions_dict
            }
        elif stable_state == "low_light":
            print(f"[FACE] status=LOW_LIGHT")
            return _default("low_light", "low_light")
        elif stable_state == "multiple_faces":
            print(f"[FACE] status=MULTIPLE_FACES")
            return _default("multiple_faces", "multiple_faces")
        else:
            print(f"[FACE] status=NO_FACE")
            return _default("no_face", "no_face")

    except Exception as e:
        print(f"[EmotionDetector] Exception: {e}")
        return _default("error", "no_face")


def check_face_present(frame_b64: str) -> bool:
    _lazy_init()
    if not cv2:
        return False
    try:
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",")[1]
        arr   = np.frombuffer(base64.b64decode(frame_b64), np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        
        # Brightness filter
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        if brightness < LOW_LIGHT_THRESHOLD:
            return False

        gray = cv2.equalizeHist(gray)
        frame_h, frame_w = frame.shape[:2]
        frame_area = frame_h * frame_w

        if fer_available:
            results = detector.detect_emotions(frame)
            if results:
                for res in results:
                    box = res["box"]
                    w, h = box[2], box[3]
                    area_ratio = (w * h) / frame_area
                    if (w >= MIN_FACE_WIDTH and
                        h >= MIN_FACE_HEIGHT and
                        area_ratio >= MIN_FACE_AREA_RATIO):
                        return True
            return False
        else:
            rects, rejectLevels, levelWeights = face_cascade.detectMultiScale3(
                gray, 
                scaleFactor=1.05, 
                minNeighbors=3, 
                minSize=(20, 20),
                outputRejectLevels=True
            )
            if len(rects) > 0:
                for i, (x, y, w, h) in enumerate(rects):
                    weight = levelWeights[i] if i < len(levelWeights) else 5.0
                    confidence = min(1.0, float(weight) / 10.0)
                    area_ratio = (w * h) / frame_area
                    if (confidence >= FACE_CONFIDENCE_THRESHOLD and
                        w >= MIN_FACE_WIDTH and
                        h >= MIN_FACE_HEIGHT and
                        area_ratio >= MIN_FACE_AREA_RATIO):
                        return True
            return False
    except:
        return False


def _default(reason: str, status: str) -> dict:
    face_det = False
    dom_em = "unknown" if status in ["low_light", "unknown"] else "neutral"
    
    return {
        "face_detected":    face_det,
        "status":           status,
        "confidence":       0.0,
        "dominant_emotion": dom_em,
        "interview_score":  65,
        "emotions":         {"neutral": 100.0},
        "reason":           reason
    }
