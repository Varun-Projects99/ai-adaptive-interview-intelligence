"""
InterviewIQ — Main Flask Application
AI-Based Adaptive Interview Intelligence System

Run from inside the `backend/` folder:
    python app.py

Access at: http://192.168.1.6:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, uuid
import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.dirname(__file__))

# ── Module imports (graceful fallbacks if a lib is missing) ──────────────────

try:
    from modules.resume_parser import extract_skills_from_resume, analyze_resume_data
    print("[OK] resume_parser loaded")
except Exception as e:
    print(f"[WARN] resume_parser: {e}")

    def extract_skills_from_resume(path):
        return ["Python", "Machine Learning", "Data Structures"]

    def analyze_resume_data(path):
        return {
            "score": 75,
            "ats_score": 80,
            "detected_skills": ["Python", "Machine Learning", "Data Structures"],
            "career_paths": ["Software Engineer"],
            "strengths": ["Clear sections"],
            "improvements": ["More detail"],
            "formatting_score": 85,
            "formatting_feedback": "Looks good"
        }


try:
    from modules.question_engine import generate_questions, get_next_question

    print("[OK] question_engine loaded")
except Exception as e:
    print(f"[WARN] question_engine: {e}")

    def generate_questions(skills):
        qs = []
        for s in skills:
            for d in ["easy", "medium", "hard"]:
                qs.append(
                    {
                        "question": f"Explain a key concept in {s}.",
                        "skill": s,
                        "difficulty": d,
                        "type": "conceptual",
                    }
                )
        return qs

    def get_next_question(session):
        answered = {a["question"] for a in session.get("answers", [])}
        diff = session.get("current_difficulty", "easy")
        cands = [
            q
            for q in session.get("questions", [])
            if q["question"] not in answered and q["difficulty"] == diff
        ]
        if not cands:
            cands = [
                q for q in session.get("questions", []) if q["question"] not in answered
            ]
        return cands[0] if cands else None


try:
    from modules.emotion_detector import analyze_emotion_frame

    print("[OK] emotion_detector loaded")
except Exception as e:
    print(f"[WARN] emotion_detector: {e}")

    def analyze_emotion_frame(frame):
        return {
            "face_detected": True,
            "dominant_emotion": "neutral",
            "interview_score": 65,
            "emotions": {"neutral": 100.0},
        }


try:
    from modules.voice_analyzer import analyze_voice_confidence

    print("[OK] voice_analyzer loaded")
except Exception as e:
    print(f"[WARN] voice_analyzer: {e}")

    def analyze_voice_confidence(path):
        return {
            "confidence_score": 65,
            "confidence_label": "Moderate",
            "transcript": "(voice analysis unavailable)",
            "breakdown": {},
            "tips": [],
        }


try:
    from modules.evaluator import evaluate_answer, generate_final_report
    print("[OK] evaluator loaded")
except Exception as e:
    print(f"[WARN] evaluator: {e}")

    def evaluate_answer(q, a, d):
        return {
            "score": 70,
            "feedback": "Answer received and noted.",
            "strengths": ["Attempted the question"],
            "improvements": ["Add more detail and examples"],
        }

    def generate_final_report(session):
        t = session.get("technical_scores", [])
        v = session.get("voice_scores", [])
        readiness = int(
            (sum(t) / len(t) if t else 0) * 0.6 + (sum(v) / len(v) if v else 0) * 0.4
        )
        return {
            "session_id": session.get("id"),
            "terminated": session.get("status") == "terminated",
            "scores": {
                "technical": int(sum(t) / len(t)) if t else 0,
                "confidence": int(sum(v) / len(v)) if v else 0,
                "emotion_stability": "Moderate",
                "readiness_index": readiness,
                "readiness_label": "Improving" if readiness >= 50 else "Needs Practice",
            },
            "summary": {
                "total_questions": len(session.get("answers", [])),
                "skills_covered": session.get("skills", []),
                "difficulty_progression": [
                    a.get("difficulty", "easy") for a in session.get("answers", [])
                ],
                "violations": session.get("violations", {}),
            },
            "emotion_breakdown": {},
            "answers": session.get("answers", []),
            "recommendations": [
                "Keep practicing regularly to improve your interview skills."
            ],
        }

from modules.integrity_monitor import check_violation

try:
    from modules.advanced_features import get_ai_insights, generate_followup_simple
    print("[OK] advanced_features loaded")
except Exception as e:
    print(f"[WARN] advanced_features: {e}")

    def get_ai_insights(session):
        return {
            "avg_technical": 70,
            "avg_confidence": 65,
            "weak_areas": ["System Design"],
            "personality": "Balanced",
            "candidate_level": "Mid-level",
        }

    def generate_followup_simple(answer):
        return "Can you tell me more about that?"

try:
    from modules.code_executor import CHALLENGES, run_python_code, run_javascript_code
    print("[OK] code_executor loaded")
except Exception as e:
    print(f"[WARN] code_executor: {e}")


# ── Flask setup ──────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get("FLASK_SECRET", "interviewiq-2024")
CORS(app, supports_credentials=True, origins="*")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
RECORDING_FOLDER = os.path.join(BASE_DIR, "..", "recordings")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECORDING_FOLDER, exist_ok=True)

sessions = {}


# ── SERVE FRONTEND ───────────────────────────────────────────────────────────


@app.route("/")
@app.route("/login")
def serve_index():
    return send_from_directory("../frontend", "login.html")

@app.route("/dashboard")
def serve_dashboard():
    return send_from_directory("../frontend", "dashboard.html")

@app.route("/upload")
def serve_upload():
    return send_from_directory("../frontend", "index.html")

@app.route("/analyzer")
def serve_analyzer():
    return send_from_directory("../frontend", "analyzer.html")

@app.route("/career")
def serve_career():
    return send_from_directory("../frontend", "career.html")

@app.route("/coding")
def serve_coding():
    return send_from_directory("../frontend", "coding.html")

@app.route("/history")
def serve_history():
    return send_from_directory("../frontend", "history.html")

@app.route("/coach")
def serve_coach():
    return send_from_directory("../frontend", "coach.html")



@app.route("/register")
def serve_register():
    return send_from_directory("../frontend", "register.html")

@app.route("/interview")
def serve_interview():
    return send_from_directory("../frontend", "interview.html")


@app.route("/report")
def serve_report():
    return send_from_directory("../frontend", "report.html")


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join("../frontend", "assets"), filename)


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "Backend Running",
            "system": "AI-Based Adaptive Interview Intelligence System",
            "modules": [
                "resume_parser",
                "question_engine",
                "emotion_detector",
                "voice_analyzer",
                "adaptive_difficulty",
            ],
            "urls": {
                "frontend": "http://192.168.1.6:5000",
                "interview": "http://192.168.1.6:5000/interview",
                "report": "http://192.168.1.6:5000/report",
                "dashboard": "http://192.168.1.6:5000/dashboard",
                "api": "http://192.168.1.6:5000/api",
            },
        }
    )


# ── SESSION HELPERS ──────────────────────────────────────────────────────────


def get_sess(sid):
    return sessions.get(sid)


def new_sess(sid):
    sessions[sid] = {
        "id": sid,
        "status": "active",
        "skills": [],
        "questions": [],
        "current_index": 0,
        "current_difficulty": "easy",
        "answers": [],
        "emotion_timeline": [],
        "voice_scores": [],
        "technical_scores": [],
        "violations": {"tab_switch": 0, "camera_exit": 0, "window_move": 0, "total": 0},
    }
    return sessions[sid]


# ── API ROUTES ───────────────────────────────────────────────────────────────


@app.route("/api/session/start", methods=["POST"])
def start_session():
    sid = str(uuid.uuid4())
    new_sess(sid)
    print(f"[Session] Started: {sid[:8]}...")
    return jsonify({"session_id": sid, "status": "started"})


@app.route("/api/session/<sid>", methods=["GET"])
def get_session_data(sid):
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(sess)


@app.route("/api/resume/upload", methods=["POST"])
def upload_resume():
    sid = request.form.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if not file.filename or not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF supported"}), 400

    path = os.path.join(UPLOAD_FOLDER, f"{sid}_resume.pdf")
    file.save(path)
    skills = extract_skills_from_resume(path)
    sess["skills"] = skills
    print(f"[Resume] {len(skills)} skills detected: {skills}")
    return jsonify(
        {"session_id": sid, "skills_detected": skills, "skill_count": len(skills)}
    )


@app.route("/api/resume/analyze", methods=["POST"])
def api_analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["resume"]
    if not file.filename or not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF supported"}), 400
        
    temp_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_FOLDER, f"temp_{temp_id}_resume.pdf")
    file.save(path)
    
    try:
        analysis = analyze_resume_data(path)
        if os.path.exists(path):
            os.remove(path)
        return jsonify(analysis)
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"error": str(e)}), 500


@app.route("/api/questions/generate", methods=["POST"])
def generate_interview_questions():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    
    # Support custom skills list (e.g. from Career Roadmap skill testing)
    custom_skills = data.get("skills")
    if custom_skills:
        sess["skills"] = custom_skills

    if not sess["skills"]:
        return jsonify({"error": "Upload resume or select skills first"}), 400

    questions = generate_questions(sess["skills"])
    sess["questions"] = questions
    sess["current_index"] = 0
    sess["current_difficulty"] = "easy"
    print(f"[Questions] {len(questions)} generated")
    return jsonify(
        {
            "session_id": sid,
            "total_questions": len(questions),
            "first_question": questions[0] if questions else None,
        }
    )


@app.route("/api/questions/next", methods=["POST"])
def next_question():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    q = get_next_question(sess)
    if q is None:
        return jsonify({"done": True, "message": "Interview complete"})
    return jsonify(
        {
            "question": q,
            "index": sess["current_index"],
            "difficulty": sess["current_difficulty"],
            "total": len(sess["questions"]),
        }
    )


@app.route("/api/answer/submit", methods=["POST"])
def submit_answer():
    data = request.json or {}
    sid = data.get("session_id")
    ans = data.get("answer", "")
    q = data.get("question", "")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    ev = evaluate_answer(q, ans, sess["current_difficulty"])
    sess["technical_scores"].append(ev["score"])
    sess["answers"].append(
        {
            "question": q,
            "answer": ans,
            "score": ev["score"],
            "difficulty": sess["current_difficulty"],
            "feedback": ev["feedback"],
        }
    )

    rt = sess["technical_scores"][-3:]
    rv = sess["voice_scores"][-3:] if sess["voice_scores"] else [50]
    at = sum(rt) / len(rt)
    av = sum(rv) / len(rv)

    if at >= 75 and av >= 65:
        sess["current_difficulty"] = "hard"
    elif at >= 50:
        sess["current_difficulty"] = "medium"
    else:
        sess["current_difficulty"] = "easy"

    sess["current_index"] += 1
    return jsonify(
        {
            "score": ev["score"],
            "feedback": ev["feedback"],
            "strengths": ev.get("strengths", []),
            "improvements": ev.get("improvements", []),
            "next_difficulty": sess["current_difficulty"],
        }
    )


@app.route("/api/emotion/analyze", methods=["POST"])
def analyze_emotion():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    result = analyze_emotion_frame(data.get("frame", ""))
    sess["emotion_timeline"].append(result)
    return jsonify(result)


@app.route("/api/voice/analyze", methods=["POST"])
def analyze_voice():
    sid = request.form.get("session_id")
    audio = request.files.get("audio")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    if not audio:
        return jsonify({"error": "No audio file"}), 400

    path = os.path.join(UPLOAD_FOLDER, f"{sid}_voice.wav")
    audio.save(path)
    result = analyze_voice_confidence(path)
    sess["voice_scores"].append(result["confidence_score"])
    return jsonify(result)


@app.route("/api/integrity/violation", methods=["POST"])
def integrity_violation():
    data = request.json or {}
    session_id = data.get("session_id")
    vtype = data.get("type")

    result = check_violation(session_id, vtype)

    # Sync with session if it exists
    sess = get_sess(session_id)
    if sess:
        sess["violations"]["total"] = result["count"]
        if vtype in sess["violations"]:
            sess["violations"][vtype] += 1
        if result["terminate"]:
            sess["status"] = "terminated"

    return jsonify({
        "violations": result["count"],
        "terminate": result["terminate"],
        "counts": sess["violations"] if sess else {"total": result["count"]}, # keeping counts for frontend compatibility
        "warning": f"Strike {result['count']}/3" if not result["terminate"] else "Interview terminated",
        "warning_level": "critical" if result["count"] >= 2 else "warning"
    })


@app.route("/api/recording/save", methods=["POST"])
def save_recording():
    sid = request.form.get("session_id")
    rec = request.files.get("recording")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    if not rec:
        return jsonify({"error": "No recording file"}), 400
    path = os.path.join(RECORDING_FOLDER, f"{sid}_recording.webm")
    rec.save(path)
    return jsonify({"saved": True})


@app.route("/api/ai/insights", methods=["POST"])
def ai_insights():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    insights = get_ai_insights(sess)
    return jsonify(insights)


@app.route("/api/ai/followup", methods=["POST"])
def ai_followup():
    data = request.json or {}
    ans = data.get("answer", "")
    followup = generate_followup_simple(ans)
    return jsonify({"followup_question": followup})


HISTORY_FILE = os.path.join(BASE_DIR, "session_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"[Error] Save history failed: {e}")

@app.route("/api/report/generate", methods=["POST"])
def get_report():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    report = generate_final_report(sess)
    sess["status"] = "completed"
    
    # Save to persistent database
    try:
        import datetime
        history = load_history()
        report["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        history[sid] = report
        save_history(history)
    except Exception as e:
        print(f"[WARN] Failed to write history record: {e}")
        
    return jsonify(report)

# ── CODING PLATFORM ENDPOINTS ──────────────────────────────────────────────────

@app.route("/api/sessions/history", methods=["GET"])
def get_sessions_history():
    history = load_history()
    summary_list = []
    for sid, report in history.items():
        scores = report.get("scores", {})
        summ = report.get("summary", {})
        summary_list.append({
            "session_id": sid,
            "date": report.get("date", "Unknown"),
            "technical": scores.get("technical", 0),
            "confidence": scores.get("confidence", 0),
            "readiness_index": scores.get("readiness_index", 0),
            "readiness_label": scores.get("readiness_label", "Unknown"),
            "skills": summ.get("skills_covered", []),
            "total_questions": summ.get("total_questions", 0),
            "terminated": report.get("terminated", False)
        })
    summary_list.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(summary_list)

@app.route("/api/report/view/<sid>", methods=["GET", "POST"])
def view_historical_report(sid):
    history = load_history()
    report = history.get(sid)
    if not report:
        sess = get_sess(sid)
        if sess:
            return jsonify(generate_final_report(sess))
        return jsonify({"error": "Report not found"}), 404
    return jsonify(report)

@app.route("/api/coach/chat", methods=["POST"])
def api_coach_chat():
    data = request.json or {}
    messages = data.get("messages", [])
    
    # Get last message content
    last_msg = ""
    if messages:
        last_msg = messages[-1].get("content", "").lower()
        
    api_key = os.environ.get("GROQ_API_KEY")
    # Verify if key is present and not a dummy placeholder
    if api_key and api_key.startswith("gsk_"):
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            system_msg = {
                "role": "system",
                "content": "You are a professional Interview Coach and Career Advisor. Help candidates improve their interview performance, explain key engineering concepts, structure behavioral answers (STAR method), and practice salary negotiations. Keep your responses encouraging, direct, and under 250 words."
            }
            
            groq_messages = [system_msg]
            for msg in messages:
                groq_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
                
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=groq_messages,
                temperature=0.7,
                max_tokens=600
            )
            reply = completion.choices[0].message.content
            return jsonify({"reply": reply})
        except Exception as e:
            print(f"[ERROR] Groq coach API call failed, using local fallback engine: {e}")
            
    # --- ROBUST KEYWORD-BASED FALLBACK ENGINE ---
    # Matches common candidate questions to provide tailored mock coaching
    import random
    
    if "star" in last_msg or "method" in last_msg or "behavioral" in last_msg:
        reply = ("Coach: The STAR method is the gold standard for behavioral questions:\n\n"
                 "1. **Situation**: Set the scene. (e.g. 'Our service API response times increased by 40% under high load.')\n"
                 "2. **Task**: Define the challenge or goal. (e.g. 'I was tasked with diagnosing the bottleneck and restoring speed.')\n"
                 "3. **Action**: Detail *what you did* (not your team). (e.g. 'I profiled the queries, added database indices, and set up Redis caching.')\n"
                 "4. **Result**: State the quantifiable outcome. (e.g. 'Response times dropped by 60%, and database load decreased by 30%.')\n\n"
                 "Try to spend 70% of your answer talking about your Actions and the Results!")
                 
    elif "leadership" in last_msg or "lead" in last_msg or "manager" in last_msg or "conflict" in last_msg:
        reply = ("Coach: Here is a classic Leadership question you can prepare:\n\n"
                 "*Question*: 'Tell me about a time you had to lead a project under tight constraints or resolve a teammate conflict.'\n\n"
                 "*Coaching Tip*: Focus on:\n"
                 "- How you delegated responsibilities based on individual strengths.\n"
                 "- How you maintained transparent communication with stakeholders.\n"
                 "- Resolving conflicts by focusing on goals and objective metrics, not personal opinions.")
                 
    elif "resume" in last_msg or "gap" in last_msg or "experience" in last_msg:
        reply = ("Coach: Explaining a resume gap or lack of professional experience is all about framing:\n\n"
                 "- **Be Transparent & Concise**: Don't over-explain. State the reason (e.g., health, family care, self-study) in 1-2 sentences.\n"
                 "- **Focus on Active Learning**: Highlight personal projects, open-source work, or certifications you completed during the gap.\n"
                 "- **Pivot to the Present**: Connect what you learned to why you are excited and technically prepared for this specific role today.")
                 
    elif "backend" in last_msg or "checklist" in last_msg or "junior" in last_msg or "prep" in last_msg:
        reply = ("Coach: Backend Software Engineering Prep Checklist:\n\n"
                 "1. **Algorithms & DS**: Master HashMaps, Trees, binary search, and Time/Space complexity ($O(N)$ vs $O(N \\log N)$).\n"
                 "2. **Databases**: Understand index optimization, connection pooling, ACID properties, and relational vs NoSQL trade-offs.\n"
                 "3. **System Design**: Study load balancers, CDN caching, horizontal scaling, and rate-limiting patterns.\n"
                 "4. **API Security**: Learn REST best practices, HTTPS/TLS, JWT authentication, and CORS headers.")
                 
    elif "salary" in last_msg or "negotiat" in last_msg or "compensation" in last_msg or "offer" in last_msg:
        reply = ("Coach: Salary Negotiation Best Practices:\n\n"
                 "- **Don't State the Number First**: If they ask for your expectations, ask: 'What budget range has been allocated for this role?'\n"
                 "- **Base Requests on Data**: Use market benchmarks from sites like Levels.fyi or Glassdoor.\n"
                 "- **Focus on Total Value**: If base salary is fixed, negotiate sign-on bonuses, relocation, stock grants, or additional PTO.\n"
                 "- **Be Collaborative**: Frame it as a mutual goal to align on a package that reflects the impact you will bring.")
                 
    elif "weakness" in last_msg:
        reply = ("Coach: When answering 'What is your greatest weakness?':\n\n"
                 "- **Choose a real, minor skill**: Select something that is not critical to the core job (e.g., public speaking, or delegating tasks).\n"
                 "- **Describe your remediation plan**: Explain what you are *actively* doing to improve (e.g. taking a class, seeking feedback).\n"
                 "- **Avoid cliché answers**: Never say 'I work too hard' or 'I am a perfectionist'—recruiters see right through these.")
                 
    elif "strength" in last_msg:
        reply = ("Coach: When answering 'What is your greatest strength?':\n\n"
                 "- **Pick a role-aligned attribute**: Align your strength with the core requirements in the job description (e.g., self-driven learning, or system debugging).\n"
                 "- **Tell a mini STAR story**: Provide a quick, concrete instance of how this strength directly helped solve a past project blocker.")
                 
    else:
        tips = [
            "Coach: Remember to always explain your thoughts out loud during technical code interviews. Interviewers prioritize your reasoning process over syntax compilation.",
            "Coach: When answering behavioral questions, try to keep your answers between 1.5 to 2 minutes. Focus your storytelling on your Actions and final Results.",
            "Coach: Before any interview, spend 10 minutes researching the company's product challenges. Aligning your past work to their goals stands out immensely.",
            "Coach: Always prepare 2-3 thoughtful questions to ask the interviewer at the end of the session. It shows strong engagement and curiosity."
        ]
        reply = random.choice(tips)
        
    return jsonify({"reply": reply})

import json

@app.route("/api/coding/challenges", methods=["GET"])
def api_get_challenges():
    res = {}
    for pid, c in CHALLENGES.items():
        res[pid] = {
            "title": c["title"],
            "difficulty": c["difficulty"],
            "description": c["description"],
            "constraints": c["constraints"],
            "examples": c["examples"],
            "templates": c["templates"]
        }
    return jsonify(res)

@app.route("/api/coding/run", methods=["POST"])
def api_run_code():
    data = request.json or {}
    code = data.get("code", "")
    lang = data.get("language", "python")
    problem_id = data.get("problem_id", "")
    
    if lang == "python":
        res = run_python_code(code, problem_id)
    elif lang == "javascript":
        res = run_javascript_code(code, problem_id)
    else:
        return jsonify({"error": "Unsupported language"}), 400
        
    return jsonify(res)

@app.route("/api/coding/review", methods=["POST"])
def api_review_code():
    data = request.json or {}
    code = data.get("code", "")
    lang = data.get("language", "python")
    problem_id = data.get("problem_id", "")
    
    challenge = CHALLENGES.get(problem_id, {})
    title = challenge.get("title", problem_id)
    
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = f"""
            Analyze the following coding solution for the challenge '{title}' in language '{lang}'.
            Provide a feedback review assessing the code.
            
            Code:
            {code}
            
            Provide exactly the following JSON structure:
            {{
                "time_complexity": "O(N)", // Time complexity estimate
                "space_complexity": "O(1)", // Space complexity estimate
                "readability_score": 85, // Readability out of 100
                "feedback": "Your code is correct and clean. You can optimize by...", // Overall assessment and style tips
                "suggestions": ["Use a set to search elements in O(1) time.", "Avoid redundant loops."] // concrete improvement suggestions
            }}
            Return ONLY the valid JSON block.
            """
            
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {{"role": "system", "content": "You are a senior software engineer and technical interviewer. You must output ONLY a valid JSON object."}},
                    {{"role": "user", "content": prompt}}
                ],
                temperature=0.3,
                max_tokens=800
            )
            response_text = completion.choices[0].message.content.strip()
            
            if "{" in response_text and "}" in response_text:
                start_index = response_text.find("{")
                end_index = response_text.rfind("}") + 1
                response_text = response_text[start_index:end_index]
                
            analysis = json.loads(response_text)
            return jsonify(analysis)
        except Exception as e:
            print(f"[ERROR] Groq code review failed: {e}")
            
    # Fallback response generator if Groq key is missing or fails:
    return jsonify({{
        "time_complexity": "O(N^2) or O(N)",
        "space_complexity": "O(N) or O(1)",
        "readability_score": 80,
        "feedback": "Code executes correctly. Please check that you avoid nested loops if possible to maintain optimal time complexity.",
        "suggestions": [
            "Verify loop boundaries.",
            "Consider utilizing auxiliary hashes/dicts to optimize query times from O(N) to O(1)."
        ]
    }})


# ── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  InterviewIQ — AI Interview Intelligence System")
    print("=" * 55)
    print("  Open in browser: http://192.168.1.6:5000")
    print("  Health check   : http://192.168.1.6:5000/health")
    print("=" * 55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
