"""
Resume Intelligence Module
Extracts text from PDF resume and detects all technical skills under skills sections.
"""

import os
import re
import json
import unicodedata

KNOWN_SPECIFIC_SKILLS = [
    # Languages
    "Python", "Java", "C++", "C#", "C", "JavaScript", "TypeScript", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "SQL",
    # Frontend & Web
    "React.js", "React", "Next.js", "Vue.js", "Angular", "HTML", "CSS", "Tailwind CSS", "Bootstrap", "Redux", "Web Development",
    # Backend
    "FastAPI", "Flask", "Node.js", "Express.js", "Django", "Spring Boot", "GraphQL", "REST APIs", "Microservices",
    # Databases
    "MongoDB", "MySQL", "PostgreSQL", "SQLite", "Redis", "Oracle", "Cassandra", "DynamoDB", "DBMS",
    # AI / ML / Data
    "TensorFlow", "PyTorch", "OpenCV", "Scikit-Learn", "NLP", "Machine Learning", "Deep Learning", "Data Analytics", "Pandas", "NumPy", "GenAI", "LLMs", "RAG", "Prompt Engineering", "Computer Vision",
    # Cloud & DevOps
    "AWS", "Azure", "Docker", "Kubernetes", "Git & GitHub", "Git", "GitHub", "Terraform", "CI/CD", "Jenkins", "Linux", "Ansible", "Helm",
    # Core
    "DSA", "Data Structures", "Algorithms", "Cybersecurity", "System Design", "Agile"
]

SKILL_TAXONOMY = {
    "Python":           ["python", "django", "flask", "fastapi", "pandas", "numpy", "scipy"],
    "Java":             ["java", "spring", "spring boot", "hibernate", "maven", "gradle", "j2ee"],
    "C":                ["c programming", "embedded c", "c language", "c99"],
    "C++":              ["c++", "cpp", "stl", "boost", "opengl"],
    "DSA":              ["data structures", "algorithms", "dsa", "linked list", "binary tree", "dynamic programming", "graphs", "sorting", "searching", "big o"],
    "DBMS":             ["dbms", "database management", "nosql", "mongodb", "postgresql", "mysql", "oracle"],
    "OS":               ["operating system", "os", "linux", "unix", "windows administration", "shell scripting"],
    "CN":               ["computer networks", "networking", "tcp/ip", "dns", "http", "routing", "switching", "ip addressing"],
    "SQL":              ["sql", "sqlite", "mysql", "postgresql", "pl/sql", "t-sql"],
    "HTML/CSS":         ["html", "css", "html5", "css3", "bootstrap", "tailwind", "sass", "less"],
    "JavaScript":       ["javascript", "js", "typescript", "ts", "es6", "vanilla js"],
    "React":            ["react", "reactjs", "next.js", "nextjs", "redux", "react native"],
    "DevOps":           ["devops", "ci/cd", "jenkins", "docker", "kubernetes", "ansible", "terraform", "github actions"],
    "AWS":              ["aws", "amazon web services", "ec2", "s3", "rds", "lambda", "iam", "vpc"],
    "AI/ML":            ["ai", "ml", "artificial intelligence", "machine learning", "deep learning", "neural networks", "pytorch", "tensorflow", "scikit-learn"],
    "Cybersecurity":    ["cybersecurity", "penetration testing", "ethical hacking", "cryptography", "kali linux"]
}


def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"[ResumeParser] pdfplumber error: {e}")

    # Fallback to pdfminer if text is sparse
    if len(text.strip()) < 30:
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            t = pdfminer_extract(path)
            if t:
                text += "\n" + t
        except Exception as e2:
            print(f"[ResumeParser] pdfminer fallback error: {e2}")

    text = unicodedata.normalize("NFKD", text)
    return text.strip()


def extract_skills_from_resume(path: str) -> list:
    raw = extract_text_from_pdf(path)
    if not raw:
        return []

    found = []

    # 1. Parse text directly under "Technical Skills" / "Skills" headers
    section_skills = _extract_skills_from_section(raw)
    found.extend(section_skills)

    # 2. Match known specific skills across full document
    norm = raw.lower()
    for skill in KNOWN_SPECIFIC_SKILLS:
        pattern = r'(?:\b|_)' + re.escape(skill.lower()) + r'(?:\b|_)'
        if "+" in skill or "." in skill or "&" in skill or "/" in skill:
            pattern = re.escape(skill.lower())
        if re.search(pattern, norm):
            found.append(skill)

    # 3. Fallback to category taxonomy if skills are sparse
    if len(found) < 3:
        for skill, keywords in SKILL_TAXONOMY.items():
            for kw in keywords:
                pattern = r'(?:\b|_)' + re.escape(kw) + r'(?:\b|_)'
                if kw in ["c++", "c/c++", "next.js", "node.js", "ci/cd"]:
                    pattern = re.escape(kw)
                if re.search(pattern, norm):
                    found.append(skill)
                    break

    # Clean & deduplicate skills
    seen = set()
    final_skills = []
    for s in found:
        formatted = _format_skill_name(s)
        if formatted and formatted.lower() not in seen and len(formatted) >= 2:
            # Filter duplicates like Git vs Git & GitHub
            if formatted == "Git" and "Git & GitHub" in seen:
                continue
            if formatted == "GitHub" and "Git & GitHub" in seen:
                continue
            seen.add(formatted.lower())
            final_skills.append(formatted)

    print(f"[ResumeParser] Skills detected ({len(final_skills)}): {final_skills}")
    return final_skills


def _extract_skills_from_section(text: str) -> list:
    lines = text.split("\n")
    in_skills_section = False
    items = []

    skill_headers = [
        "technical skills", "skills", "technologies", "tools & technologies",
        "core competencies", "skill set", "technical proficiency", "key skills",
        "skills & technologies", "technical expertise"
    ]
    stop_headers = [
        "projects", "experience", "work experience", "education", "certifications",
        "achievements", "publications", "personal details", "declaration", "interests"
    ]

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        lower_line = clean_line.lower()

        if any(h in lower_line for h in skill_headers) and len(clean_line) < 45:
            in_skills_section = True
            if ":" in clean_line:
                after_colon = clean_line.split(":", 1)[1]
                _parse_line_items(after_colon, items)
            continue

        if in_skills_section and any(sh in lower_line for sh in stop_headers) and len(clean_line) < 45:
            in_skills_section = False
            break

        if in_skills_section:
            _parse_line_items(clean_line, items)

    return items


def _parse_line_items(line: str, out_list: list):
    if ":" in line:
        line = line.split(":", 1)[1]

    parts = re.split(r'[,|•*;\n]', line)
    for part in parts:
        clean = part.strip()
        clean = re.sub(r'\(.*?\)', '', clean).strip()
        clean = re.sub(r'^[-–—•*\s]+', '', clean).strip()
        if clean and len(clean) >= 2 and len(clean) <= 35:
            if clean.lower() not in ["languages", "frontend", "backend", "databases", "genai", "devops", "tools", "frameworks", "libraries"]:
                out_list.append(clean)


def _format_skill_name(s: str) -> str:
    known = {
        "python": "Python", "java": "Java", "c++": "C++", "c": "C", "javascript": "JavaScript",
        "js": "JavaScript", "typescript": "TypeScript", "ts": "TypeScript", "sql": "SQL",
        "react": "React", "react.js": "React.js", "next.js": "Next.js", "vue.js": "Vue.js",
        "node.js": "Node.js", "express": "Express.js", "express.js": "Express.js", "fastapi": "FastAPI",
        "flask": "Flask", "mongodb": "MongoDB", "mysql": "MySQL", "postgresql": "PostgreSQL",
        "aws": "AWS", "azure": "Azure", "docker": "Docker", "kubernetes": "Kubernetes",
        "git": "Git", "github": "GitHub", "git & github": "Git & GitHub", "rest api": "REST APIs",
        "rest apis": "REST APIs", "nlp": "NLP", "llm": "LLMs", "llms": "LLMs", "rag": "RAG",
        "ai": "AI/ML", "ml": "Machine Learning", "machine learning": "Machine Learning",
        "dsa": "DSA", "html": "HTML", "css": "CSS", "ci/cd": "CI/CD", "jenkins": "Jenkins",
        "terraform": "Terraform", "linux": "Linux", "postman": "Postman", "vs code": "VS Code"
    }
    return known.get(s.lower(), s.strip().title())


def extract_candidate_name(path: str) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            lines = [l.strip() for l in (pdf.pages[0].extract_text() or "").split("\n") if l.strip()]
            return lines[0] if lines else "Candidate"
    except:
        return "Candidate"


def analyze_resume_data(path: str) -> dict:
    raw_text = extract_text_from_pdf(path)
    skills = extract_skills_from_resume(path)

    api_key = os.environ.get("GROQ_API_KEY")
    if api_key and raw_text:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = f"""
            Analyze the following resume text and provide a structured JSON assessment.
            Resume text:
            {raw_text[:3000]}
            
            Provide exactly the following JSON structure:
            {{
                "score": 85,
                "ats_score": 80,
                "detected_skills": {json.dumps(skills)},
                "career_paths": ["Full Stack Developer", "Data Scientist"],
                "strengths": ["Strong background in software engineering"],
                "improvements": ["Detail your project metrics"],
                "formatting_score": 90,
                "formatting_feedback": "Resume is well structured."
            }}
            Return ONLY valid JSON.
            """
            
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter and ATS parser. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            response_text = completion.choices[0].message.content.strip()
            
            if "{" in response_text and "}" in response_text:
                start_index = response_text.find("{")
                end_index = response_text.rfind("}") + 1
                response_text = response_text[start_index:end_index]
                
            analysis = json.loads(response_text)
            analysis["detected_skills"] = skills
            return analysis
        except Exception as e:
            print(f"[ERROR] Groq resume analysis failed: {e}")

    score = min(50 + len(skills) * 5, 95)
    ats_score = min(55 + len(skills) * 4, 92)
    formatting_score = 80 if len(raw_text) > 100 else 40

    career_paths = ["Software Engineer", "Full Stack Developer"]
    strengths = [f"Found {len(skills)} core technical skills in profile.", "Clean section headings and readable PDF format."]
    improvements = ["Include more quantifiable metrics in your experience.", "Add more cloud/deployment platforms if applicable."]

    return {
        "score": score,
        "ats_score": ats_score,
        "detected_skills": skills,
        "career_paths": career_paths,
        "strengths": strengths,
        "improvements": improvements,
        "formatting_score": formatting_score,
        "formatting_feedback": "Layout parsed correctly."
    }
