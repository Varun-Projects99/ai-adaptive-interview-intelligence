import os
import json
import random
import re
import pymongo

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

def stem_word(word):
    """Simple stemmer to normalize plurals for comparison by removing trailing 's'."""
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word

def normalize_text(text):
    """Tokenize and normalize question text for Jaccard similarity."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    words = text.split()
    
    filler_words = {
        "what", "is", "the", "difference", "between", "a", "an", "and", "in", 
        "of", "to", "for", "with", "on", "describe", "tell", "me", "about", 
        "write", "code", "use", "using", "why", "does", "can", "you", "show", 
        "give", "example", "concept", "how", "are", "from", "do", "does", 
        "did", "explain", "different", "would", "your", "we", "us", "our",
        "they", "them", "he", "she", "it", "this", "that", "these", "those"
    }
    
    filtered = [stem_word(w) for w in words if w not in filler_words]
    return set(filtered)

def are_questions_similar(q1, q2, threshold=0.55):
    """Check Jaccard similarity of two normalized questions."""
    w1 = normalize_text(q1)
    w2 = normalize_text(q2)
    if not w1 or not w2:
        return False
    intersection = w1.intersection(w2)
    union = w1.union(w2)
    similarity = len(intersection) / len(union)
    return similarity >= threshold

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

def add_to_user_history(user_id, session_id, question_text, skill):
    """Record asked question to MongoDB to prevent future repetitions."""
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
            "skill": skill
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
        add_to_user_history(user_id, session["id"], question_text, skill)

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
        if recent_perf < 40:
            difficulty = "easy"
        elif recent_perf < 60:
            difficulty = "medium" if recent_perf >= 50 else "easy"
        elif recent_perf < 75:
            difficulty = "medium"
        elif recent_perf < 90:
            difficulty = "hard" if recent_perf >= 82 else "medium"
        else:
            difficulty = "hard"
        reason = f"Practice session: recent performance {recent_perf}% mapped to {difficulty}."
        return (selected_skill, difficulty, reason)

    # Check dynamic profile for this skill's persistent depth
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
    Select an appropriate fallback question from local JSON datasets,
    ensuring it matches skill and difficulty, and passes repetition filtering.
    """
    initialize_adaptive_state(session, user_id)
    
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(modules_dir)
    workspace_dir = os.path.dirname(backend_dir)
    
    datasets_dir = os.path.join(workspace_dir, "datasets")
    if not os.path.exists(datasets_dir):
        datasets_dir = os.path.join(backend_dir, "datasets")

    DATASET_MAP = {
        "Python": "python.json", "Java": "java.json", "C": "c.json", "C++": "cpp.json",
        "DSA": "dsa.json", "DBMS": "dbms.json", "OS": "os.json", "CN": "cn.json",
        "SQL": "sql.json", "HTML/CSS": "html_css.json", "JavaScript": "javascript.json",
        "React": "react.json", "DevOps": "devops.json", "AWS": "aws.json",
        "AI/ML": "ai_ml.json", "HR": "hr.json", "Aptitude": "aptitude.json",
        "Cybersecurity": "cybersecurity.json"
    }

    filename = DATASET_MAP.get(target_skill)
    if not filename:
        filename = "hr.json"  # default fallback
        
    file_path = os.path.join(datasets_dir, filename)
    candidates = []
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                q_list = json.load(f)
                for q in q_list:
                    if q.get("difficulty", "").lower() == target_difficulty.lower():
                        candidates.append(q["question"])
        except Exception as e:
            print(f"[WARN] Error reading dataset {filename}: {e}")

    # If no matching difficulty found, get any from the dataset
    if not candidates and os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                q_list = json.load(f)
                candidates = [q["question"] for q in q_list]
        except:
            pass

    # Hardcoded global safety fallbacks
    if not candidates:
        candidates = [
            "Explain your understanding of scalability in system engineering.",
            "How do you design secure Rest APIs?",
            "Explain time and space complexity of sorting algorithms."
        ]

    # Gather user's total historic questions to prevent duplicates
    history_asked = session["asked_questions"][:]
    if user_id:
        history_asked.extend(get_user_history(user_id))

    # Filter out candidates similar to previously asked questions
    fresh_candidates = []
    for c in candidates:
        is_dup = False
        for prev in history_asked:
            if are_questions_similar(c, prev):
                is_dup = True
                break
        if not is_dup:
            fresh_candidates.append(c)

    # Return a unique question if possible, else return a random candidate
    if fresh_candidates:
        return random.choice(fresh_candidates)
    return random.choice(candidates)

def generate_adaptive_question(session, target_skill, target_difficulty, user_id=None):
    """
    Generate a question using Groq LLM with full context of candidate performance,
    repetition prevention, and fallback to local JSON database.
    """
    initialize_adaptive_state(session, user_id)
    api_key = os.environ.get("GROQ_API_KEY")
    
    # Check language configuration
    lang = session.get("interviewer", {}).get("language", "en")
    lang_name = "English"
    if lang == "hi":
        lang_name = "Hindi"
    elif lang == "kn":
        lang_name = "Kannada"

    if not api_key:
        print("[WARN] Groq API key missing. Fetching from local fallback database.")
        q_text = get_fallback_question(session, target_skill, target_difficulty, user_id)
        if lang in ["hi", "kn"]:
            from modules.question_engine import translate_text
            q_text = translate_text(q_text, lang)
        return q_text

    # Prepare historic questions to pass as anti-examples to AI
    history_asked = session["asked_questions"][-10:]
    if user_id:
        history_asked.extend(get_user_history(user_id)[-10:])
        
    history_str = "\n".join([f"- {q}" for q in history_asked])

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
        
        # Cleanup quotes if LLM returned them
        if q_text.startswith('"') and q_text.endswith('"'):
            q_text = q_text[1:-1]
        elif q_text.startswith("'") and q_text.endswith("'"):
            q_text = q_text[1:-1]
            
        # Repetition sanity check on AI generated question
        is_dup = False
        for prev in history_asked:
            if are_questions_similar(q_text, prev):
                is_dup = True
                break
                
        if is_dup:
            print("[WARN] AI generated a duplicate question. Fetching from local fallback database.")
            raise ValueError("Duplicate generated by AI")

        return q_text
    except Exception as e:
        print(f"[WARN] Groq AI question generation failed: {e}. Falling back to local database.")
        q_text = get_fallback_question(session, target_skill, target_difficulty, user_id)
        if lang in ["hi", "kn"]:
            from modules.question_engine import translate_text
            q_text = translate_text(q_text, lang)
        return q_text

def should_interview_finish(session):
    """
    Dynamic Interview Length Decision: Determine if we should end the interview
    based on topic coverage, information gain, and safety boundaries.
    """
    initialize_adaptive_state(session)
    total_answered = len(session.get("answers", []))
    
    # 1. Safety Minimum boundary limit
    if total_answered < 10:
        return False
        
    # 2. Safety Maximum boundary limit
    if total_answered >= 30:
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
