"""
InterviewIQ — Live Job Search Subsystem
Integrates TheirStack Job Search API for resume-driven live job matching in Bengaluru.
"""

import os
import time
import requests
import re
import datetime

# In-memory server-side cache: key -> (timestamp, result_dict)
_JOB_CACHE = {}

# Skill Normalization Map
SKILL_NORMALIZATION_MAP = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "ml": "Machine Learning",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python": "Python",
    "express": "Express.js",
    "expressjs": "Express.js",
    "next": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL"
}

def normalize_skills(skills: list) -> list:
    """Lightweight skill normalization preventing over-normalization."""
    if not skills:
        return []
    normalized = []
    seen = set()
    for s in skills:
        if not s or not isinstance(s, str):
            continue
        s_clean = s.strip()
        s_lower = s_clean.lower()
        norm = SKILL_NORMALIZATION_MAP.get(s_lower, s_clean)
        if norm.lower() not in seen:
            seen.add(norm.lower())
            normalized.append(norm)
    return normalized


def derive_job_titles_from_skills(skills: list) -> list:
    """Dynamically derives relevant job search titles based on actual resume skills."""
    skills_lower = set([s.lower() for s in skills])
    titles = set()

    # Rule-based title derivation from actual resume skills
    if any(k in skills_lower for k in ["python", "flask", "django", "fastapi"]):
        titles.add("Python Developer")
        titles.add("Backend Developer")
    if any(k in skills_lower for k in ["java", "spring", "spring boot", "hibernate"]):
        titles.add("Java Developer")
        titles.add("Backend Developer")
    if any(k in skills_lower for k in ["react", "vue", "angular", "javascript", "typescript", "frontend", "html", "css"]):
        titles.add("Frontend Developer")
        titles.add("Software Engineer")
    if any(k in skills_lower for k in ["node.js", "express.js", "backend"]):
        titles.add("Backend Developer")
    if ("python" in skills_lower or "java" in skills_lower or "c++" in skills_lower) and ("react" in skills_lower or "javascript" in skills_lower or "node.js" in skills_lower):
        titles.add("Full Stack Developer")
    if any(k in skills_lower for k in ["machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow", "ai/ml", "ai"]):
        titles.add("AI/ML Engineer")
        titles.add("Machine Learning Engineer")
        titles.add("Data Scientist")
    if any(k in skills_lower for k in ["pandas", "numpy", "sql", "data analytics"]):
        titles.add("Data Analyst")
    if any(k in skills_lower for k in ["docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "devops"]):
        titles.add("DevOps Engineer")
        titles.add("Cloud Engineer")

    if not titles:
        titles = {"Software Engineer", "Backend Developer"}

    return list(titles)[:5]


def calculate_resume_match(candidate_skills: list, job: dict) -> dict:
    """
    Calculates deterministic InterviewIQ Resume Match percentage and skill overlap.
    Considers candidate skills, job description text, and job technologies list.
    """
    cand_skills_lower = set([s.lower() for s in candidate_skills])
    
    # Extract job description / title / technologies
    job_title = job.get("job_title") or job.get("title") or ""
    job_desc = (str(job.get("description") or "") + " " + str(job_title)).lower()
    raw_techs = job.get("technologies") or []

    # Clean up tech list from job
    job_techs = []
    if isinstance(raw_techs, list):
        for t in raw_techs:
            if isinstance(t, str):
                job_techs.append(t.strip())
            elif isinstance(t, dict) and "name" in t:
                job_techs.append(t["name"].strip())

    techs_to_check = set([t.lower() for t in job_techs])
    
    # Find matched skills (candidate skill explicitly in job desc or job techs)
    matched_skills = []
    for skill in candidate_skills:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, job_desc) or skill.lower() in techs_to_check:
            matched_skills.append(skill)

    # Find missing skills (job techs not in candidate resume)
    missing_skills = []
    for tech in job_techs:
        if tech.lower() not in cand_skills_lower and len(tech) <= 25:
            missing_skills.append(tech.title())

    # Deterministic heuristic score calculation
    base_score = 50.0
    if candidate_skills:
        skill_match_ratio = len(matched_skills) / max(1, len(candidate_skills))
        base_score += skill_match_ratio * 40.0

    # Title relevance bonus
    job_title_lower = job_title.lower()
    for s in candidate_skills:
        if s.lower() in job_title_lower:
            base_score += 5.0
            break

    match_percentage = min(98, max(45, round(base_score)))

    return {
        "score": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:4]
    }


def fetch_theirstack_jobs(skills: list, location: str = None, max_age_days: int = None, force_refresh: bool = False) -> dict:
    """
    Fetches real job postings using TheirStack API with caching and error handling.
    """
    if location is None:
        location = os.environ.get("DEFAULT_JOB_LOCATION", "Bengaluru")
    if max_age_days is None:
        max_age_days = int(os.environ.get("JOB_POSTED_MAX_AGE_DAYS", "15"))

    api_key = os.environ.get("THEIRSTACK_API_KEY", "").strip()

    if not api_key or api_key.startswith("your_"):
        return {
            "success": False,
            "error_type": "missing_api_key",
            "message": "Live job search is not configured yet.",
            "jobs": []
        }

    # Normalize candidate skills
    norm_skills = normalize_skills(skills)
    if not norm_skills:
        return {
            "success": False,
            "error_type": "no_skills",
            "message": "Upload or select a resume to see jobs matched to your skills.",
            "jobs": []
        }

    # Cache lookup
    ttl_seconds = int(os.environ.get("JOB_CACHE_TTL_SECONDS", "300"))
    sorted_skills_str = ",".join(sorted([s.lower() for s in norm_skills]))
    cache_key = f"{location.lower()}_{max_age_days}_{sorted_skills_str}"

    now = time.time()
    if not force_refresh and cache_key in _JOB_CACHE:
        cache_ts, cached_result = _JOB_CACHE[cache_key]
        if now - cache_ts < ttl_seconds:
            res_copy = dict(cached_result)
            res_copy["cached"] = True
            mins = int((now - cache_ts) / 60)
            res_copy["freshness_text"] = "Updated just now" if mins < 1 else f"Updated {mins} min ago"
            return res_copy

    # Construct TheirStack dynamic request payload
    titles = derive_job_titles_from_skills(norm_skills)
    limit = int(os.environ.get("JOB_RESULTS_LIMIT", "10"))

    payload = {
        "job_title_or": titles,
        "job_country_code_or": ["IN"],
        "job_location_pattern_or": [location, "Bangalore", "Karnataka"],
        "posted_at_max_age_days": max_age_days,
        "is_closed": False,
        "limit": limit,
        "page": 0
    }

    url = "https://api.theirstack.com/v1/jobs/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if resp.status_code == 401 or resp.status_code == 403:
            return {
                "success": False,
                "error_type": "auth_error",
                "message": "Live job search authentication failed. Please check the TheirStack API configuration.",
                "jobs": []
            }
        elif resp.status_code == 429:
            return {
                "success": False,
                "error_type": "rate_limited",
                "message": "Live job search is temporarily rate-limited. Please try again shortly.",
                "jobs": []
            }
        elif resp.status_code != 200:
            return {
                "success": False,
                "error_type": "api_error",
                "message": f"TheirStack API returned status {resp.status_code}. Please try again later.",
                "jobs": []
            }

        data = resp.json()
        raw_jobs = data.get("data", []) or data.get("jobs", []) or []

        if not raw_jobs:
            res = {
                "success": True,
                "error_type": None,
                "message": f"No matching live jobs found for this resume in {location}.",
                "location": location,
                "freshness_text": "Updated just now",
                "count": 0,
                "jobs": []
            }
            _JOB_CACHE[cache_key] = (now, res)
            return res

        # Process real job postings
        processed_jobs = []
        seen_ids = set()

        for j in raw_jobs:
            job_id = j.get("id") or j.get("job_id") or j.get("url")
            if job_id in seen_ids:
                continue
            if job_id:
                seen_ids.add(job_id)

            title = j.get("job_title") or j.get("title") or "Software Engineer"
            company = j.get("company_name") or j.get("company") or "Company Not Disclosed"
            loc = j.get("location") or j.get("job_location") or f"{location}, Karnataka"
            job_url = j.get("url") or j.get("final_url") or j.get("job_url") or j.get("source_url")
            
            # Salary formatting
            sal_min = j.get("salary_min")
            sal_max = j.get("salary_max")
            sal_curr = j.get("salary_currency", "₹")
            sal_str = j.get("salary_string")

            if sal_str:
                salary = str(sal_str)
            elif sal_min and sal_max:
                salary = f"{sal_curr}{sal_min:,} - {sal_curr}{sal_max:,}"
            elif sal_min:
                salary = f"From {sal_curr}{sal_min:,}"
            else:
                salary = "Salary not disclosed"

            # Posting date formatting
            posted_at = j.get("date_posted") or j.get("posted_at") or j.get("created_at")
            posted_ago = "Posted recently"
            if posted_at:
                try:
                    p_date = datetime.datetime.fromisoformat(str(posted_at).replace('Z', '+00:00'))
                    days = (datetime.datetime.now(datetime.timezone.utc) - p_date).days
                    if days <= 0:
                        posted_ago = "Posted today"
                    elif days == 1:
                        posted_ago = "Posted 1 day ago"
                    else:
                        posted_ago = f"Posted {days} days ago"
                except Exception:
                    posted_ago = f"Posted on {str(posted_at)[:10]}"

            emp_type = j.get("employment_type") or j.get("type") or "Full-time"
            seniority = j.get("seniority") or "0–2 years"
            
            desc = str(j.get("description") or j.get("snippet") or "")
            desc_clean = re.sub(r'<[^>]+>', '', desc).strip()
            if len(desc_clean) > 160:
                desc_clean = desc_clean[:160] + "..."

            match_info = calculate_resume_match(norm_skills, j)

            processed_jobs.append({
                "id": str(job_id) if job_id else "",
                "title": title,
                "company": company,
                "location": loc,
                "salary": salary,
                "employment_type": emp_type,
                "experience": seniority,
                "posted_ago": posted_ago,
                "url": job_url,
                "description": desc_clean,
                "match_score": match_info["score"],
                "matched_skills": match_info["matched_skills"],
                "missing_skills": match_info["missing_skills"]
            })

        res = {
            "success": True,
            "error_type": None,
            "message": f"Found {len(processed_jobs)} live job(s) matching your resume in {location}.",
            "location": location,
            "freshness_text": "Updated just now",
            "count": len(processed_jobs),
            "jobs": processed_jobs
        }

        _JOB_CACHE[cache_key] = (now, res)
        return res

    except requests.Timeout:
        return {
            "success": False,
            "error_type": "timeout",
            "message": "Live job search request timed out. Please try refreshing.",
            "jobs": []
        }
    except Exception:
        return {
            "success": False,
            "error_type": "exception",
            "message": "Failed to connect to job search service. Please try again later.",
            "jobs": []
        }
