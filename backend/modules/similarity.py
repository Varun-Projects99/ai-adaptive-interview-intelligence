"""
Text Similarity Utilities
==========================
Pure, dependency-free helpers used to detect near-duplicate interview
questions so the same (or a paraphrased) question is not asked twice to
the same candidate.

Algorithm: Jaccard similarity over a stemmed, stop-word-filtered token set.
This is a classical, explainable information-retrieval technique — NOT a
machine-learning model. There is nothing "trained" here.

Previously this logic lived only inside adaptive_engine.py. It is factored
out here so both the adaptive engine (per-question repetition checks) and
the dataset-driven question bank (bulk pool de-duplication) share a single
implementation instead of two copies drifting apart.
"""

import re

FILLER_WORDS = {
    "what", "is", "the", "difference", "between", "a", "an", "and", "in",
    "of", "to", "for", "with", "on", "describe", "tell", "me", "about",
    "write", "code", "use", "using", "why", "does", "can", "you", "show",
    "give", "example", "concept", "how", "are", "from", "do", "does",
    "did", "explain", "different", "would", "your", "we", "us", "our",
    "they", "them", "he", "she", "it", "this", "that", "these", "those"
}


def stem_word(word: str) -> str:
    """Simple suffix stemmer to normalize plurals by removing a trailing 's'."""
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def normalize_text(text: str) -> set:
    """Tokenize, lowercase, strip punctuation, drop filler words, and stem."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = text.split()
    return {stem_word(w) for w in words if w not in FILLER_WORDS}


def jaccard_similarity(q1: str, q2: str) -> float:
    """Jaccard similarity of the normalized token sets of two questions."""
    w1 = normalize_text(q1)
    w2 = normalize_text(q2)
    if not w1 or not w2:
        return 0.0
    intersection = w1.intersection(w2)
    union = w1.union(w2)
    return len(intersection) / len(union) if union else 0.0


def are_questions_similar(q1: str, q2: str, threshold: float = 0.55) -> bool:
    """True if two questions are near-duplicates by Jaccard similarity."""
    return jaccard_similarity(q1, q2) >= threshold


def is_duplicate_of_any(question: str, previous_questions, threshold: float = 0.55) -> bool:
    """True if `question` is a near-duplicate of any question in `previous_questions`."""
    for prev in previous_questions:
        if are_questions_similar(question, prev, threshold=threshold):
            return True
    return False
