"""
Centralized configuration for the Face Analysis + Interview Integrity
Monitoring subsystem.

Every threshold, timing window, and severity/strike classification used by
the proctoring pipeline (backend/modules/emotion_detector.py,
/api/emotion/analyze, /api/integrity/violation, frontend/assets/js/emotion.js,
frontend/assets/js/integrity.js) is defined here instead of being scattered
as magic numbers across those files, so the whole system's behavior can be
tuned/audited from one place.

IMPORTANT -- no fabricated accuracy:
None of the detectors backing these thresholds are trained/calibrated ML
classifiers with a measured accuracy figure specific to this project. Face
detection is OpenCV Haar cascades (classical computer vision, no training
data of ours involved). Head-pose is an approximate geometric estimate
(solvePnP against a generic/textbook 3D face template, NOT calibrated to
each candidate's real face geometry). Phone detection is a general-purpose,
lightweight COCO object detector (NanoDet-Plus) whose own published
"cell phone" class accuracy is modest (AP50 33.7%, mAP 22.8% on COCO2017val
-- see backend/models/README.md for the source). The thresholds below are
heuristics chosen to keep false positives low, not outputs of a validation
study on real interview footage, and must never be described elsewhere in
the codebase or product copy as guaranteed-accurate or "trained for this
project."
"""

import os as _os

# ── Brightness / low light (existing values, unchanged) ─────────────────
SEVERE_LOW_LIGHT_THRESHOLD = 15.0   # Hard cutoff: too dark to attempt detection at all
LOW_LIGHT_THRESHOLD        = 28.0   # Soft cutoff: face may still be found but flagged

# ── Face size / shape sanity (existing values, unchanged) ────────────────
MIN_FACE_WIDTH       = 15
MIN_FACE_HEIGHT      = 15
MIN_FACE_AREA_RATIO  = 0.001

# ── Multiple-face confirmation (existing values, unchanged) ─────────────
MULTI_FACE_MIN_NEIGHBORS     = 7
MULTI_FACE_MIN_RELATIVE_AREA = 0.35

# ── Face position (new, Tier 1) ──────────────────────────────────────────
# Classifies an already-confirmed face by how much of the frame it fills and
# whether its box touches a frame edge. Heuristic, not a trained model.
FACE_TOO_FAR_AREA_RATIO   = 0.03   # face fills <3% of the frame -> likely too far away
FACE_TOO_CLOSE_AREA_RATIO = 0.50   # face fills >50% of the frame -> likely too close
FACE_EDGE_MARGIN_PX       = 4      # box within this many px of an edge -> partially out of frame

# ── Blur / image quality (new, Tier 1) ───────────────────────────────────
# Standard "variance of Laplacian" heuristic (cv2.Laplacian(...).var());
# lower variance = blurrier. Not a trained model.
BLUR_VARIANCE_THRESHOLD = 60.0

# ── Head pose (new, Tier 2) ──────────────────────────────────────────────
HEAD_POSE_YAW_CENTER_DEG   = 18.0   # |yaw| below this   -> "center"
HEAD_POSE_PITCH_CENTER_DEG = 15.0   # |pitch| below this -> "center"
HEAD_POSE_CONFIRM_SECONDS  = 6.0    # sustained (same non-center direction) span required
                                     # before a HEAD_* warning is ever logged -- a brief
                                     # natural glance never reaches this

# ── Phone / object detection (new, Tier 2) ───────────────────────────────
PHONE_MIN_CONFIDENCE  = 0.50        # NanoDet "cell phone" class score floor
PHONE_CONFIRM_SECONDS = 6.0         # sustained detection span required before PHONE_DETECTED fires

# ── Generic warning-event confirmation windows (new Tier-1 telemetry) ────
LOW_LIGHT_CONFIRM_SECONDS     = 6.0
BLUR_CONFIRM_SECONDS          = 6.0
FACE_POSITION_CONFIRM_SECONDS = 6.0

# ── Detection state name constants ───────────────────────────────────────
STATE_FACE_PRESENT           = "FACE_PRESENT"
STATE_FACE_ABSENT            = "FACE_ABSENT"
STATE_FACE_PARTIALLY_VISIBLE = "FACE_PARTIALLY_VISIBLE"
STATE_MULTIPLE_FACES         = "MULTIPLE_FACES"
STATE_FACE_TOO_FAR           = "FACE_TOO_FAR"
STATE_FACE_TOO_CLOSE         = "FACE_TOO_CLOSE"
STATE_FACE_OUT_OF_FRAME      = "FACE_OUT_OF_FRAME"
STATE_LOW_LIGHT              = "LOW_LIGHT"
STATE_SEVERE_LOW_LIGHT       = "SEVERE_LOW_LIGHT"
STATE_BLURRY_IMAGE           = "BLURRY_IMAGE"
STATE_CAMERA_UNAVAILABLE     = "CAMERA_UNAVAILABLE"
STATE_HEAD_LEFT              = "HEAD_LEFT"
STATE_HEAD_RIGHT             = "HEAD_RIGHT"
STATE_HEAD_UP                = "HEAD_UP"
STATE_HEAD_DOWN              = "HEAD_DOWN"
STATE_HEAD_CENTER            = "HEAD_CENTER"
STATE_HEAD_UNKNOWN           = "HEAD_UNKNOWN"
STATE_PHONE_DETECTED         = "PHONE_DETECTED"
STATE_FULLSCREEN_EXIT        = "FULLSCREEN_EXIT"
STATE_TAB_SWITCH             = "TAB_SWITCH"
STATE_WINDOW_FOCUS_LOST      = "WINDOW_FOCUS_LOST"

# ── Severity classification ──────────────────────────────────────────────
SEVERITY_INFO     = "info"
SEVERITY_WARNING  = "warning"
SEVERITY_CRITICAL = "critical"

EVENT_SEVERITY = {
    STATE_LOW_LIGHT:              SEVERITY_INFO,
    STATE_SEVERE_LOW_LIGHT:       SEVERITY_INFO,
    STATE_BLURRY_IMAGE:           SEVERITY_INFO,
    STATE_FACE_TOO_FAR:           SEVERITY_WARNING,
    STATE_FACE_TOO_CLOSE:         SEVERITY_WARNING,
    STATE_FACE_PARTIALLY_VISIBLE: SEVERITY_WARNING,
    STATE_FACE_OUT_OF_FRAME:      SEVERITY_WARNING,
    STATE_FACE_ABSENT:            SEVERITY_WARNING,
    STATE_MULTIPLE_FACES:         SEVERITY_CRITICAL,
    STATE_HEAD_LEFT:              SEVERITY_WARNING,
    STATE_HEAD_RIGHT:             SEVERITY_WARNING,
    STATE_HEAD_UP:                SEVERITY_WARNING,
    STATE_HEAD_DOWN:              SEVERITY_WARNING,
    STATE_PHONE_DETECTED:         SEVERITY_CRITICAL,
    STATE_FULLSCREEN_EXIT:        SEVERITY_CRITICAL,
    STATE_TAB_SWITCH:             SEVERITY_CRITICAL,
    STATE_WINDOW_FOCUS_LOST:      SEVERITY_CRITICAL,
}

# ── Strike classification ────────────────────────────────────────────────
# The ONLY violation types allowed to ever contribute to the 3-strike
# termination count. Everything else is informational/warning-tier and is
# only ever appended to the integrity_events log, never to
# sess["violations"]. tab_switch / camera_exit / window_move /
# multiple_faces are the pre-existing set (unchanged); fullscreen_exit and
# phone_detected are the two new additions, both reusing the exact same
# strike pipeline.
STRIKE_ELIGIBLE_VIOLATION_TYPES = {
    "tab_switch",
    "camera_exit",
    "window_move",
    "multiple_faces",
    "fullscreen_exit",
    "phone_detected",
}

# Defensive hard guarantee (enforced in /api/integrity/violation itself, not
# just by the frontend choosing which route to call): if any of these ever
# arrives as a violation "type", it is logged as an event and NEVER
# increments sess["violations"]. This is the concrete fix for "low light
# must never contribute to the 3-strike count."
NEVER_STRIKE_EVENT_TYPES = {
    "low_light", "severe_low_light", "blurry_image",
    "face_too_far", "face_too_close", "face_partially_visible",
    "face_out_of_frame",
    "head_left", "head_right", "head_up", "head_down",
}

# ── Tier-2 model file locations ──────────────────────────────────────────
_MODELS_DIR = _os.path.join(_os.path.dirname(__file__), "..", "models")
YUNET_MODEL_PATH   = _os.path.join(_MODELS_DIR, "face_detection_yunet_2023mar.onnx")
NANODET_MODEL_PATH = _os.path.join(_MODELS_DIR, "object_detection_nanodet_2022nov.onnx")
NANODET_INPUT_SIZE = (416, 416)
# Index of "cell phone" in NanoDet-Plus's own fixed 80-class COCO label
# list (contiguous 0-79 ordering as used by the model's official OpenCV Zoo
# demo.py -- NOT the raw/sparse COCO category-id numbering).
NANODET_PHONE_CLASS_INDEX = 67
