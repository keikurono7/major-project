from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict
import logging
import uuid
from datetime import datetime

from .models import (
    StudentMark, IAMarkEntry, SemesterExamMark, 
    QuestionTopicMapping, VTUFetchRequest, ERPFetchRequest
)
from .firebase import firebase_client
from .ollama import ollama_client
from .intelligence import schedule_intelligence

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ia/upload")
async def upload_ia_marks(entries: List[IAMarkEntry]):
    """Upload IA test marks with question-topic mapping"""
    try:
        for entry in entries:
            mark_id = str(uuid.uuid4())
            
            # Save to student_marks collection
            student_mark = StudentMark(
                student_id=entry.student_id,
                subject_id=entry.subject_id,
                source_type="ia_test",
                assessment_id=f"IA{entry.test_number}_{entry.subject_id}",
                marks_obtained=entry.marks,
                max_marks=entry.max_marks,
                question_topic_mapping=entry.question_topic_mapping,
                fetched_from="manual",
                metadata={"test_number": entry.test_number}
            )
            
            firebase_client.save_document("student_marks", mark_id, student_mark.dict())
            
            # Update BKT scores for each topic
            await update_student_bkt(entry.student_id, entry.subject_id, 
                                    entry.question_topic_mapping, entry.marks, entry.max_marks)
        
        return {"message": f"Successfully uploaded {len(entries)} IA marks"}
        
    except Exception as e:
        logger.error(f"Error uploading IA marks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semester/upload")
async def upload_semester_marks(entries: List[SemesterExamMark]):
    """Upload semester exam marks"""
    try:
        for entry in entries:
            mark_id = str(uuid.uuid4())
            
            student_mark = StudentMark(
                student_id=entry.student_id,
                subject_id=entry.subject_id,
                source_type="semester_exam",
                assessment_id=f"SEM{entry.semester}_{entry.year}_{entry.subject_id}",
                marks_obtained=entry.marks,
                max_marks=entry.max_marks,
                question_topic_mapping=entry.question_topic_mapping,
                fetched_from=entry.fetched_from
            )
            
            firebase_client.save_document("student_marks", mark_id, student_mark.dict())
            
            # Update BKT scores
            await update_student_bkt(entry.student_id, entry.subject_id,
                                    entry.question_topic_mapping, entry.marks, entry.max_marks)
        
        return {"message": f"Successfully uploaded {len(entries)} semester marks"}
        
    except Exception as e:
        logger.error(f"Error uploading semester marks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vtu/fetch")
async def fetch_vtu_marks(request: VTUFetchRequest):
    """Fetch marks from VTU portal (placeholder for future implementation)"""
    # This would integrate with VTU API/scraping
    return {
        "status": "pending",
        "message": "VTU integration not yet implemented. Please use manual upload.",
        "usn": request.student_usn
    }


@router.post("/erp/fetch")
async def fetch_erp_marks(request: ERPFetchRequest):
    """Fetch marks from college ERP (placeholder)"""
    # This would integrate with college ERP API
    return {
        "status": "pending",
        "message": "ERP integration not yet implemented. Please use manual upload.",
        "subject": request.subject_id
    }


@router.post("/question-paper/analyze")
async def analyze_question_paper(file: UploadFile = File(...), subject_id: str = None):
    """Analyze question paper and map questions to topics using AI"""
    try:
        # Read file
        content = await file.read()
        text = content.decode('utf-8')
        
        # Get subject topics
        syllabus = firebase_client.get_document("syllabi", subject_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Subject syllabus not found")
        
        topics = []
        for unit in syllabus.get("units", []):
            topics.extend(unit.get("topics", []))
        
        # Use Ollama to analyze and map
        prompt = f"""
        Analyze this question paper and map each question to relevant topics.
        
        Available Topics:
        {', '.join(topics)}
        
        Question Paper:
        {text}
        
        For each question, provide:
        1. Question number/id
        2. Question text (summary)
        3. Mapped topic from the list above
        4. Marks allocated
        5. Difficulty level (easy/medium/hard)
        
        Return in JSON format:
        {{
            "questions": [
                {{
                    "question_id": "Q1",
                    "question_text": "summary",
                    "topic": "topic name",
                    "marks": 5,
                    "difficulty": "medium"
                }}
            ]
        }}
        
        Only return valid JSON.
        """
        
        response = await ollama_client.generate_content(prompt)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to analyze question paper")
        
        # Parse response
        import json
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            analysis = json.loads(response[start:end])
        else:
            raise json.JSONDecodeError("No JSON found", response, 0)
        
        # Save analysis
        analysis_id = str(uuid.uuid4())
        firebase_client.save_document("question_paper_analysis", analysis_id, {
            "id": analysis_id,
            "subject_id": subject_id,
            "filename": file.filename,
            "analysis": analysis,
            "analyzed_at": datetime.now()
        })
        
        return {
            "analysis_id": analysis_id,
            "questions": analysis["questions"],
            "total_questions": len(analysis["questions"])
        }
        
    except Exception as e:
        logger.error(f"Error analyzing question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_student_bkt(student_id: str, subject_id: str,
                             question_topic_mapping: List[QuestionTopicMapping],
                             marks_obtained: float, max_marks: float):
    """Update student's BKT scores based on new marks"""
    try:
        # Group marks by topic
        topic_marks = {}
        for mapping in question_topic_mapping:
            if mapping.topic_id not in topic_marks:
                topic_marks[mapping.topic_id] = {"obtained": 0, "max": 0}
            topic_marks[mapping.topic_id]["obtained"] += marks_obtained * (mapping.marks_allocated / max_marks)
            topic_marks[mapping.topic_id]["max"] += mapping.marks_allocated
        
        # Update BKT for each topic
        for topic_id, marks in topic_marks.items():
            score = marks["obtained"] / marks["max"] if marks["max"] > 0 else 0
            
            # Get existing performance
            perf_doc = firebase_client.get_document(
                "student_performances",
                f"{student_id}_{topic_id}"
            )
            
            if perf_doc:
                # Update existing BKT
                current_bkt = perf_doc.get("weighted_bkt", 0)
                new_bkt = schedule_intelligence.update_bkt_incremental(
                    current_bkt, score, "ia_test"  # or appropriate source
                )
                
                perf_doc["weighted_bkt"] = new_bkt
                perf_doc["last_practiced"] = datetime.now()
            else:
                # Create new performance record
                perf_doc = {
                    "student_id": student_id,
                    "topic_id": topic_id,
                    "weighted_bkt": score,
                    "data_sources": {"ia_test": score},
                    "last_practiced": datetime.now()
                }
            
            firebase_client.save_document(
                "student_performances",
                f"{student_id}_{topic_id}",
                perf_doc
            )
        
    except Exception as e:
        logger.error(f"Error updating BKT: {e}")


@router.get("/student/{student_id}/marks")
async def get_student_marks(student_id: str, subject_id: str = None):
    """Get all marks for a student"""
    try:
        filters = {"student_id": student_id}
        if subject_id:
            filters["subject_id"] = subject_id
        
        marks = firebase_client.query_documents("student_marks", filters, limit=1000)
        
        # Group by source type
        grouped = {}
        for mark in marks:
            source = mark.get("source_type")
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(mark)
        
        return {
            "student_id": student_id,
            "marks_by_source": grouped,
            "total_assessments": len(marks)
        }
        
    except Exception as e:
        logger.error(f"Error getting student marks: {e}")
        raise HTTPException(status_code=500, detail=str(e))