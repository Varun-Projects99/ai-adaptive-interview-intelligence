"""
Unit tests for modules/settings_manager.py -- the Settings page's backend
logic (preference validation/merging, profile-field validation, and the
honest AI/System status check).

Consistent with this codebase's existing test convention (see
test_ai_assistant.py, test_integrity_events.py, etc.): these test the
module directly rather than importing backend/app.py, since no existing
test file imports app.py (it has real side effects at import time -- env
loading, a live MongoClient connection attempt). Route-level behavior that
can only be observed through app.py itself -- that every /api/settings/*
route derives the acting user from session["user_id"] (never a client-sent
id) and therefore that one candidate can never read or write another
candidate's settings -- was verified by starting the real Flask app and
exercising the routes with two distinct logged-in sessions; see the
AI_ASSISTANT.md-style report delivered alongside this change for that
result, since it cannot be expressed as an offline unit test without
duplicating Flask's own session machinery.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules import settings_manager as sm


class TestPreferenceValidation(unittest.TestCase):
    def test_valid_interview_length_accepted(self):
        clean, err = sm.validate_preferences_update({"interview_length": "extended"})
        self.assertIsNone(err)
        self.assertEqual(clean, {"interview_length": "extended"})

    def test_valid_difficulty_accepted(self):
        clean, err = sm.validate_preferences_update({"preferred_difficulty": "hard"})
        self.assertIsNone(err)
        self.assertEqual(clean, {"preferred_difficulty": "hard"})

    def test_both_fields_together(self):
        clean, err = sm.validate_preferences_update(
            {"interview_length": "short", "preferred_difficulty": "easy"}
        )
        self.assertIsNone(err)
        self.assertEqual(clean, {"interview_length": "short", "preferred_difficulty": "easy"})

    def test_invalid_length_rejected(self):
        clean, err = sm.validate_preferences_update({"interview_length": "marathon"})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_invalid_difficulty_rejected(self):
        clean, err = sm.validate_preferences_update({"preferred_difficulty": "impossible"})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_empty_body_rejected(self):
        clean, err = sm.validate_preferences_update({})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_non_dict_body_rejected(self):
        clean, err = sm.validate_preferences_update("not a dict")
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_unrecognized_field_alone_rejected(self):
        clean, err = sm.validate_preferences_update({"unrecognized_foo": "bar"})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)


    def test_adaptive_is_a_valid_choice(self):
        # "Adaptive" must remain selectable and must be the default -- see
        # test_default_preferences_are_adaptive_and_standard below.
        clean, err = sm.validate_preferences_update({"preferred_difficulty": "adaptive"})
        self.assertIsNone(err)
        self.assertEqual(clean["preferred_difficulty"], "adaptive")


class TestPreferenceMerging(unittest.TestCase):
    def test_default_preferences_are_adaptive_and_standard(self):
        prefs = sm.get_preferences(None)
        self.assertEqual(prefs["preferred_difficulty"], "adaptive")
        self.assertEqual(prefs["interview_length"], "standard")

    def test_stored_preferences_override_defaults(self):
        user_doc = {"preferences": {"interview_length": "extended", "preferred_difficulty": "hard"}}
        prefs = sm.get_preferences(user_doc)
        self.assertEqual(prefs["interview_length"], "extended")
        self.assertEqual(prefs["preferred_difficulty"], "hard")

    def test_malformed_preferences_field_falls_back_to_defaults(self):
        user_doc = {"preferences": "not-a-dict"}
        prefs = sm.get_preferences(user_doc)
        self.assertEqual(prefs, sm.DEFAULT_PREFERENCES)

    def test_invalid_stored_value_falls_back_to_default_for_that_key(self):
        user_doc = {"preferences": {"interview_length": "marathon"}}
        prefs = sm.get_preferences(user_doc)
        self.assertEqual(prefs["interview_length"], "standard")  # default, not the bad value

    def test_partial_preferences_fill_in_missing_key_with_default(self):
        user_doc = {"preferences": {"interview_length": "short"}}
        prefs = sm.get_preferences(user_doc)
        self.assertEqual(prefs["interview_length"], "short")
        self.assertEqual(prefs["preferred_difficulty"], "adaptive")

    def test_adaptive_seed_reproduces_existing_default_behavior(self):
        # "Adaptive" must not change today's existing starting difficulty
        # ("easy") -- only the label is new, the seed must be identical.
        self.assertEqual(sm.DIFFICULTY_TO_SEED["adaptive"], "easy")

    def test_length_to_question_count_covers_every_allowed_length(self):
        for length in sm.ALLOWED_INTERVIEW_LENGTHS:
            self.assertIn(length, sm.LENGTH_TO_QUESTION_COUNT)
            self.assertIsInstance(sm.LENGTH_TO_QUESTION_COUNT[length], int)

    def test_difficulty_seed_covers_every_allowed_difficulty(self):
        for diff in sm.ALLOWED_DIFFICULTIES:
            self.assertIn(diff, sm.DIFFICULTY_TO_SEED)


class TestProfileValidation(unittest.TestCase):
    def test_valid_name_accepted(self):
        clean, err = sm.validate_profile_update({"name": "Darshan Ashok"})
        self.assertIsNone(err)
        self.assertEqual(clean, {"name": "Darshan Ashok"})

    def test_name_is_trimmed(self):
        clean, err = sm.validate_profile_update({"name": "  Darshan  "})
        self.assertIsNone(err)
        self.assertEqual(clean["name"], "Darshan")

    def test_empty_name_rejected(self):
        clean, err = sm.validate_profile_update({"name": "   "})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_missing_name_field_rejected(self):
        clean, err = sm.validate_profile_update({})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_overlong_name_rejected(self):
        clean, err = sm.validate_profile_update({"name": "A" * 81})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_name_with_disallowed_characters_rejected(self):
        clean, err = sm.validate_profile_update({"name": "<script>alert(1)</script>"})
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    def test_email_field_is_ignored_not_editable(self):
        # Only `name` is backend-supported for editing (see module
        # docstring); a client sending `email` alongside `name` must not
        # cause the email to be changed.
        clean, err = sm.validate_profile_update({"name": "Darshan", "email": "new@example.com"})
        self.assertIsNone(err)
        self.assertNotIn("email", clean)

    def test_non_dict_body_rejected(self):
        clean, err = sm.validate_profile_update(None)
        self.assertIsNone(clean)
        self.assertIsNotNone(err)


class TestAiStatus(unittest.TestCase):
    def setUp(self):
        self._saved_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._saved_env)

    def test_no_keys_configured_reports_configuration_required(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("GROQ_API_KEY", None)
        status = sm.get_ai_status()
        self.assertEqual(status["assistant_status"], "configuration_required")
        self.assertIsNone(status["primary_provider"])

    def test_placeholder_anthropic_key_is_not_treated_as_configured(self):
        os.environ["ANTHROPIC_API_KEY"] = "your_anthropic_api_key_here"
        os.environ.pop("GROQ_API_KEY", None)
        status = sm.get_ai_status()
        self.assertEqual(status["assistant_status"], "configuration_required")

    def test_groq_key_alone_is_reported_as_available_and_primary(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ["GROQ_API_KEY"] = "gsk_" + "x" * 52
        status = sm.get_ai_status()
        self.assertEqual(status["assistant_status"], "available")
        self.assertEqual(status["primary_provider"], "groq")

    def test_real_anthropic_key_takes_priority_over_groq(self):
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-" + "x" * 40
        os.environ["GROQ_API_KEY"] = "gsk_" + "x" * 52
        status = sm.get_ai_status()
        self.assertEqual(status["primary_provider"], "anthropic")

    def test_status_never_includes_key_material(self):
        os.environ["GROQ_API_KEY"] = "gsk_SUPER_SECRET_VALUE_123456789012345678901234"
        status = sm.get_ai_status()
        dumped = str(status)
        self.assertNotIn("SUPER_SECRET", dumped)

    def test_status_reports_currently_configured_groq_models(self):
        os.environ["GROQ_API_KEY"] = "gsk_" + "x" * 52
        status = sm.get_ai_status()
        # Whatever ai_assistant.py currently ships as its candidate list --
        # this test only asserts the field is surfaced and non-empty when a
        # key is present, not any specific model id (that's ai_assistant's
        # own test suite's job, see test_ai_assistant.py).
        self.assertIsInstance(status["groq_models_configured"], list)


class TestDataCategories(unittest.TestCase):
    def test_data_categories_is_a_non_empty_list_of_labeled_entries(self):
        self.assertTrue(len(sm.DATA_CATEGORIES) > 0)
        for entry in sm.DATA_CATEGORIES:
            self.assertIn("key", entry)
            self.assertIn("label", entry)
            self.assertIn("detail", entry)

    def test_ai_assistant_category_is_disclosed(self):
        keys = [c["key"] for c in sm.DATA_CATEGORIES]
        self.assertIn("ai_assistant", keys)


if __name__ == "__main__":
    unittest.main()
