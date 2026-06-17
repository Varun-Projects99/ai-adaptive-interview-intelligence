"""
Elite Features Module for InterviewIQ
Provides advanced analytics: Replay, Coaching, Heatmaps, and Skill Analysis.
"""

def generate_replay(session):
    """
    Generates a structured replay of the interview session.
    """
    if not session:
        return {"error": "No session data"}
    
    answers = session.get("answers", [])
    emotions = session.get("emotion_timeline", [])
    
    replay_data = []
    for i, ans in enumerate(answers):
        # Tie emotions to answers if possible, or just provide the timeline
        entry = {
            "index": i + 1,
            "question": ans.get("question"),
            "answer": ans.get("answer"),
            "score": ans.get("score"),
            "feedback": ans.get("feedback"),
            "timestamp_index": i # Simple placeholder for mapping
        }
        replay_data.append(entry)
        
    return {
        "session_id": session.get("id"),
        "total_steps": len(replay_data),
        "replay": replay_data,
        "emotion_summary": emotions[-1] if emotions else {}
    }

def generate_coaching(session):
    """
    Provides personalized coaching based on session performance.
    """
    if not session:
        return {"error": "No session data"}
    
    technical_scores = session.get("technical_scores", [])
    voice_scores = session.get("voice_scores", [])
    violations = session.get("violations", {})
    
    avg_tech = sum(technical_scores) / len(technical_scores) if technical_scores else 0
    avg_voice = sum(voice_scores) / len(voice_scores) if voice_scores else 0
    
    coaching_tips = []
    if avg_tech < 60:
        coaching_tips.append("Focus on deepening your technical knowledge in the identified weak areas.")
    else:
        coaching_tips.append("Strong technical foundation. Try to provide more real-world examples.")
        
    if avg_voice < 60:
        coaching_tips.append("Work on your vocal clarity and confidence. Avoid long pauses.")
    
    if violations.get("total", 0) > 0:
        coaching_tips.append("Maintain better eye contact and avoid switching tabs during the interview.")

    return {
        "session_id": session.get("id"),
        "performance_summary": {
            "technical_aptitude": "High" if avg_tech > 75 else "Moderate" if avg_tech > 50 else "Low",
            "communication_clarity": "High" if avg_voice > 75 else "Moderate" if avg_voice > 50 else "Low"
        },
        "coaching_tips": coaching_tips,
        "next_steps": ["Review fundamental concepts", "Practice mock interviews", "Record and listen to your answers"]
    }

def confidence_heatmap(session):
    """
    Generates a confidence heatmap over the session timeline.
    """
    if not session:
        return {"error": "No session data"}
    
    voice_scores = session.get("voice_scores", [])
    technical_scores = session.get("technical_scores", [])
    
    # Combine scores into a timeline
    heatmap = []
    max_len = max(len(voice_scores), len(technical_scores))
    
    for i in range(max_len):
        v = voice_scores[i] if i < len(voice_scores) else 50
        t = technical_scores[i] if i < len(technical_scores) else 50
        confidence = (v + t) / 2
        heatmap.append({
            "step": i + 1,
            "confidence_level": confidence,
            "intensity": "High" if confidence > 80 else "Medium" if confidence > 50 else "Low"
        })
        
    return {
        "session_id": session.get("id"),
        "heatmap": heatmap,
        "overall_stability": "Stable" if len(heatmap) > 0 else "N/A"
    }

def skill_analysis(session):
    """
    Analyzes skill proficiency based on interview answers.
    """
    if not session:
        return {"error": "No session data"}
    
    skills = session.get("skills", [])
    answers = session.get("answers", [])
    
    skill_performance = {}
    for s in skills:
        relevant_scores = [a["score"] for a in answers if s.lower() in a["question"].lower()]
        if relevant_scores:
            skill_performance[s] = {
                "score": sum(relevant_scores) / len(relevant_scores),
                "status": "Proficient" if (sum(relevant_scores) / len(relevant_scores)) > 70 else "Learning"
            }
        else:
            skill_performance[s] = {"score": 0, "status": "Not Evaluated"}
            
    return {
        "session_id": session.get("id"),
        "skill_proficiency": skill_performance,
        "top_skill": max(skill_performance, key=lambda k: skill_performance[k]["score"]) if skill_performance else "None"
    }
