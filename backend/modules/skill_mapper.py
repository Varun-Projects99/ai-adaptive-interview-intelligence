"""
Skill Normalization / Mapping Layer
====================================
Single source of truth connecting resume-detected skill strings (as produced
by modules/resume_parser.py) to the canonical skill buckets that are actually
backed by a local question dataset in datasets/*.json.

This REPLACES the two previously-duplicated `DATASET_MAP` dictionaries that
used to live independently inside modules/question_engine.py and
modules/adaptive_engine.py (same data, two places to edit, easy to drift).

Design rule (per project requirement): only map a skill when there is
reasonable topical evidence that a dataset actually covers it. A skill with
no reasonable dataset match is left UNMAPPED — it is never force-matched to
an unrelated bucket. Unmapped skills are exactly the skills the LLM fallback
(modules/question_engine.py / modules/adaptive_engine.py) is responsible for
covering, per the "dataset primary, LLM fallback" architecture.

Nothing here is inferred statistically or learned from data — it is an
explicit, auditable lookup table. That is a deliberate choice: silently
"guessing" a skill mapping is exactly the kind of false-positive skill
detection the project rules prohibit.
"""

# The only skills that have a real backing dataset (datasets/<file>.json).
# Keys are the exact `skill` field values found inside those datasets.
CANONICAL_SKILLS = {
    "Python":        "python.json",
    "Java":          "java.json",
    "C":             "c.json",
    "C++":           "cpp.json",
    "DSA":           "dsa.json",
    "DBMS":          "dbms.json",
    "OS":            "os.json",
    "CN":            "cn.json",
    "SQL":           "sql.json",
    "HTML/CSS":      "html_css.json",
    "JavaScript":    "javascript.json",
    "React":         "react.json",
    "DevOps":        "devops.json",
    "AWS":           "aws.json",
    "AI/ML":         "ai_ml.json",
    "HR":            "hr.json",
    "Aptitude":      "aptitude.json",
    "Cybersecurity": "cybersecurity.json",
}

# Resume-skill-string (lowercased, trimmed) -> canonical dataset skill.
# Only entries with genuine topical overlap are included. Documented
# judgment calls (e.g. MongoDB -> DBMS, not SQL; Azure/GCP left unmapped
# rather than forced into AWS) are called out inline.
_ALIAS_MAP = {
    # Python
    "python": "Python", "python programming": "Python", "python3": "Python",
    "python 3": "Python", "django": "Python", "flask": "Python", "fastapi": "Python",
    "pandas": "Python", "numpy": "Python", "scipy": "Python",

    # Java
    "java": "Java", "core java": "Java", "spring": "Java", "spring boot": "Java",
    "hibernate": "Java", "j2ee": "Java", "maven": "Java", "gradle": "Java",

    # C
    "c": "C", "c programming": "C", "embedded c": "C", "c language": "C", "c99": "C",

    # C++
    "c++": "C++", "cpp": "C++", "c plus plus": "C++", "stl": "C++", "boost": "C++",

    # DSA
    "dsa": "DSA", "data structures": "DSA", "data structure": "DSA",
    "data structures and algorithms": "DSA", "algorithms": "DSA",
    "linked list": "DSA", "binary tree": "DSA", "dynamic programming": "DSA",

    # DBMS (general database-management concepts, including NoSQL —
    # dbms.json's own sample question is "document stores vs key-value
    # stores", i.e. it explicitly covers NoSQL, so NoSQL engines map here
    # rather than to SQL).
    "dbms": "DBMS", "database management": "DBMS", "database": "DBMS",
    "databases": "DBMS", "database management system": "DBMS", "nosql": "DBMS",
    "mongodb": "DBMS", "dynamodb": "DBMS", "cassandra": "DBMS", "redis": "DBMS",

    # OS
    "os": "OS", "operating system": "OS", "operating systems": "OS",
    "linux": "OS", "unix": "OS", "shell scripting": "OS",

    # CN
    "cn": "CN", "computer networks": "CN", "computer networking": "CN",
    "networking": "CN", "tcp/ip": "CN",

    # SQL (relational query language specifically)
    "sql": "SQL", "mysql": "SQL", "postgresql": "SQL", "sqlite": "SQL",
    "oracle": "SQL", "pl/sql": "SQL", "t-sql": "SQL",

    # HTML/CSS
    "html": "HTML/CSS", "css": "HTML/CSS", "html5": "HTML/CSS", "css3": "HTML/CSS",
    "html/css": "HTML/CSS", "tailwind css": "HTML/CSS", "bootstrap": "HTML/CSS",
    "sass": "HTML/CSS", "less": "HTML/CSS",

    # JavaScript (JS-ecosystem frameworks with no dedicated dataset are
    # deliberately routed here rather than left unmapped, since they are
    # still fundamentally JavaScript question material)
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "JavaScript",
    "ts": "JavaScript", "es6": "JavaScript", "vanilla js": "JavaScript",
    "node.js": "JavaScript", "node": "JavaScript", "nodejs": "JavaScript",
    "express.js": "JavaScript", "express": "JavaScript",
    "next.js": "JavaScript", "nextjs": "JavaScript",

    # React
    "react": "React", "react.js": "React", "reactjs": "React",
    "redux": "React", "react native": "React",

    # DevOps
    "devops": "DevOps", "ci/cd": "DevOps", "jenkins": "DevOps", "docker": "DevOps",
    "kubernetes": "DevOps", "ansible": "DevOps", "terraform": "DevOps",
    "github actions": "DevOps", "helm": "DevOps",

    # AWS (cloud questions are only mapped here when AWS-specific; Azure/GCP
    # are intentionally left UNMAPPED rather than forced into an AWS-flavored
    # question set that would misrepresent the candidate's actual stack)
    "aws": "AWS", "amazon web services": "AWS", "ec2": "AWS", "s3": "AWS",
    "rds": "AWS", "lambda": "AWS", "iam": "AWS", "vpc": "AWS",

    # AI/ML
    "ai": "AI/ML", "ml": "AI/ML", "ai/ml": "AI/ML", "artificial intelligence": "AI/ML",
    "machine learning": "AI/ML", "deep learning": "AI/ML", "neural networks": "AI/ML",
    "pytorch": "AI/ML", "tensorflow": "AI/ML", "scikit-learn": "AI/ML",
    "nlp": "AI/ML", "computer vision": "AI/ML", "llm": "AI/ML", "llms": "AI/ML",
    "rag": "AI/ML", "prompt engineering": "AI/ML", "genai": "AI/ML",
    "data analytics": "AI/ML",

    # HR / behavioral
    "hr": "HR", "behavioral": "HR", "behavioural": "HR",

    # Aptitude
    "aptitude": "Aptitude", "quantitative aptitude": "Aptitude",
    "logical reasoning": "Aptitude",

    # Cybersecurity
    "cybersecurity": "Cybersecurity", "penetration testing": "Cybersecurity",
    "ethical hacking": "Cybersecurity", "cryptography": "Cybersecurity",
    "kali linux": "Cybersecurity", "security": "Cybersecurity",
}


def normalize_skill(raw_skill: str):
    """
    Map one resume-detected skill string to a canonical dataset skill.
    Returns the canonical skill name, or None if there is no dataset with
    reasonable topical coverage for it (never guesses).
    """
    if not raw_skill:
        return None
    key = str(raw_skill).strip().lower()

    # Exact canonical name already (case-insensitive)
    for canonical in CANONICAL_SKILLS:
        if canonical.lower() == key:
            return canonical

    return _ALIAS_MAP.get(key)


def map_resume_skills(skills):
    """
    Map a list of resume-detected skills to canonical dataset skills.

    Returns:
        {
            "mapped": {raw_skill: canonical_skill, ...},
            "unmapped": [raw_skill, ...],   # no reasonable dataset match
            "canonical_skills": [canonical_skill, ...]  # de-duplicated
        }
    """
    mapped = {}
    unmapped = []
    canonical_seen = []

    for s in skills or []:
        canonical = normalize_skill(s)
        if canonical:
            mapped[s] = canonical
            if canonical not in canonical_seen:
                canonical_seen.append(canonical)
        else:
            unmapped.append(s)

    return {
        "mapped": mapped,
        "unmapped": unmapped,
        "canonical_skills": canonical_seen,
    }


def has_dataset(canonical_skill: str) -> bool:
    return canonical_skill in CANONICAL_SKILLS


def dataset_filename(canonical_skill: str):
    return CANONICAL_SKILLS.get(canonical_skill)
