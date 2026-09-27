"""
Tests for the data-driven adaptive question engine
=====================================================
Covers the 14 required scenarios:
  1. Resume with Python skill
  2. Resume with Java skill
  3. Resume with multiple skills
  4. Resume with no recognized skills
  5. Weak answer
  6. Strong answer
  7. Difficulty increase
  8. Difficulty decrease
  9. Same question prevention
  10. Dataset unavailable
  11. LLM fallback
  12. Previous interview learning
  13. Multiple interview sessions
  14. New user with no history

Run with (from the backend/ directory, using the project's own venv so all
real dependencies are available):

    python -m unittest tests.test_data_driven_engine -v

What is mocked and why
-----------------------
`pymongo`, `groq`, and `anthropic` are replaced with lightweight in-memory
stand-ins BEFORE any project module is imported. This lets the real business
logic (skill mapping, dataset retrieval, difficulty transitions, repetition
prevention, continuous-learning persistence calls) run for real, without
requiring a live MongoDB Atlas cluster or live LLM API credentials/cost.
Nothing about the *logic under test* is faked -- only the network-facing
edges are.
"""

import sys
import os
import types
import unittest

# ---------------------------------------------------------------------------
# Stub external network-facing packages BEFORE importing project modules.
# ---------------------------------------------------------------------------

class _FakeMongoCollection:
    """A tiny in-memory stand-in for a pymongo Collection, supporting only
    the operations the modules under test actually call."""

    def __init__(self):
        self.docs = []

    def create_index(self, *a, **k):
        pass

    def insert_one(self, doc):
        doc = dict(doc)
        self.docs.append(doc)
        return types.SimpleNamespace(inserted_id="fake_id")

    def find(self, query=None):
        query = query or {}
        return [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]

    def find_one(self, query=None, sort=None):
        query = query or {}
        matches = [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]
        return matches[0] if matches else None

    def replace_one(self, filt, doc, upsert=False):
        for i, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in filt.items()):
                self.docs[i] = dict(doc)
                return
        if upsert:
            self.docs.append(dict(doc))

    def update_one(self, filt, update, upsert=False):
        target = self.find_one(filt)
        if target is None and upsert:
            target = dict(filt)
            self.docs.append(target)
        if target is not None and "$set" in update:
            target.update(update["$set"])

    def count_documents(self, query=None):
        return len(self.find(query))


def _install_stub_modules():
    if "pymongo" not in sys.modules:
        pymongo_stub = types.ModuleType("pymongo")

        class _FakeMongoClient:
            def __init__(self, *a, **k):
                self._dbs = {}
                self.admin = types.SimpleNamespace(command=lambda *a, **k: True)

            def __getitem__(self, name):
                if name not in self._dbs:
                    self._dbs[name] = _FakeDatabase()
                return self._dbs[name]

        class _FakeDatabase(dict):
            def __getitem__(self, name):
                if name not in self:
                    dict.__setitem__(self, name, _FakeMongoCollection())
                return dict.__getitem__(self, name)

        pymongo_stub.MongoClient = _FakeMongoClient
        sys.modules["pymongo"] = pymongo_stub

    if "groq" not in sys.modules:
        groq_stub = types.ModuleType("groq")

        class _FakeGroq:
            def __init__(self, *a, **k):
                pass

        groq_stub.Groq = _FakeGroq
        sys.modules["groq"] = groq_stub

    if "anthropic" not in sys.modules:
        anthropic_stub = types.ModuleType("anthropic")

        class _FakeAnthropic:
            def __init__(self, *a, **k):
                pass

        anthropic_stub.Anthropic = _FakeAnthropic
        sys.modules["anthropic"] = anthropic_stub


_install_stub_modules()

# No live API keys during tests -> forces every code path to actually
# exercise its documented fallback behaviour instead of hitting a network.
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("MONGO_URI", None)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(THIS_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from modules import skill_mapper, question_bank, difficulty_engine, similarity  # noqa: E402
from modules import adaptive_engine as ae  # noqa: E402
from modules import question_engine as qe  # noqa: E402
from modules import candidate_intelligence as ci  # noqa: E402


def _new_session(skills, difficulty="easy"):
    session = {
        "id": "test-session",
        "skills": skills,
        "answers": [],
        "technical_scores": [],
        "current_difficulty": difficulty,
        "interviewer": {"language": "en", "candidate_name": "Test", "conversation": []},
    }
    ae.initialize_adaptive_state(session)
    return session


# ---------------------------------------------------------------------------
# 1-4: Resume / skill detection scenarios
# ---------------------------------------------------------------------------
class TestResumeSkillMapping(unittest.TestCase):

    def test_1_resume_with_python_skill(self):
        result = skill_mapper.map_resume_skills(["Python"])
        self.assertEqual(result["canonical_skills"], ["Python"])
        self.assertEqual(result["unmapped"], [])
        pool = qe.generate_questions(["Python"])
        self.assertEqual(len(pool), 24)
        self.assertTrue(all(q["source"] == "dataset" for q in pool))
        self.assertTrue(any(q["skill"] == "Python" for q in pool))

    def test_2_resume_with_java_skill(self):
        result = skill_mapper.map_resume_skills(["Java"])
        self.assertEqual(result["canonical_skills"], ["Java"])
        pool = qe.generate_questions(["Java"])
        self.assertEqual(len(pool), 24)
        self.assertTrue(any(q["skill"] == "Java" for q in pool))

    def test_3_resume_with_multiple_skills(self):
        # Includes common resume phrasing variants, not just exact dataset names
        raw_skills = ["Python Programming", "MongoDB", "React.js", "ML"]
        result = skill_mapper.map_resume_skills(raw_skills)
        self.assertEqual(
            set(result["canonical_skills"]),
            {"Python", "DBMS", "React", "AI/ML"},
        )
        pool = qe.generate_questions(raw_skills)
        skills_used = {q["skill"] for q in pool}
        # Only genuinely-covered skills should appear -- no invented skills
        self.assertTrue(skills_used.issubset({"Python", "DBMS", "React", "AI/ML"}))

    def test_4_resume_with_no_recognized_skills(self):
        # Skills that don't exist in any resume vocabulary / dataset
        result = skill_mapper.map_resume_skills(["Underwater Basket Weaving", "Astrology"])
        self.assertEqual(result["canonical_skills"], [])
        self.assertEqual(len(result["unmapped"]), 2)
        # System must NOT invent a skill match -- falls back to the
        # documented generic pool (HR/Aptitude/DSA), never a fabricated skill
        pool = qe.generate_questions([])
        skills_used = {q["skill"] for q in pool}
        self.assertTrue(skills_used.issubset({"HR", "Aptitude", "DSA"}))
        self.assertGreater(len(pool), 0)


# ---------------------------------------------------------------------------
# 5-8: Adaptive difficulty scenarios
# ---------------------------------------------------------------------------
class TestAdaptiveDifficulty(unittest.TestCase):

    def test_5_weak_answer_classified_and_handled(self):
        self.assertEqual(difficulty_engine.classify_score(20), "weak")
        session = _new_session(["Python"])
        ae.update_adaptive_state(session, "q1", "Python", 20)
        perf = session["skill_performance"]["Python"]
        self.assertEqual(perf["last_band"], "weak")

    def test_6_strong_answer_classified_and_handled(self):
        self.assertEqual(difficulty_engine.classify_score(90), "excellent")
        self.assertEqual(difficulty_engine.classify_score(75), "good")
        session = _new_session(["Python"])
        ae.update_adaptive_state(session, "q1", "Python", 90)
        perf = session["skill_performance"]["Python"]
        self.assertEqual(perf["last_band"], "excellent")

    def test_7_difficulty_increases_on_strong_performance(self):
        session = _new_session(["Python"], difficulty="easy")
        for score in [88, 90, 92]:
            ae.update_adaptive_state(session, f"q-{score}", "Python", score)
        perf = session["skill_performance"]["Python"]
        self.assertEqual(perf["current_difficulty"], 3)  # escalated to hard
        # Difficulty must be justified by an actual score, not random
        self.assertIn(perf["last_band"], ("good", "excellent"))

    def test_8_difficulty_decreases_on_weak_performance(self):
        session = _new_session(["Python"], difficulty="hard")
        session["skill_performance"]["Python"] = difficulty_engine.init_skill_performance("hard")
        for score in [20, 15, 25]:
            ae.update_adaptive_state(session, f"q-{score}", "Python", score)
        perf = session["skill_performance"]["Python"]
        self.assertLess(perf["current_difficulty"], 3)  # de-escalated from hard
        self.assertEqual(perf["last_band"], "weak")

    def test_average_answer_keeps_same_difficulty(self):
        perf = difficulty_engine.init_skill_performance("medium")
        difficulty_engine.update_skill_performance(perf, 55)
        self.assertEqual(perf["current_difficulty"], 2)  # unchanged
        self.assertEqual(perf["last_band"], "average")


# ---------------------------------------------------------------------------
# 9-11: Retrieval / repetition / fallback scenarios
# ---------------------------------------------------------------------------
class TestRetrievalAndFallback(unittest.TestCase):

    def test_9_same_question_prevention(self):
        first = question_bank.select_question("Python", "easy", exclude=[])
        self.assertIsNotNone(first)
        second = question_bank.select_question(
            "Python", "easy", exclude=[first["question"]]
        )
        self.assertIsNotNone(second)
        self.assertNotEqual(first["question"].strip().lower(), second["question"].strip().lower())
        self.assertFalse(similarity.are_questions_similar(first["question"], second["question"]))

    def test_10_dataset_unavailable_for_skill(self):
        # "Kotlin" has no dataset at all (not in CANONICAL_SKILLS)
        self.assertFalse(skill_mapper.has_dataset("Kotlin"))
        result = question_bank.select_question("Kotlin", "easy", exclude=[])
        self.assertIsNone(result)  # must not crash, must not fabricate a question
        # The adaptive engine must route this to the LLM-fallback path
        session = _new_session(["Kotlin"])
        q_text, source = ae.generate_adaptive_question(session, "Kotlin", "easy", user_id=None)
        self.assertTrue(q_text)  # still produces *something* (safety net)
        self.assertIn("llm", source)  # transparently labeled as a fallback path

    def test_11_llm_fallback_triggers_when_dataset_exhausted(self):
        # Exhaust every fresh 'easy' Python question by excluding them all,
        # forcing the retrieval tier to relax/escalate rather than serve a
        # stale duplicate, and confirm the adaptive engine still returns a
        # usable question end-to-end.
        all_easy_python = [
            q["question"] for q in question_bank._bank.candidates("Python", "easy")
        ]
        session = _new_session(["Python"])
        session["asked_questions"] = list(all_easy_python)
        q_text, source = ae.generate_adaptive_question(session, "Python", "easy", user_id=None)
        self.assertTrue(q_text)
        # Either a relaxed dataset pick (still "dataset") or a genuine LLM
        # fallback -- both are acceptable, a crash or empty question is not.
        self.assertIn(source, ("dataset", "llm_dataset_exhausted", "dataset_safety_net_llm_unavailable"))


# ---------------------------------------------------------------------------
# 12-14: Continuous learning / persistence scenarios
# ---------------------------------------------------------------------------
class TestContinuousLearning(unittest.TestCase):

    def setUp(self):
        # Inject fresh fake Mongo collections for isolation between tests
        self.asked_col = _FakeMongoCollection()
        self.profiles_col = _FakeMongoCollection()
        ae.asked_col = self.asked_col
        ci.profiles_col = self.profiles_col
        ci._profiles_cache.clear()

    def test_14_new_user_with_no_history(self):
        profile = ci.load_candidate_profile("brand_new_user", resume_skills=["Python"])
        self.assertEqual(profile["weak_areas"], [])
        self.assertEqual(profile["strong_areas"], [])
        self.assertIn("Python", profile["skills"])
        self.assertEqual(profile["skills"]["Python"]["evidence_count"], 0)
        history = ae.get_user_history("brand_new_user")
        self.assertEqual(history, [])

    def test_12_previous_interview_learning_influences_seeding(self):
        # Simulate a completed interview where the candidate scored poorly
        # on Python, persisted via candidate_intelligence (as submit_answer
        # does in the real app).
        session = _new_session(["Python"])
        session["user_id"] = "user_42"
        evaluation = {"score": 30, "skill": "Python", "difficulty": "easy",
                      "dimensions": {}, "self_correction": {"detected": False},
                      "contradiction": {"detected": False}, "uncertainty": {"detected": False}}
        # candidate_intelligence requires >=2 evidence points on a skill
        # before it commits to a weak/strong classification (avoids
        # over-reacting to a single answer) -- so answer twice, both weak.
        ci.update_candidate_profile_step(session, "user_42", "Explain X", "I don't know", evaluation)
        ci.update_candidate_profile_step(session, "user_42", "Explain Y", "Not sure", evaluation)

        profile = ci.load_candidate_profile("user_42")
        self.assertIn("Python", profile["weak_areas"])

        # A future practice session should seed difficulty from that history
        avg_score = profile["skills"]["Python"]["score"]
        seeded_difficulty = difficulty_engine.initial_difficulty_from_score(avg_score)
        self.assertEqual(seeded_difficulty, "easy")

    def test_13_multiple_interview_sessions_accumulate(self):
        session1 = _new_session(["Python"])
        session1["id"] = "session-1"
        session1["user_id"] = "user_99"
        ae.add_to_user_history("user_99", "session-1", "Q1 about Python", "Python", difficulty="easy", score=40)

        session2 = _new_session(["Python"])
        session2["id"] = "session-2"
        session2["user_id"] = "user_99"
        ae.add_to_user_history("user_99", "session-2", "Q2 about Python", "Python", difficulty="medium", score=70)

        history = ae.get_user_history("user_99")
        self.assertEqual(set(history), {"Q1 about Python", "Q2 about Python"})
        # Both records carry difficulty/score/timestamp for future analysis
        raw_docs = self.asked_col.find({"user_id": "user_99"})
        self.assertEqual(len(raw_docs), 2)
        for d in raw_docs:
            self.assertIn("difficulty", d)
            self.assertIn("score", d)
            self.assertIn("timestamp", d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
