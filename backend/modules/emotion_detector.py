"""
Real-Time Face Analysis & Interview Integrity Detection Module
----------------------------------------------------------------
Uses OpenCV Cascade Classifiers (face/eye), OpenCV's built-in YuNet face
detector (for approximate head-pose landmarks), and OpenCV's built-in DNN
module with a lightweight NanoDet-Plus COCO object detector (for
"potential phone in frame") to analyze one candidate webcam frame at a
time.

No component here is a model trained by/for this project, and none of the
detection is guaranteed-accurate -- see backend/modules/integrity_config.py
for the full explanation and every threshold used below. Everything in
this module reports approximate, best-effort, explainable signals; nothing
here should ever be presented to a candidate or recruiter as proof of
cheating.
"""

import base64
import time
import math
import numpy as np
import cv2
import os

from modules.integrity_config import (
    SEVERE_LOW_LIGHT_THRESHOLD, LOW_LIGHT_THRESHOLD,
    MIN_FACE_WIDTH, MIN_FACE_HEIGHT, MIN_FACE_AREA_RATIO,
    MULTI_FACE_MIN_NEIGHBORS, MULTI_FACE_MIN_RELATIVE_AREA,
    FACE_TOO_FAR_AREA_RATIO, FACE_TOO_CLOSE_AREA_RATIO, FACE_EDGE_MARGIN_PX,
    BLUR_VARIANCE_THRESHOLD,
    HEAD_POSE_YAW_CENTER_DEG, HEAD_POSE_PITCH_CENTER_DEG, HEAD_POSE_CONFIRM_SECONDS,
    PHONE_MIN_CONFIDENCE, PHONE_CONFIRM_SECONDS,
    LOW_LIGHT_CONFIRM_SECONDS, BLUR_CONFIRM_SECONDS, FACE_POSITION_CONFIRM_SECONDS,
    STATE_LOW_LIGHT, STATE_BLURRY_IMAGE,
    STATE_FACE_TOO_FAR, STATE_FACE_TOO_CLOSE, STATE_FACE_PARTIALLY_VISIBLE,
    STATE_HEAD_LEFT, STATE_HEAD_RIGHT, STATE_HEAD_UP, STATE_HEAD_DOWN,
    STATE_PHONE_DETECTED,
    EVENT_SEVERITY,
    YUNET_MODEL_PATH, NANODET_MODEL_PATH, NANODET_INPUT_SIZE, NANODET_PHONE_CLASS_INDEX,
)

face_cascade = None
eye_cascade = None
cv2_initialized = False

# Tier-2 detectors are optional: if the model file is missing or fails to
# load, the corresponding signal silently degrades to "unknown"/"not
# detected" rather than crashing /api/emotion/analyze (see _lazy_init_yunet
# / _lazy_init_nanodet).
_yunet = None
_yunet_size = None
_yunet_load_attempted = False
_nanodet_net = None
_nanodet_load_attempted = False


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


def _lazy_init_yunet():
    """Load the YuNet face-landmark detector (core opencv-python, no new pip
    dependency). Used ONLY to derive an approximate head-pose signal for a
    frame the Haar cascade has already confirmed contains exactly one face
    -- it never participates in the primary face_detected/status decision.
    Returns True if a usable detector is loaded."""
    global _yunet, _yunet_load_attempted
    if _yunet is not None:
        return True
    if _yunet_load_attempted:
        return False
    _yunet_load_attempted = True
    try:
        if not os.path.exists(YUNET_MODEL_PATH):
            print(f"[EmotionDetector] YuNet model not found at {YUNET_MODEL_PATH} -- head-pose will report 'unknown'")
            return False
        # input size is set per-call via .setInputSize(); (320,320) here is a placeholder
        _yunet = cv2.FaceDetectorYN.create(YUNET_MODEL_PATH, "", (320, 320), score_threshold=0.7)
        print("[EmotionDetector] YuNet head-pose landmark model loaded")
        return True
    except Exception as e:
        print(f"[EmotionDetector] YuNet load failed (head-pose disabled): {e}")
        _yunet = None
        return False


def _lazy_init_nanodet():
    """Load the NanoDet-Plus COCO object detector (core opencv-python DNN
    module, no new pip dependency) used for the phone/object signal.
    Returns True if a usable detector is loaded."""
    global _nanodet_net, _nanodet_load_attempted
    if _nanodet_net is not None:
        return True
    if _nanodet_load_attempted:
        return False
    _nanodet_load_attempted = True
    try:
        if not os.path.exists(NANODET_MODEL_PATH):
            print(f"[EmotionDetector] NanoDet model not found at {NANODET_MODEL_PATH} -- phone detection disabled")
            return False
        _nanodet_net = cv2.dnn.readNet(NANODET_MODEL_PATH)
        print("[EmotionDetector] NanoDet phone/object detection model loaded")
        return True
    except Exception as e:
        print(f"[EmotionDetector] NanoDet load failed (phone detection disabled): {e}")
        _nanodet_net = None
        return False


EMOTION_MAP = {
    "happy":"confident","neutral":"neutral","surprise":"neutral",
    "fear":"nervous","sad":"nervous","angry":"stressed","disgust":"stressed"
}
EMOTION_SCORE = {"confident":90,"neutral":65,"nervous":35,"stressed":20}


def _filter_valid_faces(faces, frame_area):
    """Drop detections too small/thin to plausibly be a real face in frame."""
    valid = []
    for (x, y, w, h) in faces:
        area_ratio = (w * h) / frame_area
        if w >= MIN_FACE_WIDTH and h >= MIN_FACE_HEIGHT and area_ratio >= MIN_FACE_AREA_RATIO:
            valid.append((x, y, w, h))
    return valid


def _resolve_multi_face_count(strict_valid_faces):
    """
    Decide the final face count once the lenient detection pass has already
    reported more than one face candidate.

    Haar-cascade detection can hallucinate a "second face" from shadows,
    posters, hands, hair, or reflections -- especially at the low
    minNeighbors needed to reliably find one real face in typical webcam
    lighting. Reporting every such candidate as a "Multiple Person" integrity
    event would make that event unreliable, so a second face only counts as
    real when BOTH of these deterministic, rule-based checks pass (this is
    not a trained classifier -- no model, no accuracy/precision claims):

      1. It still survives a much stricter re-detection pass
         (minNeighbors=MULTI_FACE_MIN_NEIGHBORS) on the same frame.
      2. It is a reasonably similar size to the largest confirmed face --
         a genuine second head is roughly head-sized too, while a
         false-positive blob is usually much smaller and inconsistent.

    `strict_valid_faces` is the already size/area-filtered output of the
    strict pass (see _filter_valid_faces). Returns 1 if the "extra" face(s)
    don't hold up under this confirmation, else the confirmed count.
    """
    if len(strict_valid_faces) <= 1:
        return 1
    max_area = max(w * h for (_, _, w, h) in strict_valid_faces)
    similar_sized = [f for f in strict_valid_faces if (f[2] * f[3]) >= MULTI_FACE_MIN_RELATIVE_AREA * max_area]
    return len(similar_sized) if len(similar_sized) > 1 else 1


def _compute_blur_score(gray_img) -> float:
    """Standard 'variance of Laplacian' sharpness heuristic. Lower = blurrier.
    Not a trained model -- see integrity_config.py."""
    try:
        return float(cv2.Laplacian(gray_img, cv2.CV_64F).var())
    except Exception:
        return float("nan")


def _classify_face_position(x, y, w, h, frame_w, frame_h) -> str:
    """Classify a confirmed face's bounding box as in_frame / too_far /
    too_close / partially_visible, from simple geometry only -- no new
    detector, reuses the box the Haar cascade already produced."""
    frame_area = frame_w * frame_h
    area_ratio = (w * h) / frame_area if frame_area else 0.0

    touches_edge = (
        x <= FACE_EDGE_MARGIN_PX or y <= FACE_EDGE_MARGIN_PX or
        (x + w) >= (frame_w - FACE_EDGE_MARGIN_PX) or
        (y + h) >= (frame_h - FACE_EDGE_MARGIN_PX)
    )
    if touches_edge:
        return "partially_visible"
    if area_ratio < FACE_TOO_FAR_AREA_RATIO:
        return "too_far"
    if area_ratio > FACE_TOO_CLOSE_AREA_RATIO:
        return "too_close"
    return "in_frame"


# YuNet 5-point landmark order: right eye, left eye, nose tip, right mouth
# corner, left mouth corner (as documented by the model's own OpenCV Zoo
# demo). Paired with a generic/textbook 3D face model -- NOT calibrated to
# any individual candidate's real face geometry. This is an approximation,
# not a precise measurement; see integrity_config.py.
_GENERIC_FACE_3D = np.array([
    [-30.0,  32.7, -26.0],
    [ 30.0,  32.7, -26.0],
    [  0.0,   0.0,   0.0],
    [-25.0, -28.9, -24.1],
    [ 25.0, -28.9, -24.1],
], dtype=np.float64)


def _estimate_head_pose(frame, face_box):
    """Best-effort, approximate head-pose direction for the single confirmed
    face in `face_box` (x, y, w, h). Returns (direction, yaw_deg, pitch_deg)
    where direction is one of center/left/right/up/down/unknown. Returns
    ("unknown", None, None) if the YuNet model isn't available or landmark
    extraction/solvePnP doesn't succeed for this frame -- this is a
    graceful degrade, never a crash."""
    global _yunet_size
    if not _lazy_init_yunet():
        return "unknown", None, None

    try:
        frame_h, frame_w = frame.shape[:2]
        if _yunet_size != (frame_w, frame_h):
            _yunet.setInputSize((frame_w, frame_h))
            _yunet_size = (frame_w, frame_h)
        _, faces = _yunet.detect(frame)
        if faces is None or len(faces) == 0:
            return "unknown", None, None

        # Pick the YuNet detection whose box center is closest to the
        # Haar-confirmed face's center (they are two different detectors
        # looking at the same frame and may not agree pixel-for-pixel).
        fx, fy, fw, fh = face_box
        target_cx, target_cy = fx + fw / 2.0, fy + fh / 2.0

        def _dist(det):
            dx, dy, dw, dh = det[0], det[1], det[2], det[3]
            cx, cy = dx + dw / 2.0, dy + dh / 2.0
            return (cx - target_cx) ** 2 + (cy - target_cy) ** 2

        best = min(faces, key=_dist)
        lm2d = np.array([
            [best[4], best[5]], [best[6], best[7]], [best[8], best[9]],
            [best[10], best[11]], [best[12], best[13]],
        ], dtype=np.float64)

        focal = frame_w
        cam_matrix = np.array([[focal, 0, frame_w / 2.0],
                                [0, focal, frame_h / 2.0],
                                [0, 0, 1]], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        ok, rvec, _tvec = cv2.solvePnP(
            _GENERIC_FACE_3D, lm2d, cam_matrix, dist_coeffs, flags=cv2.SOLVEPNP_EPNP
        )
        if not ok:
            return "unknown", None, None

        rmat, _ = cv2.Rodrigues(rvec)
        sy = math.sqrt(rmat[0, 0] ** 2 + rmat[1, 0] ** 2)
        pitch = math.degrees(math.atan2(-rmat[2, 0], sy))
        yaw = math.degrees(math.atan2(rmat[1, 0], rmat[0, 0]))

        if abs(yaw) <= HEAD_POSE_YAW_CENTER_DEG and abs(pitch) <= HEAD_POSE_PITCH_CENTER_DEG:
            direction = "center"
        elif abs(yaw) > abs(pitch):
            direction = "right" if yaw > 0 else "left"
        else:
            direction = "down" if pitch > 0 else "up"

        return direction, round(yaw, 1), round(pitch, 1)
    except Exception as e:
        print(f"[EmotionDetector] head-pose estimation error: {e}")
        return "unknown", None, None


def _detect_phone(frame):
    """Best-effort phone/object detection using NanoDet-Plus (COCO 80-class,
    includes 'cell phone'). Returns (detected: bool, confidence: float).
    Returns (False, 0.0) if the model isn't available or nothing crosses
    PHONE_MIN_CONFIDENCE -- a graceful degrade, never a crash. This is a
    general-purpose object detector, not one trained for this project; see
    integrity_config.py for its published accuracy on the 'cell phone'
    class and why the confidence floor + temporal confirmation exist."""
    if not _lazy_init_nanodet():
        return False, 0.0

    try:
        h, w = frame.shape[:2]
        side = max(h, w)
        square = np.zeros((side, side, 3), dtype=np.uint8)
        square[:h, :w] = frame
        resized = cv2.resize(square, NANODET_INPUT_SIZE).astype(np.float32)

        mean = np.array([103.53, 116.28, 123.675], dtype=np.float32).reshape(1, 1, 3)
        std = np.array([57.375, 57.12, 58.395], dtype=np.float32).reshape(1, 1, 3)
        normed = (resized - mean) / std
        blob = cv2.dnn.blobFromImage(normed)

        _nanodet_net.setInput(blob)
        outs = _nanodet_net.forward(_nanodet_net.getUnconnectedOutLayersNames())

        # Outputs alternate [cls_scores, bbox_preds] per FPN level (see the
        # model's own OpenCV Zoo demo/nanodet.py -- only the classification
        # scores are needed here, since we only care whether a "cell phone"
        # is present above threshold, not its exact box).
        best_conf = 0.0
        for cls_score in outs[0::2]:
            arr = np.asarray(cls_score)
            if arr.ndim == 3:
                arr = arr.squeeze(axis=0)
            if arr.ndim != 2 or arr.shape[1] <= NANODET_PHONE_CLASS_INDEX:
                continue
            level_max = float(arr[:, NANODET_PHONE_CLASS_INDEX].max()) if arr.shape[0] else 0.0
            best_conf = max(best_conf, level_max)

        detected = best_conf >= PHONE_MIN_CONFIDENCE
        return detected, round(best_conf, 3)
    except Exception as e:
        print(f"[EmotionDetector] phone detection error: {e}")
        return False, 0.0


def _confirm_episode(sess, key, active, now, confirm_seconds, event_type, confidence, extra=None):
    """
    Server-side temporal confirmation + one-event-per-continuous-episode +
    dedup, applied uniformly to every NEW (Tier 1/2) warning-tier signal.

    `sess["_integrity_state"][key]` tracks one signal's episode:
      - not present / inactive  -> nothing happening
      - "first_seen"            -> when `active` first became True
      - "confirmed"             -> whether this episode already produced a
                                    logged event (so it fires exactly once
                                    per continuous episode, not every frame)

    On recovery (active=False) the episode resets, so the SAME condition
    happening again later starts a fresh confirmation window and can log a
    new event -- this is the "cooldown/deduplication" + "recovers and
    occurs again" behavior the existing tab/camera/window violations
    already have, applied the same way here.

    This function only ever appends to sess["integrity_events"]; it never
    touches sess["violations"], so nothing routed through here can ever
    contribute to the 3-strike count (see integrity_config.NEVER_STRIKE_
    EVENT_TYPES for the matching hard guarantee on the violation route).

    Returns True exactly once, the moment an episode is newly confirmed
    (edge-triggered) -- callers use this to know when to surface a fresh
    toast/badge instead of on every single frame.
    """
    if sess is None:
        return False
    state = sess.setdefault("_integrity_state", {})
    ep = state.get(key)

    if not active:
        if ep is not None:
            state[key] = None
        return False

    if ep is None:
        state[key] = {"first_seen": now, "confirmed": False}
        return False

    if ep.get("confirmed"):
        return False

    if now - ep["first_seen"] >= confirm_seconds:
        ep["confirmed"] = True
        duration = round(now - ep["first_seen"], 1)
        events = sess.setdefault("integrity_events", [])
        events.append({
            "type": event_type,
            "severity": EVENT_SEVERITY.get(event_type, "info"),
            "confidence": confidence,
            "start_ts": ep["first_seen"],
            "end_ts": now,
            "duration_sec": duration,
            "timestamp": now,
            "details": extra or {},
        })
        return True

    return False


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

        now = time.time()

        # 1. Calculate luminance / brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        blur_score = _compute_blur_score(gray)
        is_blurry = blur_score < BLUR_VARIANCE_THRESHOLD

        # New Tier-1/2 telemetry that can run independently of whether a
        # face is found this frame: image quality + phone/object presence.
        # These NEVER affect face_detected/status/strike behavior below --
        # they are purely additive fields, confirmed server-side (see
        # _confirm_episode) before ever being logged as an event.
        new_events = []
        if _confirm_episode(sess, "blur", is_blurry, now, BLUR_CONFIRM_SECONDS,
                             STATE_BLURRY_IMAGE, confidence=None,
                             extra={"blur_score": round(blur_score, 1) if blur_score == blur_score else None}):
            new_events.append(STATE_BLURRY_IMAGE)

        phone_detected, phone_confidence = _detect_phone(frame)
        phone_strike = _confirm_episode(sess, "phone", phone_detected, now, PHONE_CONFIRM_SECONDS,
                                         STATE_PHONE_DETECTED, confidence=phone_confidence)
        if phone_strike:
            new_events.append(STATE_PHONE_DETECTED)

        # Check for extreme low light
        if brightness < SEVERE_LOW_LIGHT_THRESHOLD:
            print(f"[FACE] Low brightness: {brightness:.2f}")
            _confirm_episode(sess, "low_light", True, now, LOW_LIGHT_CONFIRM_SECONDS,
                              STATE_LOW_LIGHT, confidence=None,
                              extra={"brightness": round(brightness, 1)})
            result = _default("low_light", "low_light")
            _attach_quality(result, brightness, blur_score, is_blurry, phone_detected, phone_confidence, phone_strike)
            return result
        else:
            _confirm_episode(sess, "low_light", False, now, LOW_LIGHT_CONFIRM_SECONDS, STATE_LOW_LIGHT, confidence=None)

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

        valid_faces = _filter_valid_faces(faces, frame_area)
        valid_count = len(valid_faces)
        print(f"[FACE] brightness={brightness:.1f}, valid_count={valid_count}")

        # Case: No Face Detected
        if valid_count == 0:
            result = _default("no_face", "no_face")
            _attach_quality(result, brightness, blur_score, is_blurry, phone_detected, phone_confidence, phone_strike)
            return result

        # Case: Multiple Faces Detected -- confirm with a stricter re-detection
        # pass before reporting it (see _resolve_multi_face_count docstring).
        if valid_count > 1:
            strict_faces = face_cascade.detectMultiScale(
                gray_eq,
                scaleFactor=1.1,
                minNeighbors=MULTI_FACE_MIN_NEIGHBORS,
                minSize=(20, 20)
            )
            strict_valid = _filter_valid_faces(strict_faces, frame_area)
            confirmed_count = _resolve_multi_face_count(strict_valid)
            print(f"[FACE] multi-face candidate={valid_count}, confirmed={confirmed_count}")
            if confirmed_count > 1:
                result = _default("multiple_faces", "multiple_faces")
                _attach_quality(result, brightness, blur_score, is_blurry, phone_detected, phone_confidence, phone_strike)
                result["face_count"] = confirmed_count
                return result
            # Not confirmed -- fall through and treat as a single face using
            # the strongest single detection from the lenient pass.
            valid_faces = [max(valid_faces, key=lambda f: f[2] * f[3])]
            valid_count = 1

        # Exactly 1 Face Found! Check eyes & visibility
        x, y, w, h = valid_faces[0]
        face_roi = gray[y : y + int(h * 0.65), x : x + w]

        eyes = []
        if eye_cascade and not eye_cascade.empty():
            eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=1, minSize=(6, 6))

        eyes_visible = len(eyes) > 0

        # New Tier-1: face position (too far / too close / partially visible)
        position = _classify_face_position(x, y, w, h, frame_w, frame_h)
        position_state_map = {
            "too_far": STATE_FACE_TOO_FAR,
            "too_close": STATE_FACE_TOO_CLOSE,
            "partially_visible": STATE_FACE_PARTIALLY_VISIBLE,
        }
        for pos_key, pos_state in position_state_map.items():
            _confirm_episode(sess, f"position_{pos_key}", position == pos_key, now,
                              FACE_POSITION_CONFIRM_SECONDS, pos_state, confidence=None)

        # New Tier-2: approximate head pose (only computed once a single
        # face is already confirmed by the primary Haar path above).
        head_direction, yaw_deg, pitch_deg = _estimate_head_pose(frame, (x, y, w, h))
        head_state_map = {
            "left": STATE_HEAD_LEFT, "right": STATE_HEAD_RIGHT,
            "up": STATE_HEAD_UP, "down": STATE_HEAD_DOWN,
        }
        for dir_key, dir_state in head_state_map.items():
            _confirm_episode(sess, f"head_{dir_key}", head_direction == dir_key, now,
                              HEAD_POSE_CONFIRM_SECONDS, dir_state, confidence=None,
                              extra={"yaw_deg": yaw_deg, "pitch_deg": pitch_deg})

        # Check if lighting is dim
        if brightness < LOW_LIGHT_THRESHOLD:
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

        result = {
            "face_detected": face_detected,
            "status": status_state,
            "confidence": 0.90 if eyes_visible else 0.70,
            "dominant_emotion": "neutral",
            "interview_score": 75 if eyes_visible else 55,
            "emotions": {"neutral": 100.0},
            "eyes_visible": eyes_visible,
            "reason": reason,
            "face_count": 1,
            "face_position": position,
            "head_pose": {
                "direction": head_direction,
                "yaw_deg": yaw_deg,
                "pitch_deg": pitch_deg,
                "available": _yunet is not None,
            },
        }
        _attach_quality(result, brightness, blur_score, is_blurry, phone_detected, phone_confidence, phone_strike)
        if new_events:
            result["new_events"] = new_events
        return result

    except Exception as e:
        print(f"[EmotionDetector] Error: {e}")
        return _default("error", "no_face")


def _attach_quality(result: dict, brightness, blur_score, is_blurry, phone_detected, phone_confidence, phone_strike):
    """Additive-only telemetry attached to every response (Tier 1 fix for
    'no event duration/severity/timestamp metadata' -- see
    integrity_config.py / _confirm_episode for where the actual events get
    logged). Never overwrites any pre-existing top-level key."""
    result["quality"] = {
        "brightness": round(brightness, 1),
        "blur_score": round(blur_score, 1) if blur_score == blur_score else None,  # NaN check
        "blurry": bool(is_blurry),
    }
    result["phone"] = {
        "detected": bool(phone_detected),
        "confidence": phone_confidence,
        "confirmed_strike": bool(phone_strike),
        "available": _nanodet_net is not None,
    }
    result.setdefault("face_position", "unknown")
    result.setdefault("head_pose", {"direction": "unknown", "yaw_deg": None, "pitch_deg": None, "available": _yunet is not None})
    result.setdefault("face_count", 0)


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
