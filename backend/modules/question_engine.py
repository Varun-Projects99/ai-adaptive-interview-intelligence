import os
import json
import random
from groq import Groq

from modules import skill_mapper, question_bank


def generate_questions(skills, lang="en", personality="professional"):
    """
    DATASET-PRIMARY initial question pool builder (up to 24 questions).

    Order of operations (LLM is a FALLBACK, never the primary source, per
    project requirement):
      1. Map detected resume skills to canonical dataset-backed skills via
         modules/skill_mapper.py (only maps when there is reasonable
         topical evidence -- never guesses).
      2. Build the pool primarily from modules/question_bank.py / the local
         datasets, via get_fallback_questions() below (name kept for
         backward compatibility -- despite the name, this IS the dataset
         retrieval path, not a last-resort).
      3. The Groq LLM is only ever called to cover detected skills that
         have NO backing dataset at all (skill_mapper reports them
         "unmapped"). If every detected skill maps to a dataset, the LLM is
         not called at all for this step.

    Every returned question carries a "source" key ("dataset" or
    "llm_fallback") so this is auditable rather than just asserted.
    """
    mapping = skill_mapper.map_resume_skills(skills or [])
    canonical_skills = mapping["canonical_skills"]
    unmapped_skills = mapping["unmapped"]

    dataset_questions = get_fallback_questions(canonical_skills or (skills or []), lang=lang)
    for q in dataset_questions:
        q["source"] = "dataset"

    if not unmapped_skills:
        print(f"[Questions] Pool built entirely from local datasets "
              f"({len(dataset_questions)} questions, 0 LLM calls) for skills: {canonical_skills}")
        return dataset_questions

    print(f"[Questions] {len(unmapped_skills)} detected skill(s) have no local dataset "
          f"coverage ({unmapped_skills}) -> supplementing with LLM fallback for those only.")

    llm_questions = _generate_llm_questions_for_skills(unmapped_skills, lang=lang, personality=personality)
    for q in llm_questions:
        q["source"] = "llm_fallback"

    combined = dataset_questions + llm_questions
    random.shuffle(combined)
    return combined


def _generate_llm_questions_for_skills(skills, lang="en", personality="professional", max_questions=12):
    """
    LLM FALLBACK ONLY: generates a small supplemental set of questions for
    resume-detected skills that have no local dataset coverage at all (see
    generate_questions() above). Deliberately capped (max_questions) since
    this is meant to fill a genuine gap, not to be the primary source.
    Returns [] (never raises) if no API key is configured or the call
    fails -- the dataset-built portion of the pool is always sufficient on
    its own to run an interview.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print(f"[Questions] GROQ_API_KEY not configured -- skills {skills} will simply "
              f"not get dedicated questions in the initial pool (adaptive per-question "
              f"generation may still cover them later via the same LLM-fallback path).")
        return []

    lang_name = "English"
    if lang == "hi":
        lang_name = "Hindi"
    elif lang == "kn":
        lang_name = "Kannada"

    skills_str = ", ".join(skills)
    count = min(max_questions, max(6, len(skills) * 3))

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Generate exactly {count} technical interview questions covering ONLY these skills
        (which have no local question bank available): {skills_str}.
        Make sure to write the questions in the {lang_name} language (using native {lang_name} script,
        e.g. Devanagari for Hindi, Kannada script for Kannada).
        Adopt a {personality} interviewer tone.
        Spread the questions roughly evenly across easy, medium, and hard difficulty.

        Return ONLY a JSON list of objects. Each object MUST have "question", "difficulty", and "skill" keys.
        The "skill" key must be one of: {skills_str}.
        Example Format:
        [
          {{"question": "What is a closure in JavaScript?", "difficulty": "easy", "skill": "{skills[0]}"}}
        ]
        """
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer. You must only output valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        response_text = completion.choices[0].message.content.strip()
        if "[" in response_text and "]" in response_text:
            start_index = response_text.find("[")
            end_index = response_text.rfind("]") + 1
            response_text = response_text[start_index:end_index]

        questions = json.loads(response_text)
        if isinstance(questions, list) and len(questions) > 0:
            return questions
        return []
    except Exception as e:
        print(f"[WARN] LLM gap-fill question generation failed for {skills}: {e}")
        return []


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
        
        # Generate or load fallback question dynamically (dataset-primary,
        # LLM fallback -- see modules/adaptive_engine.generate_adaptive_question)
        q_text, q_source = generate_adaptive_question(session, target_skill, target_difficulty, user_id=user_id)
        
        # Ensure it is unique and format it
        q = {
            "question": q_text,
            "skill": target_skill,
            "difficulty": target_difficulty,
            "reason": reason,
            "source": q_source
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
    """
    Build a skill-balanced pool of up to 24 questions PRIMARILY from the
    local datasets (modules/question_bank.py).

    NOTE (bug fix, previously): this function used to always merge the
    *entire* HR + Aptitude datasets into the candidate pool "just in case
    padding was needed", even when the detected skills already had plenty
    of coverage -- which meant generic HR/Aptitude questions could leak
    into a pool for a candidate whose resume only listed e.g. Python and
    React. modules/question_bank.pool_for_skills() only pads with a
    skill's own dataset and reports a genuine shortfall instead of
    silently mixing in unrelated skills, so that padding bug cannot
    reoccur here.
    """
    matched_skills = [s for s in (skills or []) if skill_mapper.has_dataset(s)]

    if not matched_skills:
        # No recognized skill -> generic, clearly-labeled default pool.
        # This is NOT "inventing" a skill match; it is the documented
        # fallback for a resume with no dataset-backed skills at all.
        matched_skills = ["Aptitude", "HR", "DSA"]

    pool, shortfall = question_bank.pool_for_skills(matched_skills, target_total=24, per_difficulty=8)

    # Convert to the schema the rest of the app expects (string difficulty
    # label, not the internal int) -- matches the pre-existing public
    # contract of this function exactly.
    final_questions = [
        {"question": q["question"], "difficulty": q["difficulty_label"], "skill": q["skill"]}
        for q in pool
    ]

    if any(shortfall.values()):
        print(f"[Questions] Dataset pool short by {shortfall} for skills {matched_skills} "
              f"-- proceeding with {len(final_questions)}/24 dataset questions "
              f"(generate_questions() handles topping up unmapped skills via LLM separately).")

    # Absolute last resort: dataset directory itself unreadable/missing.
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
