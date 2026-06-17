"""
Answer Evaluation + Final Report Generator
Uses Claude API to score answers and produce composite performance report.
"""

import os, json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL  = "claude-3-5-sonnet-20240620"


def evaluate_answer(question: str, answer: str, difficulty: str) -> dict:
    if not answer or len(answer.strip()) < 5:
        return {"score":0,"feedback":"No answer provided.",
                "strengths":[],"improvements":["Please provide a detailed answer."]}

    prompt = f"""You are an expert technical interviewer. Evaluate this candidate answer.

Question ({difficulty} difficulty): {question}
Answer: {answer}

Respond ONLY with raw JSON. No markdown, no preamble.
{{
  "score": <0-100>,
  "feedback": "<2-3 sentence summary>",
  "strengths": ["...","..."],
  "improvements": ["...","..."]
}}

Scoring: 85-100=Excellent, 65-84=Good, 45-64=Adequate, 25-44=Weak, 0-24=Incorrect"""

    try:
        res = client.messages.create(model=MODEL, max_tokens=500,
                                     messages=[{"role":"user","content":prompt}])
        raw = res.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[Evaluator] {e}")
        return {"score":50,"feedback":"Evaluation temporarily unavailable.",
                "strengths":["Response provided"],"improvements":["Please elaborate further."]}


def generate_final_report(session: dict) -> dict:
    tech   = session.get("technical_scores", [])
    voice  = session.get("voice_scores", [])
    emot   = session.get("emotion_timeline", [])
    ans    = session.get("answers", [])
    viols  = session.get("violations", {})

    tech_score = int(sum(tech)/len(tech)) if tech else 0
    conf_score = int(sum(voice)/len(voice)) if voice else 0

    emap  = {"confident":1.0,"neutral":0.7,"nervous":0.3,"stressed":0.2}
    avg_e = (sum(emap.get(e.get("dominant_emotion","neutral"),0.5) for e in emot)/len(emot)
             if emot else 0.5)

    elabel = ("Excellent" if avg_e>=0.75 else "Good" if avg_e>=0.55
              else "Moderate" if avg_e>=0.35 else "Needs Improvement")

    readiness = int(tech_score*0.50 + conf_score*0.30 + avg_e*100*0.20)
    rlabel    = ("Interview Ready" if readiness>=80 else "Improving" if readiness>=60
                 else "Needs Practice" if readiness>=40 else "Early Stage")

    # Emotion breakdown %
    ecounts = {}
    for e in emot:
        cat = e.get("dominant_emotion","neutral")
        ecounts[cat] = ecounts.get(cat,0)+1
    total_e = sum(ecounts.values()) or 1
    ebreakdown = {k:round(v/total_e*100,1) for k,v in ecounts.items()}

    return {
        "session_id":  session.get("id"),
        "terminated":  session.get("status") == "terminated",
        "scores": {
            "technical":         tech_score,
            "confidence":        conf_score,
            "emotion_stability": elabel,
            "readiness_index":   readiness,
            "readiness_label":   rlabel
        },
        "summary": {
            "total_questions":        len(ans),
            "skills_covered":         list(set(session.get("skills",[]))),
            "difficulty_progression": [a.get("difficulty","easy") for a in ans],
            "violations":             viols
        },
        "emotion_breakdown":  ebreakdown,
        "answers":            ans,
        "recommendations":    _recommendations(tech_score, conf_score, avg_e)
    }


def _recommendations(tech, conf, emot):
    tips = []
    if tech < 60:  tips.append("Strengthen core technical concepts — review fundamentals and practice coding daily.")
    elif tech < 80: tips.append("Good technical base. Focus on explaining your reasoning clearly with examples.")
    if conf < 50:  tips.append("Work on speaking confidence — record yourself and practice mock answers aloud.")
    if emot < 0.4: tips.append("Practice relaxation techniques before interviews. Deep breathing reduces stress.")
    if tech >= 80 and conf >= 70:
        tips.append("Excellent performance! Target system design and behavioral questions to go further.")
    return tips or ["Solid performance. Keep up regular mock interview practice."]
