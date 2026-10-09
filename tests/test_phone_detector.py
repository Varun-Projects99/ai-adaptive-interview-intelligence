"""
test_phone_detector.py — Unit and Integration Tests for Mobile Phone Detector
InterviewIQ AI Adaptive Interview Intelligence System
"""

import sys
import os
import unittest
import numpy as np
import cv2

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from modules.integrity_monitor.phone_detector import detect_phone, PhoneDetector, PhoneDetectorStabilizer

class TestPhoneDetector(unittest.TestCase):

    def setUp(self):
        self.detector = PhoneDetector()
        self.stabilizer = PhoneDetectorStabilizer(confirm_frames=3, lost_frames=2, confidence_threshold=0.35)

    def test_01_no_phone_detection(self):
        """TEST 1: Blank frame without phone -> expected detected = False"""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        res = self.detector.detect(blank_frame)

        self.assertIn("detected", res)
        self.assertIn("confidence", res)
        self.assertIn("bbox", res)
        self.assertFalse(res["detected"])
        self.assertEqual(res["confidence"], 0.0)
        self.assertIsNone(res["bbox"])
        print("✓ Test 1 Passed: Blank frame correctly identified as no phone.")

    def test_02_synthetic_phone_detection_schema(self):
        """TEST 2: Verify detection payload schema compliance"""
        phone_frame = np.full((480, 640, 3), 150, dtype=np.uint8)
        cv2.rectangle(phone_frame, (200, 150), (320, 380), (30, 30, 30), -1)

        res = self.detector.detect(phone_frame)

        self.assertIsInstance(res["detected"], bool)
        self.assertIsInstance(res["confidence"], float)
        self.assertTrue(res["bbox"] is None or isinstance(res["bbox"], list))
        print("✓ Test 2 Passed: Payload schema verified successfully.")

    def test_03_temporal_stabilizer(self):
        """TEST 3 & 9: Verify temporal buffer confirmation and loss logic"""
        positive_res = {"detected": True, "confidence": 0.85, "bbox": [100, 100, 200, 300]}
        negative_res = {"detected": False, "confidence": 0.0, "bbox": None}

        # Frame 1: positive detection -> not confirmed yet (1/3)
        st1 = self.stabilizer.update(positive_res)
        self.assertFalse(st1["confirmed"])

        # Frame 2: positive detection -> not confirmed yet (2/3)
        st2 = self.stabilizer.update(positive_res)
        self.assertFalse(st2["confirmed"])

        # Frame 3: positive detection -> confirmed (3/3)!
        st3 = self.stabilizer.update(positive_res)
        self.assertTrue(st3["confirmed"])

        # Frame 4: miss 1 -> still confirmed (loss buffer 1/2)
        st4 = self.stabilizer.update(negative_res)
        self.assertTrue(st4["confirmed"])

        # Frame 5: miss 2 -> cleared (loss buffer 2/2)!
        st5 = self.stabilizer.update(negative_res)
        self.assertFalse(st5["confirmed"])

        print("✓ Test 3 Passed: Temporal stabilizer confirmed and cleared state correctly.")

    def test_04_detector_singleton(self):
        """Verify PhoneDetector maintains singleton instance"""
        d1 = PhoneDetector()
        d2 = PhoneDetector()
        self.assertIs(d1, d2)
        print("✓ Test 4 Passed: Singleton pattern verified.")

if __name__ == "__main__":
    unittest.main()
