"""
Resume Intelligence Module
Extracts text from PDF resume and detects technical skills.
"""

import re
import pdfplumber

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
    "HR":               ["hr", "behavioral", "communication", "soft skills", "leadership", "teamwork", "management"],
    "Aptitude":         ["aptitude", "quantitative", "logical reasoning", "verbal", "analytical", "problem solving"],
    "Cybersecurity":    ["cybersecurity", "penetration testing", "ethical hacking", "cryptography", "kali linux"]
}


def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"[ResumeParser] PDF error: {e}")
    return text


def extract_skills_from_resume(path: str) -> list:
    raw  = extract_text_from_pdf(path)
    if not raw:
        return []

    norm = raw.lower()
    found = []

    for skill, keywords in SKILL_TAXONOMY.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', norm):
                found.append(skill)
                break

    # Deduplicate preserving order
    seen, unique = set(), []
    for s in found:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    print(f"[ResumeParser] Skills: {unique}")
    return unique


def extract_candidate_name(path: str) -> str:
    try:
        with pdfplumber.open(path) as pdf:
            lines = [l.strip() for l in (pdf.pages[0].extract_text() or "").split("\n") if l.strip()]
            return lines[0] if lines else "Candidate"
    except:
        return "Candidate"


import os
import json

def analyze_resume_data(path: str) -> dict:
    raw_text = extract_text_from_pdf(path)
    skills = extract_skills_from_resume(path)
    
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            prompt = f"""
            Analyze the following resume text and provide a structured JSON assessment.
            Resume text:
            {raw_text}
            
            Provide exactly the following JSON structure:
            {{
                "score": 85, // Overall score out of 100
                "ats_score": 80, // ATS friendly score out of 100
                "detected_skills": ["Python", "JavaScript", "SQL"], // Skills found
                "career_paths": ["Full Stack Developer", "Data Scientist"], // Suggested career paths (list of strings)
                "strengths": ["Strong background in backend development", "Proficient in database design"], // strengths (list of strings)
                "improvements": ["Add more cloud experience", "Detail your project metrics"], // areas of improvement (list of strings)
                "formatting_score": 90, // score for layout/formatting out of 100
                "formatting_feedback": "Resume is well structured but has too much text." // layout feedback
            }}
            Return ONLY the valid JSON block.
            """
            
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter and resume ATS parsing engine. You must output ONLY a valid JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            response_text = completion.choices[0].message.content.strip()
            
            if "{" in response_text and "}" in response_text:
                start_index = response_text.find("{")
                end_index = response_text.rfind("}") + 1
                response_text = response_text[start_index:end_index]
                
            analysis = json.loads(response_text)
            return analysis
        except Exception as e:
            print(f"[ERROR] Groq resume analysis failed: {e}")
            
    # Fallback response generator if Groq key is missing or fails:
    score = min(50 + len(skills) * 5, 95)
    ats_score = min(55 + len(skills) * 4, 92)
    formatting_score = 80 if len(raw_text) > 100 else 40
    
    career_paths = []
    if "Python" in skills or "Machine Learning" in skills or "Data Science" in skills:
        career_paths.append("Data Scientist / ML Engineer")
    if "JavaScript" in skills or "Web Development" in skills:
        career_paths.append("Full Stack Developer")
    if "Java" in skills or "C++" in skills or "Python" in skills:
        career_paths.append("Backend Software Engineer")
    if "Android" in skills or "iOS" in skills:
        career_paths.append("Mobile Application Developer")
    if not career_paths:
        career_paths.append("Software Engineer")
        
    strengths = [
        f"Found {len(skills)} core technical skills in the profile.",
        "Clear section headings and readable PDF format."
    ]
    
    improvements = [
        "Include more quantifiable metrics in your experience (e.g., 'improved performance by 20%').",
        "Add more cloud/deployment platforms (AWS/GCP/Docker) if applicable."
    ]
    if len(skills) < 5:
        improvements.append("Consider listing more relevant tools and languages in a dedicated Skills section.")
        
    return {
        "score": score,
        "ats_score": ats_score,
        "detected_skills": skills,
        "career_paths": career_paths,
        "strengths": strengths,
        "improvements": improvements,
        "formatting_score": formatting_score,
        "formatting_feedback": "Layout parsed correctly. Recommended to keep the format simple and clean for ATS search systems."
    }
