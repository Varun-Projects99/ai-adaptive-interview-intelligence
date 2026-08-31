import os
import json
import random
from groq import Groq

def generate_questions(skills, lang="en", personality="professional"):
    """
    Initial question generation from AI (Groq llama3-8b-8192)
    based on resume skills. Generates a balanced set of questions.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[WARN] GROQ_API_KEY not found. Falling back to basic questions.")
        return get_fallback_questions(skills, lang=lang)

    lang_name = "English"

    try:
        client = Groq(api_key=api_key)
        
        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
        
        if "HR" in skills or "Behavioral" in skills:
            prompt = f"""
            Generate exactly 24 behavioral, situational, or HR interview questions (e.g., STAR method, leadership, problem solving, teamwork, conflicts, strengths/weaknesses).
            Make sure to write the questions in the {lang_name} language (using native {lang_name} script, e.g. Devanagari for Hindi, Kannada script for Kannada).
            Adopt a {personality} interviewer tone.
            Provide exactly:
            - 8 easy questions
            - 8 medium questions
            - 8 hard questions
            
            Return ONLY a JSON list of objects. Each object MUST have "question", "difficulty", and "skill" keys.
            The "skill" key should be "Behavioral".
            Example Format:
            [
              {{"question": "Describe a time you faced a conflict with a coworker and how you resolved it.", "difficulty": "medium", "skill": "Behavioral"}}
            ]
            """
        else:
            prompt = f"""
            Generate exactly 24 technical interview questions for a candidate with these skills: {skills_str}.
            Make sure to generate questions covering ALL the listed skills.
            Make sure to write the questions in the {lang_name} language (using native {lang_name} script, e.g. Devanagari for Hindi, Kannada script for Kannada).
            Adopt a {personality} interviewer tone.
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
        return get_fallback_questions(skills, lang=lang)

def get_next_question(session):
    """
    Adaptive Decision Engine: Dynamically determines the highest-information skill/topic
    to target, determines the difficulty based on candidate score, prevents repetition,
    and returns a tailored question.
    """
    try:
        from modules.adaptive_engine import (
            select_next_topic, 
            generate_adaptive_question, 
            should_interview_finish, 
            initialize_adaptive_state,
            are_questions_similar
        )
        
        user_id = session.get("user_id")
        initialize_adaptive_state(session, user_id=user_id)
        
        # Check if interview has reached sufficient confidence to finish early
        if should_interview_finish(session):
            print("[AdaptiveEngine] Decision: Sufficient confidence achieved. Finishing interview.")
            return None
            
        # Select next skill/topic and difficulty level using our formula
        target_skill, target_difficulty, reason = select_next_topic(session)
        print(f"[AdaptiveEngine] Next target skill: {target_skill} ({target_difficulty}) | Reason: {reason}")
        
        # Generate or load fallback question dynamically
        q_text = generate_adaptive_question(session, target_skill, target_difficulty, user_id=user_id)
        
        # Ensure it is unique and format it
        q = {
            "question": q_text,
            "skill": target_skill,
            "difficulty": target_difficulty,
            "reason": reason
        }
        
        # Sync indices and target difficulty
        session["current_difficulty"] = target_difficulty
        session["current_index"] = len(session.get("answers", []))
        
        # Save to session questions history log
        if not session.get("questions"):
            session["questions"] = []
        
        # Avoid duplicate entries in the questions list
        if not any(are_questions_similar(q["question"], x["question"]) for x in session["questions"]):
            session["questions"].append(q)
            
        return q
        
    except Exception as e:
        print(f"[ERROR] Adaptive Engine failed in get_next_question: {e}. Falling back to default question selector.")
        # Default fallback logic
        all_qs = session.get("questions", [])
        ans_qs = {a["question"] for a in session.get("answers", [])}
        target_diff = session.get("current_difficulty", "easy")

        candidates = [q for q in all_qs if q["difficulty"].lower() == target_diff.lower() and q["question"] not in ans_qs]
        if not candidates:
            candidates = [q for q in all_qs if q["question"] not in ans_qs]
        if not candidates:
            return None
            
        q = candidates[0]
        session["current_index"] = len(session.get("answers", []))
        return q

def get_fallback_questions(skills, lang="en"):
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
        final_questions = [
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
        
    # Translate questions on generation if target language is Hindi or Kannada
    if lang in ["hi", "kn"]:
        print(f"[Questions] Translating question set to {lang}...")
        for q in final_questions:
            q["question"] = translate_text(q["question"], lang)

    random.shuffle(final_questions)
    return final_questions


def translate_text(text, target_lang):
    """Translates an English interview question to Hindi or Kannada using free MyMemory Translation API with fallback."""
    import urllib.parse
    import requests

    lang_code = "hi" if target_lang == "hi" else "kn"
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{lang_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.ok:
            data = res.json()
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated:
                print(f"[Translation] Translated successfully via MyMemory API.")
                return translated
    except Exception as e:
        print(f"[Translation] MyMemory Translation API failed: {e}")

    api_key_ant = os.environ.get("ANTHROPIC_API_KEY")
    api_key_groq = os.environ.get("GROQ_API_KEY")
    
    lang_name = "Hindi" if target_lang == "hi" else "Kannada"
    prompt = f"Translate the following interview question into {lang_name}. Return ONLY the translated question text and nothing else.\nQuestion: {text}"
    
    use_groq = True
    if api_key_ant and "your_anthropic_api_key_here" not in api_key_ant:
        use_groq = False
        
    try:
        if not use_groq:
            import anthropic
            ant_client = anthropic.Anthropic(api_key=api_key_ant)
            res = ant_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.content[0].text.strip()
        elif api_key_groq:
            from groq import Groq
            groq_client = Groq(api_key=api_key_groq)
            completion = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Translation] Fallback translation to {lang_name} failed: {e}")
        
    return ""
