"""
Resume Intelligence Module
Extracts text from PDF resume and detects technical skills.
"""

import re
import pdfplumber

SKILL_TAXONOMY = {
    "Python":           ["python","django","flask","fastapi","pandas","numpy","scipy","pytorch","tensorflow","pyspark"],
    "JavaScript":       ["javascript","nodejs","node.js","react","reactjs","vue","angular","typescript","express","next.js"],
    "Java":             ["java","spring","spring boot","hibernate","maven","gradle","j2ee"],
    "C++":              ["c++","cpp","stl","boost","opengl"],
    "C":                ["c programming","embedded c","c language","c99"],
    "Machine Learning": ["machine learning","scikit-learn","sklearn","random forest","xgboost","gradient boosting","svm","naive bayes"],
    "Deep Learning":    ["deep learning","neural network","cnn","rnn","lstm","transformer","bert","keras"],
    "Data Structures":  ["data structures","algorithms","dsa","linked list","binary tree","dynamic programming","big o"],
    "Databases":        ["sql","mysql","postgresql","mongodb","redis","sqlite","oracle","nosql"],
    "Cloud":            ["aws","azure","gcp","google cloud","docker","kubernetes","terraform","devops","ci/cd"],
    "Data Science":     ["data science","data analysis","tableau","power bi","matplotlib","seaborn","jupyter","statistics"],
    "NLP":              ["nlp","natural language processing","spacy","nltk","huggingface","transformers"],
    "Computer Vision":  ["computer vision","opencv","image processing","object detection","yolo"],
    "Web Development":  ["html","css","bootstrap","tailwind","rest api","graphql","microservices"],
    "Cybersecurity":    ["cybersecurity","penetration testing","ethical hacking","cryptography","kali linux"],
    "Android":          ["android","kotlin","android studio","jetpack compose"],
    "iOS":              ["ios","swift","swiftui","xcode"],
    "Git":              ["git","github","gitlab","version control","bitbucket"],
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
