from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import uuid
import json
from datetime import datetime

from .models import ProjectRequest, ProjectEvaluationRequest, GeneratedContent, EvaluationResponse
from .firebase import firebase_client
from .ollama import ollama_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=GeneratedContent)
async def generate_project(request: ProjectRequest):
    """Generate project assignment using Ollama"""
    try:
        project_id = str(uuid.uuid4())
        
        prompt = f"""Generate a comprehensive project assignment:

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
Format as a clear, structured document."""
        
        content = await ollama_client.generate(
            prompt,
            system="You are an expert education project designer. Create detailed, practical project assignments that enhance student learning."
        )
        
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
                "duration_weeks": request.duration_weeks,
                "project_type": request.project_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_project(request: ProjectEvaluationRequest):
    """Evaluate project submission using Ollama"""
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
                
                # Analyze each code file
                code_prompt = f"""Analyze this {language} code:

Filename: {filename}

Code:
```{language}
{code}
```

Analyze for:
1. Code quality and organization
2. Best practices and conventions
3. Error handling
4. Performance considerations
5. Security issues
6. Documentation quality
7. Testing coverage (if applicable)

Return analysis in JSON format:
{{
  "quality_score": 0-100,
  "strengths": ["strength1", "strength2"],
  "issues": [
    {{"severity": "high|medium|low", "description": "...", "line": 0}}
  ],
  "suggestions": ["suggestion1", "suggestion2"],
  "best_practices_followed": ["practice1", "practice2"],
  "best_practices_violated": ["violation1", "violation2"]
}}"""

                analysis_response = await ollama_client.generate(
                    code_prompt,
                    system="You are an expert code reviewer. Provide detailed, constructive analysis."
                )
                
                # Parse code analysis
                try:
                    if "```json" in analysis_response:
                        analysis_response = analysis_response.split("```json")[1].split("```")[0]
                    elif "```" in analysis_response:
                        analysis_response = analysis_response.split("```")[1].split("```")[0]
                    
                    code_analysis[filename] = json.loads(analysis_response.strip())
                except Exception as e:
                    logger.warning(f"Failed to parse code analysis for {filename}: {e}")
                    code_analysis[filename] = {
                        "quality_score": 0,
                        "raw_analysis": analysis_response
                    }
        
        # Build evaluation prompt
        evaluation_prompt = f"""Evaluate this project submission comprehensively:

Original Project Requirements:
{project['content']}

Student Submission Description:
{request.submission_text}

Code Analysis Results:
{json.dumps(code_analysis, indent=2)}

Evaluate based on:
1. Completeness of requirements (30%)
2. Code quality and organization (25%)
3. Documentation (15%)
4. Testing and error handling (15%)
5. Innovation and creativity (10%)
6. Best practices (5%)

Provide detailed evaluation in JSON format:
{{
  "score": 0-100,
  "breakdown": {{
    "completeness": {{
      "score": 0-30,
      "feedback": "..."
    }},
    "code_quality": {{
      "score": 0-25,
      "feedback": "..."
    }},
    "documentation": {{
      "score": 0-15,
      "feedback": "..."
    }},
    "testing": {{
      "score": 0-15,
      "feedback": "..."
    }},
    "innovation": {{
      "score": 0-10,
      "feedback": "..."
    }},
    "best_practices": {{
      "score": 0-5,
      "feedback": "..."
    }}
  }},
  "overall_feedback": "Comprehensive feedback paragraph",
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "suggestions": ["suggestion1", "suggestion2"],
  "grade": "A|B|C|D|F"
}}"""
        
        evaluation_response = await ollama_client.generate(
            evaluation_prompt,
            system="You are an expert project evaluator. Provide fair, detailed, and constructive evaluation that helps students improve."
        )
        
        if not evaluation_response:
            raise HTTPException(status_code=500, detail="Failed to evaluate project")
        
        # Parse evaluation
        try:
            if "```json" in evaluation_response:
                evaluation_response = evaluation_response.split("```json")[1].split("```")[0]
            elif "```" in evaluation_response:
                evaluation_response = evaluation_response.split("```")[1].split("```")[0]
            
            eval_data = json.loads(evaluation_response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            # Fallback response
            eval_data = {
                "score": 70,
                "overall_feedback": evaluation_response[:500],
                "strengths": ["Submission received"],
                "improvements": ["See detailed feedback"],
                "grade": "C"
            }
        
        # Save evaluation
        submission_id = str(uuid.uuid4())
        firebase_client.save_document("project_submissions", submission_id, {
            "submission_id": submission_id,
            "project_id": request.project_id,
            "submission_text": request.submission_text,
            "code_files": request.code_files,
            "code_analysis": code_analysis,
            "evaluation": eval_data,
            "submitted_at": datetime.now()
        })
        
        return EvaluationResponse(
            score=eval_data.get("score", 0),
            feedback=eval_data.get("overall_feedback", ""),
            strengths=eval_data.get("strengths", []),
            improvements=eval_data.get("improvements", []),
            details={
                "breakdown": eval_data.get("breakdown", {}),
                "code_analysis": code_analysis,
                "grade": eval_data.get("grade", "N/A"),
                "suggestions": eval_data.get("suggestions", [])
            }
        )
        
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
async def list_projects(difficulty: str = None, project_type: str = None, limit: int = 20):
    """List projects with optional filtering"""
    try:
        filters = {}
        if difficulty:
            filters["difficulty"] = difficulty
        if project_type:
            filters["project_type"] = project_type
            
        projects = firebase_client.query_documents("projects", filters, limit=limit)
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{project_id}")
async def get_project_submissions(project_id: str, limit: int = 50):
    """Get all submissions for a project"""
    try:
        submissions = firebase_client.query_documents(
            "project_submissions",
            {"project_id": project_id},
            limit=limit
        )
        return {
            "project_id": project_id,
            "submissions": submissions,
            "count": len(submissions)
        }
    except Exception as e:
        logger.error(f"Error getting project submissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        firebase_client.delete_document("projects", project_id)
        return {"message": "Project deleted successfully", "project_id": project_id}
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/regenerate")
async def regenerate_project(project_id: str):
    """Regenerate project with similar requirements using Ollama"""
    try:
        # Get original project
        project = firebase_client.get_document("projects", project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        prompt = f"""Based on this existing project, generate a NEW project with similar difficulty and learning objectives but DIFFERENT implementation:

Original Project:
{project['content']}

Topic: {project['topic']}
Difficulty: {project['difficulty']}
Type: {project['project_type']}
Duration: {project['duration_weeks']} weeks

Create a completely different project that:
1. Tests the same skills and concepts
2. Uses a different domain/scenario
3. Has different technical requirements
4. Maintains the same difficulty level
5. Provides fresh learning experience

Generate the new project with the same structure as the original."""

        new_content = await ollama_client.generate(
            prompt,
            system="You are an expert at creating diverse project assignments. Generate unique projects that test the same skills differently."
        )
        
        if not new_content:
            raise HTTPException(status_code=500, detail="Failed to regenerate project")
        
        # Create new project
        new_project_id = str(uuid.uuid4())
        new_project_data = {
            "id": new_project_id,
            "topic": project['topic'],
            "difficulty": project['difficulty'],
            "project_type": project['project_type'],
            "duration_weeks": project['duration_weeks'],
            "content": new_content,
            "regenerated_from": project_id,
            "created_at": datetime.now()
        }
        
        firebase_client.save_document("projects", new_project_id, new_project_data)
        
        return {
            "message": "Project regenerated successfully",
            "original_project_id": project_id,
            "new_project_id": new_project_id,
            "content": new_content
        }
        
    except Exception as e:
        logger.error(f"Error regenerating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))