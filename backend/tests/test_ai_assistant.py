"""
Unit tests for the new InterviewIQ AI Assistant (modules/ai_assistant.py)
and its Flask routes (backend/app.py: /ai-assistant, /api/ai-assistant/chat).

These test the deterministic, offline-testable pieces directly: intent
routing, the candidate-context builder's data-isolation and honesty
behavior, rate limiting, input validation, and the Anthropic-then-Groq
provider fallback -- using fake in-memory Mongo-like collections and fake
provider SDK modules rather than a live database or live network calls
(consistent with the existing backend/tests/test_integrity_events.py,
which uses synthetic frames + a mocked clock rather than a live webcam).
"""
import io
import os
import sys
import types
import unittest
import contextlib
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules import ai_assistant as aa


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeCollection:
    """Minimal stand-in for a pymongo Collection, recording every query
    filter it is called with so tests can assert data isolation (every
    query must be scoped to the correct user_id, never another user's)."""

    def __init__(self, docs=None):
        self.docs = docs or []
        self.calls = []

    def find_one(self, query, sort=None):
        self.calls.append(("find_one", query, sort))
        for d in self.docs:
            if all(d.get(k) == v for k, v in query.items()):
                return d
        return None

    def update_one(self, filter_, update, upsert=False):
        self.calls.append(("update_one", filter_, update, upsert))

    def delete_many(self, query):
        self.calls.append(("delete_many", query))
        matched = [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]
        self.docs = [d for d in self.docs if d not in matched]

        class _Result:
            deleted_count = len(matched)
        return _Result()


class FakeQuestionBank:
    def __init__(self, pool):
        self.pool = pool
        self.calls = []

    def pool_for_skills(self, skills, target_total=24, per_difficulty=8):
        self.calls.append((skills, target_total, per_difficulty))
        return self.pool[:target_total], {"easy": 0, "medium": 0, "hard": 0}


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

class TestClassifyIntent(unittest.TestCase):
    def test_project_feature(self):
        self.assertEqual(aa.classify_intent("What is InterviewIQ?"), "PROJECT_FEATURE")

    def test_adaptive_difficulty(self):
        self.assertEqual(aa.classify_intent("Why did my interview become harder?"), "ADAPTIVE_DIFFICULTY")

    def test_resume_skill_order_independent(self):
        # "skill" appears BEFORE "resume" here -- a naive left-to-right
        # phrase match would miss this.
        self.assertEqual(aa.classify_intent("What skills did my resume contain?"), "RESUME")
        self.assertEqual(aa.classify_intent("What does my resume's skill section say?"), "RESUME")

    def test_integrity(self):
        self.assertEqual(aa.classify_intent("How does the integrity monitor work?"), "INTEGRITY")
        self.assertEqual(aa.classify_intent("What happens after 3 integrity strikes?"), "INTEGRITY")

    def test_interview_performance_non_adjacent(self):
        # "my" and "performance" are not adjacent -- must still match.
        self.assertEqual(aa.classify_intent("Explain my latest interview performance"), "INTERVIEW_PERFORMANCE")

    def test_learning_weak_areas_plural(self):
        self.assertEqual(aa.classify_intent("What are my weak areas?"), "LEARNING")

    def test_general_technical_fallback(self):
        self.assertEqual(aa.classify_intent("Explain polymorphism"), "GENERAL_TECHNICAL")

    def test_empty_message_is_general_technical(self):
        self.assertEqual(aa.classify_intent(""), "GENERAL_TECHNICAL")

    def test_is_personal_intent(self):
        self.assertTrue(aa.is_personal_intent("INTERVIEW_PERFORMANCE"))
        self.assertTrue(aa.is_personal_intent("RESUME"))
        self.assertFalse(aa.is_personal_intent("GENERAL_TECHNICAL"))
        self.assertFalse(aa.is_personal_intent("PROJECT_FEATURE"))

    def test_datasets_intent(self):
        self.assertEqual(aa.classify_intent("Does InterviewIQ use datasets?"), "DATASETS")
        self.assertEqual(aa.classify_intent("Where do interview questions come from?"), "DATASETS")
        self.assertEqual(aa.classify_intent("Is the question generation completely AI-generated?"), "DATASETS")

    def test_database_intent(self):
        self.assertEqual(aa.classify_intent("What information does InterviewIQ store?"), "DATABASE")
        self.assertEqual(aa.classify_intent("Does InterviewIQ use MongoDB?"), "DATABASE")

    def test_ai_architecture_intent(self):
        self.assertEqual(aa.classify_intent("How is AI used in InterviewIQ?"), "AI_ARCHITECTURE")
        self.assertEqual(aa.classify_intent("What happens if the AI provider is unavailable?"), "AI_ARCHITECTURE")
        self.assertEqual(aa.classify_intent("Does InterviewIQ use Claude or Groq?"), "AI_ARCHITECTURE")

    def test_datasets_intent_not_confused_with_general(self):
        # These must attach real project knowledge, not fall through to
        # GENERAL_INTERVIEW/GENERAL_TECHNICAL (which attach none).
        self.assertNotIn(aa.classify_intent("Where do interview questions come from?"),
                          ("GENERAL_INTERVIEW", "GENERAL_TECHNICAL"))
        self.assertNotIn(aa.classify_intent("What technologies are used?"),
                          ("GENERAL_INTERVIEW", "GENERAL_TECHNICAL"))


# ---------------------------------------------------------------------------
# Knowledge-base self-consistency (Step 24 -- "if the knowledge base says a
# feature exists but the code does not, fix the knowledge base" implies the
# reverse invariant too: every knowledge key referenced by an intent must
# actually exist).
# ---------------------------------------------------------------------------

class TestKnowledgeBaseConsistency(unittest.TestCase):
    def test_all_referenced_knowledge_keys_exist(self):
        for intent, keys in aa._INTENT_KNOWLEDGE_KEYS.items():
            for k in keys:
                self.assertIn(k, aa.PROJECT_KNOWLEDGE, f"{intent} references missing knowledge key {k!r}")

    def test_no_fake_claim_phrases_asserted_as_true_in_project_knowledge(self):
        # SYSTEM_RULES is allowed to NAME these phrases in order to forbid
        # them (rule 7 below) -- what must never happen is PROJECT_KNOWLEDGE
        # itself asserting one of these as a true claim about InterviewIQ.
        banned = ["100% accurate", "always verified", "guaranteed correct",
                  "detects cheating with certainty", "understands emotions perfectly"]
        for phrase in banned:
            for key, text in aa.PROJECT_KNOWLEDGE.items():
                self.assertNotIn(phrase.lower(), text.lower(), f"{key!r} asserts banned phrase {phrase!r}")

    def test_system_rules_explicitly_forbids_fake_claim_phrases(self):
        for phrase in ["100% accurate", "always verified", "guaranteed correct", "detects cheating with certainty"]:
            self.assertIn(phrase.lower(), aa.SYSTEM_RULES.lower())


# ---------------------------------------------------------------------------
# Candidate context builder -- data isolation & honesty
# ---------------------------------------------------------------------------

class TestBuildCandidateContext(unittest.TestCase):
    def test_non_personal_intent_returns_empty(self):
        self.assertEqual(aa.build_candidate_context("user-1", "GENERAL_TECHNICAL"), "")
        self.assertEqual(aa.build_candidate_context("user-1", "PROJECT_FEATURE"), "")

    def test_missing_user_id_returns_empty(self):
        self.assertEqual(aa.build_candidate_context(None, "INTERVIEW_PERFORMANCE"), "")

    def test_honest_when_no_data_stored(self):
        with mock.patch.object(aa, "reports_col", FakeCollection([])), \
             mock.patch.object(aa, "profiles_col", FakeCollection([])), \
             mock.patch.object(aa, "progress_col", FakeCollection([])):
            ctx = aa.build_candidate_context("user-1", "INTERVIEW_PERFORMANCE")
            self.assertIn("No stored", ctx)
            # must never fabricate a score when there is none
            self.assertNotIn("score:", ctx.lower())

    def test_uses_only_the_requesting_users_report(self):
        report_a = {
            "user_id": "user-A", "status": "completed",
            "report": {"scores": {"technical": 90, "confidence": 80, "readiness_index": 88, "readiness_label": "Interview Ready"},
                       "summary": {"skills_covered": ["Python"], "violations": {}},
                       "skill_scores": {"Python": 90}, "weak_areas": [], "strong_areas": ["Python"]},
        }
        report_b = {
            "user_id": "user-B", "status": "completed",
            "report": {"scores": {"technical": 20, "confidence": 15, "readiness_index": 18, "readiness_label": "Early Stage"},
                       "summary": {"skills_covered": ["Java"], "violations": {}},
                       "skill_scores": {"Java": 20}, "weak_areas": ["Java"], "strong_areas": []},
        }
        fake_reports = FakeCollection([report_a, report_b])
        with mock.patch.object(aa, "reports_col", fake_reports), \
             mock.patch.object(aa, "profiles_col", FakeCollection([])), \
             mock.patch.object(aa, "progress_col", FakeCollection([])):
            ctx = aa.build_candidate_context("user-A", "INTERVIEW_PERFORMANCE")
            self.assertIn("90", ctx)
            self.assertNotIn("Java", ctx)  # never leaks user-B's data
            # verify the actual Mongo filter used real isolation, not a
            # coincidence of list order
            find_calls = [c for c in fake_reports.calls if c[0] == "find_one"]
            self.assertEqual(find_calls[0][1], {"user_id": "user-A", "status": "completed"})

    def test_resume_intent_lists_stored_skills_or_says_none(self):
        profile = {"user_id": "user-1", "skills": {"Python": {}, "SQL": {}}}
        with mock.patch.object(aa, "profiles_col", FakeCollection([profile])):
            ctx = aa.build_candidate_context("user-1", "RESUME")
            self.assertIn("Python", ctx)
            self.assertIn("SQL", ctx)

        with mock.patch.object(aa, "profiles_col", FakeCollection([])):
            ctx = aa.build_candidate_context("user-1", "RESUME")
            self.assertIn("No stored skill data", ctx)


# ---------------------------------------------------------------------------
# Practice-question dataset reuse (Step 9)
# ---------------------------------------------------------------------------

class TestPracticeQuestions(unittest.TestCase):
    def test_non_practice_message_returns_none(self):
        self.assertIsNone(aa.get_practice_questions("user-1", "What is InterviewIQ?"))

    def test_practice_request_with_named_skill_uses_dataset(self):
        fake_bank = FakeQuestionBank([
            {"question": "What is a Python decorator?", "difficulty_label": "medium", "skill": "Python"},
            {"question": "Explain GIL.", "difficulty_label": "hard", "skill": "Python"},
        ])
        with mock.patch.object(aa, "question_bank", fake_bank):
            block = aa.get_practice_questions("user-1", "Give me 2 Python questions")
            self.assertIsNotNone(block)
            self.assertIn("decorator", block)
            self.assertIn("Python", fake_bank.calls[0][0])

    def test_practice_request_never_invents_when_no_dataset_skill_resolved(self):
        # No named skill and no stored weak areas to fall back to.
        with mock.patch.object(aa, "reports_col", FakeCollection([])):
            block = aa.get_practice_questions("user-1", "Give me some interview questions")
            self.assertIsNone(block)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimit(unittest.TestCase):
    def test_allows_up_to_the_limit_then_blocks(self):
        aa._rate_state.clear()
        user = "rl-test-user"
        for _ in range(aa.RATE_LIMIT_MAX_REQUESTS):
            allowed, _ = aa.check_rate_limit(user)
            self.assertTrue(allowed)
        allowed, retry_after = aa.check_rate_limit(user)
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_rate_limit_is_per_user(self):
        aa._rate_state.clear()
        for _ in range(aa.RATE_LIMIT_MAX_REQUESTS):
            aa.check_rate_limit("user-a")
        allowed, _ = aa.check_rate_limit("user-b")
        self.assertTrue(allowed)


# ---------------------------------------------------------------------------
# Input validation (handle_chat_message)
# ---------------------------------------------------------------------------

class TestHandleChatMessageValidation(unittest.TestCase):
    def test_empty_message_raises(self):
        with self.assertRaises(ValueError):
            aa.handle_chat_message("user-1", "   ")

    def test_oversized_message_raises(self):
        huge = "a" * (aa.MAX_MESSAGE_LENGTH + 1)
        with self.assertRaises(ValueError):
            aa.handle_chat_message("user-1", huge)

    def test_provider_failure_raises_assistant_provider_error(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": ""}, clear=False), \
             mock.patch.object(aa, "conversations_col", None):
            with self.assertRaises(aa.AssistantProviderError):
                aa.handle_chat_message("user-1", "Hello there")


# ---------------------------------------------------------------------------
# AI provider fallback (Anthropic primary -> Groq fallback), using fake SDK
# modules instead of real network calls.
# ---------------------------------------------------------------------------

class TestProviderFallback(unittest.TestCase):
    def _fake_anthropic_module(self, should_fail):
        mod = types.ModuleType("anthropic")

        class FakeAnthropic:
            def __init__(self, api_key=None):
                pass

            class messages:
                @staticmethod
                def create(**kwargs):
                    if should_fail:
                        raise RuntimeError("simulated Anthropic outage")
                    block = types.SimpleNamespace(text="Anthropic reply")
                    return types.SimpleNamespace(content=[block])

        mod.Anthropic = FakeAnthropic
        return mod

    def _fake_groq_module(self):
        mod = types.ModuleType("groq")

        class FakeGroq:
            def __init__(self, api_key=None):
                pass

            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        msg = types.SimpleNamespace(content="Groq reply")
                        choice = types.SimpleNamespace(message=msg)
                        return types.SimpleNamespace(choices=[choice])

        mod.Groq = FakeGroq
        return mod

    def test_anthropic_used_when_configured_and_healthy(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "real-key", "GROQ_API_KEY": "gsk_x"}), \
             mock.patch.dict(sys.modules, {"anthropic": self._fake_anthropic_module(should_fail=False)}):
            reply = aa.call_ai_provider("system", "user message")
            self.assertEqual(reply, "Anthropic reply")

    def test_falls_back_to_groq_when_anthropic_fails(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "real-key", "GROQ_API_KEY": "gsk_x"}), \
             mock.patch.dict(sys.modules, {
                 "anthropic": self._fake_anthropic_module(should_fail=True),
                 "groq": self._fake_groq_module(),
             }):
            reply = aa.call_ai_provider("system", "user message")
            self.assertEqual(reply, "Groq reply")

    def test_raises_when_no_provider_configured(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": ""}):
            with self.assertRaises(aa.AssistantProviderError):
                aa.call_ai_provider("system", "user message")

    def test_placeholder_anthropic_key_is_treated_as_unconfigured(self):
        # Matches the exact convention used everywhere else in the project
        # (evaluator.py / question_engine.py / resume_parser.py / app.py).
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "your_anthropic_api_key_here", "GROQ_API_KEY": "gsk_x"}), \
             mock.patch.dict(sys.modules, {"groq": self._fake_groq_module()}):
            reply = aa.call_ai_provider("system", "user message")
            self.assertEqual(reply, "Groq reply")

    def test_falls_back_to_next_groq_model_when_first_is_decommissioned(self):
        # Regression test for the actual reported bug: a Groq model id can
        # be retired/decommissioned by Groq itself. The assistant must not
        # go down with just one stale model id -- it must try the next
        # candidate in _GROQ_MODEL_CANDIDATES before giving up.
        mod = types.ModuleType("groq")
        attempted = []

        class FakeGroq:
            def __init__(self, api_key=None):
                pass

            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        attempted.append(kwargs["model"])
                        if kwargs["model"] == aa._GROQ_MODEL_CANDIDATES[0]:
                            raise RuntimeError("model_decommissioned: this model is no longer supported")
                        msg = types.SimpleNamespace(content="Groq reply from second model")
                        choice = types.SimpleNamespace(message=msg)
                        return types.SimpleNamespace(choices=[choice])

        mod.Groq = FakeGroq
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": "gsk_x"}), \
             mock.patch.dict(sys.modules, {"groq": mod}):
            reply = aa.call_ai_provider("system", "user message")
            self.assertEqual(reply, "Groq reply from second model")
            self.assertEqual(attempted, aa._GROQ_MODEL_CANDIDATES[:2])

    def test_raises_with_last_error_when_every_groq_model_fails(self):
        mod = types.ModuleType("groq")

        class FakeGroq:
            def __init__(self, api_key=None):
                pass

            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        raise RuntimeError(f"decommissioned: {kwargs['model']}")

        mod.Groq = FakeGroq
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": "gsk_x"}), \
             mock.patch.dict(sys.modules, {"groq": mod}):
            with self.assertRaises(aa.AssistantProviderError):
                aa.call_ai_provider("system", "user message")

    def test_model_not_found_is_explicitly_flagged_in_server_log(self):
        # Regression test for the actual reported failure: Groq returning
        # HTTP 404 "model_not_found" for a retired/renamed model id must be
        # clearly identifiable in the server log (never the browser), not
        # lumped in with a generic error.
        mod = types.ModuleType("groq")

        class FakeNotFoundError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.status_code = 404

        class FakeGroq:
            def __init__(self, api_key=None):
                pass

            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        raise FakeNotFoundError(
                            f"The model '{kwargs['model']}' does not exist or you do not have access to it."
                        )

        mod.Groq = FakeGroq
        fake_key = "gsk_" + "x" * 52  # realistic length, so prefix-masking is actually exercised
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": fake_key}), \
             mock.patch.dict(sys.modules, {"groq": mod}), \
             contextlib.redirect_stdout(buf):
            with self.assertRaises(aa.AssistantProviderError):
                aa.call_ai_provider("system", "user message")
        log_output = buf.getvalue()
        self.assertIn("MODEL_NOT_FOUND", log_output)
        self.assertIn("status=404", log_output)
        # The diagnostic must appear; the full key must never be logged,
        # only its short masked prefix.
        self.assertNotIn(fake_key, log_output)

    def test_no_api_key_configured_raises_cleanly(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": ""}, clear=False):
            with self.assertRaises(aa.AssistantProviderError):
                aa.call_ai_provider("system", "user message")

    def test_successful_groq_response_uses_a_candidate_model(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "GROQ_API_KEY": "gsk_x"}), \
             mock.patch.dict(sys.modules, {"groq": self._fake_groq_module()}):
            reply = aa.call_ai_provider("system", "user message")
            self.assertEqual(reply, "Groq reply")


class TestClearConversationsForUser(unittest.TestCase):
    """Settings > Privacy & Data > 'Clear AI Assistant Conversation'."""

    def test_deletes_only_the_given_users_conversations(self):
        docs = [
            {"conversation_id": "c1", "user_id": "user-a"},
            {"conversation_id": "c2", "user_id": "user-a"},
            {"conversation_id": "c3", "user_id": "user-b"},
        ]
        fake = FakeCollection(docs)
        with mock.patch.object(aa, "conversations_col", fake):
            deleted = aa.clear_conversations_for_user("user-a")
        self.assertEqual(deleted, 2)
        remaining_users = {d["user_id"] for d in fake.docs}
        self.assertEqual(remaining_users, {"user-b"})

    def test_returns_zero_when_mongo_unavailable(self):
        with mock.patch.object(aa, "conversations_col", None):
            deleted = aa.clear_conversations_for_user("user-a")
        self.assertEqual(deleted, 0)

    def test_never_raises_if_delete_fails(self):
        class ExplodingCollection:
            def delete_many(self, query):
                raise RuntimeError("Mongo is down")

        with mock.patch.object(aa, "conversations_col", ExplodingCollection()):
            deleted = aa.clear_conversations_for_user("user-a")
        self.assertEqual(deleted, 0)


if __name__ == "__main__":
    unittest.main()
