import os
import json
import random
import re
import datetime
import pymongo

from modules.similarity import stem_word, normalize_text, are_questions_similar, is_duplicate_of_any  # re-exported, see below
from modules import skill_mapper, question_bank, difficulty_engine

# MongoDB connection setup
MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "interviewiq")

db = None
asked_col = None

if MONGO_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = mongo_client[MONGO_DB_NAME]
        asked_col = db["asked_questions"]
        asked_col.create_index([("user_id", 1), ("question_fingerprint", 1)])
        print("[OK] AdaptiveEngine: MongoDB initialized")
    except Exception as e:
        print(f"[WARN] AdaptiveEngine: MongoDB connection failed: {e}")

# stem_word / normalize_text / are_questions_similar now live in
# modules/similarity.py (imported above) so the adaptive engine and the
# dataset-driven question bank share one implementation instead of two.

def get_user_history(user_id):
    """Fetch user's previous questions history from MongoDB."""
    if asked_col is None or not user_id:
        return []
    try:
        cursor = asked_col.find({"user_id": str(user_id)})
        return [doc["question"] for doc in cursor]
    except Exception as e:
        print(f"[WARN] Failed to fetch user history: {e}")
        return []

def add_to_user_history(user_id, session_id, question_text, skill, difficulty=None, score=None):
    """
    Record an asked question (+ its difficulty, the answer score once known,
    and a timestamp) to MongoDB. This serves two purposes:
      1. Repetition prevention (the original purpose of this collection).
      2. A genuine, growing per-question performance log — user_id,
         interview/session id, skill, question, difficulty, score, timestamp
         — which is exactly the labeled data a future supervised difficulty
         model would need. Today there isn't enough of it to train on (see
         modules/difficulty_engine.py docstring), but this is where that
         data would come from if/when there is.
    """
    if asked_col is None or not user_id:
        return
    try:
        # Generate a lightweight unique identifier signature
        normalized = " ".join(sorted(list(normalize_text(question_text))))
        doc = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "question": question_text,
            "question_fingerprint": normalized,
            "skill": skill,
            "difficulty": difficulty,
            "score": score,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        asked_col.insert_one(doc)
    except Exception as e:
        print(f"[WARN] Failed to save asked question: {e}")

def initialize_adaptive_state(session, user_id=None):
    """Ensure all adaptive metrics are initialized in session."""
    if "skill_scores" not in session:
        session["skill_scores"] = {}
    if "strong_areas" not in session:
        session["strong_areas"] = []
    if "weak_areas" not in session:
        session["weak_areas"] = []
    if "covered_topics" not in session:
        session["covered_topics"] = []
    if "uncertainty" not in session:
        session["uncertainty"] = {s: 100 for s in session.get("skills", [])}
    if "asked_questions" not in session:
        session["asked_questions"] = []
    if "difficulty_history" not in session:
        session["difficulty_history"] = []
    if "skill_performance" not in session:
        # Per-skill deterministic performance tracker, see
        # modules/difficulty_engine.py. Schema per skill:
        # {"questions_answered": int, "average_score": int,
        #  "current_difficulty": 1|2|3, "recent_scores": [...]}
        session["skill_performance"] = {}
    if "user_id" not in session and user_id:
        session["user_id"] = str(user_id)

def update_adaptive_state(session, question_text, skill, score):
    """Update running performance metrics, strong/weak areas and coverage."""
    initialize_adaptive_state(session)
    
    # 1. Update asked questions list
    if question_text not in session["asked_questions"]:
        session["asked_questions"].append(question_text)
        
    # Add to persistent user history if user is logged in
    user_id = session.get("user_id")
    if user_id:
        add_to_user_history(
            user_id, session["id"], question_text, skill,
            difficulty=session.get("current_difficulty"), score=score
        )

    # 1b. Deterministic per-skill performance tracker (drives the NEXT
    # difficulty for this skill, see modules/difficulty_engine.py). This is
    # additive: it does not replace the skill_scores/strong/weak-area logic
    # below, which continues to drive WHICH skill to ask about next.
    if skill:
        perf_map = session["skill_performance"]
        if skill not in perf_map:
            starting = session.get("current_difficulty", "easy")
            perf_map[skill] = difficulty_engine.init_skill_performance(starting)
        difficulty_engine.update_skill_performance(perf_map[skill], score)

    # 2. Update skill scores (running average)
    if skill:
        scores = session["skill_scores"]
        if skill not in scores:
            scores[skill] = score
        else:
            # Shift towards the new score
            scores[skill] = int((scores[skill] + score) / 2)

        # 3. Drop uncertainty level
        unc = session["uncertainty"]
        if skill in unc:
            unc[skill] = max(0, unc[skill] - 30)

        # 4. Add to covered topics
        if skill not in session["covered_topics"]:
            session["covered_topics"].append(skill)

        # 5. Determine strong and weak areas (requires at least 1-2 questions to confirm)
        questions_on_skill = [a for a in session.get("answers", []) if a.get("skill") == skill or skill in a.get("question", "")]
        if len(questions_on_skill) >= 1:
            running_score = scores[skill]
            if running_score >= 80:
                if skill not in session["strong_areas"]:
                    session["strong_areas"].append(skill)
                if skill in session["weak_areas"]:
                    session["weak_areas"].remove(skill)
            elif running_score < 60:
                if skill not in session["weak_areas"]:
                    session["weak_areas"].append(skill)
                if skill in session["strong_areas"]:
                    session["strong_areas"].remove(skill)
            else:
                # Neutral score, remove from both if present
                if skill in session["strong_areas"]:
                    session["strong_areas"].remove(skill)
                if skill in session["weak_areas"]:
                    session["weak_areas"].remove(skill)

def select_next_topic(session):
    """
    Adaptive Decision Engine: Calculate information gain metric for each skill
    to select the best topic and determine the appropriate difficulty level.
    Integrates persistent Candidate Intelligence profile metrics (depth, confidence).
    """
    initialize_adaptive_state(session)
    skills = session.get("skills", [])
    if not skills:
        return ("General", "medium", "No skills extracted from resume.")

    running_scores = session["skill_scores"]
    uncertainty = session["uncertainty"]
    covered = session["covered_topics"]
    weak = session["weak_areas"]
    strong = session["strong_areas"]

    profile = session.get("candidate_profile")
    profile_skills = profile.get("skills", {}) if profile else {}

    # Calculate selection scores
    rankings = []
    for s in skills:
        # Default priority
        priority = 50
        
        # 1. Topic coverage need: Untested skills get a massive priority boost
        if s not in covered:
            priority += 100
            
        # 2. Uncertainty / Confidence: Boost skills with low confidence in the profile
        if s in profile_skills:
            conf = profile_skills[s].get("confidence", 0)
            priority += (100 - conf) * 0.8
        else:
            priority += uncertainty.get(s, 100) * 0.5
        
        # 3. Weak-area diagnostic need: Prioritize diagnostic testing on weak skills
        if s in weak:
            priority += 40
            
        # 4. Repetition penalty: Check if it was the absolute last topic asked
        answers = session.get("answers", [])
        if answers and answers[-1].get("skill") == s:
            priority -= 60
            
        rankings.append((s, priority))

    # Sort descending by priority score
    rankings.sort(key=lambda x: x[1], reverse=True)
    selected_skill = rankings[0][0]

    if session.get("is_practice"):
        tech_scores = session.get("technical_scores", [])
        recent_perf = tech_scores[-1] if tech_scores else 50
        difficulty = difficulty_engine.initial_difficulty_from_score(recent_perf)
        band = difficulty_engine.classify_score(recent_perf)
        reason = f"Practice session: recent performance {recent_perf}% classified as '{band}' -> {difficulty}."
        return (selected_skill, difficulty, reason)

    # PRIMARY difficulty signal (per project requirement: difficulty must
    # depend on actual measured performance, never be randomly chosen):
    # this skill's own deterministic performance tracker, if it already has
    # data from this session. See modules/difficulty_engine.py.
    skill_perf = session.get("skill_performance", {}).get(selected_skill)
    if skill_perf and skill_perf.get("questions_answered", 0) > 0:
        difficulty = difficulty_engine.recommend_difficulty_label(skill_perf)
        band = skill_perf.get("last_band", "average")
        reason = (
            f"Score-band adaptation: recent answer(s) on {selected_skill} classified as "
            f"'{band}' -> {difficulty} (deterministic rule, see difficulty_engine.py)."
        )
        return (selected_skill, difficulty, reason)

    # Cold start for this skill this session (no answers on it yet): fall
    # back to the candidate's persistent cross-session profile depth, then
    # to the overall moving average, exactly as before.
    sk_info = profile_skills.get(selected_skill, {})
    depth = sk_info.get("depth", "Basic")

    if depth == "Advanced":
        difficulty = "hard"
        reason = f"Candidate's profile shows Advanced competency in {selected_skill}. Challenging with advanced scenario."
    elif depth == "Basic" and sk_info.get("evidence_count", 0) >= 2:
        difficulty = "easy"
        reason = f"Candidate struggles with {selected_skill} (Basic level). Asking supporting diagnostic question."
    else:
        # Determine difficulty based on skill score and overall moving average
        skill_score = running_scores.get(selected_skill, 50)
        tech_scores = session.get("technical_scores", [])
        moving_avg = sum(tech_scores[-3:]) / len(tech_scores[-3:]) if tech_scores else 50
        perf_indicator = (skill_score + moving_avg) / 2

        if selected_skill in strong or perf_indicator >= 78:
            difficulty = "hard"
            reason = f"Candidate has shown strong competence in {selected_skill}. Challenging with advanced concepts."
        elif selected_skill in weak or perf_indicator < 55:
            difficulty = "easy"
            reason = f"Candidate struggles in {selected_skill}. Asking supporting/diagnostic question to gauge fundamentals."
        else:
            difficulty = "medium"
            reason = f"Assessing intermediate concepts for {selected_skill}."

    return (selected_skill, difficulty, reason)

def get_fallback_question(session, target_skill, target_difficulty, user_id=None):
    """
    Select a fresh question straight from the local dataset
    (modules/question_bank.py), applying the same repetition filtering used
    everywhere else (this-session history + persistent per-user history).
    Kept as a thin, name-stable wrapper so existing call sites are
    unaffected by the introduction of question_bank.py.
    """
    initialize_adaptive_state(session, user_id)

    canonical_skill = skill_mapper.normalize_skill(target_skill) or target_skill

    history_asked = session["asked_questions"][:]
    if user_id:
        history_asked.extend(get_user_history(user_id))

    result = question_bank.select_question(canonical_skill, target_difficulty, exclude=history_asked)
    if result:
        return result["question"]

    # Dataset has nothing at all for this skill (e.g. an unmapped skill with
    # no backing dataset) -> last-resort hardcoded safety question.
    return question_bank.safety_question()


def generate_adaptive_question(session, target_skill, target_difficulty, user_id=None):
    """
    DATASET-PRIMARY question selection.

    Order of operations (the LLM is a FALLBACK, never the primary source,
    per project requirement):
      1. Try modules/question_bank.py (the local datasets) for a fresh
         question matching target_skill + target_difficulty.
      2. Only if the dataset genuinely cannot satisfy the request -- the
         skill has no backing dataset at all, or every available question
         for that skill/difficulty has already been asked to this
         candidate -- does this fall through to the Groq LLM.
      3. Translation to Hindi/Kannada (when configured) is an
         LLM/translation-API *enrichment* step applied AFTER selection,
         regardless of which source produced the question. This is exactly
         the "translation/enrichment" LLM use case the project spec allows.

    Returns:
        (question_text: str, source: str)
        source is one of:
          "dataset"                                   -- served from the primary source
          "llm_no_dataset_for_skill"                   -- skill has no dataset at all
          "llm_dataset_exhausted"                       -- dataset had this skill, but no fresh question left
          "dataset_safety_net_llm_unavailable"          -- LLM fallback needed but no API key configured
          "dataset_safety_net_llm_failed"               -- LLM fallback attempted but errored/produced a duplicate
    """
    initialize_adaptive_state(session, user_id)

    lang = session.get("interviewer", {}).get("language", "en")
    lang_name = "English"
    if lang == "hi":
        lang_name = "Hindi"
    elif lang == "kn":
        lang_name = "Kannada"

    history_asked = session["asked_questions"][:]
    if user_id:
        history_asked.extend(get_user_history(user_id))

    canonical_skill = skill_mapper.normalize_skill(target_skill) or target_skill
    dataset_available = skill_mapper.has_dataset(canonical_skill)

    def _translate_if_needed(text):
        if lang in ["hi", "kn"]:
            from modules.question_engine import translate_text
            return translate_text(text, lang)
        return text

    # ---- 1. PRIMARY: dataset retrieval ----
    if dataset_available:
        result = question_bank.select_question(canonical_skill, target_difficulty, exclude=history_asked)
        if result:
            print(f"[AdaptiveEngine] Question served from PRIMARY dataset source "
                  f"({canonical_skill}/{result['difficulty_label']}).")
            return _translate_if_needed(result["question"]), "dataset"
        llm_reason = "llm_dataset_exhausted"
        print(f"[AdaptiveEngine] Dataset exhausted for {canonical_skill}/{target_difficulty} "
              f"(candidate has already seen all available {canonical_skill} questions) -> LLM fallback.")
    else:
        llm_reason = "llm_no_dataset_for_skill"
        print(f"[AdaptiveEngine] No dataset backs skill \'{target_skill}\' -> LLM fallback.")

    # ---- 2. FALLBACK: LLM generation (only reached when the dataset could not help) ----
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[WARN] Groq API key missing. Using local safety-net question instead of LLM fallback.")
        q_text = get_fallback_question(session, target_skill, target_difficulty, user_id)
        return _translate_if_needed(q_text), "dataset_safety_net_llm_unavailable"

    history_for_prompt = history_asked[-10:]
    history_str = "\n".join([f"- {q}" for q in history_for_prompt])

    prompt = f"""You are a professional AI Technical Interviewer.
Candidate Details & Status:
Name: {session.get("interviewer", {}).get("candidate_name", "Candidate")}
Detected Resume Skills: {session.get("skills", [])}

Target Question Focus:
Testing Skill/Topic: {target_skill}
Target Difficulty: {target_difficulty.upper()}
Candidate Strong Skills so far: {session.get("strong_areas", [])}
Candidate Weak Skills so far: {session.get("weak_areas", [])}
Covered Skills: {session.get("covered_topics", [])}

Language: {lang_name} (Generate the question directly in native {lang_name} script, e.g. Devanagari for Hindi, Kannada script for Kannada).

CRITICAL - DO NOT repeat or ask anything similar to these previously asked questions:
{history_str if history_str else "(None yet)"}

Guidelines for the question:
1. Target concepts within the topic of {target_skill}.
2. Ensure complexity fits exactly the {target_difficulty.upper()} category.
3. If {target_skill} is in weak areas, generate a supporting, fundamental diagnostic question to check core concepts.
4. If {target_skill} is in strong areas, generate a challenging problem-solving scenario or architectural query.
5. Provide ONLY the final question text in {lang_name}. No introduction, no comments, no markdown formatting.
"""

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a direct, professional technical interviewer. Return only the raw question text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        q_text = completion.choices[0].message.content.strip()

        if q_text.startswith('"') and q_text.endswith('"'):
            q_text = q_text[1:-1]
        elif q_text.startswith("'") and q_text.endswith("'"):
            q_text = q_text[1:-1]

        if is_duplicate_of_any(q_text, history_asked):
            print("[WARN] AI generated a duplicate question. Falling back to local dataset safety net.")
            raise ValueError("Duplicate generated by AI")

        print(f"[AdaptiveEngine] Question served from LLM FALLBACK ({llm_reason}).")
        return q_text, llm_reason
    except Exception as e:
        print(f"[WARN] Groq AI question generation failed: {e}. Falling back to local dataset safety net.")
        q_text = get_fallback_question(session, target_skill, target_difficulty, user_id)
        return _translate_if_needed(q_text), "dataset_safety_net_llm_failed"


def should_interview_finish(session):
    """
    Dynamic Interview Length Decision: Determine if we should end the interview
    based on topic coverage, information gain, and safety boundaries.
    """
    initialize_adaptive_state(session)
    # round_started_at_answer_count is an additive, default-0 offset set by
    # modules/round_manager.py for a multi-round session, so each round gets
    # its own fresh 10-30 question window instead of inheriting the
    # cumulative count from earlier rounds. It is never set for an ordinary
    # single-round session, so total_answered is unchanged there.
    total_answered = len(session.get("answers", [])) - session.get("round_started_at_answer_count", 0)

    # 1. Safety Minimum boundary limit (spec: minimum 12 questions per round)
    if total_answered < 12:
        return False

    # 2. Safety Maximum boundary limit (spec: maximum 25 questions per round)
    if total_answered >= 25:
        return True

    # 3. Check Uncertainty of all resume skills
    uncertainties = session["uncertainty"].values()
    max_uncertainty = max(uncertainties) if uncertainties else 0
    
    # If maximum uncertainty on any skill is low (< 40), it means we have
    # sufficiently evaluated all skills, and can complete early!
    if max_uncertainty < 45:
        print(f"[Length Engine] Confidence high across all topics. Completing early at question {total_answered}.")
        return True
        
    # If we have weak areas that still have high uncertainty, continue
    weak = session["weak_areas"]
    if weak:
        # Check if there is any weak skill with high uncertainty
        for w_skill in weak:
            if session["uncertainty"].get(w_skill, 100) > 40:
                print(f"[Length Engine] Unresolved uncertainty on weak area '{w_skill}'. Continuing interview.")
                return False

    return False
