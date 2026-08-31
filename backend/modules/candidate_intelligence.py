import os
import json
import datetime
import pymongo

# MongoDB connection setup
MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "interviewiq")

db = None
profiles_col = None

if MONGO_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = mongo_client[MONGO_DB_NAME]
        profiles_col = db["candidate_profiles"]
        profiles_col.create_index([("user_id", 1)], unique=True)
        print("[OK] CandidateIntelligence: MongoDB initialized")
    except Exception as e:
        print(f"[WARN] CandidateIntelligence: MongoDB connection failed: {e}")

def calculate_knowledge_depth(easy_scores, medium_scores, hard_scores):
    """
    Progressive knowledge depth logic (BASIC, INTERMEDIATE, ADVANCED)
    based on actual progressive difficulty performance.
    """
    avg_easy = sum(easy_scores) / len(easy_scores) if easy_scores else None
    avg_medium = sum(medium_scores) / len(medium_scores) if medium_scores else None
    avg_hard = sum(hard_scores) / len(hard_scores) if hard_scores else None

    if avg_hard is not None and avg_hard >= 75:
        return "Advanced"
    
    if avg_medium is not None and avg_medium >= 70:
        if avg_hard is not None and avg_hard >= 50:
            return "Advanced"
        return "Intermediate"
        
    if avg_easy is not None and avg_easy >= 70:
        if avg_medium is not None and avg_medium >= 45:
            return "Intermediate"
        return "Basic"
        
    return "Basic"

def calculate_consistency(scores):
    """Evaluate candidate consistency score variance."""
    if len(scores) < 2:
        return "High"
        
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5
    
    if std_dev <= 15:
        return "High"
    elif std_dev <= 30:
        return "Medium"
    else:
        return "Low"

def calculate_evidence_confidence(count, avg_score, consistency, contradictions_count, uncertainty_count):
    """Weighted evidence confidence score (0-100%)."""
    if count == 0:
        return 0
        
    # 1. Base weight on count (1=25%, 2=50%, 3=75%, 4+=100% of volume score)
    volume_score = min(1.0, count / 4.0) * 50
    
    # 2. Quality weight
    quality_score = (avg_score / 100.0) * 30
    
    # 3. Consistency boost (scaled by quality percentage to avoid rewarding consistent bad scores)
    consistency_map = {"High": 20, "Medium": 10, "Low": 0}
    consistency_score = consistency_map.get(consistency, 10) * (avg_score / 100.0)
    
    total = volume_score + quality_score + consistency_score
    
    # Apply penalties
    total -= contradictions_count * 15
    total -= uncertainty_count * 5
    
    return int(max(0, min(100, total)))

_profiles_cache = {}

def load_candidate_profile(user_id, resume_skills=None):
    """Fetch profile from MongoDB (fallback to in-memory cache) or initialize a new structure."""
    if not user_id:
        # Return transient profile for unauthenticated guests
        return create_blank_profile("guest", resume_skills or [])
        
    # 1. Try PyMongo connection if alive
    if profiles_col is not None:
        try:
            profile = profiles_col.find_one({"user_id": str(user_id)})
            if profile:
                # Sync any new resume skills
                if resume_skills:
                    for s in resume_skills:
                        if s not in profile.get("skills", {}):
                            profile["skills"][s] = {
                                "score": 0, "depth": "Basic", "confidence": 0, "consistency": "High",
                                "evidence_count": 0, "easy_scores": [], "medium_scores": [], "hard_scores": [],
                                "scores": [], "uncertainty_count": 0, "contradictions_count": 0
                            }
                return profile
        except Exception as e:
            print(f"[WARN] Failed to load candidate profile from MongoDB: {e}")
            
    # 2. Try in-memory fallback cache (essential for offline testing)
    if str(user_id) in _profiles_cache:
        profile = _profiles_cache[str(user_id)]
        if resume_skills:
            for s in resume_skills:
                if s not in profile.get("skills", {}):
                    profile["skills"][s] = {
                        "score": 0, "depth": "Basic", "confidence": 0, "consistency": "High",
                        "evidence_count": 0, "easy_scores": [], "medium_scores": [], "hard_scores": [],
                        "scores": [], "uncertainty_count": 0, "contradictions_count": 0
                    }
        return profile
        
    return create_blank_profile(user_id, resume_skills or [])

def save_candidate_profile(profile):
    """Persist candidate profile to MongoDB and update local memory cache."""
    user_id = profile.get("user_id")
    if not user_id or user_id == "guest":
        return
        
    # Always keep in-memory cache updated
    _profiles_cache[str(user_id)] = profile
    
    if profiles_col is not None:
        try:
            profile["updated_at"] = datetime.datetime.utcnow().isoformat()
            profiles_col.replace_one(
                {"user_id": str(user_id)},
                profile,
                upsert=True
            )
        except Exception as e:
            print(f"[WARN] Failed to save candidate profile to MongoDB: {e}")

def create_blank_profile(user_id, skills):
    """Construct an empty candidate profile structure."""
    skills_dict = {}
    for s in skills:
        skills_dict[s] = {
            "score": 0,
            "depth": "Basic",
            "confidence": 0,
            "consistency": "High",
            "evidence_count": 0,
            "easy_scores": [],
            "medium_scores": [],
            "hard_scores": [],
            "scores": [],
            "uncertainty_count": 0,
            "contradictions_count": 0
        }
        
    return {
        "user_id": str(user_id),
        "skills": skills_dict,
        "strong_areas": [],
        "weak_areas": [],
        "contradictions": [],
        "self_corrections": [],
        "knowledge_map": {},
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

def update_candidate_profile_step(session, user_id, question, answer, evaluation, voice_confidence=None):
    """
    Dynamic update called at every step. Analyzes the question & answer to update
    the candidate's dynamic profile, knowledge depth, contradictions, map, and confidence.
    """
    # 1. Load current profile
    profile = load_candidate_profile(user_id, session.get("skills", []))
    
    # 2. Extract skill and difficulty
    skill = evaluation.get("skill") or "General"
    # Find matching resume skill if "General"
    if skill == "General":
        for s in session.get("skills", []):
            if s.lower() in question.lower():
                skill = s
                break
                
    difficulty = evaluation.get("difficulty") or session.get("current_difficulty", "easy")
    score = evaluation.get("score", 50)
    sub_topic = evaluation.get("sub_topic") or "General"

    # Add skill block to profile if it was not detected earlier
    if skill not in profile["skills"]:
        profile["skills"][skill] = {
            "score": 0,
            "depth": "Basic",
            "confidence": 0,
            "consistency": "High",
            "evidence_count": 0,
            "easy_scores": [],
            "medium_scores": [],
            "hard_scores": [],
            "scores": [],
            "uncertainty_count": 0,
            "contradictions_count": 0,
            "technical_correctness_scores": [],
            "relevance_scores": [],
            "depth_scores": [],
            "completeness_scores": [],
            "technical_correctness": 0,
            "relevance": 0,
            "depth_score": 0,
            "completeness": 0
        }
        
    sk = profile["skills"][skill]
    sk["evidence_count"] += 1
    sk["scores"].append(score)
    sk["score"] = int(sum(sk["scores"]) / len(sk["scores"]))
    
    # Update evaluation dimension averages
    dims = evaluation.get("dimensions", {})
    
    tc_score = dims.get("technical_correctness", {}).get("score")
    if tc_score is not None:
        if "technical_correctness_scores" not in sk: sk["technical_correctness_scores"] = []
        sk["technical_correctness_scores"].append(tc_score)
        sk["technical_correctness"] = int(sum(sk["technical_correctness_scores"]) / len(sk["technical_correctness_scores"]))
        
    rel_score = dims.get("relevance", {}).get("score")
    if rel_score is not None:
        if "relevance_scores" not in sk: sk["relevance_scores"] = []
        sk["relevance_scores"].append(rel_score)
        sk["relevance"] = int(sum(sk["relevance_scores"]) / len(sk["relevance_scores"]))
        
    dep_score = dims.get("depth", {}).get("score")
    if dep_score is not None:
        if "depth_scores" not in sk: sk["depth_scores"] = []
        sk["depth_scores"].append(dep_score)
        sk["depth_score"] = int(sum(sk["depth_scores"]) / len(sk["depth_scores"]))
        
    comp_score = dims.get("completeness", {}).get("score")
    if comp_score is not None:
        if "completeness_scores" not in sk: sk["completeness_scores"] = []
        sk["completeness_scores"].append(comp_score)
        sk["completeness"] = int(sum(sk["completeness_scores"]) / len(sk["completeness_scores"]))
    
    # Add score to difficulty bin
    diff_key = f"{difficulty.lower()}_scores"
    if diff_key not in sk:
        sk[diff_key] = []
    sk[diff_key].append(score)

    # 3. Check for uncertainty signals
    uncertainty_eval = evaluation.get("uncertainty", {})
    uncertainty_detected = uncertainty_eval.get("detected", False)
    if not uncertainty_detected:
        # Fallback keyword checks
        ans_lower = answer.lower()
        uncertain_phrases = ["i think", "maybe", "im not sure", "i believe", "probably", "perhaps"]
        if any(p in ans_lower for p in uncertain_phrases) or (voice_confidence is not None and voice_confidence < 50):
            uncertainty_detected = True
            
    if uncertainty_detected:
        sk["uncertainty_count"] += 1
        # Log uncertainty event
        if "uncertainties_log" not in profile:
            profile["uncertainties_log"] = []
        profile["uncertainties_log"].append({
            "session_id": session.get("id"),
            "question": question,
            "answer": answer,
            "skill": skill,
            "voice_confidence": voice_confidence,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # 4. Check for self-corrections
    sc_eval = evaluation.get("self_correction", {})
    if sc_eval.get("detected", False):
        profile["self_corrections"].append({
            "session_id": session.get("id"),
            "skill": skill,
            "original": sc_eval.get("original", ""),
            "corrected": sc_eval.get("corrected", ""),
            "is_correct": sc_eval.get("is_correct", True),
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

    # 5. Check for logical contradictions
    contra_eval = evaluation.get("contradiction", {})
    if contra_eval.get("detected", False):
        sk["contradictions_count"] += 1
        profile["contradictions"].append({
            "session_id": session.get("id"),
            "skill": skill,
            "explanation": contra_eval.get("explanation", "Contradiction detected"),
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    else:
        # Cross-interview validation fallback (e.g. check "never used docker" vs usage statements)
        prev_answers = [a for a in session.get("answers", [])]
        ans_lower = answer.lower()
        if "never used" in ans_lower or "don't know" in ans_lower or "do not know" in ans_lower:
            # Check if they answered positively on same skill earlier
            for prev in prev_answers:
                if prev.get("score", 0) > 75 and skill.lower() in prev.get("question", "").lower():
                    sk["contradictions_count"] += 1
                    profile["contradictions"].append({
                        "session_id": session.get("id"),
                        "skill": skill,
                        "explanation": f"Candidate claimed lack of familiarity, but previously scored {prev.get('score')} demonstrating understanding.",
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    })
                    break

    # 6. Recalculate depth, consistency and confidence
    sk["depth"] = calculate_knowledge_depth(sk.get("easy_scores", []), sk.get("medium_scores", []), sk.get("hard_scores", []))
    sk["consistency"] = calculate_consistency(sk["scores"])
    sk["confidence"] = calculate_evidence_confidence(
        sk["evidence_count"],
        sk["score"],
        sk["consistency"],
        sk["contradictions_count"],
        sk["uncertainty_count"]
    )

    # 7. Update Knowledge Map (nested structure)
    if skill not in profile["knowledge_map"]:
        profile["knowledge_map"][skill] = {}
        
    # Rate subtopic coverage
    level = "Low"
    if score >= 80:
        level = "High"
    elif score >= 60:
        level = "Medium"
    profile["knowledge_map"][skill][sub_topic] = level

    # 8. Update Strong/Weak areas lists
    if sk["evidence_count"] >= 2:
        if sk["score"] >= 80:
            if skill not in profile["strong_areas"]:
                profile["strong_areas"].append(skill)
            if skill in profile["weak_areas"]:
                profile["weak_areas"].remove(skill)
        elif sk["score"] < 60:
            if skill not in profile["weak_areas"]:
                profile["weak_areas"].append(skill)
            if skill in profile["strong_areas"]:
                profile["strong_areas"].remove(skill)
        else:
            if skill in profile["strong_areas"]:
                profile["strong_areas"].remove(skill)
            if skill in profile["weak_areas"]:
                profile["weak_areas"].remove(skill)

    # 9. Sync changes back to active session
    session["skill_scores"] = {k: v["score"] for k, v in profile["skills"].items()}
    session["strong_areas"] = profile["strong_areas"]
    session["weak_areas"] = profile["weak_areas"]
    
    # 10. Persist profile document
    save_candidate_profile(profile)
    
    # Also attach the active updated profile inside the session for easy dashboarding/reporting
    session["candidate_profile"] = profile
    return profile
