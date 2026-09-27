"""
Unit tests for the new Tier-1/Tier-2 Face & Integrity Monitoring logic in
modules/emotion_detector.py + modules/integrity_config.py.

These exercise the deterministic, rule-based pieces directly (face position
classification, blur heuristic, the severity/strike classification tables,
and the server-side temporal confirmation/dedup state machine) using
synthetic frames and a mocked clock -- not a live webcam. Real accuracy of
head-pose/phone detection on live footage cannot be validated in this
environment (no real interview footage available here); see
backend/models/README.md for that limitation.
"""
import os
import sys
import time
import base64
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import cv2

from modules import emotion_detector as ed
from modules.integrity_config import (
    NEVER_STRIKE_EVENT_TYPES, STRIKE_ELIGIBLE_VIOLATION_TYPES,
    EVENT_SEVERITY, STATE_LOW_LIGHT, STATE_BLURRY_IMAGE, STATE_PHONE_DETECTED,
)


def _b64(img):
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return base64.b64encode(buf).decode()


class TestSeverityAndStrikeClassification(unittest.TestCase):
    def test_never_strike_types_are_disjoint_from_strike_eligible(self):
        self.assertEqual(NEVER_STRIKE_EVENT_TYPES & STRIKE_ELIGIBLE_VIOLATION_TYPES, set())

    def test_low_light_is_never_strike_eligible(self):
        self.assertIn("low_light", NEVER_STRIKE_EVENT_TYPES)
        self.assertNotIn("low_light", STRIKE_ELIGIBLE_VIOLATION_TYPES)

    def test_phone_and_fullscreen_are_strike_eligible(self):
        self.assertIn("phone_detected", STRIKE_ELIGIBLE_VIOLATION_TYPES)
        self.assertIn("fullscreen_exit", STRIKE_ELIGIBLE_VIOLATION_TYPES)

    def test_every_severity_is_one_of_the_three_levels(self):
        for state, sev in EVENT_SEVERITY.items():
            self.assertIn(sev, ("info", "warning", "critical"), state)

    def test_low_light_and_blur_are_info_severity_never_critical(self):
        self.assertEqual(EVENT_SEVERITY[STATE_LOW_LIGHT], "info")
        self.assertEqual(EVENT_SEVERITY[STATE_BLURRY_IMAGE], "info")

    def test_phone_is_critical_severity(self):
        self.assertEqual(EVENT_SEVERITY[STATE_PHONE_DETECTED], "critical")


class TestFacePositionClassification(unittest.TestCase):
    def test_in_frame_face_is_in_frame(self):
        # 100x100 face centered in a 320x240 frame, comfortably away from edges
        pos = ed._classify_face_position(110, 70, 100, 100, 320, 240)
        self.assertEqual(pos, "in_frame")

    def test_tiny_face_is_too_far(self):
        pos = ed._classify_face_position(150, 110, 20, 20, 320, 240)  # ~0.5% of frame
        self.assertEqual(pos, "too_far")

    def test_huge_face_is_too_close(self):
        pos = ed._classify_face_position(20, 10, 280, 220, 320, 240)  # ~80% of frame
        self.assertEqual(pos, "too_close")

    def test_edge_touching_face_is_partially_visible(self):
        pos = ed._classify_face_position(0, 70, 100, 100, 320, 240)  # x touches left edge
        self.assertEqual(pos, "partially_visible")


class TestBlurScore(unittest.TestCase):
    def test_sharp_vs_blurry_ordering(self):
        rng = np.random.default_rng(0)
        sharp = (rng.random((200, 200)) * 255).astype(np.uint8)  # high-frequency noise = "sharp"
        blurry = cv2.GaussianBlur(sharp, (25, 25), 0)
        sharp_score = ed._compute_blur_score(sharp)
        blurry_score = ed._compute_blur_score(blurry)
        self.assertGreater(sharp_score, blurry_score)


class TestTemporalConfirmationAndDedup(unittest.TestCase):
    """Exercises _confirm_episode directly with a controlled fake clock --
    this is the mechanism behind 'sustained condition only', 'one event per
    continuous episode', and 'recovers and occurs again -> new event'."""

    def test_no_event_before_confirm_window_elapses(self):
        sess = {}
        self.assertFalse(ed._confirm_episode(sess, "k", True, 0.0, 6.0, "X", None))
        self.assertFalse(ed._confirm_episode(sess, "k", True, 3.0, 6.0, "X", None))
        self.assertEqual(sess.get("integrity_events", []), [])

    def test_event_fires_exactly_once_after_confirm_window(self):
        sess = {}
        ed._confirm_episode(sess, "k", True, 0.0, 6.0, "X", None)
        fired = ed._confirm_episode(sess, "k", True, 7.0, 6.0, "X", None)
        self.assertTrue(fired)
        self.assertEqual(len(sess["integrity_events"]), 1)
        # still active, same episode -> must not fire again
        fired_again = ed._confirm_episode(sess, "k", True, 10.0, 6.0, "X", None)
        self.assertFalse(fired_again)
        self.assertEqual(len(sess["integrity_events"]), 1)

    def test_recovery_then_reoccurrence_logs_a_second_independent_event(self):
        sess = {}
        ed._confirm_episode(sess, "k", True, 0.0, 6.0, "X", None)
        ed._confirm_episode(sess, "k", True, 7.0, 6.0, "X", None)
        self.assertEqual(len(sess["integrity_events"]), 1)
        # recovery
        ed._confirm_episode(sess, "k", False, 8.0, 6.0, "X", None)
        self.assertIsNone(sess["_integrity_state"]["k"])
        # re-occurrence -- fresh window, must not immediately re-fire
        ed._confirm_episode(sess, "k", True, 9.0, 6.0, "X", None)
        self.assertEqual(len(sess["integrity_events"]), 1)
        fired = ed._confirm_episode(sess, "k", True, 16.0, 6.0, "X", None)
        self.assertTrue(fired)
        self.assertEqual(len(sess["integrity_events"]), 2)

    def test_never_touches_violations_dict(self):
        sess = {"violations": {"total": 0}}
        ed._confirm_episode(sess, "k", True, 0.0, 6.0, "X", None)
        ed._confirm_episode(sess, "k", True, 7.0, 6.0, "X", None)
        self.assertEqual(sess["violations"]["total"], 0)

    def test_sess_none_is_a_safe_noop(self):
        # analyze_emotion_frame(frame) with no session (e.g. check_face_present)
        # must not crash even though confirmation state has nowhere to live.
        self.assertFalse(ed._confirm_episode(None, "k", True, 0.0, 6.0, "X", None))


class TestAnalyzeEmotionFrameEndToEnd(unittest.TestCase):
    def test_severe_low_light_never_populates_violations(self):
        dark = np.zeros((240, 320, 3), dtype=np.uint8) + 5
        sess = {}
        result = ed.analyze_emotion_frame(_b64(dark), sess=sess)
        self.assertEqual(result["status"], "low_light")
        self.assertNotIn("violations", sess)

    def test_no_face_frame_reports_zero_face_count(self):
        rng = np.random.default_rng(1)
        noise = (rng.random((240, 320, 3)) * 255).astype(np.uint8)
        result = ed.analyze_emotion_frame(_b64(noise), sess={})
        self.assertFalse(result["face_detected"])
        self.assertEqual(result.get("face_count"), 0)

    def test_response_always_has_additive_quality_fields_without_removing_old_keys(self):
        rng = np.random.default_rng(2)
        noise = (rng.random((240, 320, 3)) * 255).astype(np.uint8)
        result = ed.analyze_emotion_frame(_b64(noise), sess={})
        # Pre-existing keys (contract with emotion.js / evaluator.py) must
        # still all be present.
        for key in ("face_detected", "status", "confidence", "dominant_emotion",
                    "interview_score", "emotions", "reason"):
            self.assertIn(key, result)
        # New additive keys.
        for key in ("quality", "phone", "face_position", "head_pose", "face_count"):
            self.assertIn(key, result)

    def test_graceful_degrade_when_tier2_models_missing(self):
        # Point both Tier-2 model paths somewhere that doesn't exist and
        # confirm analyze_emotion_frame degrades to "unknown"/"not detected"
        # instead of raising. Patched on the emotion_detector module itself
        # (its own `from ... import NAME` binding), not on integrity_config,
        # since a plain `from module import NAME` copies the reference at
        # import time rather than keeping a live link back to the source
        # module's attribute.
        old_yunet, old_nano = ed.YUNET_MODEL_PATH, ed.NANODET_MODEL_PATH
        old_yunet_loaded, old_nano_loaded = ed._yunet, ed._nanodet_net
        old_yunet_attempted, old_nano_attempted = ed._yunet_load_attempted, ed._nanodet_load_attempted
        try:
            ed.YUNET_MODEL_PATH = "/nonexistent/yunet.onnx"
            ed.NANODET_MODEL_PATH = "/nonexistent/nanodet.onnx"
            ed._yunet = None
            ed._nanodet_net = None
            ed._yunet_load_attempted = False
            ed._nanodet_load_attempted = False
            rng = np.random.default_rng(3)
            noise = (rng.random((240, 320, 3)) * 255).astype(np.uint8)
            result = ed.analyze_emotion_frame(_b64(noise), sess={})
            self.assertEqual(result["head_pose"]["direction"], "unknown")
            self.assertFalse(result["phone"]["detected"])
            self.assertFalse(result["phone"]["available"])
        finally:
            ed.YUNET_MODEL_PATH, ed.NANODET_MODEL_PATH = old_yunet, old_nano
            ed._yunet, ed._nanodet_net = old_yunet_loaded, old_nano_loaded
            ed._yunet_load_attempted, ed._nanodet_load_attempted = old_yunet_attempted, old_nano_attempted


if __name__ == "__main__":
    unittest.main()
