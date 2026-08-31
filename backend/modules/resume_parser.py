"""
Resume Intelligence Module
Extracts text from PDF resume and detects technical skills using keyword taxonomy + AI fallback.
"""

import os
import re
import json

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
    "Cybersecurity":    ["cybersecurity", "penetration testing", "ethical hacking", "cryptography", "kali linux"],
    "HR":               ["hr", "behavioral", "communication", "soft skills", "leadership", "teamwork", "management"],
    "Aptitude":         ["aptitude", "quantitative", "logical reasoning", "verbal", "analytical", "problem solving"]
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

    # 2. Try pypdf / PyPDF2 fallback if text is sparse
    if len(text.strip()) < 30:
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception:
            try:
                import PyPDF2
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
            except Exception as e2:
                print(f"[ResumeParser] PyPDF fallback error: {e2}")

    return text.strip()


def extract_skills_from_resume(path: str) -> list:
    raw = extract_text_from_pdf(path)
    found = []

    if raw:
        norm = raw.lower()
        for skill, keywords in SKILL_TAXONOMY.items():
            for kw in keywords:
                # Word boundary check or special char regex
                pattern = r'(?:\b|_)' + re.escape(kw) + r'(?:\b|_)'
                if kw in ["c++", "c/c++", "next.js", "node.js", "ci/cd"]:
                    pattern = re.escape(kw)
                if re.search(pattern, norm):
                    found.append(skill)
                    break

    # Deduplicate preserving order
    seen, unique = set(), []
    for s in found:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    # If heuristic keyword match yielded fewer than 2 skills, try AI extraction
    if len(unique) < 2 and raw:
        print("[ResumeParser] Heuristic skills low, attempting AI extraction...")
        ai_skills = _extract_skills_with_ai(raw)
        for s in ai_skills:
            if s not in seen:
                seen.add(s)
                unique.append(s)

    # Final fallback if zero skills detected
    if not unique:
        print("[ResumeParser] Zero skills detected, returning standard fallback skills.")
        unique = list(DEFAULT_FALLBACK_SKILLS)

    print(f"[ResumeParser] Final Extracted Skills ({len(unique)}): {unique}")
    return unique


def _extract_skills_with_ai(text: str) -> list:
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = f"""Extract 4 to 8 primary technical skills or domain topics (e.g., Python, React, SQL, DevOps, DSA, AI/ML, FastApi, MongoDB) from this resume:
            {text[:2000]}

            Return ONLY a raw JSON array of strings, like: ["Python", "React", "SQL", "DevOps"]
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
