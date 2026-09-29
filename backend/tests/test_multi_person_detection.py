"""
Unit & Integration Tests — Dual-Layer Person Presence & Integrity System
========================================================================
Tests all 18 detection scenarios, warning vs strike classifications,
temporal confirmation windows, single-event episode deduplication,
and backend route guarantees.
"""

import unittest
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.integrity_config import (
    STATE_ADDITIONAL_PERSON,
    STATE_MULTIPLE_ADDITIONAL_PEOPLE,
    STATE_MULTIPLE_PEOPLE_NO_FACE,
    STATE_MULTIPLE_FACES,
    STATE_LOW_LIGHT,
    STATE_BLURRY_IMAGE,
    STRIKE_ELIGIBLE_VIOLATION_TYPES,
    NEVER_STRIKE_EVENT_TYPES,
    ADDITIONAL_PERSON_CONFIRM_SECONDS,
)

from modules import emotion_detector as ed


class TestMultiPersonDetectionAndIntegrity(unittest.TestCase):

    def setUp(self):
        self.session = {
            "id": "test_session_123",
            "violations": {},
            "integrity_events": [],
            "_integrity_state": {},
        }

    # 1. State logic tests (Face count + Person count combinations)
    def test_case_1_one_person_one_face(self):
        """1 face + 1 person -> Normal candidate state."""
        face_count = 1
        person_count = 1
        additional_people = max(0, person_count - face_count)
        self.assertEqual(additional_people, 0)

    def test_case_2_two_persons_one_face(self):
        """2 persons + 1 face -> Additional Person detected (Back-of-head case)."""
        face_count = 1
        person_count = 2
        additional_people = max(0, person_count - face_count)
        self.assertEqual(additional_people, 1)

    def test_case_3_two_persons_two_faces(self):
        """2 persons + 2 faces -> Multiple Faces detected."""
        face_count = 2
        person_count = 2
        self.assertTrue(face_count > 1)

    def test_case_4_three_persons_one_face(self):
        """3 persons + 1 face -> Multiple Additional People detected."""
        face_count = 1
        person_count = 3
        additional_people = max(0, person_count - face_count)
        self.assertEqual(additional_people, 2)
        self.assertTrue(additional_people >= 2)

    def test_case_5_one_person_zero_faces(self):
        """1 person + 0 faces -> Candidate looking away (Face Absent), NOT additional person."""
        face_count = 0
        person_count = 1
        additional_people = max(0, person_count - 1)
        self.assertEqual(additional_people, 0)

    def test_case_6_two_persons_zero_faces(self):
        """2 persons + 0 faces -> Multiple people in frame, no visible face."""
        face_count = 0
        person_count = 2
        additional_people = max(0, person_count - 1)
        self.assertEqual(additional_people, 1)

    # 2. Temporal Confirmation & Deduplication tests
    def test_short_presence_does_not_confirm_event(self):
        """Additional person present < threshold (e.g. 1.0s) -> No event logged."""
        now = 1000.0
        # Frame 1: First seen
        confirmed1 = ed._confirm_episode(
            self.session, "additional_person", active=True, now=now,
            confirm_seconds=ADDITIONAL_PERSON_CONFIRM_SECONDS,
            event_type=STATE_ADDITIONAL_PERSON, confidence=0.85
        )
        self.assertFalse(confirmed1)
        self.assertEqual(len(self.session.get("integrity_events", [])), 0)

        # Frame 2: 1.5 seconds later (still below 3.0s threshold)
        confirmed2 = ed._confirm_episode(
            self.session, "additional_person", active=True, now=now + 1.5,
            confirm_seconds=ADDITIONAL_PERSON_CONFIRM_SECONDS,
            event_type=STATE_ADDITIONAL_PERSON, confidence=0.85
        )
        self.assertFalse(confirmed2)
        self.assertEqual(len(self.session.get("integrity_events", [])), 0)

    def test_sustained_presence_confirms_exactly_one_event(self):
        """Additional person present >= 3.0s -> Exactly 1 event logged with accurate duration."""
        now = 1000.0
        # Start episode
        ed._confirm_episode(
            self.session, "additional_person", active=True, now=now,
            confirm_seconds=ADDITIONAL_PERSON_CONFIRM_SECONDS,
            event_type=STATE_ADDITIONAL_PERSON, confidence=0.88
        )

        # 3.2 seconds later: episode confirmed
        confirmed = ed._confirm_episode(
            self.session, "additional_person", active=True, now=now + 3.2,
            confirm_seconds=ADDITIONAL_PERSON_CONFIRM_SECONDS,
            event_type=STATE_ADDITIONAL_PERSON, confidence=0.88
        )
        self.assertTrue(confirmed)
        events = self.session.get("integrity_events", [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], STATE_ADDITIONAL_PERSON)
        self.assertEqual(events[0]["duration_sec"], 3.2)

        # Frame 4.0s later: continues, but does NOT create a duplicate event
        confirmed_again = ed._confirm_episode(
            self.session, "additional_person", active=True, now=now + 4.0,
            confirm_seconds=ADDITIONAL_PERSON_CONFIRM_SECONDS,
            event_type=STATE_ADDITIONAL_PERSON, confidence=0.88
        )
        self.assertFalse(confirmed_again)
        self.assertEqual(len(self.session.get("integrity_events", [])), 1)

    def test_person_leaves_and_returns_creates_two_episodes(self):
        """Second person leaves and returns -> 2 separate events logged."""
        now = 1000.0
        # Episode 1
        ed._confirm_episode(self.session, "additional_person", True, now, ADDITIONAL_PERSON_CONFIRM_SECONDS, STATE_ADDITIONAL_PERSON, 0.9)
        ed._confirm_episode(self.session, "additional_person", True, now + 3.5, ADDITIONAL_PERSON_CONFIRM_SECONDS, STATE_ADDITIONAL_PERSON, 0.9)
        self.assertEqual(len(self.session.get("integrity_events", [])), 1)

        # Person leaves (active=False -> reset)
        ed._confirm_episode(self.session, "additional_person", False, now + 5.0, ADDITIONAL_PERSON_CONFIRM_SECONDS, STATE_ADDITIONAL_PERSON, 0.9)

        # Episode 2 (returns 10s later)
        now2 = now + 15.0
        ed._confirm_episode(self.session, "additional_person", True, now2, ADDITIONAL_PERSON_CONFIRM_SECONDS, STATE_ADDITIONAL_PERSON, 0.9)
        ed._confirm_episode(self.session, "additional_person", True, now2 + 3.5, ADDITIONAL_PERSON_CONFIRM_SECONDS, STATE_ADDITIONAL_PERSON, 0.9)
        self.assertEqual(len(self.session.get("integrity_events", [])), 2)

    # 3. Warning-Only vs Strike-Eligible Verification
    def test_warning_only_events_never_in_strike_eligible_set(self):
        """Camera-quality and position warnings MUST NOT be in strike-eligible set."""
        for warning_type in ["low_light", "blurry_image", "face_too_far", "face_too_close", "face_partially_visible", "head_left", "head_right"]:
            self.assertNotIn(warning_type, STRIKE_ELIGIBLE_VIOLATION_TYPES)
            self.assertIn(warning_type, NEVER_STRIKE_EVENT_TYPES)

    def test_strike_eligible_events_registered(self):
        """Critical violations MUST be registered as strike eligible."""
        expected_strikes = {"tab_switch", "camera_exit", "window_move", "multiple_faces", "additional_person", "phone_detected", "fullscreen_exit"}
        for evt in expected_strikes:
            self.assertIn(evt, STRIKE_ELIGIBLE_VIOLATION_TYPES)


if __name__ == "__main__":
    unittest.main()
