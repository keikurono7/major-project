from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import uuid
import json
from datetime import datetime

from app.models import ProjectRequest, ProjectEvaluationRequest, GeneratedContent, EvaluationResponse
from app.firebase import firebase_client
from app.gemini import gemini_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=GeneratedContent)
async def generate_project(request: ProjectRequest):
    """Generate project assignment"""
    try:
        project_id = str(uuid.uuid4())
        
        prompt = f"""
        Generate a comprehensive project assignment:
        
        Topic: {request.topic}
        Difficulty: {request.difficulty}
        Type: {request.project_type}
        Duration: {request.duration_weeks} weeks
        
        Include:
        1. Project Title and Overview
        2. Learning Objectives
        3. Detailed Requirements
        4. Technical Specifications
        5. Deliverables
        6. Evaluation Criteria (with weightage)
        7. Milestones and Timeline
        8. Resources and References
        9. Bonus/Advanced Features (optional)
        
        Make it suitable for {request.difficulty} level students.
        """
        
        content = gemini_client.generate_content(prompt)
        if not content:
            raise HTTPException(status_code=500, detail="Failed to generate project")
        
        # Save to Firebase
        project_data = {
            "id": project_id,
            "topic": request.topic,
            "difficulty": request.difficulty,
            "project_type": request.project_type,
            "duration_weeks": request.duration_weeks,
            "content": content,
            "created_at": datetime.now()
        }
        
        firebase_client.save_document("projects", project_id, project_data)
        
        return GeneratedContent(
            id=project_id,
            content=content,
            metadata={
                "topic": request.topic,
                "difficulty": request.difficulty,
                "duration_weeks": request.duration_weeks
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_project(request: ProjectEvaluationRequest):
    """Evaluate project submission"""
    try:
        # Get original project
        project = firebase_client.get_document("projects", request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Analyze code if provided
        code_analysis = {}
        if request.code_files:
            for filename, code in request.code_files.items():
                language = filename.split('.')[-1]
                analysis = gemini_client.analyze_code(code, language)
                if analysis:
                    code_analysis[filename] = analysis
        
        # Build evaluation prompt
        prompt = f"""
        Evaluate this project submission:
        
        Original Project:
        {project['content']}
        
        Student Submission:
        {request.submission_text}
        
        Code Analysis:
        {json.dumps(code_analysis, indent=2)}
        
        Evaluate based on:
        1. Completeness of requirements
        2. Code quality and organization
        3. Documentation
        4. Testing and error handling
        5. Innovation and creativity
        6. Best practices
        
        Provide:
        - Overall score (0-100)
        - Detailed feedback for each criterion
        - Strengths
        - Areas for improvement
        - Suggestions for enhancement
        
        Return in JSON format.
        """
        
        evaluation = gemini_client.generate_content(prompt)
        if not evaluation:
            raise HTTPException(status_code=500, detail="Failed to evaluate project")
        
        # Parse evaluation
        eval_data = json.loads(evaluation)
        
        # Save evaluation
        submission_id = str(uuid.uuid4())
        firebase_client.save_document("project_submissions", submission_id, {
            "project_id": request.project_id,
            "submission_text": request.submission_text,
            "code_files": request.code_files,
            "code_analysis": code_analysis,
            "evaluation": eval_data,
            "submitted_at": datetime.now()
        })
        
        return EvaluationResponse(
            score=eval_data.get("score", 0),
            feedback=eval_data.get("feedback", ""),
            strengths=eval_data.get("strengths", []),
            improvements=eval_data.get("improvements", []),
            details=code_analysis
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse evaluation")
    except Exception as e:
        logger.error(f"Error evaluating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get project by ID"""
    try:
        project = firebase_client.get_document("projects", project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_projects(difficulty: str = None, limit: int = 20):
    """List projects with optional filtering"""
    try:
        filters = {"difficulty": difficulty} if difficulty else {}
        projects = firebase_client.query_documents("projects", filters, limit=limit)
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))