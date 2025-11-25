from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime
import PyPDF2
import io

from .models import Syllabus, SyllabusAnalysis
from .firebase import firebase_client
from .ollama import ollama_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_syllabus(file: UploadFile = File(...), subject_id: str = None):
    """Upload and parse syllabus PDF using Ollama"""
    try:
        # Read PDF content
        pdf_content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        # Extract text from all pages
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n"
        
        if not full_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Generate subject_id if not provided
        if not subject_id:
            subject_id = str(uuid.uuid4())
        
        # Parse syllabus using Ollama
        prompt = f"""Analyze this course syllabus and extract structured information:

Syllabus Content:
{full_text}

Extract and return in JSON format:
{{
  "subject_name": "Course name",
  "subject_code": "Course code",
  "credits": 4,
  "modules": [
    {{
      "module_number": 1,
      "module_name": "Module name",
      "topics": ["Topic 1", "Topic 2", ...],
      "learning_outcomes": ["Outcome 1", "Outcome 2", ...],
      "hours": 8
    }}
  ],
  "textbooks": [
    {{
      "title": "Book title",
      "authors": ["Author 1"],
      "edition": "1st"
    }}
  ],
  "reference_books": [...],
  "assessment_scheme": {{
    "ia_tests": 50,
    "semester_exam": 100,
    "assignments": 0,
    "projects": 0
  }},
  "total_hours": 40
}}"""

        # Analyze using Ollama
        response = await ollama_client.generate(
            prompt,
            system="You are an expert at analyzing educational syllabi. Extract structured information accurately."
        )
        
        # Parse response
        import json
        try:
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text)
        except Exception as e:
            logger.error(f"Error parsing syllabus analysis: {e}")
            # Fallback: save raw text
            analysis = {
                "subject_name": file.filename.replace(".pdf", ""),
                "content": full_text,
                "modules": []
            }
        
        # Create syllabus object
        syllabus = Syllabus(
            subject_id=subject_id,
            subject_name=analysis.get("subject_name", file.filename),
            subject_code=analysis.get("subject_code", ""),
            content=full_text,
            modules=analysis.get("modules", []),
            textbooks=analysis.get("textbooks", []),
            reference_books=analysis.get("reference_books", []),
            assessment_scheme=analysis.get("assessment_scheme", {}),
            total_hours=analysis.get("total_hours", 0),
            credits=analysis.get("credits", 4),
            uploaded_at=datetime.now()
        )
        
        # Save to Firebase
        firebase_client.save_document("syllabus", subject_id, syllabus.dict())
        
        # Extract topics for later use
        all_topics = []
        for module in syllabus.modules:
            for topic in module.get("topics", []):
                topic_id = str(uuid.uuid4())
                all_topics.append({
                    "topic_id": topic_id,
                    "topic_name": topic,
                    "module_number": module.get("module_number"),
                    "module_name": module.get("module_name"),
                    "subject_id": subject_id
                })
        
        # Save topics
        for topic in all_topics:
            firebase_client.save_document("topics", topic["topic_id"], topic)
        
        logger.info(f"Uploaded syllabus for {subject_id} with {len(all_topics)} topics")
        
        return {
            "message": "Syllabus uploaded and analyzed successfully",
            "subject_id": subject_id,
            "analysis": analysis,
            "total_topics": len(all_topics)
        }
        
    except Exception as e:
        logger.error(f"Error uploading syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subject_id}")
async def get_syllabus(subject_id: str):
    """Get syllabus details"""
    try:
        syllabus = firebase_client.get_document("syllabus", subject_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return syllabus
        
    except Exception as e:
        logger.error(f"Error getting syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_syllabi():
    """List all syllabi"""
    try:
        syllabi = firebase_client.query_documents("syllabus", {}, limit=100)
        return {"syllabi": syllabi}
        
    except Exception as e:
        logger.error(f"Error listing syllabi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subject_id}/topics")
async def get_syllabus_topics(subject_id: str):
    """Get all topics for a subject"""
    try:
        topics = firebase_client.query_documents("topics", {"subject_id": subject_id}, limit=500)
        
        # Group by module
        modules = {}
        for topic in topics:
            module_num = topic.get("module_number", 0)
            if module_num not in modules:
                modules[module_num] = {
                    "module_number": module_num,
                    "module_name": topic.get("module_name", f"Module {module_num}"),
                    "topics": []
                }
            modules[module_num]["topics"].append(topic)
        
        return {
            "subject_id": subject_id,
            "modules": sorted(modules.values(), key=lambda x: x["module_number"]),
            "total_topics": len(topics)
        }
        
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{subject_id}/analyze-gaps")
async def analyze_syllabus_gaps(subject_id: str, student_id: str):
    """Analyze student's knowledge gaps against syllabus using Ollama"""
    try:
        # Get syllabus
        syllabus = firebase_client.get_document("syllabus", subject_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        
        # Get student performance
        performances = firebase_client.query_documents(
            "student_performances",
            {"student_id": student_id, "subject_id": subject_id},
            limit=1000
        )
        
        # Build gap analysis prompt
        topics_coverage = {}
        for perf in performances:
            topic = perf.get("topic_name", perf.get("topic_id"))
            topics_coverage[topic] = perf.get("weighted_bkt", 0)
        
        prompt = f"""Analyze the student's knowledge gaps in this course:

Syllabus Modules:
{json.dumps(syllabus.get('modules', []), indent=2)}

Student's Current Knowledge (BKT Scores):
{json.dumps(topics_coverage, indent=2)}

Identify:
1. Topics not yet covered (missing from student's knowledge)
2. Topics with low mastery (BKT < 0.6)
3. Prerequisite topics that need strengthening
4. Suggested learning path priority

Return in JSON format:
{{
  "uncovered_topics": ["topic1", "topic2"],
  "weak_topics": [
    {{"topic": "topic_name", "current_bkt": 0.4, "priority": "high"}}
  ],
  "prerequisite_gaps": ["topic1", "topic2"],
  "suggested_learning_path": [
    {{"topic": "...", "reason": "...", "estimated_hours": 3}}
  ],
  "overall_progress_percentage": 65
}}"""

        # Analyze using Ollama
        response = await ollama_client.generate(
            prompt,
            system="You are an expert educational analyst. Provide detailed, actionable gap analysis."
        )
        
        # Parse response
        import json
        try:
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            gap_analysis = json.loads(response_text)
        except Exception as e:
            logger.error(f"Error parsing gap analysis: {e}")
            gap_analysis = {
                "error": "Failed to parse analysis",
                "raw_response": response[:500]
            }
        
        return {
            "student_id": student_id,
            "subject_id": subject_id,
            "analysis": gap_analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{subject_id}")
async def delete_syllabus(subject_id: str):
    """Delete a syllabus"""
    try:
        firebase_client.delete_document("syllabus", subject_id)
        
        # Also delete associated topics
        topics = firebase_client.query_documents("topics", {"subject_id": subject_id}, limit=500)
        for topic in topics:
            firebase_client.delete_document("topics", topic["topic_id"])
        
        return {"message": "Syllabus and associated topics deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))