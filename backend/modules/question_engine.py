import os
import json
import random
from groq import Groq

def generate_questions(skills):
    """
    Initial question generation from AI (Groq llama3-8b-8192)
    based on resume skills. Generates a balanced set of questions.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[WARN] GROQ_API_KEY not found. Falling back to basic questions.")
        return get_fallback_questions(skills)

    try:
        client = Groq(api_key=api_key)
        
        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
        
        if "HR" in skills or "Behavioral" in skills:
            prompt = f"""
            Generate exactly 24 behavioral, situational, or HR interview questions (e.g., STAR method, leadership, problem solving, teamwork, conflicts, strengths/weaknesses).
            Provide exactly:
            - 8 easy questions (e.g., standard introduction/strengths)
            - 8 medium questions (e.g., situational conflict resolution or teamwork)
            - 8 hard questions (e.g., complex ethical dilemmas, prioritization under stress, or failure recovery)
            
            Return ONLY a JSON list of objects. Each object MUST have "question", "difficulty", and "skill" keys.
            The "skill" key should be "Behavioral".
            Example Format:
            [
              {{"question": "Describe a time you faced a conflict with a coworker and how you resolved it.", "difficulty": "medium", "skill": "Behavioral"}},
              {{"question": "What are your long-term career aspirations?", "difficulty": "easy", "skill": "Behavioral"}}
            ]
            """
        else:
            prompt = f"""
            Generate exactly 24 technical interview questions for a candidate with these skills: {skills_str}.
            Make sure to generate questions covering ALL the listed skills.
            Provide exactly:
            - 8 easy questions
            - 8 medium questions
            - 8 hard questions
            
            Return ONLY a JSON list of objects. Each object MUST have "question", "difficulty", and "skill" keys.
            The "skill" key should match one of the provided skills.
            Example Format:
            [
              {{"question": "What is a closure in JavaScript?", "difficulty": "easy", "skill": "JavaScript"}},
              {{"question": "Explain the difference between SQL and NoSQL.", "difficulty": "medium", "skill": "Databases"}}
            ]
            """

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer. You must only output valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        response_text = completion.choices[0].message.content.strip()
        
        if "[" in response_text and "]" in response_text:
            start_index = response_text.find("[")
            end_index = response_text.rfind("]") + 1
            response_text = response_text[start_index:end_index]
            
        questions = json.loads(response_text)
        
        if isinstance(questions, list) and len(questions) > 0:
            return questions
        else:
            raise ValueError("Invalid JSON format or empty list")

    except Exception as e:
        print(f"[ERROR] Groq API question generation failed: {e}")
        return get_fallback_questions(skills)

def get_next_question(session):
    """
    Returns the next question from the session based on current_difficulty.
    If no question matches current_difficulty, it falls back to others.
    """
    try:
        all_qs = session.get("questions", [])
        ans_qs = {a["question"] for a in session.get("answers", [])}
        target_diff = session.get("current_difficulty", "easy")

        # 1. Try to find a question with the target difficulty that hasn't been answered
        candidates = [q for q in all_qs if q["difficulty"].lower() == target_diff.lower() and q["question"] not in ans_qs]
        
        if not candidates:
            # 2. If none, try any unanswered question
            candidates = [q for q in all_qs if q["question"] not in ans_qs]
            
        if not candidates:
            return None
            
        # Return the first candidate and update session index (if used by frontend)
        # Note: app.py uses session["current_index"] to track position
        q = candidates[0]
        session["current_index"] = len(session.get("answers", []))
        return q

    except Exception as e:
        print(f"[ERROR] get_next_question: {e}")
        return None

def get_fallback_questions(skills):
    """Loads a balanced set of 24 questions covering ALL detected skills."""
    import os
    import json
    import random
    
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(modules_dir)
    workspace_dir = os.path.dirname(backend_dir)
    
    datasets_dir = os.path.join(workspace_dir, "datasets")
    if not os.path.exists(datasets_dir):
        datasets_dir = os.path.join(backend_dir, "datasets")
    
    DATASET_MAP = {
        "Python": "python.json",
        "Java": "java.json",
        "C": "c.json",
        "C++": "cpp.json",
        "DSA": "dsa.json",
        "DBMS": "dbms.json",
        "OS": "os.json",
        "CN": "cn.json",
        "SQL": "sql.json",
        "HTML/CSS": "html_css.json",
        "JavaScript": "javascript.json",
        "React": "react.json",
        "DevOps": "devops.json",
        "AWS": "aws.json",
        "AI/ML": "ai_ml.json",
        "HR": "hr.json",
        "Aptitude": "aptitude.json",
        "Cybersecurity": "cybersecurity.json"
    }
    
    # Deduplicate/filter valid skills
    matched_skills = [s for s in skills if s in DATASET_MAP]
    
    # If no valid skills found, load Aptitude, HR, and DSA questions
    if not matched_skills:
        matched_skills = ["Aptitude", "HR", "DSA"]
        
    questions_by_diff = {"easy": [], "medium": [], "hard": []}
    
    for skill in matched_skills:
        filename = DATASET_MAP.get(skill)
        if not filename:
            continue
        file_path = os.path.join(datasets_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    q_list = json.load(f)
                    for q in q_list:
                        diff = q.get("difficulty", "").lower()
                        if diff in questions_by_diff:
                            questions_by_diff[diff].append(q)
            except Exception as e:
                print(f"[WARN] Error loading dataset {filename}: {e}")
                
    # If we need padding, load from HR and Aptitude
    padding_skills = ["HR", "Aptitude"]
    for p_skill in padding_skills:
        filename = DATASET_MAP.get(p_skill)
        file_path = os.path.join(datasets_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    q_list = json.load(f)
                    for q in q_list:
                        diff = q.get("difficulty", "").lower()
                        if diff in questions_by_diff:
                            questions_by_diff[diff].append(q)
            except Exception as e:
                pass

    final_questions = []
    
    for diff in ["easy", "medium", "hard"]:
        qs = questions_by_diff[diff]
        # Deduplicate list of dicts based on question text
        seen = set()
        unique_qs = []
        for q in qs:
            if q["question"] not in seen:
                seen.add(q["question"])
                unique_qs.append(q)
                
        selected = []
        if len(unique_qs) >= 8:
            by_skill = {}
            for q in unique_qs:
                s = q["skill"]
                if s not in by_skill:
                    by_skill[s] = []
                by_skill[s].append(q)
                
            skill_list = list(by_skill.keys())
            while len(selected) < 8 and skill_list:
                for s in list(skill_list):
                    if by_skill[s]:
                        selected.append(by_skill[s].pop(random.randint(0, len(by_skill[s]) - 1)))
                        if len(selected) == 8:
                            break
                    else:
                        skill_list.remove(s)
            
            if len(selected) < 8:
                remaining_candidates = [q for q in unique_qs if q not in selected]
                if remaining_candidates:
                    selected.extend(random.sample(remaining_candidates, min(8 - len(selected), len(remaining_candidates))))
        else:
            selected = unique_qs
            
        final_questions.extend(selected)
        
    # Ensure exactly 24 questions in total
    all_flat_unique = []
    seen = set()
    for diff in ["easy", "medium", "hard"]:
        for q in questions_by_diff[diff]:
            if q["question"] not in seen:
                seen.add(q["question"])
                all_flat_unique.append(q)
                
    remaining = [q for q in all_flat_unique if q not in final_questions]
    while len(final_questions) < 24 and remaining:
        chosen = random.choice(remaining)
        final_questions.append(chosen)
        remaining.remove(chosen)
        
    # If we still failed to get 24 questions, fall back to a minimal hardcoded set
    if not final_questions:
        return [
            {"question": "Explain a challenging technical project you worked on.", "difficulty": "medium", "skill": "General"},
            {"question": "How do you handle debugging complex issues?", "difficulty": "easy", "skill": "General"},
            {"question": "What is the difference between synchronous and asynchronous programming?", "difficulty": "medium", "skill": "General"},
            {"question": "Explain the concept of Big O notation and why it matters.", "difficulty": "hard", "skill": "DSA"},
            {"question": "Tell me about a time you failed. What did you learn from the experience?", "difficulty": "medium", "skill": "HR"},
            {"question": "How do you handle prioritization when you have multiple urgent tasks?", "difficulty": "hard", "skill": "HR"},
            {"question": "Describe a time you faced a conflict with a coworker and how you resolved it.", "difficulty": "medium", "skill": "HR"},
            {"question": "What are your long-term career aspirations?", "difficulty": "easy", "skill": "HR"},
            {"question": "Why are you interested in this role and our company?", "difficulty": "easy", "skill": "HR"}
        ]
        
    random.shuffle(final_questions)
    return final_questions
