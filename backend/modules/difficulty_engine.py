"""
Deterministic Adaptive Difficulty Engine
==========================================
IMPORTANT — read before citing this module in a report/presentation:

This is NOT a machine-learning model. It is a deterministic, rule-based
state machine. It was built this way deliberately: the local question
datasets (datasets/*.json) contain only {question, difficulty, skill} —
there is no candidate-performance / outcome label anywhere that a
supervised model (Decision Tree, Random Forest, Logistic Regression, etc.)
could be legitimately trained against. Fabricating training accuracy for
a model that was never actually fit to real labeled data would misrepresent
the system, so this module implements the explicitly-specified deterministic
alternative instead.

Score bands
-----------
    0-39   -> "weak"
    40-69  -> "average"
    70-84  -> "good"
    85-100 -> "excellent"

Difficulty transition rule (per-skill, 3 discrete levels: 1=easy, 2=medium,
3=hard):
    weak      -> one level EASIER  (floor at 1)
    average   -> SAME level
    good      -> one level HARDER  (cap at 3)
    excellent -> one level HARDER, EXCEPT starting from "easy" (1), where an
                 excellent answer jumps straight to "hard" (3). This is the
                 one place "good" and "excellent" are made to behave
                 differently, as required — with only 3 discrete levels,
                 "moderately harder" (good) and "harder" (excellent) are
                 otherwise indistinguishable except at the easy->? boundary,
                 where excellent performance justifies skipping the
                 intermediate step entirely.

This transition is a fixed lookup table, not a statistical estimate: the
same (band, current_difficulty) pair always produces the same output.
"""

WEAK_MAX = 39
AVERAGE_MAX = 69
GOOD_MAX = 84
# 85-100 = excellent

DIFFICULTY_NUM = {"easy": 1, "medium": 2, "hard": 3}
DIFFICULTY_LABEL = {1: "easy", 2: "medium", 3: "hard"}


def classify_score(score) -> str:
    """Map a 0-100 answer score to a performance band."""
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 50.0
    score = max(0.0, min(100.0, score))

    if score <= WEAK_MAX:
        return "weak"
    if score <= AVERAGE_MAX:
        return "average"
    if score <= GOOD_MAX:
        return "good"
    return "excellent"


def next_difficulty(current_difficulty, band: str) -> int:
    """
    Deterministic difficulty transition. `current_difficulty` may be an int
    (1-3) or a label ("easy"/"medium"/"hard"). Returns an int 1-3.
    """
    if isinstance(current_difficulty, str):
        current = DIFFICULTY_NUM.get(current_difficulty.lower(), 2)
    else:
        current = int(current_difficulty) if current_difficulty in (1, 2, 3) else 2

    if band == "weak":
        return max(1, current - 1)
    if band == "average":
        return current
    if band == "good":
        return min(3, current + 1)
    if band == "excellent":
        if current == 1:
            return 3  # easy -> hard jump on an excellent answer
        return min(3, current + 1)
    return current  # unknown band -> no change, never a random guess


def next_difficulty_label(current_difficulty, score) -> str:
    band = classify_score(score)
    return DIFFICULTY_LABEL[next_difficulty(current_difficulty, band)]


# ---------------------------------------------------------------------------
# Per-skill performance tracking
# ---------------------------------------------------------------------------
# Matches the schema requested for skill-aware adaptation:
#   {
#     "Python": {
#         "questions_answered": 5,
#         "average_score": 82,
#         "current_difficulty": 3,
#         "recent_scores": [70, 75, 82, 90, 88]
#     },
#     ...
#   }

RECENT_WINDOW = 3  # how many of the most recent scores drive the next-difficulty decision


def init_skill_performance(starting_difficulty="easy") -> dict:
    return {
        "questions_answered": 0,
        "average_score": 0,
        "current_difficulty": DIFFICULTY_NUM.get(starting_difficulty, 1),
        "recent_scores": [],
    }


def update_skill_performance(perf: dict, score) -> dict:
    """
    Update one skill's performance entry with a new answer score and
    deterministically recompute its next current_difficulty. Mutates and
    returns `perf`.
    """
    if perf is None:
        perf = init_skill_performance()

    try:
        score = int(round(float(score)))
    except (TypeError, ValueError):
        score = 50
    score = max(0, min(100, score))

    perf["questions_answered"] = perf.get("questions_answered", 0) + 1
    recent = perf.get("recent_scores", [])
    recent.append(score)
    perf["recent_scores"] = recent[-10:]  # keep a bounded history

    all_time_count = perf["questions_answered"]
    prev_avg = perf.get("average_score", 0)
    # Running average across the whole skill history (not just the window)
    perf["average_score"] = int(round(
        ((prev_avg * (all_time_count - 1)) + score) / all_time_count
    ))

    # The NEXT difficulty is driven by recent performance (last RECENT_WINDOW
    # scores), not the lifetime average, so the candidate can recover from
    # (or lose) momentum within a single skill instead of being permanently
    # anchored to their very first answer.
    window = recent[-RECENT_WINDOW:]
    window_avg = sum(window) / len(window)
    band = classify_score(window_avg)

    current = perf.get("current_difficulty", 1)
    perf["current_difficulty"] = next_difficulty(current, band)
    perf["last_band"] = band  # exposed for transparent, explainable logging

    return perf


def recommend_difficulty_label(perf: dict) -> str:
    """The dataset-lookup-ready difficulty label ("easy"/"medium"/"hard")
    this skill's performance entry currently recommends."""
    if not perf:
        return "easy"
    return DIFFICULTY_LABEL.get(perf.get("current_difficulty", 1), "easy")


def initial_difficulty_from_score(avg_score) -> str:
    """
    Used to seed the STARTING difficulty of a practice / re-interview
    session from a candidate's past average score on the target skill(s),
    using the exact same score-band table as in-session adaptation (so the
    whole system uses one difficulty rule, not several inconsistent ones).
    """
    band = classify_score(avg_score)
    # A brand-new session should start at a sensible level for that band,
    # not jump immediately to hard on a single excellent historical score.
    seed = {"weak": "easy", "average": "easy", "good": "medium", "excellent": "hard"}
    return seed[band]
