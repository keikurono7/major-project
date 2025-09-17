import os
import re
import nltk
import numpy as np
from typing import List, Dict, Any, Optional
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from firebase_ops import get_all_subjects, get_subject_modules, get_module_topics, get_student_bkt_params, update_student_bkt_params
from pyBKT.models import Model

# Initialize NLTK for sentence tokenization
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Configuration
OLLAMA_MODEL = "phi3:mini"  # Use a lightweight model for quiz generation
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"  # Update to your Ollama server

def generate_topic_quiz(
    subject_name: str,
    module_name: str,
    topic_name: str,
    num_questions: int = 3,
    student_id: Optional[str] = None,
    topic_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a quiz for a topic with difficulty adjusted based on student mastery level.
    Pass Firestore topic_id to align BKT tracking with DB IDs.
    """
    difficulty = "medium"
    
    # Use Firestore topic_id if provided; otherwise derive a deterministic slug
    topic_key = topic_id or f"{subject_name}-{module_name}-{topic_name}".replace(" ", "_").lower()

    if student_id:
        bkt_params = get_student_bkt_params(student_id, topic_key)
        p_L = bkt_params.get("p_L", 0.0)
        if p_L < 0.3:
            difficulty = "easy"
        elif p_L < 0.7:
            difficulty = "medium"
        else:
            difficulty = "hard"
        print(f"Student mastery level: {p_L:.2f}, setting difficulty to: {difficulty}")
    
    context = f"Subject: {subject_name}\nModule: {module_name}\nTopic: {topic_name}"
    prompt = f"""
    Based on the following academic context:
    {context}
    
    Create exactly {num_questions} multiple-choice questions about "{topic_name}".
    Each question must have 4 options labeled A, B, C, and D, with only one correct answer.
    Also provide a brief explanation for why the correct answer is right.
    
    Ensure the questions are of {difficulty} difficulty.
    
    Format each question exactly like this:
    
    Q1. <question text>
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4
    Answer: <A/B/C/D>
    Explanation: <short explanation>
    
    Only return the questions in this format, nothing else.
    """
    try:
        llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        raw_output = llm.invoke(prompt)
        quiz_questions = parse_quiz_to_json(raw_output)
        if not quiz_questions:
            print(f"⚠️ Failed to generate quiz for {topic_name}, using backup method")
            quiz_questions = generate_backup_questions(topic_name)
        print(f"✅ Successfully generated {len(quiz_questions)} questions for {topic_name}")
        return {
            "topic": topic_name,
            "topic_id": topic_key,
            "subject": subject_name,
            "module": module_name,
            "questions": quiz_questions,
            "question_count": len(quiz_questions)
        }
    except Exception as e:
        print(f"❌ Error generating quiz: {str(e)}")
        return {
            "topic": topic_name,
            "topic_id": topic_key,
            "subject": subject_name,
            "module": module_name,
            "questions": generate_backup_questions(topic_name),
            "question_count": 1,
            "error": str(e)
        }


def parse_quiz_to_json(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse the raw text from the LLM into a structured quiz format.
    """
    quizzes = []
    
    # Split by question pattern
    question_blocks = re.split(r'Q\d+\.', raw_text)[1:]
    
    if not question_blocks:
        # Try alternative pattern if the first one didn't work
        question_blocks = re.split(r'\d+\.\s', raw_text)[1:]
    
    for block in question_blocks:
        block = block.strip()
        
        # Extract question text
        question = block.split('A)')[0].strip()
        
        # Extract options
        options = []
        option_matches = re.findall(r'([A-D]\))(.*?)(?=[A-D]\)|Answer:|$)', block, re.DOTALL)
        
        for label, text in option_matches:
            options.append(f"{label} {text.strip()}")
        
        # If we didn't find 4 options, skip this question
        if len(options) != 4:
            continue
        
        # Extract Answer
        answer_match = re.search(r'Answer:\s*([A-D])', block, flags=re.IGNORECASE)
        answer = answer_match.group(1).upper() if answer_match else ""

        # Extract Explanation
        exp_match = re.search(r'Explanation:\s*(.*)', block, flags=re.IGNORECASE | re.DOTALL)
        explanation = exp_match.group(1).strip() if exp_match else ""

        if question and len(options) == 4 and answer:
            quizzes.append({
                "question": question,
                "options": options,
                "answer": answer,
                "explanation": explanation
            })

    return quizzes


def generate_backup_questions(topic_name: str) -> List[Dict[str, Any]]:
    """Generate a simple backup question if main generation fails"""
    return [{
        "question": f"Which of the following best describes {topic_name}?",
        "options": [
            "A) A fundamental concept in this subject area",
            "B) An advanced application of prior theories",
            "C) A historical development in the field",
            "D) A specialized technique with limited applications"
        ],
        "answer": "A",
        "explanation": "This is a backup question generated when the primary generation failed."
    }]


def evaluate_quiz_response(
    student_id: str,
    topic_id: str,
    is_correct: bool
):
    """
    Update student knowledge model based on quiz response using BKT update equations.
    This version does NOT use the pyBKT library, which is not suited for single updates.
    """
    bkt_params = {} # Initialize in case the 'try' block fails early
    try:
        # 1. Get current BKT parameters from the database
        bkt_params = get_student_bkt_params(student_id, topic_id)
        p_L_prior = bkt_params.get("p_L", 0.0) # Prior knowledge
        p_G = bkt_params.get("p_G", 0.2)       # Guess probability
        p_S = bkt_params.get("p_S", 0.1)       # Slip probability
        p_T = bkt_params.get("p_T", 0.1)       # Learning rate (transition)

        print(f"Retrieved BKT params for {student_id} on {topic_id}: {bkt_params}")

        # 2. Update mastery based on the correctness of the answer
        if is_correct:
            # Student answered correctly. They either knew it and didn't slip,
            # or didn't know it and guessed correctly.
            p_L_posterior = (p_L_prior * (1 - p_S)) / (p_L_prior * (1 - p_S) + (1 - p_L_prior) * p_G)
        else:
            # Student answered incorrectly. They either knew it and slipped,
            # or didn't know it and didn't guess correctly.
            p_L_posterior = (p_L_prior * p_S) / (p_L_prior * p_S + (1 - p_L_prior) * (1 - p_G))

        # 3. Apply the learning rate to get the final mastery for the next state
        # The student has a chance to learn (transition) from the 'not-known' state.
        p_L_new = p_L_posterior + (1 - p_L_posterior) * p_T
        
        print(f"Prior mastery: {p_L_prior:.4f} -> Posterior: {p_L_posterior:.4f} -> New mastery: {p_L_new:.4f}")

        # 4. Update the new mastery level in the database
        bkt_params["p_L"] = p_L_new
        update_student_bkt_params(student_id, topic_id, bkt_params)
        print(f"✅ Updated BKT params saved to database: {bkt_params}")

        return bkt_params

    except Exception as e:
        import traceback
        print(f"❌ Error in evaluate_quiz_response: {e}")
        traceback.print_exc()

        # Return the original parameters to avoid a complete failure
        return bkt_params if bkt_params else {
            "p_L": 0.5, "p_L0": 0.5, "p_T": 0.1, "p_G": 0.2, "p_S": 0.1
        }


def generate_quiz_for_topic(student_id: str, topic_id: str, num_questions: int = 5) -> Optional[Dict[str, Any]]:
    """
    Wrapper used by main: resolve subject/module/topic names for a Firestore topic_id,
    then call generate_topic_quiz. Keeps main simple.
    """
    try:
        subjects = get_all_subjects()
        for subject in subjects:
            modules = get_subject_modules(subject["id"])
            for module in modules:
                topics = get_module_topics(subject["id"], module["id"])
                for topic in topics:
                    if topic["id"] == topic_id:
                        return generate_topic_quiz(
                            subject_name=subject["name"],
                            module_name=module["name"],
                            topic_name=topic["name"],
                            num_questions=num_questions,
                            student_id=student_id,
                            topic_id=topic_id,
                        )
        print(f"❌ Topic ID not found: {topic_id}")
        return None
    except Exception as e:
        print(f"❌ Error generating quiz for topic {topic_id}: {e}")
        return None