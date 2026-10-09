"""
InterviewIQ — Aptitude Engine
=============================
Handles test generation, answer evaluation, score calculation,
MongoDB persistence (aptitude_results collection), history retrieval,
and candidate non-repetition question tracking algorithms.
"""

import time
import random
import uuid
import datetime
from bson import ObjectId
from modules.aptitude_bank import APTITUDE_QUESTIONS, CATEGORIES

# In-memory fallback if MongoDB is offline
IN_MEMORY_APTITUDE_RESULTS = []


def _get_db():
    try:
        from app import db
        return db
    except Exception:
        return None


def get_categories_and_topics():
    """Return all categories and sub-topics with question counts."""
    cat_counts = {}
    topic_counts = {}
    for q in APTITUDE_QUESTIONS:
        c = q["category"]
        t = q["topic"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
        topic_counts[t] = topic_counts.get(t, 0) + 1

    result = []
    for cat in CATEGORIES:
        cname = cat["name"]
        topics_with_counts = []
        for top in cat["topics"]:
            topics_with_counts.append({
                "name": top,
                "question_count": topic_counts.get(top, 0)
            })
        result.append({
            "name": cname,
            "icon": cat["icon"],
            "color": cat["color"],
            "total_questions": cat_counts.get(cname, 0),
            "topics": topics_with_counts
        })
    return result


def get_candidate_question_history(user_id: str):
    """
    Retrieves candidate's historical question IDs to enforce non-repetition.
    Returns:
      - seen_set: set of all qids seen by candidate
      - recent_qids: set of qids seen in candidate's most recent attempt
      - usage_counts: dict { qid: count } tracking how many times candidate has seen qid
    """
    user_id_str = str(user_id)
    seen_set = set()
    recent_qids = set()
    usage_counts = {}

    history = get_user_aptitude_history(user_id_str)
    if history:
        latest_attempt = history[0]
        if latest_attempt.get("detailed_review"):
            recent_qids = set(item["id"] for item in latest_attempt["detailed_review"] if isinstance(item, dict) and "id" in item)
        elif latest_attempt.get("question_ids"):
            recent_qids = set(latest_attempt.get("question_ids"))

        for attempt in history:
            q_list = []
            if attempt.get("detailed_review"):
                q_list = [item["id"] for item in attempt["detailed_review"] if isinstance(item, dict) and "id" in item]
            elif attempt.get("question_ids"):
                q_list = attempt.get("question_ids")

            for qid in q_list:
                if qid:
                    seen_set.add(qid)
                    usage_counts[qid] = usage_counts.get(qid, 0) + 1

    return seen_set, recent_qids, usage_counts


def _select_subpool_non_repeating(pool, target_count, seen_set, recent_qids, usage_counts):
    """
    Selects target_count unique questions from pool avoiding seen_set if possible.
    Never duplicates a question within the selection.
    """
    if not pool or target_count <= 0:
        return []

    # Filter unused pool
    unused = [q for q in pool if q["id"] not in seen_set]
    random.shuffle(unused)

    if len(unused) >= target_count:
        return unused[:target_count]

    # If unused is smaller than target_count, take all unused questions
    selected = list(unused)
    selected_ids = set(q["id"] for q in selected)
    needed = target_count - len(selected)

    # For the remaining pool, select least recently used questions
    used = [q for q in pool if q["id"] not in selected_ids]

    # Sort key: (is_in_most_recent_attempt [1 or 0], usage_count, random_tiebreaker)
    random.seed()
    used_sorted = sorted(used, key=lambda q: (
        1 if q["id"] in recent_qids else 0,
        usage_counts.get(q["id"], 0),
        random.random()
    ))

    selected.extend(used_sorted[:needed])
    return selected[:target_count]


TOTAL_APTITUDE_QUESTIONS = 50
APTITUDE_TEST_DURATION_MINUTES = 60


def start_aptitude_test(user_id: str, mode: str = "quick", category: str = None, topic: str = None, difficulty: str = None, num_questions: int = None):
    """
    Generates a 50-question / 60-minute aptitude test session payload.
    Enforces persistent candidate non-repetition tracking.
    Hides correct answers from client JSON to prevent cheating.
    """
    mode = mode.lower() if mode else "quick"
    seen_set, recent_qids, usage_counts = get_candidate_question_history(user_id)

    # Master pool filtering
    candidates = list(APTITUDE_QUESTIONS)
    if difficulty and difficulty != "All":
        candidates = [q for q in candidates if q["difficulty"] == difficulty]

    # Hard-enforce 50 questions and 60 minutes for every aptitude session
    target_count = TOTAL_APTITUDE_QUESTIONS
    time_limit_minutes = APTITUDE_TEST_DURATION_MINUTES

    if mode == "quick":
        title = "Aptitude Practice (50 Questions)"
    elif mode == "topic":
        title = f"{topic or category or 'Topic'} Practice (50 Questions)"
    elif mode == "full":
        title = "Full Aptitude Assessment (50 Questions)"
    else:
        title = "Aptitude Assessment (50 Questions)"

    selected_questions = []

    # 1. Topic or specific category filter
    if (category and category != "All") or (topic and topic != "All"):
        filtered_pool = list(candidates)
        if category and category != "All":
            filtered_pool = [q for q in filtered_pool if q["category"] == category]
        if topic and topic != "All":
            filtered_pool = [q for q in filtered_pool if q["topic"] == topic]
        if not filtered_pool:
            filtered_pool = list(candidates)

        selected_questions = _select_subpool_non_repeating(
            filtered_pool, min(target_count, len(filtered_pool)), seen_set, recent_qids, usage_counts
        )
    # 2. General / Full Aptitude Assessment (Distributed Quota: ~20 Quant, ~15 Logical, ~10 Verbal, ~5 DI)
    elif mode in ["full", "assessment"] or target_count >= 50:
        quotas = [
            ("Quantitative Aptitude", 20),
            ("Logical Reasoning", 15),
            ("Verbal Ability", 10),
            ("Data Interpretation", 5)
        ]

        collected_ids = set()
        for cat_name, cat_quota in quotas:
            cat_pool = [q for q in candidates if q["category"] == cat_name and q["id"] not in collected_ids]
            chosen = _select_subpool_non_repeating(cat_pool, cat_quota, seen_set, recent_qids, usage_counts)
            for q in chosen:
                collected_ids.add(q["id"])
                selected_questions.append(q)

        # Fill remaining slots if total selected < target_count
        if len(selected_questions) < target_count:
            remaining_pool = [q for q in candidates if q["id"] not in collected_ids]
            fill_count = target_count - len(selected_questions)
            extra = _select_subpool_non_repeating(remaining_pool, fill_count, seen_set, recent_qids, usage_counts)
            selected_questions.extend(extra)
    # 3. Fallback / Quick Practice
    else:
        selected_questions = _select_subpool_non_repeating(
            candidates, min(target_count, len(candidates)), seen_set, recent_qids, usage_counts
        )

    # Thoroughly randomize and mix question order across all categories & topics
    random.seed()
    random.shuffle(selected_questions)
    random.shuffle(selected_questions)

    # Prepare client-facing questions (stripping answer & explanation, shuffling options)
    client_questions = []
    for q in selected_questions:
        opts = list(q["options"])
        random.shuffle(opts)
        client_questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": opts,
            "category": q["category"],
            "topic": q["topic"],
            "difficulty": q["difficulty"]
        })

    test_id = f"apt_test_{uuid.uuid4().hex[:12]}"
    print(f"[APTITUDE TEST CREATED] User: {user_id} | Question count: {len(client_questions)} | Unique count: {len(set(q['id'] for q in client_questions))} | Test ID: {test_id}")

    return {
        "test_id": test_id,
        "title": title,
        "mode": mode,
        "category": category or "All Categories",
        "topic": topic or "All Topics",
        "difficulty": difficulty or "Mixed",
        "total_questions": len(client_questions),
        "time_limit_minutes": time_limit_minutes,
        "questions": client_questions
    }


def evaluate_aptitude_test(user_id: str, payload: dict):
    """
    Evaluates submitted candidate answers out of 50 questions, computes category/topic performance,
    persists result in MongoDB `aptitude_results`, and generates recommendations.
    """
    user_answers = payload.get("user_answers", {})
    mode = payload.get("mode", "quick")
    category_filter = payload.get("category", "All Categories")
    topic_filter = payload.get("topic", "All Topics")
    time_taken_seconds = payload.get("time_taken_seconds", 0)

    # Build master question map
    q_map = {q["id"]: q for q in APTITUDE_QUESTIONS}

    total_questions = len(payload.get("question_ids", [])) or len(user_answers) or 1
    question_ids = payload.get("question_ids", list(user_answers.keys()))

    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    category_stats = {}
    topic_stats = {}
    difficulty_stats = {}
    detailed_review = []

    for qid in question_ids:
        master_q = q_map.get(qid)
        if not master_q:
            continue

        cat = master_q["category"]
        top = master_q["topic"]
        diff = master_q["difficulty"]

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "correct": 0}
        if top not in topic_stats:
            topic_stats[top] = {"total": 0, "correct": 0}
        if diff not in difficulty_stats:
            difficulty_stats[diff] = {"total": 0, "correct": 0}

        category_stats[cat]["total"] += 1
        topic_stats[top]["total"] += 1
        difficulty_stats[diff]["total"] += 1

        user_choice = user_answers.get(qid)
        correct_ans = master_q["answer"]

        status = "unanswered"
        if user_choice:
            if user_choice == correct_ans:
                status = "correct"
                correct_count += 1
                category_stats[cat]["correct"] += 1
                topic_stats[top]["correct"] += 1
                difficulty_stats[diff]["correct"] += 1
            else:
                status = "wrong"
                wrong_count += 1
        else:
            unanswered_count += 1

        detailed_review.append({
            "id": qid,
            "question": master_q["question"],
            "options": master_q["options"],
            "user_choice": user_choice or "Not Answered",
            "correct_answer": correct_ans,
            "status": status,
            "explanation": master_q["explanation"],
            "category": cat,
            "topic": top,
            "difficulty": diff
        })

    answered_total = correct_count + wrong_count
    score_pct = int(round((correct_count / total_questions) * 100)) if total_questions else 0
    accuracy_pct = int(round((correct_count / answered_total) * 100)) if answered_total else 0

    # Calculate category percentages
    category_scores = {}
    for cat, data in category_stats.items():
        category_scores[cat] = int(round((data["correct"] / data["total"]) * 100)) if data["total"] else 0

    # Calculate topic percentages
    topic_scores = {}
    weak_topics = []
    strong_topics = []
    for top, data in topic_stats.items():
        pct = int(round((data["correct"] / data["total"]) * 100)) if data["total"] else 0
        topic_scores[top] = pct
        if pct < 60:
            weak_topics.append(top)
        elif pct >= 75:
            strong_topics.append(top)

    # Calculate difficulty percentages
    difficulty_scores = {}
    for diff, data in difficulty_stats.items():
        difficulty_scores[diff] = int(round((data["correct"] / data["total"]) * 100)) if data["total"] else 0

    result_id = f"res_{uuid.uuid4().hex[:12]}"
    created_at = datetime.datetime.utcnow().isoformat() + "Z"

    result_doc = {
        "id": result_id,
        "user_id": str(user_id),
        "mode": mode,
        "category": category_filter,
        "topic": topic_filter,
        "score": score_pct,
        "accuracy": accuracy_pct,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "unanswered_count": unanswered_count,
        "time_taken_seconds": time_taken_seconds,
        "question_ids": question_ids,
        "category_scores": category_scores,
        "topic_scores": topic_scores,
        "difficulty_scores": difficulty_scores,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "detailed_review": detailed_review,
        "created_at": created_at
    }

    # Persist to MongoDB if connected, otherwise fallback to in-memory store
    db = _get_db()
    if db is not None:
        try:
            db["aptitude_results"].insert_one(dict(result_doc))
        except Exception as e:
            print(f"[AptitudeEngine] MongoDB insert error: {e}")
            IN_MEMORY_APTITUDE_RESULTS.append(result_doc)
    else:
        IN_MEMORY_APTITUDE_RESULTS.append(result_doc)

    return result_doc


def get_user_aptitude_history(user_id: str):
    """Retrieve candidate's historical aptitude test results."""
    user_id_str = str(user_id)
    results = []

    db = _get_db()
    if db is not None:
        try:
            cursor = db["aptitude_results"].find({"user_id": user_id_str}).sort("created_at", -1)
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)
        except Exception as e:
            print(f"[AptitudeEngine] MongoDB query error: {e}")
            results = [r for r in IN_MEMORY_APTITUDE_RESULTS if r["user_id"] == user_id_str]
    else:
        results = [r for r in IN_MEMORY_APTITUDE_RESULTS if r["user_id"] == user_id_str]

    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


def get_aptitude_overview(user_id: str):
    """
    Computes overall user dashboard stats, category performance,
    history, and personalized weak topic recommendations.
    """
    history = get_user_aptitude_history(user_id)
    categories = get_categories_and_topics()

    total_tests = len(history)
    if total_tests > 0:
        avg_score = int(round(sum(r["score"] for r in history) / total_tests))
        avg_accuracy = int(round(sum(r["accuracy"] for r in history) / total_tests))
    else:
        avg_score = 0
        avg_accuracy = 0

    # Aggregate weak topics & category performance over all tests
    cat_totals = {}
    cat_corrects = {}
    weak_counter = {}

    for r in history:
        for cat, pct in r.get("category_scores", {}).items():
            cat_totals[cat] = cat_totals.get(cat, 0) + 1
            cat_corrects[cat] = cat_corrects.get(cat, 0) + pct
        for top in r.get("weak_topics", []):
            weak_counter[top] = weak_counter.get(top, 0) + 1

    cat_performance = {}
    for cat in ["Quantitative Aptitude", "Logical Reasoning", "Verbal Ability", "Data Interpretation"]:
        if cat_totals.get(cat, 0) > 0:
            cat_performance[cat] = int(round(cat_corrects[cat] / cat_totals[cat]))
        else:
            cat_performance[cat] = 0

    # Find top weak topic
    sorted_weak = sorted(weak_counter.items(), key=lambda x: x[1], reverse=True)
    top_weak_topic = sorted_weak[0][0] if sorted_weak else None

    # Recommendations based on actual performance
    recommendations = []
    if top_weak_topic:
        recommendations.append({
            "topic": top_weak_topic,
            "message": f"Your weakest area is {top_weak_topic}.",
            "action_text": f"Practice {top_weak_topic}"
        })
    elif total_tests == 0:
        recommendations.append({
            "topic": "Quantitative Aptitude",
            "message": "Take your first Quick Practice test to analyze your baseline skills.",
            "action_text": "Start Quick Practice"
        })
    else:
        recommendations.append({
            "topic": "Full Assessment",
            "message": "Great job! Challenge yourself with a 50-Question Full Aptitude Test.",
            "action_text": "Start Full Aptitude Test (50 Qs)"
        })

    return {
        "summary": {
            "total_tests": total_tests,
            "avg_score": avg_score,
            "avg_accuracy": avg_accuracy,
            "category_performance": cat_performance,
            "top_weak_topic": top_weak_topic
        },
        "recommendations": recommendations,
        "categories": categories,
        "history": history[:10]
    }
