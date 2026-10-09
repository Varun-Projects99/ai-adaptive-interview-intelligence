# InterviewIQ AI Assistant

A project-aware, authenticated chat assistant surfaced on the candidate
dashboard. This document describes what was actually built and tested;
see the end of this file for known limitations.

## Architecture

```
Candidate message (POST /api/ai-assistant/chat, session-cookie authenticated)
        |
classify_intent()            deterministic keyword routing (not a trained
                              classifier -- see modules/ai_assistant.py)
        |
build_candidate_context()    controlled MongoDB reads, scoped to the
                              session's own user_id only
        |
get_practice_questions()     if the message asks for practice questions,
                              pulls REAL questions from the existing
                              dataset-first question bank instead of
                              letting the AI invent them
        |
build_prompt()                system rules + relevant slice of project
                              knowledge + candidate context + last few
                              turns of this conversation
        |
call_ai_provider()            Anthropic Claude (primary) -> Groq Llama-3
                              (fallback) -- the SAME provider pattern
                              already used by evaluator.py /
                              question_engine.py / resume_parser.py
        |
reply returned + optionally persisted to db["ai_assistant_conversations"]
```

All of this lives in one new module, `backend/modules/ai_assistant.py`,
plus a page (`frontend/assistant.html`) and two small additions to
`backend/app.py` (an import block and two routes) and one new card in
`frontend/dashboard.html`. No existing file's existing behavior was
changed.

## Endpoint

`POST /api/ai-assistant/chat`

Request:
```json
{ "message": "What are my weak areas?", "conversation_id": "optional-uuid" }
```

Response (200):
```json
{ "reply": "...", "conversation_id": "uuid", "intent": "LEARNING" }
```

Error responses: `400` (empty/oversized message, invalid conversation_id),
`401` (not authenticated -- handled by the existing `login_required`
decorator, same as every other authenticated route in the project), `429`
(rate limited), `503` (both AI providers unavailable), `500` (unexpected).
Error bodies never include a stack trace or internal exception text.

Page route: `GET /ai-assistant` (also `login_required`), serves
`frontend/assistant.html`.

## Authentication & data isolation

- Both routes use the project's existing `login_required` decorator --
  no new auth mechanism was introduced.
- The candidate's identity is read ONLY from `session["user_id"]` (the
  server-side session Flask already manages after login). The request
  body's `message`/`conversation_id` are never trusted as an identity
  source.
- Every MongoDB query in `modules/ai_assistant.py` filters by that
  `user_id` string, matching the exact `user_id` format already used in
  `candidate_profiles`, `reports`, and `learning_progress` (`str(user["_id"])`).
  A dedicated test (`test_uses_only_the_requesting_users_report`) asserts
  the query filter itself, not just the response, to catch a future
  regression that might read broadly and filter client-side by mistake.

## AI providers

Reuses the exact Anthropic-primary/Groq-fallback pattern already used
throughout the project (same model names, same "your_anthropic_api_key_here"
placeholder convention). No new provider, no new environment variable --
`ANTHROPIC_API_KEY` and `GROQ_API_KEY` are the same variables the rest of
the app already reads.

## MongoDB

One new, optional collection: `ai_assistant_conversations`
(`{conversation_id, user_id, messages: [{role, content, timestamp}], created_at, updated_at}`).
Conversation history is capped at 40 stored messages per conversation, and
only the last 3 turn-pairs (6 messages) are ever sent to the AI provider,
to keep prompt size, latency and cost bounded. If `MONGO_URI` is not
configured, the assistant still works -- it simply can't persist
conversations (each request is answered from scratch), which is the same
graceful-degrade behavior every other Mongo-backed module in this project
already has.

No other collection was modified. `candidate_profiles`, `reports`, and
`learning_progress` are read-only from this module's perspective.

## Project knowledge (Layer A)

A hand-maintained Python dict, `PROJECT_KNOWLEDGE` in
`modules/ai_assistant.py`, with one entry per real, audited feature area
(resume analysis, adaptive interview, adaptive difficulty, answer
evaluation, voice analysis, face/integrity monitoring, reports, history,
coding practice, auth, learning). Each entry was written directly from
reading the corresponding module's code, not from assumption. Two
features were confirmed to be **not persisted**, and this is stated
explicitly rather than glossed over:
- A standalone Resume Analyzer run (`/api/resume/analyze`) is not saved
  anywhere.
- Coding Practice runs/reviews (`/api/coding/run`, `/api/coding/review`)
  are not saved anywhere.

**Maintaining this knowledge base:** it is not auto-generated. When a
described feature's behavior changes, update its entry in
`PROJECT_KNOWLEDGE` in the same commit/PR that changes the code. There is
a test (`test_all_referenced_knowledge_keys_exist`) that fails the build
if an intent references a knowledge key that no longer exists, as a
minimal safety net -- but keeping the text itself accurate is a manual
process, the same as keeping any other code comment accurate.

## Candidate context (Layer B)

Built per-request from three existing collections, scoped by intent so
only relevant fields are read (never a full-document or full-database
dump into the prompt):
- `reports` (latest `status: "completed"` report) -> scores, skill
  scores, weak/strong areas, violation counts, recent integrity events.
- `candidate_profiles` -> stored skills (for resume-related questions),
  per-skill knowledge depth.
- `learning_progress` -> existing recommendations.

If none of these have data for the candidate, the assistant is instructed
to say so plainly rather than invent a score or comparison.

## Practice-question requests

A request like "Give me 5 Python questions based on my weak areas" is
detected (`get_practice_questions`) and answered with REAL questions
pulled from the existing `modules/question_bank.py` dataset (the same
dataset-first source the adaptive interview itself uses), not questions
invented by the AI provider. If no dataset-backed skill can be resolved
(no skill named in the message, and no stored weak areas to fall back
on), this feature is skipped and the message is answered as ordinary
general/technical conversation instead of fabricating a "dataset" result.

## Rate limiting & cost control

- In-memory sliding-window limiter (`check_rate_limit`), same pattern the
  project already uses for login-attempt limiting (`app.py`'s
  `failed_logins` dict) -- no new dependency such as Flask-Limiter.
  Default: 12 requests per user per 60-second window.
- Message length capped at 1500 characters.
- Conversation history sent to the AI capped at the last 3 turn-pairs.
- AI response length capped (`max_tokens=700`).

## UI

`frontend/assistant.html`, in the existing dark/cyberpunk visual theme
(reuses `/assets/css/style.css` and the same card/chip/corner visual
language as the rest of the app, closely modeled on the existing
`coach.html` chat layout). Includes: 8 quick-start prompts, Enter-to-send
/ Shift+Enter-for-newline, a typing indicator, an error state with a
Retry button, a Clear Conversation button, and a responsive layout
(desktop two-column, single column under 900px, matching `coach.html`'s
existing breakpoint). User and assistant message text is HTML-escaped
before rendering (the pre-existing `coach.html` did not do this).

A new dashboard card ("🤖 AI Assistant") was added after the existing
Performance Reports card in `frontend/dashboard.html`, styled identically
to the other cards. No existing card, nav item, or dashboard behavior was
changed.

## The old AI Coach (`/coach`, `/api/coach/chat`)

Audited, left untouched. It is not linked from the dashboard today (it
was already orphaned before this work), so there is no user-visible
"two assistants" confusion to resolve. It was not deleted or modified,
per the instruction to avoid touching unrelated working code -- if it is
ever wired back into the UI in the future, it should probably be retired
in favor of this new assistant, since it has no authentication on its API
route and no project/candidate awareness.

## Testing

`backend/tests/test_ai_assistant.py`, 29 tests, all passing (run with
fake in-memory Mongo-collection stand-ins and fake `anthropic`/`groq` SDK
modules -- no live database or live network call is exercised):
- Intent classification (including the two ordering edge cases found and
  fixed during development: "what SKILLS did my RESUME contain" and
  "explain my LATEST interview PERFORMANCE").
- Candidate-context data isolation (a fake two-user dataset asserts the
  Mongo query filter itself, and that another user's data never leaks
  into the context string).
- Honest "no data" behavior when nothing is stored.
- Practice-question dataset reuse, and that it is skipped (not faked)
  when no dataset-backed skill can be resolved.
- Rate limiting (per-user, blocks after the configured limit).
- Input validation (empty / oversized message).
- Anthropic-primary/Groq-fallback behavior, including the placeholder-key
  convention and the "both providers fail" path.
- Knowledge-base self-consistency and the absence of banned
  overconfidence phrases as asserted claims.

Not covered by automated tests (require a live environment): the actual
`/ai-assistant` and `/api/ai-assistant/chat` Flask routes end-to-end
against a running server + real MongoDB + a real logged-in session; the
manual verification checklist below should be run once locally.

### Manual verification checklist
1. `pip install -r backend/requirements.txt` (no new packages needed) and
   start the app as usual: `cd backend && python app.py`.
2. Log in as a real candidate.
3. Confirm the dashboard shows the new "AI Assistant" card without any
   change to the other four cards.
4. Open it, and try: "What is InterviewIQ?", "How does adaptive difficulty
   work?", "What are my weak areas?" (after completing at least one real
   interview), "Explain polymorphism", "Give me 5 Python questions based
   on my weak areas".
5. Confirm an unauthenticated request to `POST /api/ai-assistant/chat`
   (no session cookie) returns 401.
6. Confirm existing features are unaffected: dashboard, AI Interview,
   Resume Analyzer, Coding Practice, Performance Reports, and the
   Face/Integrity monitoring added earlier all still work exactly as
   before.

## Known limitations

- Intent classification is deterministic keyword matching, not an ML/NLU
  classifier. A misclassified intent only affects which extra context is
  attached to the prompt -- the candidate's actual message is always sent
  to the AI model either way -- but an unusually-phrased question may get
  a slightly less-targeted set of extra context than a differently-phrased
  one.
- Resume-skill personalization only reflects skills that have made it
  into a candidate's stored profile via an actual interview session; a
  standalone Resume Analyzer run is not persisted (see above), so it
  cannot be referenced by the assistant.
- Coding Practice has no stored history at all (see above), so the
  assistant cannot discuss a candidate's coding-practice trend over time.
- The in-memory rate limiter resets if the Flask process restarts (or, on
  a serverless deployment, is scoped to a single function instance) --
  it is a lightweight abuse deterrent, not a strict distributed quota.
- No new environment variables, dependencies, or AI providers were added.
