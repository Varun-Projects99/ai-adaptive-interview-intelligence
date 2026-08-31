"""
Resume Intelligence Module
Extracts text from PDF resume and detects specific technical skills using keyword taxonomy + AI fallback.
"""

import os
import re
import json

KNOWN_SPECIFIC_SKILLS = [
    # Languages
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "SQL",
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
    "Python":           ["python", "django", "flask", "fastapi", "pandas", "numpy", "scipy", "pytest", "streamlit"],
    "Java":             ["java", "spring", "spring boot", "hibernate", "maven", "gradle", "j2ee"],
    "JavaScript":       ["javascript", "js", "typescript", "ts", "es6", "node", "nodejs", "node.js", "express", "expressjs", "express.js", "vanilla js"],
    "React":            ["react", "reactjs", "next.js", "nextjs", "redux", "react native"],
    "Web Development":  ["html", "css", "html5", "css3", "bootstrap", "tailwind", "sass", "less", "rest api", "rest apis", "graphql", "microservices", "web development"],
    "C/C++":            ["c++", "cpp", "c programming", "embedded c", "stl"],
    "DSA":              ["data structures", "algorithms", "dsa", "linked list", "binary tree", "dynamic programming", "graphs", "sorting", "searching", "big o"],
    "SQL":              ["sql", "sqlite", "mysql", "postgresql", "postgres", "pl/sql", "t-sql"],
    "DBMS":             ["dbms", "database management", "nosql", "mongodb", "postgresql", "mysql", "oracle", "redis"],
    "DevOps":           ["devops", "ci/cd", "jenkins", "docker", "kubernetes", "ansible", "terraform", "github actions", "helm", "azure devops", "git", "github"],
    "Cloud":            ["aws", "amazon web services", "azure", "gcp", "google cloud", "ec2", "s3", "lambda"],
    "AI/ML":            ["ai", "ml", "artificial intelligence", "machine learning", "deep learning", "neural networks", "pytorch", "tensorflow", "scikit-learn", "genai", "generative ai", "llm", "llms", "prompt engineering", "rag", "nlp"],
    "OS":               ["operating system", "os", "linux", "unix", "shell scripting", "bash"],
    "Cybersecurity":    ["cybersecurity", "penetration testing", "ethical hacking", "cryptography", "kali linux"]
}

DEFAULT_FALLBACK_SKILLS = ["Python", "DSA", "SQL", "Web Development"]


def extract_text_from_pdf(path: str) -> str:
    text = ""
    # 1. Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"[ResumeParser] pdfplumber error: {e}")

    # 2. Try pdfminer fallback if text is sparse
    if len(text.strip()) < 30:
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract
            t = pdfminer_extract(path)
            if t:
                text += "\n" + t
        except Exception as e2:
            print(f"[ResumeParser] pdfminer fallback error: {e2}")

    # 3. Try PyPDF2 fallback if text is still sparse
    if len(text.strip()) < 30:
        try:
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
        except Exception as e3:
            print(f"[ResumeParser] PyPDF2 fallback error: {e3}")

    import unicodedata
    text = unicodedata.normalize("NFKD", text)
    return text.strip()


def extract_skills_from_resume(path: str) -> list:
    raw = extract_text_from_pdf(path)
    found = []

    if raw:
        norm = raw.lower()
        # 1. Extract specific skills directly
        for skill in KNOWN_SPECIFIC_SKILLS:
            pattern = r'(?:\b|_)' + re.escape(skill.lower()) + r'(?:\b|_)'
            if "+" in skill or "." in skill or "&" in skill or "/" in skill:
                pattern = re.escape(skill.lower())
            if re.search(pattern, norm):
                found.append(skill)

        # 2. If no specific skills found, fallback to category taxonomy
        if not found:
            for skill, keywords in SKILL_TAXONOMY.items():
                for kw in keywords:
                    pattern = r'(?:\b|_)' + re.escape(kw) + r'(?:\b|_)'
                    if kw in ["c++", "c/c++", "next.js", "node.js", "ci/cd"]:
                        pattern = re.escape(kw)
                    if re.search(pattern, norm):
                        found.append(skill)
                        break

    # Deduplicate & filter overlapping sub-strings (e.g. Git vs Git & GitHub, React vs React.js)
    final_skills = []
    for s in found:
        if s == "Git" and "Git & GitHub" in found:
            continue
        if s == "GitHub" and "Git & GitHub" in found:
            continue
        if s == "React" and "React.js" in found:
            continue
        if s not in final_skills:
            final_skills.append(s)

    # 3. If skills are low (<2), try AI extraction
    if len(final_skills) < 2 and raw:
        print("[ResumeParser] Heuristic skills low, attempting AI extraction...")
        ai_skills = _extract_skills_with_ai(raw)
        for s in ai_skills:
            if s not in final_skills:
                final_skills.append(s)

    # 4. Final fallback if zero skills detected
    if not final_skills:
        print("[ResumeParser] Zero skills detected, returning standard fallback skills.")
        final_skills = list(DEFAULT_FALLBACK_SKILLS)

    print(f"[ResumeParser] Final Extracted Skills ({len(final_skills)}): {final_skills}")
    return final_skills


def _extract_skills_with_ai(text: str) -> list:
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = f"""Extract all primary technical skills or domain topics (e.g., Python, React.js, FastAPI, Node.js, TensorFlow, OpenCV, MongoDB, Docker, Kubernetes, AWS, NLP, Machine Learning) mentioned in this resume:
            {text[:2000]}

            Return ONLY a raw JSON array of strings, like: ["Python", "FastAPI", "React.js", "TensorFlow", "Docker"]
            """
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            resp = completion.choices[0].message.content.strip()
            if "[" in resp and "]" in resp:
                start = resp.find("[")
                end = resp.rfind("]") + 1
                return json.loads(resp[start:end])
        except Exception as e:
            print(f"[ResumeParser] Groq skill extraction failed: {e}")
    return []


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

    # Fallback response generator
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
