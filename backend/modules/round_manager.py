"""
Multi-round interview flow (Technical -> HR by default, extensible).

IMPORTANT DESIGN NOTE: this module does NOT reimplement any adaptive/
difficulty logic. It composes the EXISTING, already-tested engine
(modules/adaptive_engine.py, modules/question_engine.py) into sequential
rounds within one continuous session. Each round runs through that exact
same, unmodified decision process (should_interview_finish /
select_next_topic / generate_adaptive_question) -- this module's only job is
to decide WHEN a round has run its course, snapshot its contribution for the
final report, and reconfigure the session's skill list + per-round adaptive
state for the next round.

session["answers"], session["technical_scores"], session["voice_scores"] and
session["emotion_timeline"] are always kept CUMULATIVE across the whole
session (never reset here) so the existing final report's whole-interview
averages (modules/evaluator.py) keep meaning exactly what they always meant
for a single-round session. Only the per-round SELECTION state (skills,
uncertainty, covered topics, strong/weak areas, skill_performance,
asked_questions, current question pool/index) is reset between rounds, and
should_interview_finish() is made round-relative via
session["round_started_at_answer_count"] (an additive, default-0 offset --
see the one-line change in modules/adaptive_engine.py). A session that never
calls init_rounds() (the default for every existing flow -- practice,
re-interview, HR-only, custom-skill testing) never sets any of these fields,
so its behavior is byte-for-byte unchanged.
"""

DEFAULT_ROUNDS = ["technical", "hr"]

ROUND_LABELS = {
    "technical": "Technical Round",
    "hr": "HR Round",
    "coding": "Coding Round",
}

# The HR round always targets this fixed skill, which is already a real
# dataset-backed skill (see datasets/, modules/skill_mapper.py,
# modules/question_bank.py) -- the exact same "HR" skill the pre-existing
# dashboard.html HR-interview button already passes to generate_questions().
HR_ROUND_SKILLS = ["HR"]


def is_multi_round(session):
    return bool(session.get("rounds"))


def init_rounds(session, rounds=None):
    """
    Opt-in only: call this once, right after the candidate's resume skills
    are known (see app.py's /api/questions/generate), when the candidate or
    recruiter explicitly asked for a multi-round interview. Sessions that
    never call this behave exactly as before.
    """
    rounds = [r for r in (rounds or DEFAULT_ROUNDS) if r in ROUND_LABELS]
    if not rounds:
        rounds = list(DEFAULT_ROUNDS)

    # Capture the original resume-detected skills before the first round's
    # skill-list assignment below can touch session["skills"] -- later
    # rounds need this to know what "technical" means.
    session["resume_skills"] = list(session.get("skills") or [])

    session["rounds"] = rounds
    session["current_round_index"] = 0
    session["round_history"] = []
    session["round_started_at_answer_count"] = len(session.get("answers", []))
    session["current_round_name"] = rounds[0]

    # Round 1 ("technical") uses the resume skills exactly as a single-round
    # session would -- this is a no-op change for the first round.
    session["skills"] = _skills_for_round(session, rounds[0])


def current_round_name(session):
    rounds = session.get("rounds") or []
    idx = session.get("current_round_index", 0)
    if not rounds or idx >= len(rounds):
        return None
    return rounds[idx]


def round_progress_label(session):
    rounds = session.get("rounds") or []
    if not rounds:
        return None
    idx = session.get("current_round_index", 0)
    name = current_round_name(session)
    if name is None:
        return None
    return f"Round {idx + 1} of {len(rounds)}: {ROUND_LABELS.get(name, name)}"


def _skills_for_round(session, round_name):
    if round_name == "hr":
        return list(HR_ROUND_SKILLS)
    if round_name == "coding":
        # The coding round is a link out to the existing standalone /coding
        # workspace (see app.py's /api/coding/* routes), not adaptive Q&A --
        # nothing to generate here.
        return []
    # "technical" (or any future round type) uses the candidate's actual
    # resume-detected skills, captured once in init_rounds().
    return list(session.get("resume_skills") or session.get("skills") or [])


def _snapshot_current_round(session):
    """Slice this round's contribution out of the CUMULATIVE answers list for
    the final report's per-round breakdown, without mutating the cumulative
    lists themselves (evaluator.py's whole-interview averages depend on
    those staying intact)."""
    start = session.get("round_started_at_answer_count", 0)
    answers = session.get("answers", [])
    round_answers = answers[start:]
    scores = [a.get("score") for a in round_answers if a.get("score") is not None]
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    name = current_round_name(session)

    return {
        "round": name,
        "label": ROUND_LABELS.get(name, name or "Round"),
        "questions_answered": len(round_answers),
        "avg_score": avg_score,
        "skill_scores": {
            s: session["skill_scores"][s]
            for s in session.get("skills", [])
            if s in session.get("skill_scores", {})
        },
    }


def advance_round(session):
    """
    Called when the current round's adaptive engine has decided it is done
    (get_next_question() returned None). Snapshots the finished round,
    advances to the next configured round if one remains, and resets only
    the per-round SELECTION state (see module docstring).

    Returns the new round's name if advanced, or None if that was the last
    configured round (the caller should finish the interview as normal).
    Safe to call on a non-multi-round session -- it just returns None.
    """
    if not is_multi_round(session):
        return None

    session.setdefault("round_history", []).append(_snapshot_current_round(session))

    session["current_round_index"] = session.get("current_round_index", 0) + 1
    next_round = current_round_name(session)
    if next_round is None:
        return None  # all configured rounds are complete -> real finish

    session["current_round_name"] = next_round
    session["round_started_at_answer_count"] = len(session.get("answers", []))

    # Reset per-round adaptive SELECTION state only -- answers/
    # technical_scores/voice_scores/emotion_timeline stay cumulative.
    session["skills"] = _skills_for_round(session, next_round)
    session["skill_scores"] = {}
    session["strong_areas"] = []
    session["weak_areas"] = []
    session["covered_topics"] = []
    session["uncertainty"] = {s: 100 for s in session["skills"]}
    session["asked_questions"] = []
    session["difficulty_history"] = []
    session["skill_performance"] = {}
    session["questions"] = []
    session["current_index"] = 0
    session["current_difficulty"] = "easy"

    return next_round


def finalize(session):
    """
    Call exactly once, at the moment the interview is genuinely ending
    (action == "finish"), so whichever round was still active gets snapshot
    into round_history too -- advance_round() above only snapshots the
    rounds *between* transitions, not the final one. Safe to call on a
    non-multi-round session (no-op).
    """
    if is_multi_round(session) and current_round_name(session) is not None:
        session.setdefault("round_history", []).append(_snapshot_current_round(session))
