"""
InterviewIQ Settings
=====================
Backend logic for the candidate Settings page (/settings, /api/settings/*).

Design notes
------------
- No new MongoDB collection is created. Preferences live directly on the
  existing `users` document (see app.py's user_doc shape in api_register()/
  google_callback()) under a `preferences` sub-object, per this project's
  own rule to extend an existing user document rather than add a collection.
- Every function here takes an already-authenticated `user_id`/`user_doc`
  that the Flask route in app.py derived from session["user_id"] -- this
  module never trusts a client-sent identifier, mirroring the exact pattern
  modules/ai_assistant.py's docstring documents and uses.
- "Preferred difficulty" and "default interview length" are genuinely wired
  into self-practice interview generation (see app.py's
  generate_interview_questions()) as a STARTING seed only -- the adaptive
  difficulty engine (modules/adaptive_engine.py) still runs unmodified after
  the first question, and "adaptive" reproduces today's existing default
  exactly. Recruiter-assigned interviews (which already carry their own
  explicit difficulty/num_questions from the interview template, set in
  start_session()) are never touched by this -- app.py guards the call site
  on `not sess.get("invitation_token")`.
"""
import os
import re

# ---------------------------------------------------------------------------
# Preferences: allowed values + defaults + how they seed a self-practice
# session. These are PREFERENCES, not replacements for the adaptive engine.
# ---------------------------------------------------------------------------
ALLOWED_INTERVIEW_LENGTHS = ("short", "standard", "extended")
ALLOWED_DIFFICULTIES = ("easy", "adaptive", "hard")
ALLOWED_THEMES = ("dark", "light")

DEFAULT_PREFERENCES = {
    "interview_length": "standard",
    "preferred_difficulty": "adaptive",
    "theme": "dark",
}

# Self-practice question count per length preference. Recruiter-assigned
# interviews are unaffected (see call-site guard in app.py).
LENGTH_TO_QUESTION_COUNT = {
    "short": 5,
    "standard": 10,
    "extended": 15,
}

# Starting difficulty seed per preference. "adaptive" reproduces exactly
# today's existing hardcoded default ("easy" as a start, then the adaptive
# engine takes over) -- choosing "Adaptive" changes nothing about behavior.
DIFFICULTY_TO_SEED = {
    "easy": "easy",
    "adaptive": "easy",
    "hard": "hard",
}


def get_preferences(user_doc):
    """Merge a user's stored preferences (if any) with defaults. Never
    raises -- a missing/malformed `preferences` field just falls back to
    DEFAULT_PREFERENCES so a corrupt or absent field can't break the page
    or interview start."""
    stored = {}
    if user_doc and isinstance(user_doc.get("preferences"), dict):
        stored = user_doc["preferences"]
    merged = dict(DEFAULT_PREFERENCES)
    v = stored.get("interview_length")
    if v in ALLOWED_INTERVIEW_LENGTHS:
        merged["interview_length"] = v
    v = stored.get("preferred_difficulty")
    if v in ALLOWED_DIFFICULTIES:
        merged["preferred_difficulty"] = v
    v = stored.get("theme")
    if v in ALLOWED_THEMES:
        merged["theme"] = v
    return merged


def validate_preferences_update(data):
    """Returns (clean_dict, error_message); error_message is None on
    success. Only ever returns keys that passed validation -- the caller
    should $set exactly `preferences.<key>` for each key in clean_dict."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."
    clean = {}
    if "interview_length" in data:
        v = data.get("interview_length")
        if v not in ALLOWED_INTERVIEW_LENGTHS:
            return None, f"interview_length must be one of {ALLOWED_INTERVIEW_LENGTHS}"
        clean["interview_length"] = v
    if "preferred_difficulty" in data:
        v = data.get("preferred_difficulty")
        if v not in ALLOWED_DIFFICULTIES:
            return None, f"preferred_difficulty must be one of {ALLOWED_DIFFICULTIES}"
        clean["preferred_difficulty"] = v
    if "theme" in data:
        v = data.get("theme")
        if v not in ALLOWED_THEMES:
            return None, f"theme must be one of {ALLOWED_THEMES}"
        clean["theme"] = v
    if not clean:
        return None, "No recognized preference fields were provided."
    return clean, None


_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{0,79}$")


def validate_profile_update(data):
    """Only `name` is backend-supported for editing today. Email is the
    login identifier (used for lookup and, for Google accounts, tied to
    google_id) and is intentionally read-only here; password change is a
    separate, not-yet-requested feature. Returns (clean_dict, error)."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."
    if "name" not in data:
        return None, "No recognized profile fields were provided."
    name = str(data.get("name") or "").strip()
    if not name:
        return None, "Name cannot be empty."
    if len(name) > 80:
        return None, "Name must be 80 characters or fewer."
    if not _NAME_RE.match(name):
        return None, "Name may only contain letters, spaces, apostrophes, periods, and hyphens."
    return {"name": name}, None


def get_ai_status():
    """Real, checkable status for the Settings 'AI/System Status' section.
    Reuses the exact same env-var configuration modules/ai_assistant.py's
    call_ai_provider() itself checks, so this can never claim "Available"
    while the assistant is actually misconfigured. Never returns, logs, or
    includes any API key material -- only booleans/labels."""
    try:
        from modules import ai_assistant as aa
        groq_models = list(getattr(aa, "_GROQ_MODEL_CANDIDATES", []))
    except Exception:
        return {
            "assistant_status": "unavailable",
            "assistant_detail": "The AI Assistant module failed to load.",
            "primary_provider": None,
            "groq_models_configured": [],
        }

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    anthropic_ready = bool(anthropic_key) and "your_anthropic_api_key_here" not in anthropic_key
    groq_key = os.environ.get("GROQ_API_KEY", "")
    groq_ready = bool(groq_key)

    if anthropic_ready:
        primary = "anthropic"
    elif groq_ready:
        primary = "groq"
    else:
        primary = None

    if primary:
        status = "available"
        detail = f"AI Assistant is configured (primary provider: {primary})."
    else:
        status = "configuration_required"
        detail = "No AI provider API key is configured -- the AI Assistant cannot respond."

    return {
        "assistant_status": status,
        "assistant_detail": detail,
        "primary_provider": primary,
        "groq_models_configured": groq_models,
    }


# ---------------------------------------------------------------------------
# Privacy & Data -- what InterviewIQ actually stores, audited against the
# real MongoDB collections this codebase writes to. Kept as plain data here
# so the Settings page shows the same honest list a future caller would,
# rather than two independently-maintained copies drifting apart.
# ---------------------------------------------------------------------------
DATA_CATEGORIES = [
    {"key": "profile", "label": "Profile information",
     "detail": "Name, email, role, and login method."},
    {"key": "resume", "label": "Resume data",
     "detail": "Uploaded resume text and extracted skills, used to generate your interview questions."},
    {"key": "interviews", "label": "Interview sessions",
     "detail": "Question sets, your answers, and per-answer scores for interviews you've taken."},
    {"key": "reports", "label": "Interview reports",
     "detail": "Generated performance reports and interview history."},
    {"key": "recordings", "label": "Recordings",
     "detail": "Session recordings saved during proctored interviews, where enabled."},
    {"key": "integrity_events", "label": "Integrity monitoring events",
     "detail": "Logged events such as tab switches or camera exits during proctored interviews."},
    {"key": "ai_assistant", "label": "AI Assistant conversations",
     "detail": "Your chat history with the AI Assistant, used only to answer your own questions."},
]
