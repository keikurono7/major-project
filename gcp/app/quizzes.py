from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
import uuid
import json
from datetime import datetime

from .models import QuizRequest, GeneratedContent, EvaluationResponse
from .firebase import firebase_client
from .ollama import ollama_client  # Changed from gemini

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=GeneratedContent)
async def generate_quiz(request: QuizRequest):
    """Generate quiz based on topics"""
    try:
        quiz_id = str(uuid.uuid4())
        
        prompt = f"""
        Generate a quiz with these specifications:
        - Topics: {', '.join(request.topics)}
        - Number of questions: {request.num_questions}
        - Difficulty: {request.difficulty}
        - Question types: {', '.join(request.question_types)}
        
        Format as JSON with structure:
        {{
            "questions": [
                {{
                    "id": "q1",
                    "type": "mcq",
                    "question": "question text",
                    "options": ["a", "b", "c", "d"],
                    "correct_answer": "a",
                    "explanation": "why this is correct",
                    "points": 1
                }}
            ]
        }}
        
        Only return valid JSON, no additional text.
        """
        
        content = await ollama_client.generate_content(prompt)  # Changed to async
        if not content:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")
        
        # Extract JSON from response
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            quiz_data = json.loads(content[start:end])
        else:
            raise json.JSONDecodeError("No JSON found", content, 0)
        
        firebase_client.save_document("quizzes", quiz_id, {
            "id": quiz_id,
            "topics": request.topics,
            "difficulty": request.difficulty,
            "questions": quiz_data["questions"],
            "created_at": datetime.now()
        })
        
        return GeneratedContent(
            id=quiz_id,
            content=json.dumps(quiz_data, indent=2),
            metadata={"num_questions": len(quiz_data["questions"])}
        )
        
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=EvaluationResponse)
async def submit_quiz(quiz_id: str, answers: Dict[str, str]):
    """Submit and evaluate quiz answers"""
    try:
        quiz = firebase_client.get_document("quizzes", quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Evaluate answers
        total_points = 0
        max_points = 0
        feedback_items = []
        
        for question in quiz["questions"]:
            q_id = question["id"]
            max_points += question["points"]
            
            if q_id in answers:
                user_answer = answers[q_id].strip().lower()
                correct_answer = question["correct_answer"].strip().lower()
                
                if user_answer == correct_answer:
                    total_points += question["points"]
                    feedback_items.append(f"✓ {q_id}: Correct!")
                else:
                    feedback_items.append(
                        f"✗ {q_id}: Incorrect. Correct answer: {question['correct_answer']}. "
                        f"{question['explanation']}"
                    )
        
        score = (total_points / max_points * 100) if max_points > 0 else 0
        
        # Save submission
        submission_id = str(uuid.uuid4())
        firebase_client.save_document("quiz_submissions", submission_id, {
            "quiz_id": quiz_id,
            "answers": answers,
            "score": score,
            "total_points": total_points,
            "max_points": max_points,
            "submitted_at": datetime.now()
        })
        
        return EvaluationResponse(
            score=score,
            feedback=f"Score: {total_points}/{max_points} ({score:.1f}%)",
            strengths=[f for f in feedback_items if "✓" in f],
            improvements=[f for f in feedback_items if "✗" in f]
        )
        
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}")
async def get_quiz(quiz_id: str):
    """Get quiz by ID (without answers)"""
    try:
        quiz = firebase_client.get_document("quizzes", quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Remove correct answers from response
        questions = quiz["questions"]
        for q in questions:
            q.pop("correct_answer", None)
            q.pop("explanation", None)
        
        return {
            "id": quiz["id"],
            "topics": quiz["topics"],
            "difficulty": quiz["difficulty"],
            "questions": questions
        }
    except Exception as e:
        logger.error(f"Error getting quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))