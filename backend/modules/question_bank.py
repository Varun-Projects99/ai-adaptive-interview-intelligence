"""
Dataset-Driven Question Bank (PRIMARY question source)
========================================================
Loads every dataset in datasets/*.json exactly once, normalizes every
record into one common internal schema, and exposes retrieval functions
that the rest of the app uses as the FIRST source of interview questions.

The LLM (Groq / Anthropic, wired in modules/question_engine.py and
modules/adaptive_engine.py) is only ever consulted when this module reports
that it cannot satisfy a request — see `select_question()` /
`has_sufficient_question()` below and their callers.

Normalized question schema
---------------------------
    {
        "question":         str,
        "skill":             str,               # canonical dataset skill
        "topic":             str | None,         # not present in source data (see NOTE)
        "difficulty":         int,                # 1=easy, 2=medium, 3=hard
        "difficulty_label":   "easy"|"medium"|"hard",
        "source":             "dataset"
    }

NOTE on metadata: every record in datasets/*.json was inspected and
contains exactly three fields — `question`, `difficulty`, `skill`. There is
no `topic` field anywhere in the source data, so `topic` is populated with
the skill name itself (the closest honest substitute) rather than invented.
There is no per-question `id`, so a stable id is derived from the skill +
index at load time purely for internal bookkeeping (not claimed as source
metadata).

Difficulty fallback (documented, not statistically inferred): in the actual
datasets, difficulty is present on 100% of the 3,400 records, so this path
is not exercised today. If a future dataset entry is missing `difficulty`,
it is deterministically assigned "medium" (2) — a neutral default, chosen
because it is the least likely to mis-place a question at either extreme.
This is a fixed rule, not a learned/trained inference.
"""

import os
import json
import random

from modules.skill_mapper import CANONICAL_SKILLS
from modules.similarity import is_duplicate_of_any

DIFFICULTY_NUM = {"easy": 1, "medium": 2, "hard": 3}
DIFFICULTY_LABEL = {1: "easy", 2: "medium", 3: "hard"}
DEFAULT_DIFFICULTY_LABEL = "medium"  # documented fallback, see module docstring

# Hardcoded last-resort questions used only if the datasets are literally
# unavailable/unreadable at runtime (e.g. deployment misconfiguration).
# This mirrors the previous safety-net behaviour so nothing regresses.
_GLOBAL_SAFETY_QUESTIONS = [
    {"question": "Explain your understanding of scalability in system engineering.",
     "skill": "General", "topic": "General", "difficulty": 2,
     "difficulty_label": "medium", "source": "dataset_unavailable_fallback"},
    {"question": "How do you design secure REST APIs?",
     "skill": "General", "topic": "General", "difficulty": 2,
     "difficulty_label": "medium", "source": "dataset_unavailable_fallback"},
    {"question": "Explain the time and space complexity of common sorting algorithms.",
     "skill": "DSA", "topic": "DSA", "difficulty": 2,
     "difficulty_label": "medium", "source": "dataset_unavailable_fallback"},
]


def _resolve_datasets_dir():
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(modules_dir)
    workspace_dir = os.path.dirname(backend_dir)
    datasets_dir = os.path.join(workspace_dir, "datasets")
    if not os.path.exists(datasets_dir):
        datasets_dir = os.path.join(backend_dir, "datasets")
    return datasets_dir


def _normalize_record(raw: dict, expected_skill: str, index: int) -> dict:
    question_text = raw.get("question", "").strip()
    skill = (raw.get("skill") or expected_skill).strip()

    raw_difficulty = raw.get("difficulty")
    if raw_difficulty:
        label = str(raw_difficulty).strip().lower()
        if label not in DIFFICULTY_NUM:
            label = DEFAULT_DIFFICULTY_LABEL  # unrecognized value, documented fallback
    else:
        label = DEFAULT_DIFFICULTY_LABEL  # missing value, documented fallback

    return {
        "id": f"{skill}:{index}",
        "question": question_text,
        "skill": skill,
        "topic": skill,           # no topic field exists in source data
        "difficulty": DIFFICULTY_NUM[label],
        "difficulty_label": label,
        "source": "dataset",
    }


class _QuestionBank:
    """Loads and holds the normalized in-memory question bank (singleton)."""

    def __init__(self):
        self._by_skill_difficulty = {}   # {skill: {"easy": [...], "medium": [...], "hard": [...]}}
        self._all = []
        self._load_errors = {}
        self._loaded = False

    def load(self, force=False):
        if self._loaded and not force:
            return
        self._by_skill_difficulty = {}
        self._all = []
        self._load_errors = {}

        datasets_dir = _resolve_datasets_dir()
        for skill, filename in CANONICAL_SKILLS.items():
            path = os.path.join(datasets_dir, filename)
            bucket = {"easy": [], "medium": [], "hard": []}
            self._by_skill_difficulty[skill] = bucket
            if not os.path.exists(path):
                self._load_errors[skill] = f"dataset file not found: {path}"
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                for i, raw in enumerate(raw_list):
                    if not isinstance(raw, dict) or not raw.get("question"):
                        continue
                    norm = _normalize_record(raw, skill, i)
                    bucket[norm["difficulty_label"]].append(norm)
                    self._all.append(norm)
            except Exception as e:
                self._load_errors[skill] = f"failed to load {filename}: {e}"

        self._loaded = True
        total = len(self._all)
        print(f"[QuestionBank] Loaded {total} normalized questions across "
              f"{len(CANONICAL_SKILLS)} skills from {datasets_dir}")
        if self._load_errors:
            print(f"[QuestionBank] Load warnings: {self._load_errors}")

    def stats(self):
        self.load()
        out = {}
        for skill, buckets in self._by_skill_difficulty.items():
            out[skill] = {label: len(qs) for label, qs in buckets.items()}
        return out

    def candidates(self, skill: str, difficulty_label: str):
        self.load()
        return self._by_skill_difficulty.get(skill, {}).get(difficulty_label, [])

    def all_for_skill(self, skill: str):
        self.load()
        b = self._by_skill_difficulty.get(skill, {})
        return b.get("easy", []) + b.get("medium", []) + b.get("hard", [])


_bank = _QuestionBank()


def safety_question():
    """Last-resort question when the dataset has nothing at all for a
    skill (e.g. an unmapped skill) -- kept so the interview flow never
    dead-ends even in a misconfigured deployment."""
    return random.choice(_GLOBAL_SAFETY_QUESTIONS)["question"]


def dataset_stats():
    """Per-skill, per-difficulty question counts actually available right now."""
    return _bank.stats()


def _as_difficulty_label(difficulty):
    if isinstance(difficulty, int):
        return DIFFICULTY_LABEL.get(difficulty, DEFAULT_DIFFICULTY_LABEL)
    label = str(difficulty).strip().lower()
    return label if label in DIFFICULTY_NUM else DEFAULT_DIFFICULTY_LABEL


def select_question(skill: str, difficulty, exclude=None, allow_relaxation=True):
    """
    PRIMARY question retrieval. Returns one normalized question dict, or
    None if the dataset genuinely cannot satisfy the request (which should
    trigger the LLM fallback in the caller).

    Relaxation order (only engaged if allow_relaxation=True), each step
    logged so it is always clear which tier actually served the question:
      1. Exact skill + exact difficulty, not a near-duplicate of `exclude`.
      2. Same skill, any difficulty, not a near-duplicate of `exclude`.
      3. Same skill, any difficulty, ignoring repetition (last resort before LLM).
    """
    exclude = exclude or []
    difficulty_label = _as_difficulty_label(difficulty)

    if skill not in CANONICAL_SKILLS:
        return None  # no dataset for this skill at all -> caller should use LLM

    # Tier 1: exact skill + exact difficulty, fresh
    pool = list(_bank.candidates(skill, difficulty_label))
    random.shuffle(pool)
    for q in pool:
        if not is_duplicate_of_any(q["question"], exclude):
            return dict(q)

    if not allow_relaxation:
        return None

    # Tier 2: same skill, any difficulty, fresh
    all_skill_qs = list(_bank.all_for_skill(skill))
    random.shuffle(all_skill_qs)
    for q in all_skill_qs:
        if not is_duplicate_of_any(q["question"], exclude):
            print(f"[QuestionBank] Relaxed difficulty for {skill} "
                  f"(wanted {difficulty_label}, dataset exhausted at that level)")
            return dict(q)

    # Tier 3: same skill, any difficulty, accept repetition risk rather than
    # ask nothing (better than silently failing the interview flow)
    if all_skill_qs:
        print(f"[QuestionBank] Repetition-unavoidable fallback for {skill} "
              f"(candidate has seen all available {skill} questions)")
        return dict(random.choice(all_skill_qs))

    return None


def has_sufficient_question(skill: str, difficulty, exclude=None) -> bool:
    """True if select_question() would currently be able to return something
    for this skill/difficulty without relaxing skill (still allows
    difficulty relaxation, matching the real retrieval behaviour)."""
    return select_question(skill, difficulty, exclude=exclude, allow_relaxation=True) is not None


def pool_for_skills(canonical_skills, target_total=24, per_difficulty=8):
    """
    Build a skill-balanced initial question pool primarily from the dataset.
    Returns (pool, shortfall) where `shortfall` is
    {"easy": n_missing, "medium": n_missing, "hard": n_missing} describing
    how many additional questions per difficulty band could NOT be filled
    from the dataset (for the caller to fill via LLM fallback, per the
    "dataset primary, LLM only for genuine gaps" rule).
    """
    if not canonical_skills:
        canonical_skills = ["Aptitude", "HR", "DSA"]

    pool = []
    used_fingerprints = []
    shortfall = {"easy": 0, "medium": 0, "hard": 0}

    for diff_label in ["easy", "medium", "hard"]:
        by_skill = {}
        for skill in canonical_skills:
            qs = [q for q in _bank.candidates(skill, diff_label)]
            random.shuffle(qs)
            by_skill[skill] = qs

        selected = []
        skill_cycle = list(canonical_skills)
        while len(selected) < per_difficulty and skill_cycle:
            for skill in list(skill_cycle):
                bucket = by_skill.get(skill, [])
                picked = None
                while bucket:
                    cand = bucket.pop()
                    if not is_duplicate_of_any(cand["question"], used_fingerprints):
                        picked = cand
                        break
                if picked:
                    selected.append(picked)
                    used_fingerprints.append(picked["question"])
                    if len(selected) == per_difficulty:
                        break
                else:
                    skill_cycle.remove(skill)

        if len(selected) < per_difficulty:
            shortfall[diff_label] = per_difficulty - len(selected)

        pool.extend(selected)

    random.shuffle(pool)
    return pool, shortfall
