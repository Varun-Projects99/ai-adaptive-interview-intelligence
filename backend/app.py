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
    from modules.resume_parser import extract_skills_from_resume
    print("[OK] resume_parser loaded")
except Exception as e:
    print(f"[WARN] resume_parser: {e}")

    def extract_skills_from_resume(path):
        return ["Python", "Machine Learning", "Data Structures"]


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
def serve_index():
    return send_from_directory("../frontend", "login.html")

@app.route("/dashboard")
def serve_dashboard():
    return send_from_directory("../frontend", "dashboard.html")


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
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF supported"}), 400

    path = os.path.join(UPLOAD_FOLDER, f"{sid}_resume.pdf")
    file.save(path)
    skills = extract_skills_from_resume(path)
    sess["skills"] = skills
    print(f"[Resume] {len(skills)} skills detected: {skills}")
    return jsonify(
        {"session_id": sid, "skills_detected": skills, "skill_count": len(skills)}
    )


@app.route("/api/questions/generate", methods=["POST"])
def generate_interview_questions():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    if not sess["skills"]:
        return jsonify({"error": "Upload resume first"}), 400

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


@app.route("/api/report/generate", methods=["POST"])
def get_report():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    report = generate_final_report(sess)
    sess["status"] = "completed"
    return jsonify(report)


# ── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  InterviewIQ — AI Interview Intelligence System")
    print("=" * 55)
    print("  Open in browser: http://192.168.1.6:5000")
    print("  Health check   : http://192.168.1.6:5000/health")
    print("=" * 55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
