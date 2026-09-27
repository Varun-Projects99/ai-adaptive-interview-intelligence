"""
Unit tests for the multiple-face confirmation logic in modules/emotion_detector.py.

These test the deterministic, rule-based filtering helpers directly (not real
webcam frames / OpenCV detection) -- they verify that a small "phantom" second
detection (the kind Haar-cascade face detection commonly hallucinates from
shadows, hair, or picture frames) gets discarded, while two genuinely
comparable face-sized detections are correctly confirmed as multiple faces.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.emotion_detector import _filter_valid_faces, _resolve_multi_face_count


class TestFilterValidFaces(unittest.TestCase):
    def test_drops_tiny_detections(self):
        frame_area = 320 * 240
        faces = [(10, 10, 100, 100), (5, 5, 3, 3)]  # 2nd is too small
        valid = _filter_valid_faces(faces, frame_area)
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0], (10, 10, 100, 100))

    def test_keeps_reasonably_sized_detections(self):
        frame_area = 320 * 240
        faces = [(10, 10, 80, 80), (150, 10, 70, 70)]
        valid = _filter_valid_faces(faces, frame_area)
        self.assertEqual(len(valid), 2)


class TestResolveMultiFaceCount(unittest.TestCase):
    def test_single_strict_survivor_is_not_multiple(self):
        # Only one face survives the strict re-detection pass -> not multiple.
        strict_valid = [(10, 10, 100, 100)]
        self.assertEqual(_resolve_multi_face_count(strict_valid), 1)

    def test_empty_strict_pass_is_not_multiple(self):
        self.assertEqual(_resolve_multi_face_count([]), 1)

    def test_phantom_small_second_face_is_discarded(self):
        # Main face 100x100=10000 area; "2nd face" only 30x30=900 area (9% of
        # main) -- far below the 35% relative-size threshold, so it's treated
        # as a false positive (e.g. a shadow or a poster corner), not a
        # genuine second person.
        strict_valid = [(10, 10, 100, 100), (200, 20, 30, 30)]
        self.assertEqual(_resolve_multi_face_count(strict_valid), 1)

    def test_two_comparable_faces_confirmed_as_multiple(self):
        # Two faces of similar size (100x100 and 80x80 -> 64% of main area,
        # above the 35% threshold) both survive strict detection -> genuinely
        # multiple people in frame.
        strict_valid = [(10, 10, 100, 100), (200, 10, 80, 80)]
        self.assertEqual(_resolve_multi_face_count(strict_valid), 2)

    def test_three_comparable_faces_confirmed(self):
        strict_valid = [(10, 10, 100, 100), (150, 10, 90, 90), (300, 10, 95, 95)]
        self.assertEqual(_resolve_multi_face_count(strict_valid), 3)


if __name__ == "__main__":
    unittest.main()
