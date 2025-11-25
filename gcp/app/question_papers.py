from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
import logging
import uuid
import os
from datetime import datetime

from app.models import QuestionPaperRequest, GeneratedContent
from app.firebase import firebase_client
from app.gemini import gemini_client
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=GeneratedContent)
async def generate_question_paper(request: QuestionPaperRequest):
    """Generate a complete question paper"""
    try:
        paper_id = str(uuid.uuid4())
        
        prompt = f"""
        Generate a comprehensive question paper with:
        
        Syllabus Content:
        {request.syllabus_content}
        
        Specifications:
        - Exam Type: {request.exam_type}
        - Duration: {request.duration} minutes
        - Total Marks: {request.total_marks}
        
        Include:
        1. Header with exam details (subject, date, time, marks)
        2. General instructions
        3. Multiple sections with varied question types:
           - Section A: Multiple Choice (1 mark each)
           - Section B: Short Answer (2-3 marks each)
           - Section C: Long Answer (5-10 marks each)
        4. Proper mark distribution
        5. Clear question numbering
        
        Make questions cover all topics from syllabus with appropriate difficulty.
        """
        
        content = gemini_client.generate_content(prompt)
        if not content:
            raise HTTPException(status_code=500, detail="Failed to generate question paper")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"question_paper_{timestamp}.txt"
        file_path = os.path.join(settings.QUESTION_PAPERS_DIR, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save to Firebase
        paper_data = {
            "id": paper_id,
            "exam_type": request.exam_type,
            "duration": request.duration,
            "total_marks": request.total_marks,
            "file_path": file_path,
            "content": content,
            "created_at": datetime.now()
        }
        
        firebase_client.save_document("question_papers", paper_id, paper_data)
        
        # Upload to storage
        storage_path = f"question_papers/{filename}"
        firebase_client.upload_file(file_path, storage_path)
        
        return GeneratedContent(
            id=paper_id,
            content=content,
            metadata={
                "exam_type": request.exam_type,
                "duration": request.duration,
                "total_marks": request.total_marks,
                "file_path": file_path
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{paper_id}")
async def download_question_paper(paper_id: str):
    """Download generated question paper"""
    try:
        paper = firebase_client.get_document("question_papers", paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        
        file_path = paper.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Error downloading question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}")
async def get_question_paper(paper_id: str):
    """Get question paper details"""
    try:
        paper = firebase_client.get_document("question_papers", paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Question paper not found")
        return paper
    except Exception as e:
        logger.error(f"Error getting question paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_question_papers(limit: int = 20):
    """List all question papers"""
    try:
        papers = firebase_client.query_documents("question_papers", {}, limit=limit)
        return {"papers": papers, "count": len(papers)}
    except Exception as e:
        logger.error(f"Error listing question papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))