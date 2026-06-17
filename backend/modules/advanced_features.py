def get_ai_insights(session):
    tech = session.get("technical_scores", [])
    voice = session.get("voice_scores", [])
    answers = session.get("answers", [])

    avg_tech = sum(tech)/len(tech) if tech else 0
    avg_voice = sum(voice)/len(voice) if voice else 0

    weak = []
    for a in answers:
        if a.get("score", 0) < 50:
            weak.append(a.get("question"))

    if avg_voice > 75:
        personality = "Confident Speaker"
    elif avg_voice < 40:
        personality = "Nervous Candidate"
    else:
        personality = "Balanced"

    if avg_tech > 75:
        level = "Strong Candidate"
    elif avg_tech > 50:
        level = "Average Candidate"
    else:
        level = "Needs Improvement"

    return {
        "avg_technical": round(avg_tech, 2),
        "avg_confidence": round(avg_voice, 2),
        "weak_areas": weak[:5],
        "personality": personality,
        "candidate_level": level
    }


def generate_followup_simple(answer):
    if not answer:
        return "Can you elaborate your answer?"

    return f"Can you explain more about: {answer[:60]}?"