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
        
        prompt = f"""
        Generate 9 technical interview questions for a candidate with these skills: {skills_str}.
        Provide exactly:
        - 3 easy questions
        - 3 medium questions
        - 3 hard questions
        
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
    """Basic fallback questions based on skills."""
    fallback = []
    
    generic = [
        {"question": "Explain a challenging technical project you worked on.", "difficulty": "medium", "skill": "General"},
        {"question": "How do you handle debugging complex issues?", "difficulty": "easy", "skill": "General"},
        {"question": "Explain the importance of version control in team projects.", "difficulty": "easy", "skill": "Git"},
        {"question": "What is the difference between synchronous and asynchronous programming?", "difficulty": "medium", "skill": "General"},
        {"question": "How do you ensure your code is scalable and maintainable?", "difficulty": "hard", "skill": "Software Engineering"},
        {"question": "Explain the concept of Big O notation and why it matters.", "difficulty": "hard", "skill": "Algorithms"}
    ]
    
    if not skills:
        return generic

    for s in skills[:3]:
        fallback.append({"question": f"What are the core features of {s}?", "difficulty": "easy", "skill": s})
        fallback.append({"question": f"Explain a complex problem you solved using {s}.", "difficulty": "medium", "skill": s})
        fallback.append({"question": f"Discuss the performance implications of different data handling methods in {s}.", "difficulty": "hard", "skill": s})
        
    if len(fallback) < 9:
        fallback.extend(generic[:(9 - len(fallback))])
        
    return fallback
