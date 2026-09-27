"""
Tests for the integrity report data-consistency fix.

These exercise modules/evaluator.py's generate_final_report() directly
against synthetic session dicts shaped exactly like what
backend/app.py's /api/integrity/violation route actually produces (see
that route + modules/emotion_detector.py's _confirm_episode), asserting
that the report's authoritative integrity fields (strike_count,
auto_terminated, termination_reason/trigger/time, integrity_events) can
never contradict each other or the underlying stored violations.

This directly covers the bug that was reported: a session terminated by
strike types the report UI had no card for (phone_detected,
fullscreen_exit) showed "0" on every visible counter while still
displaying an auto-termination message. These tests assert the fix at
the DATA layer (the authoritative fields the frontend now reads), since
the frontend itself needs a browser to exercise end-to-end.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.evaluator import generate_final_report


def _base_session(**overrides):
    sess = {
        "id": "sess-1",
        "status": "active",
        "technical_scores": [70],
        "voice_scores": [70],
        "emotion_timeline": [],
        "answers": [{"skill": "Python", "difficulty": "easy", "score": 70}],
        "violations": {"tab_switch": 0, "camera_exit": 0, "window_move": 0, "multiple_faces": 0, "total": 0},
        "integrity_events": [],
        "skills": ["Python"],
    }
    sess.update(overrides)
    return sess


def _strike_event(event_type, strike_number, ts=100.0):
    return {
        "type": event_type, "severity": "critical", "confidence": None,
        "start_ts": None, "end_ts": None, "duration_sec": None,
        "timestamp": ts, "details": {"strike_number": strike_number},
    }


def _warning_event(event_type, ts=50.0, duration=5.2, confidence=None):
    return {
        "type": event_type, "severity": "info", "confidence": confidence,
        "start_ts": ts - duration, "end_ts": ts, "duration_sec": duration,
        "timestamp": ts, "details": {},
    }


class TestReportIntegrityConsistency(unittest.TestCase):

    def test_1_zero_strikes_no_termination(self):
        sess = _base_session()
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 0)
        self.assertFalse(report["summary"]["auto_terminated"])
        self.assertFalse(report["terminated"])
        self.assertIsNone(report["summary"]["termination_reason"])

    def test_2_one_strike_no_termination(self):
        sess = _base_session(
            violations={"tab_switch": 0, "camera_exit": 0, "window_move": 1, "multiple_faces": 0, "total": 1},
            integrity_events=[_strike_event("WINDOW_MOVE", 1)],
        )
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 1)
        self.assertFalse(report["summary"]["auto_terminated"])
        self.assertFalse(report["terminated"])

    def test_3_two_strikes_no_termination(self):
        sess = _base_session(
            violations={"tab_switch": 1, "camera_exit": 0, "window_move": 1, "multiple_faces": 0, "total": 2},
            integrity_events=[_strike_event("TAB_SWITCH", 1), _strike_event("WINDOW_MOVE", 2)],
        )
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 2)
        self.assertFalse(report["summary"]["auto_terminated"])
        self.assertFalse(report["terminated"])

    def test_4_three_strikes_shows_termination_and_exact_trigger(self):
        sess = _base_session(
            status="terminated",
            violations={"tab_switch": 0, "camera_exit": 0, "window_move": 2, "multiple_faces": 0,
                        "phone_detected": 0, "fullscreen_exit": 1, "total": 3},
            integrity_events=[
                _strike_event("WINDOW_MOVE", 1, ts=10),
                _strike_event("WINDOW_MOVE", 2, ts=20),
                _strike_event("FULLSCREEN_EXIT", 3, ts=30),
            ],
            termination_reason="integrity_strike_limit",
            termination_trigger_event="fullscreen_exit",
            termination_time="2026-01-01T12:00:00Z",
        )
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 3)
        self.assertTrue(report["summary"]["auto_terminated"])
        self.assertTrue(report["terminated"])
        self.assertEqual(report["summary"]["termination_reason"], "integrity_strike_limit")
        self.assertEqual(report["summary"]["termination_trigger_event"], "fullscreen_exit")
        self.assertEqual(report["summary"]["termination_time"], "2026-01-01T12:00:00Z")

    def test_5_warnings_only_no_strikes_no_termination(self):
        sess = _base_session(
            violations={"tab_switch": 0, "camera_exit": 0, "window_move": 0, "multiple_faces": 0, "total": 0},
            integrity_events=[_warning_event("LOW_LIGHT"), _warning_event("BLURRY_IMAGE")],
        )
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 0)
        self.assertFalse(report["summary"]["auto_terminated"])
        # warnings must still be visible in the timeline data
        self.assertEqual(len(report["summary"]["integrity_events"]), 2)

    def test_6_two_strikes_plus_warning_no_termination(self):
        sess = _base_session(
            violations={"tab_switch": 2, "camera_exit": 0, "window_move": 0, "multiple_faces": 0, "total": 2},
            integrity_events=[
                _strike_event("TAB_SWITCH", 1), _strike_event("TAB_SWITCH", 2),
                _warning_event("LOW_LIGHT"),
            ],
        )
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 2)
        self.assertFalse(report["summary"]["auto_terminated"])

    def test_7_three_strikes_plus_warnings_shows_exact_three_counted_events(self):
        sess = _base_session(
            status="terminated",
            violations={"tab_switch": 1, "camera_exit": 0, "window_move": 0, "multiple_faces": 1,
                        "phone_detected": 1, "fullscreen_exit": 0, "total": 3},
            integrity_events=[
                _strike_event("TAB_SWITCH", 1, ts=10),
                _warning_event("LOW_LIGHT", ts=15),
                _strike_event("MULTIPLE_FACES", 2, ts=20),
                _warning_event("BLURRY_IMAGE", ts=25),
                _strike_event("PHONE_DETECTED", 3, ts=30),
            ],
            termination_reason="integrity_strike_limit",
            termination_trigger_event="phone_detected",
            termination_time="2026-01-01T12:05:00Z",
        )
        report = generate_final_report(sess)
        self.assertEqual(report["summary"]["strike_count"], 3)
        self.assertTrue(report["summary"]["auto_terminated"])
        events = report["summary"]["integrity_events"]
        strike_events = [e for e in events if (e.get("details") or {}).get("strike_number") is not None]
        self.assertEqual(len(strike_events), 3)
        self.assertEqual(sorted(e["details"]["strike_number"] for e in strike_events), [1, 2, 3])
        # 2 warnings must still be present, but never counted as strikes
        warning_events = [e for e in events if (e.get("details") or {}).get("strike_number") is None]
        self.assertEqual(len(warning_events), 2)

    def test_8_report_is_a_pure_function_of_session_state(self):
        sess = _base_session(
            status="terminated",
            violations={"tab_switch": 0, "camera_exit": 0, "window_move": 3, "multiple_faces": 0, "total": 3},
            integrity_events=[_strike_event("WINDOW_MOVE", 1), _strike_event("WINDOW_MOVE", 2), _strike_event("WINDOW_MOVE", 3)],
            termination_reason="integrity_strike_limit",
            termination_trigger_event="window_move",
            termination_time="2026-01-01T12:10:00Z",
        )
        report_a = generate_final_report(sess)
        report_b = generate_final_report(sess)
        self.assertEqual(report_a["summary"]["strike_count"], report_b["summary"]["strike_count"])
        self.assertEqual(report_a["summary"]["auto_terminated"], report_b["summary"]["auto_terminated"])
        self.assertEqual(report_a["terminated"], report_b["terminated"])

    def test_9_never_shows_termination_without_a_termination_record(self):
        # status is "active" (never actually terminated) even though, say,
        # a stray/legacy violations dict happens to have a high total --
        # the report must not claim termination without status=="terminated".
        sess = _base_session(
            violations={"tab_switch": 5, "camera_exit": 0, "window_move": 0, "multiple_faces": 0, "total": 5},
        )
        report = generate_final_report(sess)
        self.assertFalse(report["terminated"])
        self.assertFalse(report["summary"]["auto_terminated"])
        self.assertIsNone(report["summary"]["termination_reason"])

    def test_never_contradicts_zero_strikes_with_termination(self):
        # The exact bug reported: must be structurally impossible for
        # strike_count to be 0 while auto_terminated is True.
        sess = _base_session(status="active")
        report = generate_final_report(sess)
        if report["summary"]["strike_count"] == 0:
            self.assertFalse(report["summary"]["auto_terminated"])

    def test_hidden_violation_types_still_counted_in_strike_total(self):
        # Regression test for the actual root cause: a termination driven
        # entirely by violation types the OLD report UI had no card for.
        sess = _base_session(
            status="terminated",
            violations={"tab_switch": 0, "camera_exit": 0, "window_move": 0, "multiple_faces": 0,
                        "phone_detected": 2, "fullscreen_exit": 1, "total": 3},
            integrity_events=[
                _strike_event("PHONE_DETECTED", 1), _strike_event("PHONE_DETECTED", 2), _strike_event("FULLSCREEN_EXIT", 3),
            ],
            termination_reason="integrity_strike_limit",
            termination_trigger_event="fullscreen_exit",
        )
        report = generate_final_report(sess)
        # The legacy 4 counters are indeed all zero...
        v = report["summary"]["violations"]
        self.assertEqual(v.get("tab_switch", 0) + v.get("camera_exit", 0) + v.get("window_move", 0) + v.get("multiple_faces", 0), 0)
        # ...but the AUTHORITATIVE total is still 3, and termination is reported.
        self.assertEqual(report["summary"]["strike_count"], 3)
        self.assertTrue(report["summary"]["auto_terminated"])


if __name__ == "__main__":
    unittest.main()
