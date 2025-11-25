from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import uuid
from datetime import datetime

from app.models import AssignmentRequest, GeneratedContent, EvaluationResponse
from app.firebase import firebase_client
from app.ollama import ollama_client  # Changed from gemini

router = APIRouter()
logger = logging.getLogger(__name__)

# ============= API Endpoints =============

@router.post("/generate", response_model=GeneratedContent)
async def generate_assignment(request: AssignmentRequest):
    """Generate assignments based on topics"""
    try:
        assignment_id = str(uuid.uuid4())
        
        # Build prompt
        prompt = f"""
        Generate a comprehensive assignment with the following requirements:
        - Topics: {', '.join(request.topics)}
        - Difficulty: {request.difficulty}
        - Number of questions: {request.num_questions}
        - Include coding: {request.include_coding}
        
        Format the assignment with:
        1. Clear question numbers
        2. Specific instructions for each question
        3. Expected output format
        {'4. Include coding problems with sample inputs/outputs' if request.include_coding else ''}
        
        Make it educational and challenging at {request.difficulty} level.
        """
        
        # Generate content
        content = await ollama_client.generate_content(prompt)  # Changed to async
        if not content:
            raise HTTPException(status_code=500, detail="Failed to generate assignment")
        
        # Save to Firebase
        assignment_data = {
            "id": assignment_id,
            "topics": request.topics,
            "difficulty": request.difficulty,
            "num_questions": request.num_questions,
            "content": content,
            "created_at": datetime.now(),
            "type": "assignment"
        }
        
        firebase_client.save_document("assignments", assignment_id, assignment_data)
        
        return GeneratedContent(
            id=assignment_id,
            content=content,
            metadata={"topics": request.topics, "difficulty": request.difficulty}
        )
        
    except Exception as e:
        logger.error(f"Error generating assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_assignment(assignment_id: str, answers: Dict[str, str]):
    """Evaluate student assignment submission"""
    try:
        # Get original assignment
        assignment = firebase_client.get_document("assignments", assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Build evaluation prompt
        prompt = f"""
        Evaluate this assignment submission:
        
        Original Assignment:
        {assignment['content']}
        
        Student Answers:
        {answers}
        
        Provide evaluation in JSON format:
        {{
            "score": <0-100>,
            "feedback": "detailed feedback",
            "strengths": ["strength1", "strength2"],
            "improvements": ["improvement1", "improvement2"]
        }}
        
        Only return valid JSON.
        """
        
        # Get evaluation
        evaluation = await ollama_client.generate_content(prompt)
        if not evaluation:
            raise HTTPException(status_code=500, detail="Failed to evaluate assignment")
        
        # Parse and save evaluation
        import json
        # Extract JSON from response
        start = evaluation.find('{')
        end = evaluation.rfind('}') + 1
        if start != -1 and end > start:
            eval_data = json.loads(evaluation[start:end])
        else:
            raise json.JSONDecodeError("No JSON found", evaluation, 0)
        
        submission_id = str(uuid.uuid4())
        firebase_client.save_document("submissions", submission_id, {
            "assignment_id": assignment_id,
            "answers": answers,
            "evaluation": eval_data,
            "submitted_at": datetime.now()
        })
        
        return EvaluationResponse(
            score=eval_data.get("score", 0),
            feedback=eval_data.get("feedback", ""),
            strengths=eval_data.get("strengths", []),
            improvements=eval_data.get("improvements", [])
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse evaluation")
    except Exception as e:
        logger.error(f"Error evaluating assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}")
async def get_assignment(assignment_id: str):
    """Get assignment by ID"""
    try:
        assignment = firebase_client.get_document("assignments", assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except Exception as e:
        logger.error(f"Error getting assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))