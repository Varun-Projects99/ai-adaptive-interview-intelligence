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
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, "..", ".env")
# override=True: .env is the authoritative source for these variables.
# Without this, python-dotenv silently keeps any value already present in
# the OS/terminal environment (e.g. a stale GROQ_API_KEY set earlier in a
# long-lived shell, VS Code launch config, or Windows user/system env
# vars) instead of picking up an updated .env -- which looks exactly like
# "I changed the key but it's still failing" with no visible cause.
load_dotenv(dotenv_path=dotenv_path, override=True)
print(f"[Env] Loaded .env from: {dotenv_path} (exists={os.path.exists(dotenv_path)}, override=True)")
sys.path.append(os.path.dirname(__file__))

# ── Module imports (graceful fallbacks if a lib is missing) ──────────────────

try:
    from modules.resume_parser import extract_skills_from_resume, analyze_resume_data, extract_text_from_pdf, get_ocr_reader
    from modules.resume_validator import validate_resume_document
    print("[OK] resume_parser and resume_validator loaded")
    import threading
    threading.Thread(target=get_ocr_reader, daemon=True).start()
except Exception as e:
    print(f"[WARN] resume_parser: {e}")

    def extract_skills_from_resume(path):
        return ["Python", "Machine Learning", "Data Structures"]

    def extract_text_from_pdf(path):
        return ""

    def validate_resume_document(text):
        return {"resume_valid": True, "document_type": "resume", "resume_confidence": 80, "reason": "Fallback validator"}

    def analyze_resume_data(path):
        return {
            "success": True,
            "resume_valid": True,
            "document_type": "resume",
            "resume_confidence": 80,
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
    from modules.question_engine import generate_questions, get_next_question, translate_text

    print("[OK] question_engine loaded")
except Exception as e:
    print(f"[WARN] question_engine: {e}")
    
    def translate_text(text, target_lang):
        return ""

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

    def analyze_emotion_frame(frame, sess=None):
        return {
            "face_detected": True,
            "status": "face_present",
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
    from modules.evaluator import evaluate_answer, generate_final_report, evaluate_and_transition
    print("[OK] evaluator loaded")
except Exception as e:
    print(f"[WARN] evaluator: {e}")

    def evaluate_and_transition(session, current_question, answer):
        return {
            "score": 70,
            "feedback": "Answer noted. Let's proceed.",
            "strengths": ["Answer provided"],
            "improvements": ["Elaborate further next time"],
            "action": "next_question",
            "transition": "Thank you for the answer.",
            "question": "",
            "reason": "Fallback handler"
        }

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

from modules.difficulty_engine import initial_difficulty_from_score
from modules import round_manager
from modules import outcome_model
from modules.integrity_config import NEVER_STRIKE_EVENT_TYPES


def _next_question_or_advance_round(sess):
    """
    Wraps get_next_question(sess) so a multi-round session (see
    modules/round_manager.py) transparently moves on to its next configured
    round instead of ending the interview when the current round's pool is
    exhausted. Returns (next_q, round_transitioned).

    For a non-multi-round session, round_manager.advance_round() is a no-op
    that always returns None, so next_q stays None and behavior is byte-for-
    byte identical to before this existed.
    """
    next_q = get_next_question(sess)
    if next_q is not None:
        return next_q, False

    new_round = round_manager.advance_round(sess)
    if new_round is None:
        return None, False

    lang = sess.get("interviewer", {}).get("language", "en")
    personality = sess.get("interviewer", {}).get("personality", "professional")
    sess["questions"] = generate_questions(sess["skills"], lang=lang, personality=personality)
    sess["current_index"] = 0
    sess["current_difficulty"] = "easy"
    return get_next_question(sess), True


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

try:
    from modules.ai_assistant import (
        handle_chat_message as assistant_handle_chat_message,
        check_rate_limit as assistant_check_rate_limit,
        AssistantProviderError,
        MAX_MESSAGE_LENGTH as ASSISTANT_MAX_MESSAGE_LENGTH,
        clear_conversations_for_user as assistant_clear_conversations_for_user,
    )
    print("[OK] ai_assistant loaded")
except Exception as e:
    print(f"[WARN] ai_assistant: {e}")

    class AssistantProviderError(Exception):
        pass

    ASSISTANT_MAX_MESSAGE_LENGTH = 1500

    def assistant_handle_chat_message(user_id, message, conversation_id=None):
        raise AssistantProviderError("AI Assistant module unavailable")

    def assistant_check_rate_limit(user_id):
        return True, 0

    def assistant_clear_conversations_for_user(user_id):
        return 0

try:
    from modules import settings_manager
    print("[OK] settings_manager loaded")
except Exception as e:
    print(f"[WARN] settings_manager: {e}")
    settings_manager = None


# ── Flask setup ──────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=None)

# 🔐 Secure Secret Key validation
flask_secret_env = os.environ.get("FLASK_SECRET")
if not flask_secret_env:
    print("[WARN] FLASK_SECRET key is missing from environment! Generating a dynamic session key for this launch.")
    import secrets
    app.secret_key = secrets.token_hex(32)
else:
    app.secret_key = flask_secret_env

# 🔐 Production-safe Session Cookie settings
if os.environ.get("VERCEL") or os.environ.get("PROD_MODE") == "true":
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )
else:
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )

# 🔐 Secure CORS origins
frontend_origin = os.environ.get("FRONTEND_ORIGIN")
if frontend_origin:
    origins_list = [o.strip() for o in frontend_origin.split(",")]
    CORS(app, supports_credentials=True, origins=origins_list)
else:
    CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

# 🔐 Failed logins tracker
failed_logins = {}

@app.errorhandler(Exception)
def handle_global_exception(e):
    if request.path.startswith("/api/"):
        import traceback
        tb = traceback.format_exc()
        print(f"[API Global Error] {request.path}: {e}\n{tb}")
        status_code = 500
        if hasattr(e, "code"):
            status_code = e.code
        return jsonify({
            "error": str(e)
        }), status_code
    raise e

# ── SECURITY HELPERS, DECORATORS, & AUDITING ────────────────────────────────────

def log_audit(action, user_id=None, session_id=None):
    try:
        from flask import request
        u_id = user_id
        if not u_id and "user_id" in session:
            u_id = session.get("user_id")

        ip_addr = request.remote_addr if request else "127.0.0.1"
        user_agent = request.headers.get("User-Agent", "Unknown") if request else "Unknown"

        audit_doc = {
            "user_id": str(u_id) if u_id else "anonymous",
            "action": action,
            "session_id": str(session_id) if session_id else "None",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "ip_address": ip_addr,
            "user_agent": user_agent
        }
        if db is not None:
            db["audit_logs"].insert_one(audit_doc)
            print(f"[AUDIT LOG] {action} logged for user {u_id}")
    except Exception as e:
        print(f"[WARN] Failed to write audit log entry: {e}")

def is_ip_or_email_locked(email, ip_addr):
    import time
    now = time.time()

    if email in failed_logins:
        record = failed_logins[email]
        if record["count"] >= 5 and record["lock_until"] > now:
            return True, int(record["lock_until"] - now)

    if ip_addr in failed_logins:
        record = failed_logins[ip_addr]
        if record["count"] >= 5 and record["lock_until"] > now:
            return True, int(record["lock_until"] - now)

    return False, 0

def register_failed_login(email, ip_addr):
    import time
    now = time.time()

    for key in [email, ip_addr]:
        if key not in failed_logins:
            failed_logins[key] = {"count": 1, "lock_until": 0}
        else:
            record = failed_logins[key]
            if record["lock_until"] > 0 and record["lock_until"] < now:
                record["count"] = 1
                record["lock_until"] = 0
            else:
                record["count"] += 1
                if record["count"] >= 5:
                    record["lock_until"] = now + 60

def clear_failed_logins(email, ip_addr):
    if email in failed_logins:
        failed_logins.pop(email)
    if ip_addr in failed_logins:
        failed_logins.pop(ip_addr)

def session_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not session.get("authenticated"):
            log_audit("UNAUTHORIZED_ACCESS")
            return jsonify({"error": "Unauthorized"}), 401

        sid = kwargs.get("sid") or kwargs.get("session_id")
        if not sid:
            try:
                if request.is_json:
                    data = request.json or {}
                    sid = data.get("session_id") or data.get("sid")
                else:
                    sid = request.form.get("session_id") or request.form.get("sid")
            except Exception:
                pass

        if not sid:
            return jsonify({"error": "session_id is required"}), 400

        sess = get_sess(sid)
        user_id_str = str(session.get("user_id"))

        if sess:
            if sess.get("user_id") != user_id_str:
                log_audit("FORBIDDEN_ACCESS", session_id=sid)
                return jsonify({"error": "Forbidden"}), 403
        else:
            history = load_history()
            report = history.get(sid)
            if report:
                if report.get("user_id") != user_id_str:
                    log_audit("FORBIDDEN_ACCESS", session_id=sid)
                    return jsonify({"error": "Forbidden"}), 403
            else:
                return jsonify({"error": "Session not found"}), 404

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not session.get("authenticated"):
            log_audit("UNAUTHORIZED_ACCESS")
            return jsonify({"error": "Unauthorized"}), 401

        role = session.get("role")
        if not role:
            u_id = session.get("user_id")
            user = users_col.find_one({"_id": ObjectId(u_id)}) if users_col is not None else None
            if user:
                role = user.get("role", "candidate")
                session["role"] = role

        if role != "admin":
            log_audit("FORBIDDEN_ACCESS")
            return jsonify({"error": "Forbidden"}), 403

        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://lh3.googleusercontent.com; "
        "media-src 'self' blob: data:; "
        "connect-src 'self' https://accounts.google.com;"
    )
    return response

# ── JSON SERIALIZATION CLEANING HELPER ───────────────────────────────────────────

def clean_json(obj):
    import datetime
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items() if k != "_id"}
    elif isinstance(obj, list):
        return [clean_json(i) for i in obj]
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif type(obj).__name__ == "ObjectId":
        return str(obj)
    return obj

# ── CONTINUOUS LEARNING HELPERS ──────────────────────────────────────────────────

def generate_roadmap_and_recommendations(weak_skills):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        roadmap = []
        recommendations = []
        for idx, skill in enumerate(weak_skills):
            roadmap.append({
                "priority": idx + 1,
                "topic": f"{skill} Fundamentals",
                "tasks": [f"Practice core concepts of {skill}", f"Solve basic programming questions in {skill}"]
            })
            recommendations.append({
                "topic": skill,
                "reason": f"Recommended because your technical readiness score in {skill} indicates opportunity for core learning."
            })
        return roadmap, recommendations

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = f"""Based on the candidate's detected weak skills: {", ".join(weak_skills)}, generate:
1. A step-by-step personalized learning roadmap of priority items.
2. Recommended subtopics to practice with short explanations.

Respond ONLY with a raw JSON object containing "roadmap" and "recommendations" keys. No markdown, no comments.
Format Example:
{{
  "roadmap": [
    {{
      "priority": 1,
      "topic": "AWS Security",
      "tasks": ["Practice IAM", "Practice Security Groups", "Practice IAM policies"]
    }}
  ],
  "recommendations": [
    {{
      "topic": "AWS IAM",
      "reason": "Recommended because your recent AWS security answers scored below your previous average."
    }}
  ]
}}
"""
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a professional technical training advisor. Output only raw JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        res = completion.choices[0].message.content.strip()
        if "[" in res or "{" in res:
            start_index = res.find("{")
            end_index = res.rfind("}") + 1
            res = res[start_index:end_index]
        data = json.loads(res)
        return data.get("roadmap", []), data.get("recommendations", [])
    except Exception as e:
        print(f"[WARN] Roadmap AI generation failed: {e}. Using fallback.")
        roadmap = []
        recommendations = []
        for idx, skill in enumerate(weak_skills):
            roadmap.append({
                "priority": idx + 1,
                "topic": f"{skill} Fundamentals",
                "tasks": [f"Practice core concepts of {skill}", f"Solve basic programming questions in {skill}"]
            })
            recommendations.append({
                "topic": skill,
                "reason": f"Recommended because your technical readiness score in {skill} indicates opportunity for core learning."
            })
        return roadmap, recommendations

def update_learning_progress(user_id, session_id, report, is_practice=False):
    if db is None or not user_id:
        return
    try:
        progress_col = db["learning_progress"]
        progress = progress_col.find_one({"user_id": str(user_id)})
        if not progress:
            progress = {
                "user_id": str(user_id),
                "skills": {},
                "roadmap": [],
                "recommendations": [],
                "improvement_history": []
            }

        import datetime
        date_str = datetime.datetime.now().strftime("%b %d")

        skill_scores = report.get("skill_scores", {})
        if not skill_scores:
            skill_scores = {}
            for ans in report.get("answers", []):
                sk = ans.get("skill")
                sc = ans.get("score")
                if sk and sc is not None:
                    if sk not in skill_scores:
                        skill_scores[sk] = []
                    skill_scores[sk].append(sc)
            skill_scores = {k: int(sum(v)/len(v)) for k, v in skill_scores.items() if isinstance(v, list)}

        for skill, score in skill_scores.items():
            if skill not in progress["skills"]:
                progress["skills"][skill] = {
                    "history": [],
                    "status": "Weak"
                }

            status = "Weak"
            if score >= 75:
                status = "Strong"
            elif score >= 55:
                status = "Moderate"

            progress["skills"][skill]["status"] = status

            history = progress["skills"][skill]["history"]
            if not any(h.get("session_id") == session_id for h in history):
                if history:
                    prev_score = history[-1]["score"]
                    if score > prev_score:
                        progress["improvement_history"].append({
                            "date": date_str,
                            "skill": skill,
                            "from": prev_score,
                            "to": score
                        })

                history.append({
                    "date": date_str,
                    "score": score,
                    "type": "practice" if is_practice else "interview",
                    "session_id": session_id
                })

        weak_skills = [s for s, d in progress["skills"].items() if d.get("status") == "Weak"]
        if weak_skills:
            roadmap, recommendations = generate_roadmap_and_recommendations(weak_skills)
            progress["roadmap"] = roadmap
            progress["recommendations"] = recommendations
        else:
            progress["roadmap"] = []
            progress["recommendations"] = []

        progress_col.replace_one({"user_id": str(user_id)}, progress, upsert=True)
        print(f"[Learning] Updated progress database entry for user {user_id}")
    except Exception as e:
        print(f"[WARN] Failed to update learning progress: {e}")

# ── ASYNCHRONOUS REPORT GENERATION PIPELINE ──────────────────────────────────────

def async_generate_report(sid, user_id):
    if db is None:
        print("[ERROR] Async report generation: database is not initialized.")
        return
        
    reports_col = db["reports"]
    
    # 1. Update status to generating
    reports_col.update_one(
        {"session_id": sid},
        {"$set": {
            "session_id": sid,
            "user_id": str(user_id) if user_id else "anonymous",
            "status": "generating",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }},
        upsert=True
    )
    
    import time
    t_start = time.perf_counter()
    
    try:
        sess = get_sess(sid)
        if not sess:
            history = load_history()
            report = history.get(sid)
            if report:
                reports_col.update_one(
                    {"session_id": sid},
                    {"$set": {
                        "status": "completed",
                        "report": report,
                        "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
                    }}
                )
                print(f"[Async Report] Found report in history, cached to MongoDB.")
                return
            else:
                raise ValueError("Active session not found.")
                
        # Calculate deterministic metrics locally
        t_data_start = time.perf_counter()
        report = generate_final_report(sess)
        t_data_end = time.perf_counter()
        
        # 2. Call AI ONCE to get consolidated insights
        t_ai_start = time.perf_counter()
        
        transcript_lines = []
        for idx, ans in enumerate(report.get("answers", [])):
            q_text = ans.get("question", "")
            a_text = ans.get("answer", "")
            score = ans.get("score", 0)
            feedback = ans.get("feedback", "")
            transcript_lines.append(
                f"Question {idx+1}: {q_text}\n"
                f"Candidate Answer: {a_text}\n"
                f"Score: {score}\n"
                f"Feedback: {feedback}"
            )
        transcript_str = "\n\n".join(transcript_lines)
        
        api_key = os.environ.get("GROQ_API_KEY")
        ai_data = {
            "strengths": report.get("strong_areas") or ["Communicated technical ideas correctly."],
            "weaknesses": report.get("weak_areas") or ["Provide more deep architectural details."],
            "recommendations": report.get("recommendations") or ["Focus on explaining your trade-offs."],
            "final_summary": "Overall solid performance, demonstrated strong technical competencies."
        }
        
        if api_key and api_key.startswith("gsk_"):
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                prompt = f"""You are a senior technical interviewer and engineering manager. Evaluate the candidate's complete mock interview session.
                
Interview transcript:
{transcript_str}

Provide a consolidated candidate performance review and recommendations.
Respond ONLY with a valid JSON object matching this structure:
{{
  "strengths": ["...", "..."], // top 2-3 key technical strengths demonstrated
  "weaknesses": ["...", "..."], // top 2-3 technical weak areas or missed concepts
  "recommendations": ["...", "..."], // 2-3 specific action items to improve
  "final_summary": "..." // a concise, encouraging 2-3 sentence performance summary
}}
Do NOT include markdown block or explanations outside the JSON object.
"""
                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": "You are a technical advisor. Output ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=600,
                    timeout=8.0
                )
                res_raw = completion.choices[0].message.content.strip()
                if "{" in res_raw and "}" in res_raw:
                    res_raw = res_raw[res_raw.find("{"):res_raw.rfind("}")+1]
                parsed = json.loads(res_raw)
                if isinstance(parsed, dict):
                    ai_data["strengths"] = parsed.get("strengths", ai_data["strengths"])
                    ai_data["weaknesses"] = parsed.get("weaknesses", ai_data["weaknesses"])
                    ai_data["recommendations"] = parsed.get("recommendations", ai_data["recommendations"])
                    ai_data["final_summary"] = parsed.get("final_summary", ai_data["final_summary"])
            except Exception as ai_err:
                print(f"[WARN] Consolidated AI report request failed: {ai_err}")
                
        t_ai_end = time.perf_counter()
        
        # Merge AI data into report
        report["recommendations"] = ai_data["recommendations"]
        report["strong_areas"] = ai_data["strengths"]
        report["weak_areas"] = ai_data["weaknesses"]
        report["summary"]["final_summary"] = ai_data["final_summary"]
        report["user_id"] = str(user_id) if user_id else "anonymous"
        report["is_practice"] = sess.get("is_practice", False) if sess else False
        report["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        report = clean_json(report)
        
        t_db_start = time.perf_counter()
        if sess and sess.get("invitation_token"):
            token = sess.get("invitation_token")
            if db is not None:
                db["interview_invitations"].update_one(
                    {"token": token},
                    {"$set": {
                        "status": "Completed", 
                        "completed_at": datetime.datetime.utcnow().isoformat() + "Z"
                    }}
                )
            report["interview_id"] = sess.get("interview_id")
            report["invitation_token"] = token

        reports_col.update_one(
            {"session_id": sid},
            {"$set": {
                "status": "completed",
                "report": report,
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
            }}
        )
        if user_id:
            update_learning_progress(user_id, sid, report, is_practice=report.get("is_practice", False))
            
        history = load_history()
        history[sid] = report
        save_history(history)
        t_db_end = time.perf_counter()
        
        t_total = time.perf_counter() - t_start
        data_fetch_ms = (t_data_end - t_data_start) * 1000
        ai_gen_ms = (t_ai_end - t_ai_start) * 1000
        db_save_ms = (t_db_end - t_db_start) * 1000
        total_report_ms = t_total * 1000
        
        print("\n" + "=" * 40)
        print("  REPORT START")
        print(f"  DATA FETCH TIME: {data_fetch_ms:.2f} ms")
        print(f"  AI GENERATION TIME: {ai_gen_ms:.2f} ms")
        print(f"  DATABASE SAVE TIME: {db_save_ms:.2f} ms")
        print(f"  TOTAL REPORT TIME: {total_report_ms:.2f} ms")
        print("=" * 40 + "\n")
        
        log_audit("REPORT_GENERATED", user_id=user_id, session_id=sid)
        
    except Exception as err:
        print(f"[ERROR] Async report generation failed for session {sid}: {err}")
        reports_col.update_one(
            {"session_id": sid},
            {"$set": {
                "status": "failed",
                "error_message": str(err),
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
            }}
        )

# ── MongoDB & Auth Setup ──────────────────────────────────────────────────────
import pymongo
import bcrypt
import datetime
from functools import wraps
from flask import session, redirect
from bson.objectid import ObjectId

mongo_uri = os.environ.get("MONGO_URI")
mongo_db_name = os.environ.get("MONGO_DB_NAME", "interviewiq")

db = None
users_col = None

if not mongo_uri:
    print("[ERROR] MONGO_URI is not configured in .env")
else:
    try:
        mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        # Test connection
        mongo_client.admin.command("ping")
        db = mongo_client[mongo_db_name]
        users_col = db["users"]
        users_col.create_index("email", unique=True)
        reports_col = db["reports"]
        reports_col.create_index("session_id", unique=True)
        reports_col.create_index("user_id")
        reports_col.create_index("created_at")
        print("[OK] MongoDB connected and reports collection indexed")
    except Exception as e:
        safe_error = str(e)
        if "@" in safe_error:
            # strip credentials out of the error message for safety
            parts = safe_error.split("@")
            safe_error = parts[-1]
        print(f"[ERROR] MongoDB connection failed: {safe_error}")

# Password hashing helpers
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# Route protection decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not session.get("authenticated"):
            if request.path.startswith("/api/"):
                log_audit("UNAUTHORIZED_ACCESS")
                return jsonify({"error": "Unauthorized"}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session or not session.get("authenticated"):
                if request.path.startswith("/api/"):
                    log_audit("UNAUTHORIZED_ACCESS")
                    return jsonify({"error": "Unauthorized"}), 401
                return redirect("/login")
            
            user_role = session.get("role")
            if not user_role and db is not None:
                user = db["users"].find_one({"_id": ObjectId(session["user_id"])})
                if user:
                    user_role = user.get("role", "candidate")
                    session["role"] = user_role
                    
            if user_role not in allowed_roles:
                if request.path.startswith("/api/"):
                    log_audit("FORBIDDEN_ACCESS")
                    return jsonify({"error": "Forbidden"}), 403
                return redirect("/dashboard")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

if os.environ.get("VERCEL"):
    UPLOAD_FOLDER = "/tmp"
    RECORDING_FOLDER = "/tmp"
else:
    UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "uploads"))
    RECORDING_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "recordings"))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECORDING_FOLDER, exist_ok=True)

sessions = {}


# ── SERVE FRONTEND ───────────────────────────────────────────────────────────


@app.route("/")
@app.route("/login")
def serve_index():
    if "user_id" in session and session.get("authenticated"):
        return redirect("/dashboard")
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/dashboard")
@login_required
def serve_dashboard():
    user_id = session.get("user_id")
    user_role = session.get("role")
    if not user_role and db is not None:
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if user:
            user_role = user.get("role", "candidate")
            session["role"] = user_role
    if user_role in ["recruiter", "admin"]:
        return redirect("/recruiter")
    return send_from_directory(FRONTEND_DIR, "dashboard.html")

@app.route("/recruiter")
@role_required(["recruiter", "admin"])
def serve_recruiter_dashboard():
    return send_from_directory(FRONTEND_DIR, "recruiter.html")

@app.route("/upload")
@login_required
def serve_upload():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/analyzer")
@login_required
def serve_analyzer():
    return send_from_directory(FRONTEND_DIR, "analyzer.html")
@app.route("/register")
def serve_register():
    if "user_id" in session and session.get("authenticated"):
        return redirect("/dashboard")
    return send_from_directory(FRONTEND_DIR, "register.html")

@app.route("/career")
@login_required
def serve_career():
    return send_from_directory(FRONTEND_DIR, "career.html")

@app.route("/coding")
@login_required
def serve_coding():
    return send_from_directory(FRONTEND_DIR, "coding.html")

@app.route("/ai-assistant")
@login_required
def serve_ai_assistant():
    return send_from_directory(FRONTEND_DIR, "assistant.html")

@app.route("/history")
@login_required
def serve_history():
    return send_from_directory(FRONTEND_DIR, "history.html")

@app.route("/coach")
@login_required
def serve_coach():
    return send_from_directory(FRONTEND_DIR, "coach.html")

@app.route("/interview")
@login_required
def serve_interview():
    return send_from_directory(FRONTEND_DIR, "interview.html")

@app.route("/report")
@login_required
def serve_report():
    return send_from_directory(FRONTEND_DIR, "report.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "assets"), filename)


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    if users_col is None:
        return jsonify({"error": "Database connection unavailable. Please try again later."}), 503
        
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    email = email.strip().lower()
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
    try:
        # Check duplicate
        if users_col.find_one({"email": email}):
            return jsonify({"error": "An account with this email already exists."}), 400
            
        password_hash = hash_password(password)
        
        role = data.get("role", "candidate")
        if role not in ["candidate", "recruiter", "admin"]:
            role = "candidate"
        if "admin" in email:
            role = "admin"
        elif "recruiter" in email:
            role = "recruiter"
            
        name = data.get("name", "Candidate").strip()
        user_doc = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "auth_provider": "local",
            "created_at": datetime.datetime.utcnow()
        }
        users_col.insert_one(user_doc)
        log_audit("REGISTER", user_id=email)
        return jsonify({"success": True, "message": "Account created successfully"}), 201
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        return jsonify({"error": "An error occurred during registration. Please try again."}), 500


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    if users_col is None:
        return jsonify({"error": "Database connection unavailable. Please try again later."}), 503
        
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    email = email.strip().lower()
    ip_addr = request.remote_addr or "127.0.0.1"

    # Rate limiting check
    locked, remaining = is_ip_or_email_locked(email, ip_addr)
    if locked:
        log_audit("LOGIN_FAILED", user_id=email, session_id="RATE_LIMITED")
        return jsonify({"error": f"Too many failed attempts. Try again in {remaining} seconds."}), 429
        
    try:
        user = users_col.find_one({"email": email})
        if not user:
            register_failed_login(email, ip_addr)
            log_audit("LOGIN_FAILED", user_id=email, session_id="USER_NOT_FOUND")
            return jsonify({"error": "Invalid email or password."}), 401
            
        # Check if the user is a Google OAuth user without a password
        if not user.get("password_hash"):
            return jsonify({"error": "This account uses Google Login. Please click 'Continue with Google'."}), 400
            
        if not check_password(password, user["password_hash"]):
            register_failed_login(email, ip_addr)
            log_audit("LOGIN_FAILED", user_id=str(user["_id"]), session_id="WRONG_PASSWORD")
            return jsonify({"error": "Invalid email or password."}), 401
            
        clear_failed_logins(email, ip_addr)
        session["user_id"] = str(user["_id"])
        session["user_email"] = user["email"]
        session["email"] = user["email"]
        session["role"] = user.get("role", "candidate")
        session["authenticated"] = True
        log_audit("LOGIN_SUCCESS", user_id=str(user["_id"]))
        return jsonify({"success": True, "message": "Logged in successfully", "user": {"email": user["email"], "role": session["role"]}})
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return jsonify({"error": "An error occurred during login. Please try again."}), 500


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    log_audit("LOGOUT")
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route("/api/auth/me", methods=["GET"])
def api_me():
    if "user_id" in session and session.get("authenticated"):
        email = session.get("user_email") or session.get("email")
        role = session.get("role")
        name = session.get("user_name")
        if (not role or not name) and db is not None:
            user = db["users"].find_one({"_id": ObjectId(session["user_id"])})
            if user:
                role = user.get("role", "candidate")
                name = user.get("name", "Candidate")
                session["role"] = role
                session["user_name"] = name
        return jsonify({
            "authenticated": True,
            "user": {
                "email": email,
                "role": role or "candidate",
                "name": name or "Candidate"
            }
        })
    return jsonify({"authenticated": False})


# ── GOOGLE OAUTH 2.0 API ──────────────────────────────────────────────────────
import requests
import urllib.parse

@app.route("/auth/google")
def google_login():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        if os.environ.get("VERCEL"):
            redirect_uri = f"https://{request.headers.get('Host')}/auth/google/callback"
        else:
            redirect_uri = "http://127.0.0.1:5000/auth/google/callback"
    
    if not client_id:
        return "Google OAuth is not configured in the server environment.", 500
        
    scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
    state = uuid.uuid4().hex
    session["oauth_state"] = state
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(google_auth_url)


@app.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    
    if not code:
        return redirect("/login?error=Google authentication was canceled or failed.")
        
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        if os.environ.get("VERCEL"):
            redirect_uri = f"https://{request.headers.get('Host')}/auth/google/callback"
        else:
            redirect_uri = "http://127.0.0.1:5000/auth/google/callback"
            
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        res = requests.post(token_url, data=data, timeout=5)
        # Write exact response for debugging
        with open(os.path.join(os.path.dirname(__file__), "oauth_debug.log"), "w", encoding="utf-8") as f_debug:
            f_debug.write(f"Status Code: {res.status_code}\n")
            f_debug.write(f"Response Body: {res.text}\n")
            
        res_data = res.json()
        access_token = res_data.get("access_token")
        
        if not access_token:
            err_msg = res_data.get("error_description", res_data.get("error", "unknown error"))
            print(f"[ERROR] Google token exchange failed: {err_msg}")
            with open(os.path.join(os.path.dirname(__file__), "oauth_debug.log"), "a", encoding="utf-8") as f_debug:
                f_debug.write(f"Token Exchange Error Message: {err_msg}\n")
            return redirect(f"/login?error=Google authentication failed: {err_msg}")
            
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_res = requests.get(userinfo_url, headers=headers, timeout=5)
        user_info = user_res.json()
        
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
        
        if not email:
            return redirect("/login?error=Google account does not provide email access.")
            
        email = email.lower().strip()
        
        if users_col is not None:
            user = users_col.find_one({"$or": [{"google_id": google_id}, {"email": email}]})
            now = datetime.datetime.utcnow()
            
            user_role = "candidate"
            if "admin" in email:
                user_role = "admin"
            elif "recruiter" in email:
                user_role = "recruiter"

            if user:
                user_role = user.get("role", user_role)
                users_col.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "google_id": google_id,
                            "name": name,
                            "profile_picture": picture,
                            "auth_provider": "google",
                            "role": user_role,
                            "last_login": now
                        }
                    }
                )
                user_id = str(user["_id"])
            else:
                new_user = {
                    "google_id": google_id,
                    "name": name,
                    "email": email,
                    "profile_picture": picture,
                    "role": user_role,
                    "auth_provider": "google",
                    "created_at": now,
                    "last_login": now
                }
                res_insert = users_col.insert_one(new_user)
                user_id = str(res_insert.inserted_id)
                
            session["user_id"] = user_id
            session["user_email"] = email
            session["email"] = email
            session["role"] = user_role
            session["authenticated"] = True
            log_audit("GOOGLE_LOGIN", user_id=user_id)
            return redirect("/dashboard")
        else:
            return redirect("/login?error=Database connection unavailable. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Google callback Exception: {e}")
        return redirect("/login?error=Google authentication failed. Please try again.")


@app.route("/logout", methods=["GET", "POST"])
def route_logout():
    session.clear()
    return redirect("/login")


# ── SETTINGS ──────────────────────────────────────────────────────────────
# Every route below derives the acting user from session["user_id"] (already
# verified authenticated by @login_required) -- never from the request body
# or a query parameter -- so one candidate can never read or change another
# candidate's settings. Preferences are stored on the existing `users`
# document under a `preferences` sub-object; no new MongoDB collection is
# created (see modules/settings_manager.py).

@app.route("/settings")
@login_required
def serve_settings():
    return send_from_directory(FRONTEND_DIR, "settings.html")


@app.route("/api/settings", methods=["GET"])
@login_required
def api_get_settings():
    if settings_manager is None:
        return jsonify({"error": "Settings module unavailable."}), 503
    if db is None:
        return jsonify({"error": "Database connection unavailable. Please try again later."}), 503
    try:
        user_id = session["user_id"]
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "Account not found."}), 404

        created_at = user.get("created_at")
        member_since = None
        if isinstance(created_at, datetime.datetime):
            member_since = created_at.isoformat() + "Z"

        return jsonify({
            "profile": {
                "name": user.get("name", "Candidate"),
                "email": user.get("email"),
                "role": user.get("role", "candidate"),
                "auth_provider": user.get("auth_provider", "local"),
                "member_since": member_since,
            },
            "preferences": settings_manager.get_preferences(user),
            "ai_status": settings_manager.get_ai_status(),
            "privacy": {"data_categories": settings_manager.DATA_CATEGORIES},
            "security": {
                "auth_provider": user.get("auth_provider", "local"),
                "role": user.get("role", "candidate"),
            },
        })
    except Exception as e:
        print(f"[ERROR] Settings fetch failed: {e}")
        return jsonify({"error": "Could not load settings. Please try again."}), 500


@app.route("/api/settings/profile", methods=["PUT"])
@login_required
def api_update_profile():
    if settings_manager is None:
        return jsonify({"error": "Settings module unavailable."}), 503
    if db is None:
        return jsonify({"error": "Database connection unavailable. Please try again later."}), 503
    data = request.get_json(silent=True) or {}
    clean, err = settings_manager.validate_profile_update(data)
    if err:
        return jsonify({"error": err}), 400
    try:
        user_id = session["user_id"]
        result = db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": clean})
        if result.matched_count == 0:
            return jsonify({"error": "Account not found."}), 404
        session["user_name"] = clean["name"]
        log_audit("SETTINGS_PROFILE_UPDATED", user_id=user_id)
        return jsonify({"success": True, "profile": {"name": clean["name"]}})
    except Exception as e:
        print(f"[ERROR] Profile update failed: {e}")
        return jsonify({"error": "Could not update profile. Please try again."}), 500


@app.route("/api/settings/preferences", methods=["PUT"])
@login_required
def api_update_preferences():
    if settings_manager is None:
        return jsonify({"error": "Settings module unavailable."}), 503
    if db is None:
        return jsonify({"error": "Database connection unavailable. Please try again later."}), 503
    data = request.get_json(silent=True) or {}
    clean, err = settings_manager.validate_preferences_update(data)
    if err:
        return jsonify({"error": err}), 400
    try:
        user_id = session["user_id"]
        set_fields = {f"preferences.{k}": v for k, v in clean.items()}
        result = db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": set_fields})
        if result.matched_count == 0:
            return jsonify({"error": "Account not found."}), 404
        log_audit("SETTINGS_PREFERENCES_UPDATED", user_id=user_id)
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        return jsonify({"success": True, "preferences": settings_manager.get_preferences(user)})
    except Exception as e:
        print(f"[ERROR] Preferences update failed: {e}")
        return jsonify({"error": "Could not update preferences. Please try again."}), 500


@app.route("/api/settings/ai-assistant/clear", methods=["POST"])
@login_required
def api_clear_ai_conversations():
    try:
        user_id = session["user_id"]
        deleted = assistant_clear_conversations_for_user(user_id)
        log_audit("SETTINGS_AI_CONVERSATIONS_CLEARED", user_id=user_id)
        return jsonify({"success": True, "deleted": deleted})
    except Exception as e:
        print(f"[ERROR] Clearing AI Assistant conversations failed: {e}")
        return jsonify({"error": "Could not clear conversations. Please try again."}), 500


@app.route("/api/settings/account", methods=["DELETE"])
@login_required
def api_delete_account():
    if db is None:
        return jsonify({"error": "Database connection unavailable. Please try again later."}), 503
    data = request.get_json(silent=True) or {}
    if str(data.get("confirm", "")).strip().upper() != "DELETE":
        return jsonify({"error": 'Type "DELETE" to confirm account deletion.'}), 400
    try:
        user_id = session["user_id"]
        oid = ObjectId(user_id)
        user = db["users"].find_one({"_id": oid})
        if not user:
            return jsonify({"error": "Account not found."}), 404

        # Candidate-owned personal data this account directly controls.
        # Interview reports/interviews/audit logs already shared with a
        # recruiter workflow are intentionally retained for record-keeping
        # (disclosed in the Settings page copy) -- only this account's own
        # login credentials and directly-owned personal data are removed.
        db["candidate_profiles"].delete_many({"user_id": user_id})
        db["learning_progress"].delete_many({"user_id": user_id})
        db["sessions"].delete_many({"user_id": user_id})
        try:
            assistant_clear_conversations_for_user(user_id)
        except Exception:
            pass
        db["users"].delete_one({"_id": oid})

        log_audit("ACCOUNT_DELETED", user_id=user_id)
        session.clear()
        return jsonify({"success": True, "message": "Your account has been deleted."})
    except Exception as e:
        print(f"[ERROR] Account deletion failed: {e}")
        return jsonify({"error": "Could not delete account. Please try again."}), 500


@app.route("/health")
def health():
    host = request.headers.get("Host") or "127.0.0.1:5000"
    scheme = "https" if os.environ.get("VERCEL") else "http"
    base_url = f"{scheme}://{host}"
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
                "frontend": base_url,
                "interview": f"{base_url}/interview",
                "report": f"{base_url}/report",
                "dashboard": f"{base_url}/dashboard",
                "api": f"{base_url}/api",
            },
        }
    )


# ── SESSION HELPERS ──────────────────────────────────────────────────────────


def get_candidate_name():
    email = session.get("user_email") or session.get("email") or "Candidate"
    if "@" in email:
        username = email.split("@")[0]
        name = username.split(".")[0].split("_")[0]
        name = "".join([c for c in name if c.isalpha()])
        return name.capitalize() if name else "Candidate"
    return "Candidate"


def get_sess(sid):
    if not sid:
        return None
    
    # Track accessed session ID in Flask request context if running in HTTP request
    from flask import g
    try:
        if "accessed_sessions" not in g:
            g.accessed_sessions = set()
        g.accessed_sessions.add(sid)
    except RuntimeError:
        pass
        
    if db is not None:
        doc = db["sessions"].find_one({"id": sid})
        if doc:
            doc.pop("_id", None)
            sessions[sid] = doc
            return doc
            
    return sessions.get(sid)


def new_sess(sid):
    user_id = str(session.get("user_id")) if "user_id" in session else "anonymous"
    now_iso = datetime.datetime.utcnow().isoformat()
    sess_data = {
        "id": sid,
        "user_id": user_id,
        "status": "active",
        "created_at": now_iso,
        "updated_at": now_iso,
        "skills": [],
        "questions": [],
        "current_index": 0,
        "current_difficulty": "easy",
        "answers": [],
        "emotion_timeline": [],
        "voice_scores": [],
        "technical_scores": [],
        # multiple_faces is tracked distinctly from camera_exit (see
        # /api/integrity/violation and emotion.js) so the final report and
        # recruiter view can show "Multiple Person Events" as its own signal
        # instead of folding it into the generic camera-away count.
        "violations": {"tab_switch": 0, "camera_exit": 0, "window_move": 0, "multiple_faces": 0, "total": 0},
        # Structured, additive event log for the Face/Integrity monitoring
        # subsystem (see modules/integrity_config.py + modules/
        # emotion_detector.py): every entry has type/severity/confidence/
        # duration/timestamp. Populated for BOTH warning-tier telemetry
        # (low light, blur, face position, head pose) and every real strike
        # (mirrored here too) -- never read for strike decisions itself,
        # sess["violations"] remains the sole source of truth for that.
        "integrity_events": [],
        "interviewer": {
            "personality": "professional",
            "language": "en",
            "state": "idle",
            "candidate_name": get_candidate_name(),
            "conversation": []
        }
    }
    sessions[sid] = sess_data
    
    # Track accessed session ID in Flask request context
    from flask import g
    try:
        if "accessed_sessions" not in g:
            g.accessed_sessions = set()
        g.accessed_sessions.add(sid)
    except RuntimeError:
        pass
        
    if db is not None:
        db["sessions"].replace_one({"id": sid}, sess_data, upsert=True)
        
    log_audit("SESSION_CREATED", user_id=user_id, session_id=sid)
    return sess_data


@app.after_request
def save_accessed_sessions(response):
    from flask import g
    if db is not None:
        try:
            if "accessed_sessions" in g:
                for sid in g.accessed_sessions:
                    sess = sessions.get(sid)
                    if sess:
                        # Powers the recruiter live-sessions view (see
                        # /api/recruiter/live-sessions below), which needs to
                        # tell an actively-progressing session apart from one
                        # the candidate has abandoned mid-interview.
                        sess["updated_at"] = datetime.datetime.utcnow().isoformat()
                        db["sessions"].replace_one({"id": sid}, sess, upsert=True)
        except RuntimeError:
            pass
    return response


# ── API ROUTES ───────────────────────────────────────────────────────────────


@app.route("/api/session/start", methods=["POST"])
@login_required
def start_session():
    data = request.get_json(silent=True) or {}
    invitation_token = data.get("invitation_token")
    
    sid = str(uuid.uuid4())
    new_sess(sid)
    sess = get_sess(sid)
    
    if invitation_token and db is not None:
        invite = db["interview_invitations"].find_one({"token": invitation_token})
        if not invite:
            return jsonify({"error": "Invalid invitation token"}), 400
            
        status = invite.get("status")
        if status in ["Completed", "Expired"]:
            return jsonify({"error": f"Invitation is already {status.lower()}"}), 400
            
        # Update status to Started
        db["interview_invitations"].update_one(
            {"token": invitation_token},
            {"$set": {"status": "Started", "started_at": datetime.datetime.utcnow().isoformat() + "Z"}}
        )
        
        # Load interview config
        interview = db["interviews"].find_one({"_id": ObjectId(invite["interview_id"])})
        if interview:
            sess["is_practice"] = False
            sess["invitation_token"] = invitation_token
            sess["interview_id"] = str(interview["_id"])
            sess["job_role"] = interview.get("job_role", "Software Engineer")
            sess["skills"] = interview.get("skills", [])
            sess["difficulty"] = interview.get("difficulty", "medium")
            sess["num_questions"] = interview.get("num_questions", 10)
            sess["duration"] = interview.get("duration", 30)
            sess["language"] = interview.get("language", "en")
            sess["personality"] = interview.get("personality", "professional")
            sess["type"] = interview.get("type", "technical")
            sess["adaptive"] = interview.get("adaptive", True)
            sess["ai_interviewer"] = interview.get("ai_interviewer", True)
            sess["integrity_monitoring"] = interview.get("integrity_monitoring", True)
            
            # Setup interviewer configuration dict
            sess["interviewer"] = {
                "personality": sess["personality"],
                "language": sess["language"],
                "state": "idle",
                "candidate_name": get_candidate_name(),
                "conversation": []
            }
            
            log_audit("INVITATION_ACCEPTED", user_id=str(session["user_id"]), session_id=sid)
            return jsonify({
                "session_id": sid,
                "status": "started",
                "invitation_bound": True,
                "interview_title": interview.get("title")
            })

    print(f"[Session] Started: {sid[:8]}...")
    return jsonify({"session_id": sid, "status": "started"})


@app.route("/api/session/<sid>", methods=["GET"])
@session_owner_required
def get_session_data(sid):
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(sess)


@app.route("/api/session/consent", methods=["POST"])
@session_owner_required
def session_consent():
    data = request.json or {}
    sid = data.get("session_id")
    camera = data.get("camera", False)
    microphone = data.get("microphone", False)
    recording = data.get("recording", False)

    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Session not found"}), 404

    sess["consents"] = {
        "camera": camera,
        "microphone": microphone,
        "recording": recording,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

    if camera:
        log_audit("CAMERA_CONSENT", session_id=sid)
    if microphone:
        log_audit("MICROPHONE_CONSENT", session_id=sid)
    if recording:
        log_audit("RECORDING_CONSENT", session_id=sid)

    return jsonify({"success": True, "consents": sess["consents"]})


@app.route("/api/resume/upload", methods=["POST"])
@session_owner_required
def upload_resume():
    sid = request.form.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400

    # File Size check (limit to 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB limit"}), 400

    path = os.path.join(UPLOAD_FOLDER, f"{sid}_resume.pdf")
    file.save(path)

    raw_text = extract_text_from_pdf(path)
    validation = validate_resume_document(raw_text)

    if not validation["resume_valid"]:
        sess["skills"] = []
        log_audit("RESUME_REJECTED", session_id=sid, extra={"reason": validation["reason"], "doc_type": validation["document_type"]})
        print(f"[Resume] REJECTED non-resume PDF ({validation['document_type']}): {validation['reason']}")
        return jsonify({
            "success": False,
            "resume_valid": False,
            "document_type": validation["document_type"],
            "resume_confidence": validation["resume_confidence"],
            "session_id": sid,
            "skills_detected": [],
            "skill_count": 0,
            "message": validation["reason"]
        })

    skills = extract_skills_from_resume(path)
    sess["skills"] = skills
    log_audit("RESUME_UPLOADED", session_id=sid)
    print(f"[Resume] {len(skills)} skills detected: {skills}")
    return jsonify({
        "success": True,
        "resume_valid": True,
        "document_type": "resume",
        "resume_confidence": validation["resume_confidence"],
        "session_id": sid,
        "skills_detected": skills,
        "skill_count": len(skills)
    })


@app.route("/api/resume/analyze", methods=["POST"])
@login_required
def api_analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["resume"]
    if not file.filename or not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF supported"}), 400

    # MIME Type and File Size check (limit to 5MB)
    if file.content_type != "application/pdf":
        return jsonify({"error": "Invalid file type. Only PDF is allowed."}), 400
    
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB limit"}), 400
        
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
@session_owner_required
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

    if not sess.get("skills"):
        return jsonify({"error": "Upload resume or select skills first"}), 400

    # Opt-in only (default off): candidate/recruiter explicitly asked for a
    # full multi-round interview (Technical -> HR by default). This must run
    # before generate_questions() below so the first round's skill list
    # (a no-op for "technical") is already in place. Every existing flow that
    # never sends multi_round=true is completely unaffected.
    if data.get("multi_round"):
        round_manager.init_rounds(sess, rounds=data.get("rounds"))

    try:
        lang = sess.get("interviewer", {}).get("language", "en")
        personality = sess.get("interviewer", {}).get("personality", "professional")
        questions = generate_questions(sess["skills"], lang=lang, personality=personality)
        num_q = sess.get("num_questions")
        # Self-practice sessions (no recruiter invitation) may carry the
        # candidate's own Settings > Interview Preferences as a soft
        # question-count cap and starting-difficulty seed. Recruiter-
        # assigned interviews already set num_questions/current_difficulty
        # explicitly in start_session() above and are never touched here --
        # "adaptive" (the default) reproduces today's exact prior behavior.
        starting_difficulty = "easy"
        if not sess.get("invitation_token") and settings_manager is not None \
                and "user_id" in session and db is not None:
            try:
                pref_user = db["users"].find_one({"_id": ObjectId(session["user_id"])})
                prefs = settings_manager.get_preferences(pref_user)
                if not num_q:
                    num_q = settings_manager.LENGTH_TO_QUESTION_COUNT.get(prefs["interview_length"])
                starting_difficulty = settings_manager.DIFFICULTY_TO_SEED.get(
                    prefs["preferred_difficulty"], "easy")
            except Exception as _pref_err:
                print(f"[WARN] Could not load interview preferences, using defaults: {_pref_err}")
        if num_q and isinstance(num_q, int):
            questions = questions[:num_q]
        sess["questions"] = questions
        sess["current_index"] = 0
        sess["current_difficulty"] = starting_difficulty
        log_audit("INTERVIEW_STARTED", session_id=sid)
        print(f"[Questions] {len(questions)} generated")
        return jsonify(
            {
                "session_id": sid,
                "total_questions": len(questions),
                "first_question": questions[0] if questions else None,
                "round_progress": round_manager.round_progress_label(sess),
            }
        )
    except Exception as e:
        print(f"[Questions ERROR] {e}")
        return jsonify({"error": f"Question generation failed: {str(e)}"}), 500


@app.route("/api/interviewer/configure", methods=["POST"])
@session_owner_required
def api_configure_interviewer():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    personality = data.get("personality", "professional").lower()
    language = data.get("language", "en").lower()

    if "interviewer" not in sess:
        sess["interviewer"] = {
            "personality": "professional",
            "language": "en",
            "state": "idle",
            "candidate_name": get_candidate_name(),
            "conversation": []
        }

    sess["interviewer"]["personality"] = personality
    sess["interviewer"]["language"] = language
    sess["interviewer"]["candidate_name"] = get_candidate_name()

    print(f"[Interviewer] Configured for session {sid}: personality={personality}, language={language}")
    return jsonify({"success": True, "interviewer": sess["interviewer"]})


@app.route("/api/questions/next", methods=["POST"])
@session_owner_required
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
@session_owner_required
def submit_answer():
    data = request.json or {}
    sid = data.get("session_id")
    ans = data.get("answer", "")
    q = data.get("question", "")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    # Response latency (spec: "how long the candidate takes to begin
    # answering") -- purely a performance/UX metric surfaced on the report,
    # never used to adjust scoring or flag anything. Optional and additive:
    # older frontend builds that don't send it just get None stored.
    latency_raw = data.get("response_latency_seconds")
    response_latency = None
    if isinstance(latency_raw, (int, float)) and latency_raw >= 0:
        response_latency = int(latency_raw)

    # Perform evaluation and next action decision using the AI Interviewer
    if data.get("mock_eval"):
        ev = data.get("mock_eval")
    else:
        ev = evaluate_and_transition(sess, q, ans)
    sess["technical_scores"].append(ev["score"])

    # Identify the skill corresponding to the question
    detected_skill = "General"
    for item in sess.get("questions", []):
        if item.get("question") == q:
            detected_skill = item.get("skill", "General")
            break
    if detected_skill == "General":
        for s in sess.get("skills", []):
            if s.lower() in q.lower():
                detected_skill = s
                break

    # Format the dimensions, confidence, evidence, reasons for storage
    dims = ev.get("dimensions", {})
    dimension_scores = {k: v.get("score") for k, v in dims.items()}
    confidence_map = {k: v.get("confidence") for k, v in dims.items()}
    evidence_list = []
    reasons_map = {}
    for k, v in dims.items():
        reasons_map[k] = v.get("reason", "")
        evidence_list.extend(v.get("evidence", []))

    sess["answers"].append(
        {
            "question": q,
            "answer": ans,
            "score": ev["score"],
            "overall": ev["score"],
            "overall_score": ev["score"],
            "skill": detected_skill,
            "difficulty": sess["current_difficulty"],
            "feedback": ev["feedback"],
            "evaluation": dimension_scores,
            "confidence": confidence_map,
            "evidence": evidence_list,
            "reasons": reasons_map,
            "strengths": ev.get("strengths", []),
            "improvements": ev.get("improvements", []),
            "response_latency_seconds": response_latency,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    )

    # Update running skill scores, strong/weak areas, and repetition logs in MongoDB
    from modules.adaptive_engine import update_adaptive_state
    from flask import session as flask_session
    if "user_id" in flask_session:
        sess["user_id"] = str(flask_session["user_id"])
    
    update_adaptive_state(sess, q, detected_skill, ev["score"])

    # Update candidate intelligence profile (Knowledge Depth, Consistency, Map, Confidence, Contradictions, Self-corrections)
    from modules.candidate_intelligence import update_candidate_profile_step
    u_id = sess.get("user_id") or "guest"
    last_voice_conf = sess["voice_scores"][-1] if sess.get("voice_scores") else None
    ev["skill"] = detected_skill
    ev["difficulty"] = sess["current_difficulty"]
    update_candidate_profile_step(sess, u_id, q, ans, ev, voice_confidence=last_voice_conf)

    # Compile next action
    action = ev.get("action", "next_question")
    question_text = ""
    question_skill = "Follow-up"
    
    # Track conversation history inside session
    if "interviewer" not in sess:
        sess["interviewer"] = {
            "personality": "professional",
            "language": "en",
            "state": "listening",
            "candidate_name": get_candidate_name(),
            "conversation": []
        }
    
    # Save candidate answer
    sess["interviewer"]["conversation"].append({
        "role": "candidate",
        "type": "answer",
        "text": ans
    })

    round_transitioned = False

    if action == "next_question":
        # Pull next question from the pre-generated pool (or, for a
        # multi-round session, roll into the next configured round first)
        next_q, round_transitioned = _next_question_or_advance_round(sess)
        if next_q is None:
            action = "finish"
            question_text = "That completes our questions. Thank you for your time."
            question_skill = "General"
        else:
            question_text = next_q["question"]
            question_skill = next_q.get("skill", "General")
    elif action == "follow_up" or action == "clarification":
        question_text = ev.get("question", "")
        if not question_text:
            # Fallback if AI forgot to write the question
            next_q, round_transitioned = _next_question_or_advance_round(sess)
            if next_q is None:
                action = "finish"
                question_text = "Thank you for your response. We have completed the questions."
            else:
                question_text = next_q["question"]
                question_skill = next_q.get("skill", "General")
    else:
        action = "finish"
        question_text = "Thank you. That concludes the interview."
        question_skill = "General"

    if round_transitioned:
        action = "round_complete"

    # Save next interviewer question in context if not finish
    if action != "finish":
        full_interviewer_text = (ev.get("transition", "") + " " + question_text).strip()
        sess["interviewer"]["conversation"].append({
            "role": "interviewer",
            "type": "question",
            "text": full_interviewer_text
        })

    # Update difficulty progression based on moving average. For a multi-round
    # session, this is windowed to the CURRENT round only (round_started_at_
    # answer_count, the same offset should_interview_finish uses in
    # modules/adaptive_engine.py) so a new round's difficulty trend isn't
    # skewed by the previous round's trailing scores. round_started_at_
    # answer_count is never set for an ordinary single-round session, so
    # round_scores below is just the full list there - unchanged behavior.
    round_start = sess.get("round_started_at_answer_count", 0)
    round_scores = sess["technical_scores"][round_start:] or sess["technical_scores"]
    rt = round_scores[-3:]
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

    # If the action was finish, set session status
    if action == "finish":
        # Snapshot whichever round was still active into round_history too --
        # advance_round() above only snapshots the rounds *between*
        # transitions. No-op for a non-multi-round session.
        round_manager.finalize(sess)
        sess["status"] = "completed"
        log_audit("INTERVIEW_COMPLETED", session_id=sid)
        import threading
        u_id = session.get("user_id")
        t = threading.Thread(target=async_generate_report, args=(sid, u_id))
        t.daemon = True
        t.start()

    return jsonify(
        {
            "score": ev["score"],
            "feedback": ev["feedback"],
            "strengths": ev.get("strengths", []),
            "improvements": ev.get("improvements", []),
            "dimensions": ev.get("dimensions", {}),
            "next_difficulty": sess["current_difficulty"],
            "action": action,
            "transition": ev.get("transition", ""),
            "round_complete": round_transitioned,
            "round_progress": round_manager.round_progress_label(sess),
            "next_question": {
                "question": {
                    "question": question_text,
                    "skill": question_skill,
                    "difficulty": sess["current_difficulty"]
                },
                "index": sess["current_index"],
                "difficulty": sess["current_difficulty"],
                "total": len(sess["questions"])
            },
            "done": (action == "finish")
        }
    )


@app.route("/api/interview/end-early", methods=["POST"])
@session_owner_required
def end_interview_early():
    """
    Candidate-initiated early end (the "End Interview" button + confirmation
    dialog in interview.html). Distinct from both a normal completion
    (status "completed", ends naturally when the adaptive engine/question
    cap decides enough evidence is in) and an integrity termination (status
    "terminated", set by /api/integrity/violation) -- this is a deliberate,
    voluntary stop, and the report should say so neutrally rather than
    implying either of those.
    """
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    if sess.get("status") not in ("completed", "terminated"):
        # Snapshot whichever round was active (no-op for a non-multi-round
        # session) so round_scores still reflects what was actually covered.
        round_manager.finalize(sess)
        sess["status"] = "ended_early"
        log_audit("INTERVIEW_ENDED_EARLY", session_id=sid)

        import threading
        u_id = session.get("user_id")
        t = threading.Thread(target=async_generate_report, args=(sid, u_id))
        t.daemon = True
        t.start()

    return jsonify({"success": True, "status": sess.get("status")})


@app.route("/api/emotion/analyze", methods=["POST"])
@session_owner_required
def analyze_emotion():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    result = analyze_emotion_frame(data.get("frame", ""), sess)
    sess["emotion_timeline"].append(result)
    return jsonify(result)


@app.route("/api/voice/analyze", methods=["POST"])
@session_owner_required
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
@session_owner_required
def integrity_violation():
    """
    Records one integrity event (tab_switch / camera_exit / window_move /
    multiple_faces) and applies the existing 3-strike termination rule.

    NOTE (fix): this used to decide termination from modules/
    integrity_monitor.py's `violations` dict, a plain in-process module-level
    global. That works fine in a single long-lived dev process, but under
    the project's actual Vercel/serverless deployment target each function
    invocation can get a fresh process, silently resetting that counter to 0
    -- so strikes would never reliably accumulate in production. The count
    now comes from sess["violations"]["total"], which is persisted to
    MongoDB via save_accessed_sessions on every request, so it survives
    across invocations exactly like every other piece of session state.
    """
    data = request.json or {}
    session_id = data.get("session_id")
    vtype = data.get("type")

    sess = get_sess(session_id)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400

    # Hard guarantee: certain signals (low light, blur, face too-far/too-
    # close/partially-visible, sustained head-turn) must NEVER contribute
    # to the 3-strike count, no matter what calls this route with what
    # vtype string -- see modules/integrity_config.NEVER_STRIKE_EVENT_TYPES.
    # They are logged as a structured, non-strike event instead, using the
    # same shape /api/emotion/analyze already logs Tier-1/2 telemetry with.
    if vtype in NEVER_STRIKE_EVENT_TYPES:
        sess.setdefault("integrity_events", []).append({
            "type": vtype.upper(),
            "severity": "info",
            "confidence": None,
            "start_ts": None,
            "end_ts": None,
            "duration_sec": None,
            "timestamp": datetime.datetime.utcnow().timestamp(),
            "details": {"source": "client_reported_non_strike"},
        })
        return jsonify({
            "violations": sess.get("violations", {}).get("total", 0),
            "terminate": False,
            "counts": sess.get("violations", {}),
            "warning": None,
            "warning_level": "info",
        })

    sess.setdefault("violations", {})
    sess["violations"][vtype] = sess["violations"].get(vtype, 0) + 1
    sess["violations"]["total"] = sess["violations"].get("total", 0) + 1
    count = sess["violations"]["total"]
    terminate = count >= 3

    # Mirror every real strike into the same structured event log the new
    # Tier-1/2 warning-tier telemetry uses, so the final report can show
    # one consistent timeline (type/severity/timestamp/duration) instead of
    # two disconnected data shapes.
    #
    # FIX: phone_detected is special -- modules/emotion_detector.py's
    # _confirm_episode() already appended a richer event for this exact
    # episode (real confidence + duration) the moment it was server-
    # confirmed, just before the client posted this violation. Attach the
    # strike number to THAT event instead of appending a second, poorer-
    # quality duplicate (confidence/duration all None) for the same
    # episode -- otherwise the report's integrity timeline would show the
    # same phone-detection episode twice.
    now_ts = datetime.datetime.utcnow().timestamp()
    events = sess.setdefault("integrity_events", [])
    mirrored_existing = False
    if vtype == "phone_detected":
        for ev in reversed(events):
            if (ev.get("type") == "PHONE_DETECTED"
                    and (ev.get("details") or {}).get("strike_number") is None
                    and (now_ts - (ev.get("timestamp") or 0)) < 15):
                ev["details"] = dict(ev.get("details") or {}, strike_number=count)
                mirrored_existing = True
                break

    if not mirrored_existing:
        events.append({
            "type": vtype.upper(),
            "severity": "critical",
            "confidence": None,
            "start_ts": None,
            "end_ts": None,
            "duration_sec": None,
            "timestamp": now_ts,
            "details": {"strike_number": count},
        })

    if terminate:
        sess["status"] = "terminated"
        # Explicit, authoritative termination record -- so the report can
        # show the EXACT reason/trigger/time instead of inferring it from
        # a bare boolean (see modules/evaluator.py's generate_final_report
        # and frontend/assets/js/report.js's Integrity Summary section).
        sess["termination_reason"] = "integrity_strike_limit"
        sess["termination_trigger_event"] = vtype
        sess["termination_time"] = datetime.datetime.utcnow().isoformat() + "Z"
        log_audit("INTERVIEW_TERMINATED", session_id=session_id)

        # FIX (race): persist the terminated session to MongoDB
        # SYNCHRONOUSLY, before spawning the background report thread.
        # get_sess() always does a fresh MongoDB read when db is
        # configured, but the normal persistence path
        # (@app.after_request save_accessed_sessions) only runs AFTER
        # this view function returns -- so the background thread below
        # could otherwise read a STALE pre-termination session (missing
        # this final strike, still status="active") if it happened to run
        # before that hook. This mirrors exactly what that hook does.
        if db is not None:
            try:
                sess["updated_at"] = datetime.datetime.utcnow().isoformat()
                db["sessions"].replace_one({"id": session_id}, sess, upsert=True)
            except Exception as e:
                print(f"[WARN] Failed to synchronously persist terminated session {session_id}: {e}")

        import threading
        u_id = session.get("user_id")
        t = threading.Thread(target=async_generate_report, args=(session_id, u_id))
        t.daemon = True
        t.start()

    return jsonify({
        "violations": count,
        "terminate": terminate,
        "counts": sess["violations"],  # per-type breakdown for the frontend badges
        "warning": f"Strike {count}/3" if not terminate else "Interview terminated",
        "warning_level": "critical" if count >= 2 else "warning"
    })


@app.route("/api/recording/save", methods=["POST"])
@session_owner_required
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
    log_audit("RECORDING_STOPPED", session_id=sid)
    return jsonify({"saved": True})


@app.route("/api/ai/insights", methods=["POST"])
@session_owner_required
def ai_insights():
    data = request.json or {}
    sid = data.get("session_id")
    sess = get_sess(sid)
    if not sess:
        return jsonify({"error": "Invalid session"}), 400
    insights = get_ai_insights(sess)
    return jsonify(insights)


@app.route("/api/ai/followup", methods=["POST"])
@login_required
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

@app.route("/api/report/status/<sid>", methods=["GET"])
@session_owner_required
def get_report_status(sid):
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    reports_col = db["reports"]
    report_doc = reports_col.find_one({"session_id": sid})

    if not report_doc:
        sess = get_sess(sid)
        if sess:
            reports_col.insert_one({
                "session_id": sid,
                "user_id": str(session.get("user_id")),
                "status": "generating",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z"
            })
            import threading
            t = threading.Thread(target=async_generate_report, args=(sid, session.get("user_id")))
            t.daemon = True
            t.start()
            return jsonify({"status": "generating"})
        else:
            return jsonify({"status": "missing", "message": "Session not found"}), 404

    return jsonify({
        "status": report_doc.get("status"),
        "report": clean_json(report_doc.get("report")),
        "message": report_doc.get("error_message", "")
    })

# ── CONTINUOUS LEARNING & PERSONALIZED PRACTICE ENDPOINTS ─────────────────────────

def get_report_comparison_metrics(report):
    scores = report.get("scores", {})
    answers = report.get("answers", [])
    
    tech = scores.get("technical", 0)
    comm = scores.get("confidence", 0)
    overall = scores.get("readiness_index", 0)
    
    depths = []
    clarities = []
    ps_scores = []
    
    for a in answers:
        sc = a.get("score", 50)
        diff = a.get("difficulty", "medium").lower()
        
        if diff in ["medium", "hard"]:
            ps_scores.append(sc)
            
        eval_details = a.get("eval_details", {})
        d_val = eval_details.get("depth") or eval_details.get("depth_score")
        c_val = eval_details.get("clarity") or eval_details.get("clarity_score")
        
        if d_val is not None:
            depths.append(d_val)
        else:
            depths.append(sc if diff == "hard" else (sc - 10 if diff == "medium" else sc - 20))
            
        if c_val is not None:
            clarities.append(c_val)
        else:
            clarities.append(sc)
            
    depth_avg = int(sum(depths)/len(depths)) if depths else tech - 5
    clarity_avg = int(sum(clarities)/len(clarities)) if clarities else comm
    ps_avg = int(sum(ps_scores)/len(ps_scores)) if ps_scores else tech
    
    depth_avg = max(0, min(100, depth_avg))
    clarity_avg = max(0, min(100, clarity_avg))
    ps_avg = max(0, min(100, ps_avg))
    
    skill_scores = report.get("skill_scores", {})
    if not skill_scores:
        skill_scores = {}
        for a in answers:
            sk = a.get("skill")
            sc = a.get("score")
            if sk and sc is not None:
                if sk not in skill_scores:
                    skill_scores[sk] = []
                skill_scores[sk].append(sc)
        skill_scores = {k: int(sum(v)/len(v)) for k, v in skill_scores.items()}
        
    return {
        "overall": overall,
        "technical": tech,
        "communication": comm,
        "depth": depth_avg,
        "clarity": clarity_avg,
        "problem_solving": ps_avg,
        "skills": skill_scores
    }

@app.route("/api/learning/dashboard", methods=["GET"])
@login_required
def get_learning_dashboard():
    user_id = session.get("user_id")
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    progress_col = db["learning_progress"]
    progress = progress_col.find_one({"user_id": str(user_id)})
    
    # Compute candidate profile and real-world statistics
    user_doc = db["users"].find_one({"_id": ObjectId(user_id)})
    user_name = user_doc.get("name", "Candidate") if user_doc else "Candidate"
    user_email = user_doc.get("email") if user_doc else ""
    
    profile = db["candidate_profiles"].find_one({"user_id": str(user_id)})
    resume_status = "Uploaded" if (profile and profile.get("skills")) else "Not Uploaded"
    detected_skills = list(profile.get("skills", {}).keys()) if (profile and profile.get("skills")) else []
    
    reports_col = db["reports"]
    all_completed = list(reports_col.find({
        "user_id": str(user_id),
        "status": "completed"
    }).sort("created_at", -1))
    
    total_completed = len(all_completed)
    scores = []
    recent_list = []
    
    for r in all_completed:
        rep = r.get("report", {})
        sc = rep.get("scores", {}).get("readiness_index")
        if sc is not None:
            scores.append(sc)
            
        recent_list.append({
            "session_id": r.get("session_id"),
            "is_practice": rep.get("is_practice", False),
            "job_role": rep.get("job_role", "Software Engineer"),
            "skills": list(rep.get("skill_scores", {}).keys())[:3],
            "score": sc or 0,
            "date": rep.get("date", "")
        })
        
    avg_score = int(sum(scores)/len(scores)) if scores else 0
    best_score = max(scores) if scores else 0
    latest_score = scores[0] if scores else 0
    
    skills_list = []
    skills_improved_count = 0
    if progress:
        for skill, sdata in progress.get("skills", {}).items():
            skills_list.append({
                "name": skill,
                "status": sdata.get("status", "Weak"),
                "history": sdata.get("history", [])
            })
            hist = sdata.get("history", [])
            if len(hist) > 1 and hist[-1].get("score", 0) > hist[0].get("score", 0):
                skills_improved_count += 1
                
    # Re-use existing comparisons if matching mock reports exist
    interviews = list(reports_col.find({
        "user_id": str(user_id), 
        "status": "completed",
        "report.is_practice": {"$ne": True}
    }).sort("created_at", 1))
    
    practice_reports = list(reports_col.find({
        "user_id": str(user_id),
        "status": "completed",
        "report.is_practice": True
    }).sort("created_at", -1))
    
    comp_data = {
        "previous": None,
        "practice": None,
        "latest": None
    }
    if interviews:
        comp_data["previous"] = get_report_comparison_metrics(interviews[0]["report"])
        if len(interviews) > 1:
            comp_data["latest"] = get_report_comparison_metrics(interviews[-1]["report"])
        else:
            comp_data["latest"] = comp_data["previous"]
            
    if practice_reports:
        comp_data["practice"] = get_report_comparison_metrics(practice_reports[0]["report"])
        
    response_payload = {
        "has_history": total_completed > 0,
        "weak_areas": [s["name"] for s in skills_list if s["status"] == "Weak"],
        "skills": skills_list,
        "roadmap": progress.get("roadmap", []) if progress else [],
        "recommendations": progress.get("recommendations", []) if progress else [],
        "improvement_history": progress.get("improvement_history", []) if progress else [],
        "comparison": comp_data,
        "profile": {
            "name": user_name,
            "email": user_email,
            "resume_status": resume_status,
            "detected_skills": detected_skills
        },
        "stats": {
            "total_completed": total_completed,
            "avg_score": avg_score,
            "best_score": best_score,
            "latest_score": latest_score,
            "skills_improved": skills_improved_count
        },
        "recent_interviews": recent_list
    }
    
    return jsonify(clean_json(response_payload))


@app.route("/api/practice/start", methods=["POST"])
@login_required
def start_practice_session():
    user_id = session.get("user_id")
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    progress_col = db["learning_progress"]
    progress = progress_col.find_one({"user_id": str(user_id)})
    
    from modules.candidate_intelligence import load_candidate_profile
    profile = load_candidate_profile(user_id, resume_skills=[])
    
    weak_areas = []
    if progress:
        weak_areas = [s for s, d in progress.get("skills", {}).items() if d.get("status") == "Weak"]
    if not weak_areas and profile:
        weak_areas = profile.get("weak_areas", [])
        
    if not weak_areas:
        weak_areas = list(profile.get("skills", {}).keys())
        
    if not weak_areas:
        return jsonify({"error": "No interview history found. Complete a full interview first to detect weak areas."}), 400

    sid = str(uuid.uuid4())
    new_sess(sid)
    sess = get_sess(sid)
    sess["is_practice"] = True
    sess["skills"] = weak_areas
    
    scores = []
    for s in weak_areas:
        if profile and s in profile.get("skills", {}):
            scores.append(profile["skills"][s].get("score", 50))
            
    avg_score = sum(scores)/len(scores) if scores else 50
    
    # Deterministic score-band rule shared with in-session adaptation
    # (modules/difficulty_engine.py) -- one source of truth, not a
    # bespoke ladder duplicated per endpoint.
    difficulty = initial_difficulty_from_score(avg_score)
        
    sess["current_difficulty"] = difficulty
    
    lang = sess.get("interviewer", {}).get("language", "en")
    personality = sess.get("interviewer", {}).get("personality", "professional")
    questions = generate_questions(sess["skills"], lang=lang, personality=personality)
    sess["questions"] = questions
    sess["current_index"] = 0
    
    log_audit("PRACTICE_STARTED", session_id=sid)
    return jsonify({
        "session_id": sid,
        "skills_detected": sess["skills"],
        "total_questions": len(questions),
        "first_question": questions[0] if questions else None,
        "difficulty": difficulty
    })

@app.route("/api/practice/reinterview", methods=["POST"])
@login_required
def start_reinterview_session():
    user_id = session.get("user_id")
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    progress_col = db["learning_progress"]
    progress = progress_col.find_one({"user_id": str(user_id)})
    
    from modules.candidate_intelligence import load_candidate_profile
    profile = load_candidate_profile(user_id, resume_skills=[])
    
    weak_areas = []
    if progress:
        weak_areas = [s for s, d in progress.get("skills", {}).items() if d.get("status") == "Weak"]
    if not weak_areas and profile:
        weak_areas = profile.get("weak_areas", [])
        
    if not weak_areas:
        weak_areas = list(profile.get("skills", {}).keys())
        
    if not weak_areas:
        return jsonify({"error": "No interview history found."}), 400

    sid = str(uuid.uuid4())
    new_sess(sid)
    sess = get_sess(sid)
    sess["is_practice"] = False
    sess["skills"] = weak_areas
    
    reports_col = db["reports"]
    last_practice = reports_col.find_one({
        "user_id": str(user_id),
        "status": "completed",
        "report.is_practice": True
    }, sort=[("created_at", -1)])
    
    avg_score = 50
    if last_practice:
        avg_score = last_practice.get("report", {}).get("scores", {}).get("technical", 50)
    elif profile:
        scores = [profile["skills"][s].get("score", 50) for s in weak_areas if s in profile.get("skills", {})]
        avg_score = sum(scores)/len(scores) if scores else 50
        
    # Deterministic score-band rule shared with in-session adaptation
    # (modules/difficulty_engine.py) -- one source of truth, not a
    # bespoke ladder duplicated per endpoint.
    difficulty = initial_difficulty_from_score(avg_score)
        
    sess["current_difficulty"] = difficulty
    
    lang = sess.get("interviewer", {}).get("language", "en")
    personality = sess.get("interviewer", {}).get("personality", "professional")
    questions = generate_questions(sess["skills"], lang=lang, personality=personality)
    sess["questions"] = questions
    sess["current_index"] = 0
    
    log_audit("REINTERVIEW_STARTED", session_id=sid)
    return jsonify({
        "session_id": sid,
        "skills_detected": sess["skills"],
        "total_questions": len(questions),
        "first_question": questions[0] if questions else None,
        "difficulty": difficulty
    })




@app.route("/api/report/generate", methods=["POST"])
@session_owner_required
def get_report():
    data = request.json or {}
    sid = data.get("session_id")

    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    reports_col = db["reports"]
    report_doc = reports_col.find_one({"session_id": sid})

    if report_doc:
        if report_doc.get("status") == "completed":
            return jsonify(clean_json(report_doc["report"]))
        elif report_doc.get("status") == "generating":
            return jsonify({"status": "generating"}), 202
        elif report_doc.get("status") == "failed":
            pass

    # Trigger async report generation
    reports_col.update_one(
        {"session_id": sid},
        {"$set": {
            "status": "generating",
            "user_id": str(session.get("user_id")),
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }},
        upsert=True
    )

    import threading
    t = threading.Thread(target=async_generate_report, args=(sid, session.get("user_id")))
    t.daemon = True
    t.start()

    return jsonify({"status": "generating"}), 202

# ── CODING PLATFORM ENDPOINTS ──────────────────────────────────────────────────

@app.route("/api/sessions/history", methods=["GET"])
@login_required
def get_sessions_history():
    history = load_history()
    summary_list = []
    user_id_str = str(session.get("user_id"))
    for sid, report in history.items():
        # Ensure they can only see their own sessions!
        if report.get("user_id") != user_id_str:
            continue
            
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
@session_owner_required
def view_historical_report(sid):
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    reports_col = db["reports"]
    report_doc = reports_col.find_one({"session_id": sid})
    if report_doc and report_doc.get("status") == "completed":
        return jsonify(clean_json(report_doc["report"]))

    # Fallback to history file check
    history = load_history()
    report = history.get(sid)
    if report:
        return jsonify(clean_json(report))

    # Fallback to active session
    sess = get_sess(sid)
    if sess:
        if report_doc and report_doc.get("status") == "generating":
            return jsonify({"status": "generating"}), 202
        report = generate_final_report(sess)
        return jsonify(clean_json(report))

    return jsonify({"error": "Report not found"}), 404

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


# ── INTERVIEWIQ AI ASSISTANT (authenticated, project+candidate-aware) ────────
# Distinct from the legacy /api/coach/chat above: this is the ONE
# candidate-facing AI assistant surfaced in the dashboard (see
# frontend/assistant.html). /api/coach/chat is left untouched -- it has no
# frontend link in the current dashboard and is not modified by this work.
@app.route("/api/ai-assistant/chat", methods=["POST"])
@login_required
def api_ai_assistant_chat():
    # SECURITY: the candidate identity comes ONLY from the authenticated
    # server-side session -- never from the request body.
    user_id = session.get("user_id")

    data = request.json or {}
    message = data.get("message", "")
    conversation_id = data.get("conversation_id")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(message) > ASSISTANT_MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Message is too long (max {ASSISTANT_MAX_MESSAGE_LENGTH} characters)."}), 400
    if conversation_id is not None and not isinstance(conversation_id, str):
        return jsonify({"error": "Invalid conversation_id."}), 400

    allowed, retry_after = assistant_check_rate_limit(user_id)
    if not allowed:
        return jsonify({
            "error": f"You're sending messages too quickly. Please wait {retry_after} seconds and try again."
        }), 429

    try:
        result = assistant_handle_chat_message(user_id, message, conversation_id=conversation_id)
        log_audit("AI_ASSISTANT_CHAT", user_id=user_id)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except AssistantProviderError:
        return jsonify({"error": "I'm temporarily unable to reach the AI service. Please try again in a moment."}), 503
    except Exception as e:
        print(f"[ERROR] AI Assistant chat failed: {e}")
        return jsonify({"error": "Something went wrong on our end. Please try again."}), 500


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
                    {"role": "system", "content": "You are a senior software engineer and technical interviewer. You must output ONLY a valid JSON object."},
                    {"role": "user", "content": prompt}
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
    return jsonify({
        "time_complexity": "O(N^2) or O(N)",
        "space_complexity": "O(N) or O(1)",
        "readability_score": 80,
        "feedback": "Code executes correctly. Please check that you avoid nested loops if possible to maintain optimal time complexity.",
        "suggestions": [
            "Verify loop boundaries.",
            "Consider utilizing auxiliary hashes/dicts to optimize query times from O(N) to O(1)."
        ]
    })


# ── SECURITY & ACCESS CONTROL DOWNLOADS / ADMIN ─────────────────────────────

@app.route("/api/recording/download/<sid>", methods=["GET"])
@login_required
def download_recording(sid):
    sess = get_sess(sid)
    user_id_str = str(session.get("user_id"))
    history = load_history()
    report = history.get(sid)

    owner_id = None
    if sess:
        owner_id = sess.get("user_id")
    elif report:
        owner_id = report.get("user_id")

    if not owner_id or owner_id != user_id_str:
        log_audit("FORBIDDEN_ACCESS", session_id=sid)
        return jsonify({"error": "Forbidden"}), 403

    filename = f"{sid}_recording.webm"
    file_path = os.path.join(RECORDING_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Recording file not found"}), 404

    return send_from_directory(RECORDING_FOLDER, filename)


@app.route("/api/resume/download/<sid>", methods=["GET"])
@login_required
def download_resume(sid):
    sess = get_sess(sid)
    user_id_str = str(session.get("user_id"))
    history = load_history()
    report = history.get(sid)

    owner_id = None
    if sess:
        owner_id = sess.get("user_id")
    elif report:
        owner_id = report.get("user_id")

    if not owner_id or owner_id != user_id_str:
        log_audit("FORBIDDEN_ACCESS", session_id=sid)
        return jsonify({"error": "Forbidden"}), 403

    filename = f"{sid}_resume.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Resume file not found"}), 404

    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users():
    if users_col is None:
        return jsonify({"error": "Database unavailable"}), 503
    users = list(users_col.find({}, {"password_hash": 0}))
    for u in users:
        u["_id"] = str(u["_id"])
        if "created_at" in u and isinstance(u["created_at"], datetime.datetime):
            u["created_at"] = u["created_at"].isoformat()
    return jsonify(users)


@app.route("/api/admin/audit-logs", methods=["GET"])
@admin_required
def admin_audit_logs():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
    logs = list(db["audit_logs"].find().sort("timestamp", -1).limit(100))
    for l in logs:
        l["_id"] = str(l["_id"])
    return jsonify(logs)


# ── RECRUITER ASSESSMENT TEMPLATES ──────────────────────────────────────────

@app.route("/api/recruiter/interviews", methods=["POST"])
@role_required(["recruiter", "admin"])
def recruiter_create_interview():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
    
    data = request.json or {}
    title = data.get("title", "New Interview Assessment").strip()
    job_role = data.get("job_role", "Software Engineer").strip()
    description = data.get("description", "").strip()
    skills = data.get("skills", [])
    difficulty = data.get("difficulty", "medium")
    num_questions = int(data.get("num_questions", 10))
    duration = int(data.get("duration", 30))
    language = data.get("language", "en")
    personality = data.get("personality", "professional")
    type_val = data.get("type", "technical")
    
    # Flags
    adaptive = bool(data.get("adaptive", True))
    ai_interviewer = bool(data.get("ai_interviewer", True))
    integrity_monitoring = bool(data.get("integrity_monitoring", True))
    
    recruiter_id = str(session["user_id"])
    
    interview_doc = {
        "recruiter_id": recruiter_id,
        "title": title,
        "job_role": job_role,
        "description": description,
        "skills": skills,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "duration": duration,
        "language": language,
        "personality": personality,
        "type": type_val,
        "adaptive": adaptive,
        "ai_interviewer": ai_interviewer,
        "integrity_monitoring": integrity_monitoring,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    res = db["interviews"].insert_one(interview_doc)
    interview_doc["id"] = str(res.inserted_id)
    interview_doc["_id"] = str(res.inserted_id)
    
    log_audit("INTERVIEW_CREATED", user_id=recruiter_id, session_id=interview_doc["_id"])
    return jsonify(clean_json(interview_doc)), 201


@app.route("/api/recruiter/interviews", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_get_interviews():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
    
    recruiter_id = str(session["user_id"])
    
    query = {}
    if session.get("role") != "admin":
        query["recruiter_id"] = recruiter_id
        
    interviews = list(db["interviews"].find(query).sort("created_at", -1))
    for i in interviews:
        i["id"] = str(i["_id"])
        i["_id"] = str(i["_id"])
        
    return jsonify(clean_json(interviews))


@app.route("/api/recruiter/interviews/<interview_id>", methods=["PUT"])
@role_required(["recruiter", "admin"])
def recruiter_update_interview(interview_id):
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    data = request.json or {}
    recruiter_id = str(session["user_id"])
    
    query = {"_id": ObjectId(interview_id)}
    if session.get("role") != "admin":
        query["recruiter_id"] = recruiter_id
        
    existing = db["interviews"].find_one(query)
    if not existing:
        return jsonify({"error": "Interview configuration not found or access denied"}), 404
        
    updates = {}
    fields = [
        "title", "job_role", "description", "skills", "difficulty", 
        "num_questions", "duration", "language", "personality", "type",
        "adaptive", "ai_interviewer", "integrity_monitoring"
    ]
    for f in fields:
        if f in data:
            val = data[f]
            if f in ["num_questions", "duration"]:
                val = int(val)
            elif f in ["adaptive", "ai_interviewer", "integrity_monitoring"]:
                val = bool(val)
            updates[f] = val
            
    updates["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    db["interviews"].update_one({"_id": ObjectId(interview_id)}, {"$set": updates})
    log_audit("INTERVIEW_CONFIG_CHANGED", user_id=recruiter_id, session_id=interview_id)
    
    updated_doc = db["interviews"].find_one({"_id": ObjectId(interview_id)})
    updated_doc["id"] = str(updated_doc["_id"])
    updated_doc["_id"] = str(updated_doc["_id"])
    return jsonify(clean_json(updated_doc))


# ── CANDIDATE INVITATIONS ─────────────────────────────────────────────────────

@app.route("/api/recruiter/invitations", methods=["POST"])
@role_required(["recruiter", "admin"])
def recruiter_create_invitation():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    interview_id = data.get("interview_id")
    expiration_hours = int(data.get("expiration_hours", 48))
    
    if not email or not interview_id:
        return jsonify({"error": "Email and interview_id are required"}), 400
        
    recruiter_id = str(session["user_id"])
    
    interview = db["interviews"].find_one({"_id": ObjectId(interview_id)})
    if not interview:
        return jsonify({"error": "Interview assessment configuration not found"}), 404
        
    token = str(uuid.uuid4())
    expiration_date = (datetime.datetime.utcnow() + datetime.timedelta(hours=expiration_hours)).isoformat() + "Z"
    
    invitation_doc = {
        "recruiter_id": recruiter_id,
        "email": email,
        "interview_id": interview_id,
        "interview_title": interview.get("title"),
        "job_role": interview.get("job_role"),
        "expiration_date": expiration_date,
        "status": "Pending",
        "token": token,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    db["interview_invitations"].insert_one(invitation_doc)
    invitation_doc["id"] = str(invitation_doc["_id"])
    invitation_doc["_id"] = str(invitation_doc["_id"])
    
    log_audit("CANDIDATE_INVITED", user_id=recruiter_id, session_id=token)
    return jsonify(clean_json(invitation_doc)), 201


@app.route("/api/recruiter/invitations", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_get_invitations():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    recruiter_id = str(session["user_id"])
    
    query = {}
    if session.get("role") != "admin":
        query["recruiter_id"] = recruiter_id
        
    invitations = list(db["interview_invitations"].find(query).sort("created_at", -1))
    for invite in invitations:
        invite["id"] = str(invite["_id"])
        invite["_id"] = str(invite["_id"])
        
    return jsonify(clean_json(invitations))


@app.route("/api/invite/status/<token>", methods=["GET"])
def get_invite_status(token):
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    invite = db["interview_invitations"].find_one({"token": token})
    if not invite:
        return jsonify({"error": "Invitation link is invalid"}), 404
        
    # Check expiration
    exp = invite.get("expiration_date")
    if exp:
        exp_dt = datetime.datetime.fromisoformat(exp.replace("Z", ""))
        if datetime.datetime.utcnow() > exp_dt:
            if invite.get("status") == "Pending":
                db["interview_invitations"].update_one({"token": token}, {"$set": {"status": "Expired"}})
                invite["status"] = "Expired"
                
    return jsonify({
        "interview_title": invite.get("interview_title"),
        "job_role": invite.get("job_role"),
        "status": invite.get("status"),
        "expiration_date": invite.get("expiration_date"),
        "token": token
    })


@app.route("/invite/<token>")
def serve_invite(token):
    return send_from_directory(FRONTEND_DIR, "invite.html")


# ── RECRUITER METRICS & AGGREGATION ───────────────────────────────────────────

@app.route("/api/recruiter/dashboard", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_dashboard_metrics():
    if db is None or users_col is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    recruiter_id = str(session["user_id"])
    role = session.get("role")
    
    # 1. Total candidates
    total_candidates = users_col.count_documents({"role": "candidate"})
    
    # 2. Invitations and statuses
    inv_query = {}
    if role != "admin":
        inv_query["recruiter_id"] = recruiter_id
        
    pending_invites = db["interview_invitations"].count_documents({**inv_query, "status": "Pending"})
    active_interviews = db["interview_invitations"].count_documents({**inv_query, "status": "Started"})
    completed_interviews = db["interview_invitations"].count_documents({**inv_query, "status": "Completed"})
    
    # 3. Average candidate score & Integrity violations
    rep_query = {"status": "completed"}
    if role != "admin":
        completed_invites = list(db["interview_invitations"].find({"recruiter_id": recruiter_id, "status": "Completed"}))
        completed_tokens = [i["token"] for i in completed_invites]
        rep_query["report.invitation_token"] = {"$in": completed_tokens}
    
    completed_docs = list(db["reports"].find(rep_query))
    
    scores = []
    violations_count = 0
    for doc in completed_docs:
        rep = doc.get("report", {})
        overall_score = rep.get("scores", {}).get("readiness_index")
        if overall_score is not None:
            scores.append(overall_score)
            
        integrity = rep.get("integrity", {})
        tab_switches = integrity.get("tab_switches", 0)
        camera_exits = integrity.get("camera_exits", 0)
        if tab_switches > 0 or camera_exits > 0:
            violations_count += 1
            
    avg_score = int(sum(scores)/len(scores)) if scores else 0
    
    # Recent candidates
    recent_users = list(users_col.find({"role": "candidate"}).sort("created_at", -1).limit(5))
    recent_candidates = []
    for u in recent_users:
        recent_candidates.append({
            "id": str(u["_id"]),
            "email": u.get("email"),
            "name": u.get("name", "Candidate"),
            "created_at": u.get("created_at").isoformat() if isinstance(u.get("created_at"), datetime.datetime) else str(u.get("created_at"))
        })
        
    # Recent completed interviews
    recent_interviews = []
    completed_docs_sorted = sorted(completed_docs, key=lambda x: x.get("updated_at", ""), reverse=True)[:5]
    for doc in completed_docs_sorted:
        rep = doc.get("report", {})
        overall_score = rep.get("scores", {}).get("readiness_index", 0)
        cand_id = rep.get("user_id")
        cand_email = "anonymous"
        if cand_id and cand_id != "anonymous":
            try:
                c_user = users_col.find_one({"_id": ObjectId(cand_id)})
                if c_user:
                    cand_email = c_user.get("email", cand_email)
            except Exception:
                try:
                    c_user = users_col.find_one({"email": cand_id})
                    if c_user:
                        cand_email = c_user.get("email", cand_email)
                except Exception:
                    pass
        recent_interviews.append({
            "session_id": doc.get("session_id"),
            "candidate_email": cand_email,
            "job_role": rep.get("job_role", "Software Engineer"),
            "overall_score": overall_score,
            "date": rep.get("date", ""),
            "integrity_status": "Warning" if rep.get("integrity", {}).get("tab_switches", 0) > 0 else "Normal"
        })
        
    # Top candidates
    top_candidates = []
    from collections import defaultdict
    user_scores = defaultdict(list)
    for doc in completed_docs:
        rep = doc.get("report", {})
        u_email = rep.get("user_id")
        ov_sc = rep.get("scores", {}).get("readiness_index")
        if u_email and ov_sc is not None:
            user_scores[u_email].append(ov_sc)
            
    sorted_users = sorted(user_scores.items(), key=lambda x: max(x[1]), reverse=True)[:5]
    for email_or_id, u_sc in sorted_users:
        u_doc = None
        try:
            u_doc = users_col.find_one({"_id": ObjectId(email_or_id)})
        except Exception:
            pass
        if not u_doc:
            u_doc = users_col.find_one({"email": email_or_id})
            
        display_email = u_doc.get("email") if u_doc else email_or_id
        top_candidates.append({
            "email": display_email,
            "name": u_doc.get("name", "Candidate") if u_doc else "Candidate",
            "max_score": max(u_sc),
            "avg_score": int(sum(u_sc)/len(u_sc))
        })
        
    payload = {
        "metrics": {
            "total_candidates": total_candidates,
            "active_interviews": active_interviews,
            "completed_interviews": completed_interviews,
            "pending_invitations": pending_invites,
            "average_candidate_score": avg_score,
            "integrity_violations": violations_count
        },
        "recent_candidates": recent_candidates,
        "recent_interviews": recent_interviews,
        "top_candidates": top_candidates
    }
    
    return jsonify(clean_json(payload))


# ── CANDIDATE DIRECTORY & SEARCH ──────────────────────────────────────────────

@app.route("/api/recruiter/candidates", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_get_candidates():
    if db is None or users_col is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    search_query = request.args.get("search", "").strip().lower()
    skill_filter = request.args.get("skills", "").strip()
    
    candidates = list(users_col.find({"role": "candidate"}))
    
    result = []
    for c in candidates:
        email = c.get("email", "")
        name = c.get("name", "Candidate")
        
        if search_query and search_query not in email and search_query not in name.lower():
            continue
            
        profile = db["candidate_profiles"].find_one({"user_id": str(c["_id"])})
        candidate_skills = []
        if profile and profile.get("skills"):
            candidate_skills = list(profile["skills"].keys())
            
        if skill_filter:
            required_skills = [s.strip().lower() for s in skill_filter.split(",") if s.strip()]
            candidate_skills_lower = [s.lower() for s in candidate_skills]
            match = True
            for req in required_skills:
                if req not in candidate_skills_lower:
                    match = False
                    break
            if not match:
                continue
                
        best_score = 0
        avg_score = 0
        completed_count = 0
        
        reports = list(db["reports"].find({"user_id": str(c["_id"]), "status": "completed"}))
        scores = []
        for r in reports:
            ov = r.get("report", {}).get("scores", {}).get("readiness_index")
            if ov is not None:
                scores.append(ov)
        if scores:
            best_score = max(scores)
            avg_score = int(sum(scores)/len(scores))
            completed_count = len(scores)
            
        result.append({
            "id": str(c["_id"]),
            "email": email,
            "name": name,
            "skills": candidate_skills,
            "best_score": best_score,
            "avg_score": avg_score,
            "completed_interviews": completed_count,
            "created_at": c.get("created_at").isoformat() if isinstance(c.get("created_at"), datetime.datetime) else str(c.get("created_at"))
        })

    return jsonify(clean_json(result))


@app.route("/api/recruiter/live-sessions", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_live_sessions():
    """
    Recruiter live-watch view: point-in-time STATS/integrity polling for
    interviews currently in progress (question index, running technical/voice
    scores, latest emotion read, integrity violations) -- NOT a live webcam/
    audio relay, which would need WebRTC signaling infrastructure this
    project doesn't have. Recruiters poll this endpoint (see
    frontend/recruiter.html's Live Sessions tab) every few seconds.

    A session counts as "live" if it's status=="active" and was touched
    (see save_accessed_sessions' updated_at stamp) within the last 10
    minutes -- otherwise it's treated as abandoned, not live.
    """
    if db is None or users_col is None:
        return jsonify({"error": "Database unavailable"}), 503

    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(minutes=10)).isoformat()
    docs = list(db["sessions"].find({"status": "active", "updated_at": {"$gte": cutoff}}))

    result = []
    for sess in docs:
        user_id = sess.get("user_id")
        name, email = "Guest", ""
        if user_id and user_id not in ("anonymous", "guest"):
            try:
                user = users_col.find_one({"_id": ObjectId(user_id)})
                if user:
                    name = user.get("name", "Candidate")
                    email = user.get("email", "")
            except Exception:
                pass

        tech = sess.get("technical_scores", [])
        voice = sess.get("voice_scores", [])
        emots = sess.get("emotion_timeline", [])

        result.append({
            "session_id": sess.get("id"),
            "candidate_name": name,
            "candidate_email": email,
            "is_practice": sess.get("is_practice", False),
            "current_index": sess.get("current_index", 0),
            "total_questions": len(sess.get("questions", [])),
            "current_difficulty": sess.get("current_difficulty", "easy"),
            "round_progress": round_manager.round_progress_label(sess),
            "avg_technical_score": int(sum(tech) / len(tech)) if tech else None,
            "latest_technical_score": tech[-1] if tech else None,
            "latest_voice_score": voice[-1] if voice else None,
            "latest_emotion": emots[-1].get("dominant_emotion") if emots else None,
            "violations": sess.get("violations", {}),
            "started_at": sess.get("created_at"),
            "last_activity_at": sess.get("updated_at"),
        })

    # Most recently active first
    result.sort(key=lambda r: r.get("last_activity_at") or "", reverse=True)
    return jsonify(clean_json({"sessions": result, "count": len(result)}))


VALID_INTERVIEW_OUTCOMES = {"hired", "rejected", "advanced", "no_decision"}


@app.route("/api/recruiter/interviews/<session_id>/outcome", methods=["PUT"])
@role_required(["recruiter", "admin"])
def recruiter_set_interview_outcome(session_id):
    """
    Records a recruiter's real hiring decision against a completed interview.
    This is the first genuine outcome-labeled data this project collects --
    every dataset it ships with (datasets/*.json) only has
    {question, difficulty, skill}, nothing about whether a candidate who
    scored well actually got hired. Purely additive: does not change
    scoring, reports, or any existing recruiter/candidate flow. Once enough
    labeled examples exist, this is what a real supervised "does this
    interview predict a hire" model would train on -- see
    modules/outcome_model.py's MIN_SAMPLES guard, which refuses to fabricate
    a fitted model before there's enough data for that to mean anything.
    """
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.json or {}
    outcome = (data.get("outcome") or "").strip().lower()
    notes = (data.get("notes") or "").strip()

    if outcome not in VALID_INTERVIEW_OUTCOMES:
        return jsonify({"error": f"outcome must be one of {sorted(VALID_INTERVIEW_OUTCOMES)}"}), 400

    report_doc = db["reports"].find_one({"session_id": session_id})
    if not report_doc:
        return jsonify({"error": "No completed report found for this session"}), 404

    recruiter_id = str(session["user_id"])
    human_outcome = {
        "outcome": outcome,
        "notes": notes,
        "recorded_by": recruiter_id,
        "recorded_at": datetime.datetime.utcnow().isoformat() + "Z",
    }

    db["reports"].update_one(
        {"session_id": session_id},
        {"$set": {"report.human_outcome": human_outcome}}
    )
    log_audit("INTERVIEW_OUTCOME_RECORDED", user_id=recruiter_id, session_id=session_id)

    return jsonify({"success": True, "human_outcome": human_outcome})


@app.route("/api/recruiter/outcome-model/status", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_outcome_model_status():
    """
    Honest status check for the "train the data" request: how many real,
    recruiter-recorded outcome labels exist right now, and whether that's
    enough to train anything on. See modules/outcome_model.py -- this never
    fabricates a trained model, only reports the real count.
    """
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
    return jsonify(outcome_model.train_outcome_model(db))


@app.route("/api/recruiter/candidates/<candidate_id>", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_get_candidate_profile(candidate_id):
    if db is None or users_col is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    c = users_col.find_one({"_id": ObjectId(candidate_id)})
    if not c:
        return jsonify({"error": "Candidate not found"}), 404
        
    profile = db["candidate_profiles"].find_one({"user_id": candidate_id})
    reports = list(db["reports"].find({"user_id": candidate_id, "status": "completed"}).sort("created_at", -1))
    
    history_list = []
    scores = []
    best_score = 0
    avg_score = 0
    integrity_history = []
    
    for r in reports:
        rep = r.get("report", {})
        overall_score = rep.get("scores", {}).get("readiness_index", 0)
        scores.append(overall_score)
        
        integrity = rep.get("integrity", {})
        tab_switches = integrity.get("tab_switches", 0)
        camera_exits = integrity.get("camera_exits", 0)
        total_violations = tab_switches + camera_exits
        
        integrity_status = "Normal"
        if total_violations >= 5:
            integrity_status = "High Risk"
        elif total_violations > 0:
            integrity_status = "Warning"
            
        history_list.append({
            "session_id": r.get("session_id"),
            "interview_title": rep.get("job_role", "Diagnostic Interview"),
            "date": rep.get("date", ""),
            "score": overall_score,
            "duration": rep.get("duration", 30),
            "integrity_status": integrity_status,
            "is_practice": rep.get("is_practice", False),
            # Recruiter-recorded hiring decision, if one has been set yet --
            # see /api/recruiter/interviews/<session_id>/outcome. None for
            # every existing report until a recruiter records one.
            "human_outcome": rep.get("human_outcome")
        })
        
        integrity_history.append({
            "session_id": r.get("session_id"),
            "date": rep.get("date", ""),
            "tab_switches": tab_switches,
            "camera_exits": camera_exits,
            "window_movement": integrity.get("window_movements", 0),
            "camera_available": integrity.get("camera_available", True),
            "microphone_available": integrity.get("microphone_available", True),
            "termination_reason": integrity.get("termination_reason", "Completed normally")
        })
        
    if scores:
        best_score = max(scores)
        avg_score = int(sum(scores)/len(scores))
        
    skill_progression = {}
    if profile and profile.get("skills"):
        for skill, sdata in profile["skills"].items():
            skill_progression[skill] = {
                "score": sdata.get("score", 0),
                "depth": sdata.get("depth", "Basic"),
                "consistency": sdata.get("consistency", "High"),
                "confidence": sdata.get("confidence", 0)
            }
            
    payload = {
        "candidate": {
            "id": str(c["_id"]),
            "email": c.get("email"),
            "name": c.get("name", "Candidate"),
            "created_at": c.get("created_at").isoformat() if isinstance(c.get("created_at"), datetime.datetime) else str(c.get("created_at"))
        },
        "skills": list(skill_progression.keys()),
        "weak_areas": profile.get("weak_areas", []) if profile else [],
        "strong_areas": profile.get("strong_areas", []) if profile else [],
        "best_score": best_score,
        "avg_score": avg_score,
        "history": history_list,
        "integrity_history": integrity_history,
        "skill_progression": skill_progression
    }
    
    log_audit("CANDIDATE_VIEWED", user_id=str(session["user_id"]), session_id=candidate_id)
    return jsonify(clean_json(payload))


# ── CANDIDATE COMPARISON ──────────────────────────────────────────────────────

@app.route("/api/recruiter/comparison", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_compare_candidates():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    session_ids = request.args.get("session_ids", "").split(",")
    session_ids = [sid.strip() for sid in session_ids if sid.strip()]
    
    if not session_ids:
        return jsonify({"error": "No session_ids provided for comparison"}), 400
        
    reports = list(db["reports"].find({"session_id": {"$in": session_ids}, "status": "completed"}))
    
    comparison_data = []
    for r in reports:
        rep = r.get("report", {})
        integrity = rep.get("integrity", {})
        
        u_id_str = rep.get("user_id")
        u_doc = None
        u_email = "anonymous"
        if u_id_str and u_id_str != "anonymous":
            try:
                u_doc = db["users"].find_one({"_id": ObjectId(u_id_str)})
                if u_doc:
                    u_email = u_doc.get("email", "anonymous")
            except Exception:
                pass
            if not u_doc:
                u_doc = db["users"].find_one({"email": u_id_str})
                if u_doc:
                    u_email = u_doc.get("email", "anonymous")
        c_name = u_doc.get("name", "Candidate") if u_doc else "Candidate"
        
        # Calculate dimension averages dynamically
        answers = rep.get("answers", [])
        techs = [a.get("evaluation", {}).get("technical_correctness", 50) for a in answers if a.get("evaluation", {}).get("technical_correctness") is not None]
        relevances = [a.get("evaluation", {}).get("relevance", 50) for a in answers if a.get("evaluation", {}).get("relevance") is not None]
        depths = [a.get("evaluation", {}).get("depth", 50) for a in answers if a.get("evaluation", {}).get("depth") is not None]
        clarities = [a.get("evaluation", {}).get("clarity", 50) for a in answers if a.get("evaluation", {}).get("clarity") is not None]
        completenesses = [a.get("evaluation", {}).get("completeness", 50) for a in answers if a.get("evaluation", {}).get("completeness") is not None]
        prob_solvings = [a.get("evaluation", {}).get("problem_solving", 50) for a in answers if a.get("evaluation", {}).get("problem_solving") is not None]
        
        avg_tech = int(sum(techs)/len(techs)) if techs else rep.get("scores", {}).get("technical", 50)
        avg_relevance = int(sum(relevances)/len(relevances)) if relevances else 50
        avg_depth = int(sum(depths)/len(depths)) if depths else 50
        avg_clarity = int(sum(clarities)/len(clarities)) if clarities else 50
        avg_completeness = int(sum(completenesses)/len(completenesses)) if completenesses else 50
        avg_prob_solving = int(sum(prob_solvings)/len(prob_solvings)) if prob_solvings else 50
        
        comparison_data.append({
            "session_id": r.get("session_id"),
            "candidate_name": c_name,
            "candidate_email": u_email,
            "overall_score": rep.get("scores", {}).get("readiness_index", 0),
            "technical": avg_tech,
            "relevance": avg_relevance,
            "depth": avg_depth,
            "clarity": avg_clarity,
            "problem_solving": avg_prob_solving,
            "communication": rep.get("scores", {}).get("confidence", 50),
            "completeness": avg_completeness,
            "skills": rep.get("skill_scores", {}),
            "duration": rep.get("duration", 30),
            "integrity_violations": integrity.get("tab_switches", 0) + integrity.get("camera_exits", 0)
        })
        
    log_audit("CANDIDATE_COMPARISON_PERFORMED", user_id=str(session["user_id"]))
    return jsonify(clean_json(comparison_data))


# ── AUDIT LOG ACCESS ─────────────────────────────────────────────────────────

@app.route("/api/recruiter/audit", methods=["GET"])
@role_required(["recruiter", "admin"])
def recruiter_get_audit_logs():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
        
    recruiter_id = str(session["user_id"])
    role = session.get("role")
    
    query = {}
    if role != "admin":
        query["user_id"] = recruiter_id
        
    logs = list(db["audit_logs"].find(query).sort("timestamp", -1).limit(100))
    for l in logs:
        l["_id"] = str(l["_id"])
        
@app.route("/download-presentation-pdf", methods=["GET"])
def download_presentation_pdf():
    pdf_path = os.path.abspath(os.path.join(base_dir, "..", "InterviewIQ_Presentation_Guide.pdf"))
    if os.path.exists(pdf_path):
        return send_from_directory(os.path.dirname(pdf_path), os.path.basename(pdf_path), as_attachment=True)
    return jsonify({"error": "PDF not found"}), 404


# ── RUN ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  InterviewIQ — AI Interview Intelligence System")
    print("=" * 55)
    print("  Open in browser: http://192.168.1.6:5000")
    print("  Health check   : http://192.168.1.6:5000/health")
    print("=" * 55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
