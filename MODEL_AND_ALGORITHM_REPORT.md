# InterviewIQ — Model & Algorithm Report

This document lists **only** technologies, algorithms, and models that
actually exist in the source code as of this change, verified by direct
inspection (not by the README, not by intent). It is meant to be safe to
quote in a viva/presentation without overclaiming.

## Headline statement

**No component in this system is a machine-learning or deep-learning model
that was trained by this project.** Everything either:

- calls a pretrained third-party model over an API or library (a hosted
  LLM, a speech-recognition API, an OCR engine), or
- is a deterministic, rule-based algorithm written in this codebase
  (adaptive difficulty, topic selection, skill mapping, dataset retrieval,
  text similarity).

Section F explains, in detail, *why* no supervised ML model was trained for
question-difficulty prediction: the local datasets contain only
`{question, difficulty, skill}` and no candidate-performance/outcome label,
so there is no legitimate `(features → target)` pair to fit a Decision
Tree / Random Forest / Logistic Regression against. Building one anyway
would mean fabricating labels and fabricating an accuracy figure — both
explicitly disallowed.

---

## A. Machine Learning models

**None.** No supervised/unsupervised model is trained anywhere in this
codebase. `datasets/*.json` were inspected in full (3,400 records across 18
files) and contain no performance-outcome labels a model could be trained
against — see `backend/modules/difficulty_engine.py`'s module docstring for
the full reasoning. Question-difficulty adaptation is implemented as the
deterministic algorithm in section F instead.

## B. Deep Learning models

**None trained by this project.** `tensorflow` and `fer` are listed in
`requirements.txt` / `backend/requirements.txt` but are **never imported or
called anywhere in the codebase** (verified by grep across `backend/`) —
they are dead dependencies. The one real deep-learning model in the system
is EasyOCR, a third-party pretrained model used as-is; see section H (it is
listed there, not here, because it performs OCR, not a project-trained DL
task).

## C. NLP models

No separately fine-tuned or project-trained NLP model exists. All natural-
language capability (question generation, answer evaluation, translation,
coaching chat, resume assessment) comes from the hosted LLM APIs listed in
section D.

## D. AI / API models (pretrained, accessed over the network)

| # | Model | File(s) | Function(s) | Input | Output | Purpose |
|---|---|---|---|---|---|---|
| 1 | Groq-hosted `llama3-8b-8192` | `modules/question_engine.py` | `_generate_llm_questions_for_skills()` (LLM-fallback gap-fill only, see §F) | list of resume skills with no local dataset | JSON list of {question, difficulty, skill} | Fills a genuine dataset-coverage gap only |
| 2 | Groq-hosted `llama3-8b-8192` | `modules/adaptive_engine.py` | `generate_adaptive_question()` (LLM-fallback branch only) | target skill/difficulty, candidate history | one question string | Per-question fallback when the dataset can't serve the request |
| 3 | Groq-hosted `llama3-8b-8192` | `modules/evaluator.py` | `evaluate_and_transition()` (default path when no real `ANTHROPIC_API_KEY` set) | question, answer, conversation history | 7-dimension scored JSON evaluation | Answer scoring + next-action decision |
| 4 | Groq-hosted `llama3-8b-8192` | `modules/resume_parser.py` | `analyze_resume_data()` | extracted resume text | narrative ATS assessment JSON | Resume quality/career-path narrative (skills themselves come from the deterministic extractor, not the LLM — see §F) |
| 5 | Groq-hosted `llama3-8b-8192` | `backend/app.py` | `generate_roadmap_and_recommendations()`, `async_generate_report()`, `api_coach_chat()`, `api_review_code()` | weak skills / interview transcript / chat messages / submitted code | roadmap JSON / report narrative / chat reply / code review JSON | Learning roadmap, final report narrative, interview coach, code review |
| 6 | Anthropic `claude-3-5-sonnet-20240620` | `modules/evaluator.py` | `evaluate_answer()`, `evaluate_and_transition()` (used only if a real `ANTHROPIC_API_KEY` is configured) | question, answer | scored JSON evaluation | Alternate/legacy answer evaluator |
| 7 | Anthropic `claude-3-5-sonnet-20240620` | `modules/question_engine.py` | `translate_text()` (secondary fallback, after MyMemory) | English question text | translated text | Hindi/Kannada translation fallback |
| 8 | Google Web Speech API | `modules/voice_analyzer.py` | `_speech_rate()`, `_fillers()` (via `speech_recognition.Recognizer.recognize_google`) | recorded answer audio (wav) | transcript text | Speech-to-text for rate/filler analysis |
| 9 | MyMemory Translation API | `modules/question_engine.py` | `translate_text()` (primary path) | English question text | translated text | Hindi/Kannada translation |

## E. Computer Vision algorithms

| # | Algorithm | File | Function | Input | Output | Purpose |
|---|---|---|---|---|---|---|
| 1 | Haar Cascade Classifier (Viola–Jones), `haarcascade_frontalface_default.xml` | `modules/emotion_detector.py` | `analyze_emotion_frame()` | one webcam JPEG frame (base64) | bounding boxes of detected faces | Face detection: none / one / multiple faces |
| 2 | Haar Cascade Classifier, `haarcascade_eye.xml` | `modules/emotion_detector.py` | `analyze_emotion_frame()` | face region-of-interest | bounding boxes of detected eyes | Eyes-visible proxy (**not** true gaze/attention-direction tracking) |
| 3 | Mean-luminance thresholding | `modules/emotion_detector.py` | `analyze_emotion_frame()` | grayscale frame | brightness float | Low-light detection |
| 4 | Histogram equalization (`cv2.equalizeHist`) | `modules/emotion_detector.py` | `analyze_emotion_frame()` | grayscale frame | contrast-normalized frame | Pre-processing to make face detection more robust to lighting |

**Important caveat, repeated from the audit and still true**: despite the
file name and the `dominant_emotion`/`emotions` fields it returns,
**no emotion classification runs**. `dominant_emotion` is hardcoded to
`"neutral"` in every code path in `emotion_detector.py`. `EMOTION_MAP` /
`EMOTION_SCORE` exist in that file but are dead code, never called. This
change did not touch that module — it is documented here again so this
report stays accurate.

## F. Adaptive algorithms (deterministic — NOT machine learning)

| # | Algorithm | File | Function/class | Input | Output | Purpose |
|---|---|---|---|---|---|---|
| 1 | **Score-band difficulty transition** *(new)* | `modules/difficulty_engine.py` | `classify_score()`, `next_difficulty()` | answer score 0–100, current difficulty (1–3) | performance band (weak/average/good/excellent), next difficulty (1–3) | Deterministic per-answer difficulty adaptation. Fixed lookup table: weak→easier, average→same, good→+1 (capped), excellent→+1 or easy→hard jump |
| 2 | **Per-skill performance tracker** *(new)* | `modules/difficulty_engine.py` | `update_skill_performance()`, `recommend_difficulty_label()` | a skill's running score history | `{questions_answered, average_score, current_difficulty, recent_scores}` | Tracks each detected skill independently so difficulty adapts per-skill, not just globally |
| 3 | **Dataset-primary question retrieval, 3-tier relaxation** *(new)* | `modules/question_bank.py` | `select_question()` | skill, difficulty, list of already-asked questions | one normalized question or `None` | Primary question source: exact skill+difficulty → same skill any difficulty → last-resort repeat, before ever calling an LLM |
| 4 | **Skill-balanced pool construction** *(new)* | `modules/question_bank.py` | `pool_for_skills()` | list of canonical skills, target pool size | list of question dicts + shortfall report | Builds the initial ~24-question pool from the dataset, reporting exactly what it could not fill (drives the LLM gap-fill decision) |
| 5 | **Skill alias normalization** *(new)* | `modules/skill_mapper.py` | `normalize_skill()`, `map_resume_skills()` | a resume-detected skill string | canonical dataset skill or `None` | Explicit lookup table connecting resume vocabulary ("Python Programming", "ML", "Node.js", ...) to the 18 dataset-backed skills. Never guesses — an unmapped skill stays unmapped |
| 6 | Priority-ranked topic/difficulty selection | `modules/adaptive_engine.py` | `select_next_topic()` | per-skill coverage, uncertainty, strong/weak areas, (as of this change) the per-skill performance tracker | `(skill, difficulty, reason)` | Chooses which skill to ask about next and at what difficulty; now defers difficulty to item #1/#2 above once a skill has in-session data |
| 7 | Early-finish decision | `modules/adaptive_engine.py` | `should_interview_finish()` | number answered, per-skill uncertainty | boolean | Ends the interview once 10–30 question safety bounds and per-skill confidence criteria are met |
| 8 | Section-aware resume skill extraction | `modules/resume_parser.py` | `extract_skills_from_resume()`, `_extract_skills_from_section()` | raw resume text | list of skill strings | Finds skills under a detected "Skills" header first, then a regex/taxonomy pass, with exclusion lists — not blind keyword matching |
| 9 | Knowledge-depth classification | `modules/candidate_intelligence.py` | `calculate_knowledge_depth()` | per-difficulty score history for a skill | "Basic" / "Intermediate" / "Advanced" | Rule-based depth label from progressive-difficulty performance |
| 10 | Consistency scoring | `modules/candidate_intelligence.py` | `calculate_consistency()` | list of scores for a skill | "High" / "Medium" / "Low" | Uses population standard deviation (a statistics formula, not a trained model) banded into 3 levels |
| 11 | Weighted evidence-confidence score | `modules/candidate_intelligence.py` | `calculate_evidence_confidence()` | evidence count, avg score, consistency, contradiction/uncertainty counts | 0–100 confidence | Fixed weighted formula (volume 50% + quality 30% + consistency 20%, minus penalties) |

## G. Similarity algorithms

| # | Algorithm | File | Function | Input | Output | Purpose |
|---|---|---|---|---|---|---|
| 1 | Jaccard similarity over a stemmed, stop-word-filtered token set | `modules/similarity.py` *(new, extracted from adaptive_engine.py where it used to be duplicated)* | `jaccard_similarity()`, `are_questions_similar()`, `is_duplicate_of_any()` | two question strings | similarity score 0–1 / boolean | Anti-repetition: prevents the same or a paraphrased question being asked twice, used by both `question_bank.py` and `adaptive_engine.py` |
| 2 | Naive suffix stemming | `modules/similarity.py` | `stem_word()` | a token | de-pluralized token | Normalizes plurals before similarity comparison. A single fixed rule (strip trailing "s" unless "ss") — **not** a Porter/Snowball stemmer or trained model |

## H. OCR / text-extraction models

| # | Model/technique | File | Function | Input | Output | Purpose |
|---|---|---|---|---|---|---|
| 1 | pdfplumber (text-layer extraction, not OCR) | `modules/resume_parser.py` | `extract_text_from_pdf()` tier 1 | PDF file | raw text | Primary extraction for text-based PDFs |
| 2 | pdfminer.six (text-layer extraction, not OCR) | `modules/resume_parser.py` | `extract_text_from_pdf()` tier 2 | PDF file | raw text | Fallback when pdfplumber yields little text |
| 3 | EasyOCR (pretrained deep-learning scene-text recognizer, third-party, not trained by this project) | `modules/resume_parser.py` | `get_ocr_reader()`, `extract_text_from_pdf()` tier 3 | rasterized page images (via PyMuPDF) | recognized text | Handles scanned/image-only resume PDFs |

Note: `easyocr`, `PyMuPDF` (`fitz`), and `pdfminer.six` are actively used
here but are **missing from both `requirements.txt` files** — flagged
previously in the audit, unrelated to this feature and left untouched.

## I. Voice / audio algorithms

| # | Algorithm | File | Function | Input | Output | Purpose |
|---|---|---|---|---|---|---|
| 1 | Google Web Speech API (ASR) | `modules/voice_analyzer.py` | `_speech_rate()`, `_fillers()` | audio (wav) | transcript | Speech-to-text |
| 2 | YIN pitch estimation (`librosa.pyin`) | `modules/voice_analyzer.py` | `_tone()` | audio samples | fundamental frequency track | Tone/pitch-variation scoring |
| 3 | Short-time energy framing + percentile thresholding | `modules/voice_analyzer.py` | `_pauses()` | audio samples | pause ratio | Pause/hesitation detection |
| 4 | Regex filler-word counting | `modules/voice_analyzer.py` | `_fillers()` | transcript | filler ratio | Counts "um", "uh", "like", etc. |
| 5 | Fixed-weight composite score | `modules/voice_analyzer.py` | `analyze_voice_confidence()` | the four component scores above | 0–100 confidence score | `0.25·rate + 0.30·pause + 0.25·tone + 0.20·filler` — a fixed formula, not a trained model |

---

## What changed in this session (data-driven adaptive question engine)

New files (all pure-Python, zero new third-party dependencies):
- `backend/modules/similarity.py` — Jaccard/stemming, extracted from `adaptive_engine.py` to remove duplication.
- `backend/modules/skill_mapper.py` — canonical skill list + alias table, replaces two previously-duplicated `DATASET_MAP` dicts.
- `backend/modules/question_bank.py` — loads/normalizes all 18 datasets once; primary question retrieval (`select_question`) and pool construction (`pool_for_skills`).
- `backend/modules/difficulty_engine.py` — deterministic score-band difficulty engine (section F, items 1–2).
- `backend/tests/test_data_driven_engine.py` — 15 tests covering the 14 required scenarios.

Modified files (targeted, non-destructive):
- `modules/adaptive_engine.py` — retrieval priority flipped to dataset-first, LLM-fallback only when the dataset can't serve the request; per-skill performance tracker wired into `select_next_topic()`; `add_to_user_history()` now also records difficulty/score/timestamp.
- `modules/question_engine.py` — `generate_questions()` now builds the pool from the dataset first and only calls the LLM for resume skills with zero dataset coverage; fixed a pre-existing bug in `get_fallback_questions()` where the full HR + Aptitude datasets were unconditionally merged into every pool regardless of whether padding was actually needed (caught by `test_3_resume_with_multiple_skills`).
- `modules/evaluator.py` — `generate_final_report()` now also exposes `skill_performance` (additive field).
- `backend/app.py` — two duplicated inline score→difficulty ladders (in `/api/practice/start` and `/api/practice/reinterview`) replaced with a single call to `difficulty_engine.initial_difficulty_from_score()`.

Nothing in the existing UI, routes, database schema, or the Groq/Anthropic
provider integration was removed or restructured. `datasets/*.json` were
backed up to `datasets/backup/` and are unmodified (verified byte-identical
via `diff -rq`).

---

## What changed in this session (multi-round flow, recruiter live view, outcome logging)

Requested: bring InterviewIQ closer to how real-time interview platforms
work, and "train the data" if there's anything genuine to train. Three
concrete features were scoped and built; a fourth ("live speech-to-text
captions") turned out to already exist and needed no work — see below.

### Live speech-to-text captions — already implemented, unchanged
`frontend/assets/js/voice.js`'s `Voice._initRecognition()` already uses the
browser's native `SpeechRecognition`/`webkitSpeechRecognition` API with
`continuous: true` and `interimResults: true`, streaming a live transcript
into the answer box as the candidate speaks. Nothing was added or changed
here — flagging this so it isn't mistaken for new work.

### Multi-round interview flow (Technical → HR)
New file `backend/modules/round_manager.py`: a pure orchestration layer —
it does **not** reimplement any adaptive/difficulty logic. It composes the
existing, unmodified `adaptive_engine.py`/`question_engine.py` decision
process into sequential rounds within one continuous session, and is
strictly opt-in (`multi_round: true` on `/api/questions/generate` — default
off, so every existing single-round flow is byte-for-byte unchanged).

- `session["answers"]`, `technical_scores`, `voice_scores`, `emotion_timeline`
  stay cumulative across the whole session (so the final report's whole-
  interview averages keep meaning what they always meant); only per-round
  *selection* state (skills, uncertainty, covered topics, asked questions,
  current question pool) resets between rounds.
- `modules/adaptive_engine.py`'s `should_interview_finish()` got one
  additive, default-0 offset (`round_started_at_answer_count`) so each
  round gets its own fresh 10–30 question safety window instead of
  inheriting the cumulative count from earlier rounds.
- `backend/app.py`: `/api/questions/generate` accepts `multi_round`/`rounds`;
  `/api/answer/submit` transparently rolls into the next round when the
  current one's question pool is exhausted (new `action: "round_complete"`,
  distinct from `"finish"`), and calls `round_manager.finalize()` on true
  completion so the last active round is captured too.
- `modules/evaluator.py`'s `generate_final_report()` gained two additive
  fields: `round_scores` (per-round breakdown) and a corrected
  `skills_covered` (built from the answers actually recorded, since
  `session["skills"]` only holds the *current* round's skills by the end of
  a multi-round interview and would otherwise silently drop earlier rounds).
- Frontend: an opt-in "Full multi-round interview (Technical + HR)"
  checkbox on `index.html` (default unchecked), a round-transition toast +
  updated "next" chip in `interview.js`, and a "Round Breakdown" card in
  `report.js` (renders only when `round_scores` is non-empty).
- Verified with a 6-test unit suite for `round_manager.py`, the pre-existing
  15-test regression suite (unaffected), and an end-to-end scripted run
  against the real `question_engine`/`adaptive_engine` modules confirming a
  Technical→HR transition, correct per-round score snapshots, and correct
  cross-round `skills_covered`.

### Recruiter live-watch view
This is **point-in-time stats/integrity polling, not a webcam/audio relay**
— an actual video feed would need WebRTC signaling infrastructure this
project doesn't have, and adding that was out of scope for this change.
What it does do:
- `new_sess()` now stamps `created_at`/`updated_at`; the existing
  `save_accessed_sessions` request hook stamps `updated_at` on every touch.
- New `GET /api/recruiter/live-sessions` (role-gated recruiter/admin):
  returns every session with `status == "active"` touched in the last 10
  minutes, with candidate name/email, question progress, running
  technical/voice scores, latest emotion, and integrity violation counts.
- New "Live Sessions" tab in `frontend/recruiter.html`, polling every 5
  seconds while that tab is open (stopped on navigating away).

### Outcome logging ("train the data", honestly)
The datasets this project ships with (`datasets/*.json`) only ever
contained `{question, difficulty, skill}` — never an outcome label (did
this candidate get hired?). There was nothing to legitimately train on, so
rather than fabricate a "trained" model, this starts logging **real**
outcome data:
- New `PUT /api/recruiter/interviews/<session_id>/outcome` (role-gated):
  a recruiter records `hired` / `rejected` / `advanced` / `no_decision` (+
  optional notes) against a completed report, stored at
  `report.human_outcome`. Purely additive — no existing scoring, report, or
  candidate-facing behavior changes.
- `recruiter.html`'s candidate-profile "Assessment Attempts & Reports" table
  gained an outcome dropdown per attempt.
- New `backend/modules/outcome_model.py`: a guard module, **not a model**.
  `train_outcome_model(db)` counts real labeled outcomes and reports whether
  there's enough (`MIN_SAMPLES = 50`, deliberately conservative) to
  legitimately train something — it never fits or fabricates a result
  either way. Exposed read-only via `GET /api/recruiter/outcome-model/status`.
- **Current state: 0 labeled outcomes** (brand-new feature, nothing
  recorded yet). This is infrastructure for a future, honestly-trainable
  model — not a claim that one exists today.
