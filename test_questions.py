import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from modules.question_engine import generate_questions
    print("Import successful")
    
    skills = ["Python", "Flask", "SQL"]
    questions = generate_questions(skills)
    print(f"Generated {len(questions)} questions:")
    for q in questions:
        print(f"- {q['difficulty']}: {q['question']}")
        
except Exception as e:
    print(f"Error: {e}")
