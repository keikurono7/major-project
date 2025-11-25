from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime

from .models import QuestionPaper, QuestionPaperRequest
from .firebase import firebase_client
from .ollama import ollama_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=QuestionPaper)
async def generate_question_paper(request: QuestionPaperRequest):
    """Generate a complete question paper using Ollama"""
    try:
        # Get syllabus
        syllabus_doc = firebase_client.get_document("syllabus", request.subject_id)
        if not syllabus_doc:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        
        # Build prompt
        prompt = f"""Generate a detailed question paper for {request.exam_type} examination.

Subject: {syllabus_doc.get('subject_name', 'Unknown Subject')}
Total Marks: {request.total_marks}
Duration: {request.duration_hours} hours
Difficulty Level: {request.difficulty}

Syllabus Content:
{syllabus_doc.get('content', '')}

Generate {request.num_questions} questions with the following structure:
- Mix of question types: MCQ, Short Answer, Long Answer, Problem-Solving
- Cover all modules/topics proportionally
- Include marks for each question
- Include difficulty level for each question
- Include bloom's taxonomy level for each question

Return the questions in this JSON format:
{{
  "questions": [
    {{
      "question_id": "Q1",
      "question_text": "...",
      "question_type": "mcq|short|long|problem",
      "marks": 5,
      "difficulty": "easy|medium|hard",
      "bloom_level": "remember|understand|apply|analyze|evaluate|create",
      "module": "Module 1",
      "topic": "Topic name",
      "options": ["A", "B", "C", "D"],  // only for MCQ
      "answer_key": "..."  // optional
    }}
  ]
}}"""

        # Generate using Ollama
        response = await ollama_client.generate(
            prompt,
            system="You are an expert education question paper generator. Generate high-quality, well-structured questions that properly assess student knowledge."
        )
        
        # Parse response
        import json
        try:
            # Try to extract JSON from response
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            questions_data = json.loads(response_text)
            questions = questions_data.get("questions", [])
        except Exception as e:
            logger.error(f"Error parsing Ollama response: {e}")
            # Fallback: try to parse the response as is
            questions = []
        
        if not questions:
            raise HTTPException(status_code=500, detail="Failed to generate questions")
        
        # Create question paper
        paper_id = str(uuid.uuid4())
        question_paper = QuestionPaper(
            paper_id=paper_id,
            subject_id=request.subject_id,
            exam_type=request.exam_type,
            total_marks=request.total_marks,
            duration_hours=request.duration_hours,
            questions=questions,
            created_at=datetime.now(),
            created_by=request.teacher_id
        )
        
        # Save to Firebase
        firebase_client.save_document("question_papers", paper_id, question_paper.dict())
        
        logger.info(f"Generated question paper {paper_id} with {len(questions)} questions")
        return question_paper
        
    except Exception as e:
        logger.error(f"Error generating question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_question_papers(subject_id: str = None, exam_type: str = None):
    """List all question papers with optional filters"""
    try:
        filters = {}
        if subject_id:
            filters["subject_id"] = subject_id
        if exam_type:
            filters["exam_type"] = exam_type
        
        papers = firebase_client.query_documents("question_papers", filters, limit=50)
        return {"papers": papers}
        
    except Exception as e:
        logger.error(f"Error listing question papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}")
async def get_question_paper(paper_id: str):
    """Get a specific question paper"""
    try:
        paper = firebase_client.get_document("question_papers", paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        return paper
        
    except Exception as e:
        logger.error(f"Error getting question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{paper_id}/regenerate-question")
async def regenerate_question(paper_id: str, question_id: str):
    """Regenerate a specific question using Ollama"""
    try:
        # Get paper
        paper = firebase_client.get_document("question_papers", paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        
        # Find question
        questions = paper.get("questions", [])
        question_index = next((i for i, q in enumerate(questions) if q["question_id"] == question_id), None)
        
        if question_index is None:
            raise HTTPException(status_code=404, detail="Question not found")
        
        old_question = questions[question_index]
        
        # Get syllabus for context
        syllabus_doc = firebase_client.get_document("syllabus", paper["subject_id"])
        
        # Build prompt
        prompt = f"""Regenerate this question with similar difficulty and topic but different content:

Original Question: {old_question['question_text']}
Topic: {old_question.get('topic', 'Unknown')}
Type: {old_question.get('question_type', 'Unknown')}
Marks: {old_question.get('marks', 0)}
Difficulty: {old_question.get('difficulty', 'medium')}

Syllabus Context:
{syllabus_doc.get('content', '') if syllabus_doc else ''}

Generate a new question that:
1. Tests the same concept differently
2. Maintains the same difficulty level
3. Is worth the same marks
4. Has a different approach or scenario

Return in JSON format:
{{
  "question_text": "...",
  "question_type": "...",
  "marks": {old_question.get('marks', 5)},
  "difficulty": "{old_question.get('difficulty', 'medium')}",
  "bloom_level": "...",
  "module": "{old_question.get('module', '')}",
  "topic": "{old_question.get('topic', '')}",
  "options": [],  // if MCQ
  "answer_key": ""  // optional
}}"""

        # Generate using Ollama
        response = await ollama_client.generate(
            prompt,
            system="You are an expert at generating educational questions. Create a new question that tests the same concept differently."
        )
        
        # Parse response
        import json
        try:
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            new_question = json.loads(response_text)
            new_question["question_id"] = question_id
        except Exception as e:
            logger.error(f"Error parsing regenerated question: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse regenerated question")
        
        # Update paper
        questions[question_index] = new_question
        paper["questions"] = questions
        paper["updated_at"] = datetime.now()
        
        firebase_client.save_document("question_papers", paper_id, paper)
        
        return {"message": "Question regenerated successfully", "question": new_question}
        
    except Exception as e:
        logger.error(f"Error regenerating question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{paper_id}")
async def delete_question_paper(paper_id: str):
    """Delete a question paper"""
    try:
        firebase_client.delete_document("question_papers", paper_id)
        return {"message": "Question paper deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{paper_id}/export")
async def export_question_paper(paper_id: str, format: str = "pdf"):
    """Export question paper to PDF or Word format"""
    try:
        paper = firebase_client.get_document("question_papers", paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        
        # TODO: Implement PDF/Word generation
        # For now, return a placeholder
        return {
            "message": "Export feature coming soon",
            "paper_id": paper_id,
            "format": format
        }
        
    except Exception as e:
        logger.error(f"Error exporting question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))