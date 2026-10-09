"""
Unit tests for backend/modules/aptitude_engine.py and Aptitude Flask API endpoints.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules import aptitude_engine as ae
from modules.aptitude_bank import APTITUDE_QUESTIONS, CATEGORIES


class TestAptitudeEngineUnit(unittest.TestCase):
    def test_categories_and_topics(self):
        cats = ae.get_categories_and_topics()
        self.assertEqual(len(cats), 4)
        cat_names = [c["name"] for c in cats]
        self.assertIn("Quantitative Aptitude", cat_names)
        self.assertIn("Logical Reasoning", cat_names)
        self.assertIn("Verbal Ability", cat_names)
        self.assertIn("Data Interpretation", cat_names)

    def test_start_quick_practice_test(self):
        test_data = ae.start_aptitude_test(
            user_id="user_test_123",
            mode="quick"
        )
        self.assertEqual(test_data["mode"], "quick")
        self.assertEqual(len(test_data["questions"]), 50)
        # Confirm answer and explanation are NOT present in client questions
        for q in test_data["questions"]:
            self.assertNotIn("answer", q)
            self.assertNotIn("explanation", q)
            self.assertEqual(len(q["options"]), 4)

    def test_start_full_50_questions_test(self):
        test_data = ae.start_aptitude_test(
            user_id="user_full_50",
            mode="full"
        )
        self.assertEqual(test_data["mode"], "full")
        self.assertEqual(test_data["total_questions"], 50)
        self.assertEqual(test_data["time_limit_minutes"], 60)
        
        # Verify zero intra-test duplicates
        q_ids = [q["id"] for q in test_data["questions"]]
        self.assertEqual(len(q_ids), 50)
        self.assertEqual(len(set(q_ids)), 50)

    def test_candidate_non_repetition(self):
        user_id = "user_non_repeat_test"
        
        # Attempt 1
        t1 = ae.start_aptitude_test(user_id=user_id, mode="full")
        q1_ids = set(q["id"] for q in t1["questions"])
        self.assertEqual(len(q1_ids), 50)

        # Store attempt 1
        ae.evaluate_aptitude_test(user_id=user_id, payload={
            "mode": "full",
            "question_ids": list(q1_ids),
            "user_answers": {},
            "time_taken_seconds": 1200
        })

        # Attempt 2
        t2 = ae.start_aptitude_test(user_id=user_id, mode="full")
        q2_ids = set(q["id"] for q in t2["questions"])
        self.assertEqual(len(q2_ids), 50)

        # Verify Attempt 2 has 50 new questions not present in Attempt 1
        overlap = q1_ids.intersection(q2_ids)
        self.assertEqual(len(overlap), 0, f"Found {len(overlap)} repeated questions between attempts out of 330 bank!")

    def test_start_topic_filtered_test(self):
        test_data = ae.start_aptitude_test(
            user_id="user_test_123",
            mode="topic",
            category="Quantitative Aptitude",
            topic="Percentages",
            num_questions=5
        )
        self.assertEqual(test_data["category"], "Quantitative Aptitude")
        self.assertEqual(test_data["topic"], "Percentages")
        for q in test_data["questions"]:
            self.assertEqual(q["category"], "Quantitative Aptitude")
            self.assertEqual(q["topic"], "Percentages")

    def test_evaluate_aptitude_test(self):
        # Pick 2 questions from dataset
        q1 = APTITUDE_QUESTIONS[0]
        q2 = APTITUDE_QUESTIONS[1]

        payload = {
            "mode": "quick",
            "category": "Quantitative Aptitude",
            "topic": "Percentages",
            "question_ids": [q1["id"], q2["id"]],
            "user_answers": {
                q1["id"]: q1["answer"],  # Correct
                q2["id"]: "WRONG_ANSWER" # Wrong
            },
            "time_taken_seconds": 45
        }

        result = ae.evaluate_aptitude_test(user_id="user_test_123", payload=payload)
        self.assertEqual(result["total_questions"], 2)
        self.assertEqual(result["correct_count"], 1)
        self.assertEqual(result["wrong_count"], 1)
        self.assertEqual(result["score"], 50)
        self.assertEqual(result["accuracy"], 50)
        self.assertEqual(result["time_taken_seconds"], 45)
        self.assertEqual(len(result["detailed_review"]), 2)

    def test_get_aptitude_overview_and_recommendations(self):
        overview = ae.get_aptitude_overview(user_id="user_test_456")
        self.assertIn("summary", overview)
        self.assertIn("recommendations", overview)
        self.assertIn("categories", overview)


class TestAptitudeFlaskRoutes(unittest.TestCase):
    def setUp(self):
        from app import app
        self.app = app
        self.client = app.test_client()

    def test_aptitude_page_access_and_api_endpoints(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = "user_test_789"
            sess["authenticated"] = True

        # Test page routes
        r_page = self.client.get("/aptitude")
        self.assertEqual(r_page.status_code, 200)

        r_test_page = self.client.get("/aptitude/test")
        self.assertEqual(r_test_page.status_code, 200)

        # Test API Overview
        r_ov = self.client.get("/api/aptitude/overview")
        self.assertEqual(r_ov.status_code, 200)
        d_ov = r_ov.get_json()
        self.assertIn("categories", d_ov)

        # Test API Start
        r_start = self.client.post("/api/aptitude/start", json={"mode": "quick", "num_questions": 5})
        self.assertEqual(r_start.status_code, 200)
        d_start = r_start.get_json()
        self.assertIn("questions", d_start)

        # Test API Submit
        q0 = d_start["questions"][0]
        r_sub = self.client.post("/api/aptitude/submit", json={
            "test_id": d_start["test_id"],
            "mode": "quick",
            "question_ids": [q0["id"]],
            "user_answers": {q0["id"]: q0["options"][0]},
            "time_taken_seconds": 30
        })
        self.assertEqual(r_sub.status_code, 200)
        d_sub = r_sub.get_json()
        self.assertEqual(d_sub["total_questions"], 1)
        res_id = d_sub["id"]

        # Test API History & Result Detail
        r_hist = self.client.get("/api/aptitude/history")
        self.assertEqual(r_hist.status_code, 200)

        r_det = self.client.get(f"/api/aptitude/result/{res_id}")
        self.assertEqual(r_det.status_code, 200)


if __name__ == "__main__":
    unittest.main()
