# TheirStack Live Job Search Integration — InterviewIQ

## Overview
InterviewIQ integrates real-time live job postings using the **TheirStack Job Postings API** (`POST https://api.theirstack.com/v1/jobs/search`) directly inside the Resume Analyzer page (`frontend/analyzer.html`).

The live jobs section appears immediately after **Profile Details** (`RESUME PROFILE SUMMARY`) to present candidates with real open roles in Bengaluru matched to their actual extracted resume skills.

---

## Architecture & Data Flow

```
Candidate Resume PDF Upload
        ↓
InterviewIQ Backend (resume_parser.py)
        ↓
Extracted Technical Skills (e.g. Python, Flask, MongoDB, Docker)
        ↓
POST /api/jobs/live (Flask Backend)
        ↓ (Server-side cache check / TTL 300s)
POST https://api.theirstack.com/v1/jobs/search (TheirStack API)
        ↓
Real Live Job Results from Bengaluru
        ↓
InterviewIQ Resume-to-Job Match Engine (Deterministic Heuristic)
        ↓
Live Jobs Section in Resume Analyzer UI (Immediately below Profile Details)
```

---

## Environment Configuration

Configure the following variables in `.env`:

```env
THEIRSTACK_API_KEY=your_theirstack_api_key_here
DEFAULT_JOB_LOCATION=Bengaluru
JOB_RESULTS_LIMIT=10
JOB_POSTED_MAX_AGE_DAYS=15
JOB_CACHE_TTL_SECONDS=300
```

> [!SECURITY NOTE]
> `THEIRSTACK_API_KEY` exists strictly on the backend (`os.environ`). It is **never** exposed to frontend JavaScript, HTML, query parameters, headers sent to browser, or client-side storage.

---

## Backend Subsystem (`backend/modules/job_search.py`)

### 1. Skill Normalization
- Normalizes canonical terms (e.g., `JS` → `JavaScript`, `Node` → `Node.js`, `ReactJS` → `React`, `Mongo` → `MongoDB`, `ML` → `Machine Learning`).
- Avoids over-normalization (`C` and `C++` remain distinct; `Java` and `JavaScript` remain distinct).

### 2. Job Title Derivation
- Dynamically derives relevant job search titles directly from the resume skills (e.g., `Python + Flask` → `["Python Developer", "Backend Developer"]`).

### 3. InterviewIQ Resume Match Score
- Deterministic heuristic calculating:
  - **Skill Overlap**: Overlap between candidate resume skills and job requirements (`matched_skills` vs `missing_skills`).
  - **Title Alignment**: Relevance of job title to candidate skill set.
  - **Location & Experience Compatibility**.
- Bounded match percentage (e.g. `82% Match`).

### 4. Server-Side Caching
- Key: `hash(location + max_age_days + sorted_skills)`
- Default TTL: `300 seconds`
- Reduces API consumption and prevents rate limits.

---

## API Endpoints

### `POST /api/jobs/live`
- **Request Body**:
  ```json
  {
    "skills": ["Python", "Flask", "MongoDB", "REST APIs"],
    "location": "Bengaluru",
    "force_refresh": false
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "location": "Bengaluru",
    "freshness_text": "Updated just now",
    "count": 5,
    "jobs": [
      {
        "id": "12345",
        "title": "Python Backend Developer",
        "company": "Tech Corp",
        "location": "Bengaluru, Karnataka",
        "salary": "Salary not disclosed",
        "employment_type": "Full-time",
        "experience": "0–2 years",
        "posted_ago": "Posted 2 days ago",
        "url": "https://api.theirstack.com/...",
        "description": "Short excerpt...",
        "match_score": 82,
        "matched_skills": ["Python", "Flask", "MongoDB"],
        "missing_skills": ["AWS"]
      }
    ]
  }
  ```

---

## Error & Rate Limit Handling

1. **Missing API Key**: Returns graceful response indicating live job search is not configured yet.
2. **Invalid API Key (401/403)**: Returns user-friendly authentication failure notice.
3. **Rate Limit Exceeded (429)**: Returns notice indicating temporary rate limiting without throwing unhandled exceptions.
4. **No Resume Uploaded**: Displays notice requesting resume upload.
5. **No Matching Jobs**: Displays `"No matching live jobs found for this resume in Bengaluru."`

---

## UI Placement & Design

- **Location**: Placed immediately AFTER Section 2 (**RESUME PROFILE SUMMARY**) inside `frontend/analyzer.html`.
- **Theme**: Emerald Ink + Champagne Palette (`var(--surface)`, `var(--surface2)`, `var(--accent)`, `var(--accent2)`).
- **Interactions**:
  - Live Freshness Indicator (`🟢 Live Job Data`).
  - Refresh Jobs button (`🔄 Refresh Jobs`) for manual cache invalidation.
  - Responsive layout (2-column on desktop, 1-column on mobile).
  - Original source links (`target="_blank" rel="noopener noreferrer"`) for direct job application.
