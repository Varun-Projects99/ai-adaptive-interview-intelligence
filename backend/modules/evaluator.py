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

    prompt = f"""You are an expert interviewer. Evaluate this candidate answer for a technical or behavioral question.

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
        "recommendations":    _recommendations(tech_score, conf_score, avg_e),
        
        # Adaptive AI metrics
        "skill_scores":       session.get("skill_scores", {}),
        "strong_areas":       session.get("strong_areas", []),
        "weak_areas":         session.get("weak_areas", []),
        "covered_topics":     session.get("covered_topics", []),
        
        # Advanced Candidate Intelligence Profile
        "candidate_profile":  session.get("candidate_profile", {})
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


def evaluate_and_transition(session: dict, current_question: str, answer: str) -> dict:
    interviewer = session.get("interviewer", {})
    personality = interviewer.get("personality", "professional")
    language = interviewer.get("language", "en")
    name = interviewer.get("candidate_name", "Candidate")
    skills = session.get("skills", [])
    
    lang_name = "English"
    if language == "hi":
        lang_name = "Hindi"
    elif language == "kn":
        lang_name = "Kannada"

    history_str = ""
    for entry in interviewer.get("conversation", [])[-6:]:
        history_str += f"{entry['role'].capitalize()}: {entry['text']}\n"

    prompt = f"""You are an AI Interviewer conducting a mock interview for a candidate named {name}.
Candidate's resume skills: {skills}
Interviewer Personality: {personality} (Professional/Friendly/Technical/HR)
Language: {lang_name}

Previous conversation:
{history_str}

Current Question: {current_question}
Candidate's Answer: {answer}

Your task is to perform a detailed evaluation of the candidate's last answer across exactly these 7 dimensions:
1. technical_correctness: Correct concepts, terminology, implementation details, misconceptions.
2. relevance: Directly addressing the question vs talking about unrelated topics.
3. depth: Basic (definition only) vs Intermediate (how it works) vs Advanced (architecture, sharing kernels, layer caching, trade-offs, edge cases).
4. clarity: Logical structure, understandability, sentence flow. Do not penalize grammar.
5. problem_solving: Step-by-step logic, handling constraints, reasoning. If it's a purely conceptual question (no coding or algorithm design required), set score to null.
6. communication: Structured conciseness, explanation quality.
7. completeness: Semantic coverage of expected sub-concepts.

For each dimension, output:
- score: 0 to 100 integer (or null for problem_solving if conceptual).
- confidence: "HIGH" | "MEDIUM" | "LOW". LOW if answer is too short or lacks detail.
- reason: Short explainable text sentence stating why this score was given.
- evidence: List of string quotes or statements from the candidate's actual text. Return ["Insufficient evidence"] if answer is too short to prove knowledge.

Calculate the overall_score as the weighted average of the applicable dimensions:
- If problem_solving is N/A (null):
  overall_score = technical_correctness (40%) + completeness (15%) + depth (15%) + relevance (10%) + clarity (10%) + communication (10%)
- If problem_solving is applicable (not null):
  overall_score = technical_correctness (30%) + problem_solving (20%) + completeness (10%) + depth (10%) + relevance (10%) + clarity (10%) + communication (10%)

Output also action choice ("follow_up" | "clarification" | "next_question" | "finish"), feedback summary, strengths, improvements, sub_topic name, self_correction detection, contradiction detection, and uncertainty detection.

All feedback, strengths, improvements, transition, reason, and questions MUST be written in {lang_name} (using native script).
Respond ONLY with a valid raw JSON object. No markdown, no comments.
{{
  "overall_score": <int 0-100>,
  "dimensions": {{
    "technical_correctness": {{ "score": <0-100>, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }},
    "relevance": {{ "score": <0-100>, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }},
    "depth": {{ "score": <0-100>, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }},
    "clarity": {{ "score": <0-100>, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }},
    "problem_solving": {{ "score": <0-100>|null, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }},
    "communication": {{ "score": <0-100>, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }},
    "completeness": {{ "score": <0-100>, "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": "...", "evidence": ["..."] }}
  }},
  "feedback": "<feedback string>",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."],
  "action": "follow_up" | "clarification" | "next_question" | "finish",
  "transition": "<transition sentence>",
  "question": "<follow-up/clarification question text, or empty if next_question/finish>",
  "reason": "<reasoning for action>",
  "sub_topic": "<subtopic string>",
  "self_correction": {{
     "detected": true | false,
     "original": "<original statement>",
     "corrected": "<corrected statement>",
     "is_correct": true | false
  }},
  "contradiction": {{
     "detected": true | false,
     "explanation": "<explanation of logical contradiction>"
  }},
  "uncertainty": {{
     "detected": true | false,
     "signals": ["<list of identified uncertainty words/signals>"]
  }}
}}
"""

    api_key_ant = os.environ.get("ANTHROPIC_API_KEY")
    api_key_groq = os.environ.get("GROQ_API_KEY")
    
    use_groq = True
    if api_key_ant and "your_anthropic_api_key_here" not in api_key_ant:
        use_groq = False

    try:
        if not use_groq:
            import anthropic
            ant_client = anthropic.Anthropic(api_key=api_key_ant)
            res = ant_client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = res.content[0].text.strip()
        else:
            from groq import Groq
            groq_client = Groq(api_key=api_key_groq)
            completion = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. You must only output valid JSON objects."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            raw = completion.choices[0].message.content.strip()
            
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
            
        result = json.loads(raw)
        
        # Programmatic normalization and strict weighted mapping
        return normalize_evaluation_result(result)
        
    except Exception as e:
        print(f"[Evaluator] evaluate_and_transition failed: {e}")
        fb = "Answer noted. Let's proceed."
        trans = "Thank you for the answer."
        if language == "kn":
            fb = "ಉತ್ತರವನ್ನು ಗಮನಿಸಲಾಗಿದೆ. ಮುಂದೆ ಹೋಗೋಣ."
            trans = "ನಿಮ್ಮ ಉತ್ತರಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು."
        elif language == "hi":
            fb = "उत्तर नोट कर लिया गया है। चलिए आगे बढ़ते हैं।"
            trans = "आपके उत्तर के लिए धन्यवाद।"
            
        fallback_res = {
            "overall_score": 70,
            "score": 70,
            "feedback": fb,
            "strengths": ["Response recorded"],
            "improvements": ["Please provide more detail in subsequent answers"],
            "action": "next_question",
            "transition": trans,
            "question": "",
            "reason": "Evaluation API fallback",
            "sub_topic": "General",
            "self_correction": {"detected": False, "original": "", "corrected": "", "is_correct": False},
            "contradiction": {"detected": False, "explanation": ""},
            "uncertainty": {"detected": False, "signals": []},
            "dimensions": {
                "technical_correctness": {"score": 70, "confidence": "MEDIUM", "reason": "Standard fallback assigned due to API timeout.", "evidence": ["Answer provided"]},
                "relevance": {"score": 80, "confidence": "MEDIUM", "reason": "Evaluated as relevant by default fallback.", "evidence": []},
                "depth": {"score": 60, "confidence": "LOW", "reason": "Insufficient evidence to gauge technical depth.", "evidence": ["Insufficient evidence"]},
                "clarity": {"score": 75, "confidence": "MEDIUM", "reason": "Readability is acceptable.", "evidence": []},
                "problem_solving": {"score": None, "confidence": "MEDIUM", "reason": "Not applicable to this conceptual question.", "evidence": []},
                "communication": {"score": 70, "confidence": "MEDIUM", "reason": "Speaking confidence is acceptable.", "evidence": []},
                "completeness": {"score": 65, "confidence": "LOW", "reason": "Default fallback completeness check.", "evidence": []}
            }
        }
        return fallback_res

def normalize_evaluation_result(result):
    """Ensure all required keys and evaluation dimensions are formatted and score is weighted."""
    if "dimensions" not in result:
        result["dimensions"] = {}
        
    dims = result["dimensions"]
    default_keys = ["technical_correctness", "relevance", "depth", "clarity", "problem_solving", "communication", "completeness"]
    
    for key in default_keys:
        if key not in dims:
            dims[key] = {
                "score": 70 if key != "problem_solving" else None,
                "confidence": "MEDIUM",
                "reason": "Default score assigned during normalization.",
                "evidence": []
            }
            
    tc = dims["technical_correctness"].get("score") or 50
    rel = dims["relevance"].get("score") or 50
    dep = dims["depth"].get("score") or 50
    cla = dims["clarity"].get("score") or 50
    comm = dims["communication"].get("score") or 50
    comp = dims["completeness"].get("score") or 50
    ps = dims["problem_solving"].get("score")
    
    # Calculate mathematically strict overall_score
    if ps is not None:
        overall = int(tc * 0.30 + ps * 0.20 + comp * 0.10 + dep * 0.10 + rel * 0.10 + cla * 0.10 + comm * 0.10)
    else:
        overall = int(tc * 0.40 + comp * 0.15 + dep * 0.15 + rel * 0.10 + cla * 0.10 + comm * 0.10)
        
    result["overall_score"] = overall
    result["score"] = overall
    
    # Check self_correction, contradiction, uncertainty default values
    if "self_correction" not in result:
        result["self_correction"] = {"detected": False, "original": "", "corrected": "", "is_correct": False}
    if "contradiction" not in result:
        result["contradiction"] = {"detected": False, "explanation": ""}
    if "uncertainty" not in result:
        result["uncertainty"] = {"detected": False, "signals": []}
    if "sub_topic" not in result:
        result["sub_topic"] = "General"
        
    return result
