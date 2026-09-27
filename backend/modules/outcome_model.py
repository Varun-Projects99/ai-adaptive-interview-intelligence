"""
Outcome model — infrastructure only. No model is trained or fitted here.

CONTEXT: every dataset this project ships with (datasets/*.json) is a plain
{question, difficulty, skill} bank used to seed the adaptive interview
question pool. None of it has ever contained an outcome label (did this
candidate get hired?), so there has never been anything a real supervised
model could actually learn from.

/api/recruiter/interviews/<session_id>/outcome (see app.py) now lets a
recruiter record a genuine hiring decision (hired/rejected/advanced/
no_decision) against a completed interview report, stored at
report.human_outcome in the `reports` collection. That is real, human-
provided label data starting to accumulate -- but a handful of labels is not
a trainable dataset, and claiming otherwise would violate this project's own
rule against pretending a model is "trained" when it isn't.

This module's only job is to honestly answer "do we have enough real
outcome data yet to train something meaningful on" and, if not, say so
explicitly instead of returning a fabricated result. Nothing calls
train_outcome_model() anywhere yet -- it exists so that decision has a
single, explicit place to live once there IS enough data, rather than
someone being tempted to bolt on a fake "trained" model under time
pressure.
"""

# Deliberately conservative. Below this many labeled examples, any model
# "trained" on the data would just be overfitting noise -- not a claim this
# project is willing to make. Revisit this number (with real justification)
# once outcome logging has been running for a while.
MIN_SAMPLES = 50


def count_labeled_outcomes(db):
    """
    Returns how many completed interview reports currently have a recruiter-
    recorded human_outcome. `db` is the same pymongo database handle app.py
    already uses everywhere else (db is None -> Mongo not configured).
    """
    if db is None:
        return 0
    return db["reports"].count_documents({"report.human_outcome": {"$exists": True}})


def train_outcome_model(db):
    """
    Guard function: checks whether there is enough genuinely labeled outcome
    data (see count_labeled_outcomes) to train a real supervised model, and
    ONLY reports that decision -- it never fits or fabricates a model itself.
    Wire this up to a real training pipeline (e.g. scikit-learn on the
    recorded technical/confidence/emotion scores vs. human_outcome) once
    trainable=True and MIN_SAMPLES has been validated against real data.
    """
    n = count_labeled_outcomes(db)
    return {
        "trainable": n >= MIN_SAMPLES,
        "labeled_samples": n,
        "min_samples_required": MIN_SAMPLES,
        "message": (
            f"{n} labeled outcome(s) recorded so far ({MIN_SAMPLES} needed). "
            "Not enough real data yet to train a model -- no model has been "
            "trained or fitted."
            if n < MIN_SAMPLES else
            f"{n} labeled outcomes available. Training infrastructure would "
            "need to be implemented here -- this guard only confirms enough "
            "data exists, it does not itself train anything."
        ),
    }
