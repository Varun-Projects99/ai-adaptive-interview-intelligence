"""
Unit tests for Proctoring System & Integrity Event Deduplication
"""

import os
import sys
import unittest
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.emotion_detector import _suppress_overlapping_faces, _filter_valid_faces
from modules.integrity_config import NEVER_STRIKE_EVENT_TYPES, STRIKE_ELIGIBLE_VIOLATION_TYPES

class TestProctoringIntegrity(unittest.TestCase):

    def test_overlap_suppression_single_face(self):
        # Multiple overlapping face bounding boxes for the same candidate face
        # (e.g. main box, eye region box, mouth region box)
        faces = [
            (100, 100, 150, 150), # Primary face box: area 22500
            (110, 110, 130, 130), # Overlapping box on same face: area 16900 (covers >80% of primary)
            (120, 120, 100, 100), # Another overlapping box on same face
        ]
        
        result = _suppress_overlapping_faces(faces, overlap_thresh=0.3)
        self.assertEqual(len(result), 1, "Overlapping feature boxes of 1 candidate must be merged into 1 face!")
        self.assertEqual(result[0], (100, 100, 150, 150))

    def test_overlap_suppression_two_distinct_faces(self):
        # Two distinct non-overlapping faces in frame
        faces = [
            (50, 50, 120, 120),  # Person 1
            (300, 50, 120, 120), # Person 2 (completely separate)
        ]
        
        result = _suppress_overlapping_faces(faces, overlap_thresh=0.3)
        self.assertEqual(len(result), 2, "Two non-overlapping distinct faces must yield 2 face boxes!")

    def test_strike_eligibility_classification(self):
        self.assertIn("low_light", NEVER_STRIKE_EVENT_TYPES)
        self.assertIn("blurry_image", NEVER_STRIKE_EVENT_TYPES)
        self.assertIn("tab_switch", STRIKE_ELIGIBLE_VIOLATION_TYPES)
        self.assertIn("camera_exit", STRIKE_ELIGIBLE_VIOLATION_TYPES)
        self.assertIn("multiple_faces", STRIKE_ELIGIBLE_VIOLATION_TYPES)
        self.assertIn("phone_detected", STRIKE_ELIGIBLE_VIOLATION_TYPES)


if __name__ == "__main__":
    unittest.main()
