from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any
import logging
import uuid
import json
from datetime import datetime
import PyPDF2
import docx
import io

from app.firebase import firebase_client
from app.gemini import gemini_client

router = APIRouter()
logger = logging.getLogger(__name__)

async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from various file formats"""
    content = await file.read()
    
    if file.filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    elif file.filename.endswith('.docx'):
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    elif file.filename.endswith('.txt'):
        return content.decode('utf-8')
    
    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX, or TXT")


@router.post("/upload")
async def upload_syllabus(file: UploadFile = File(...)):
    """Upload and parse syllabus document"""
    try:
        syllabus_id = str(uuid.uuid4())
        
        # Extract text from file
        raw_text = await extract_text_from_file(file)
        
        # Parse syllabus using AI
        prompt = f"""
        Parse this syllabus document and extract structured information:
        
        {raw_text}
        
        Extract and return JSON with:
        {{
            "course_name": "course name",
            "course_code": "code",
            "credits": number,
            "prerequisites": ["list"],
            "units": [
                {{
                    "unit_number": 1,
                    "title": "unit title",
                    "topics": ["topic1", "topic2"],
                    "hours": number,
                    "learning_outcomes": ["outcome1"]
                }}
            ],
            "textbooks": ["book1", "book2"],
            "reference_books": ["ref1"],
            "evaluation_scheme": {{
                "internal": 40,
                "external": 60
            }}
        }}
        """
        
        parsed_content = gemini_client.generate_content(prompt)
        if not parsed_content:
            raise HTTPException(status_code=500, detail="Failed to parse syllabus")
        
        # Parse JSON
        syllabus_data = json.loads(parsed_content)
        
        # Save to Firebase
        syllabus_data.update({
            "id": syllabus_id,
            "filename": file.filename,
            "raw_text": raw_text,
            "uploaded_at": datetime.now()
        })
        
        firebase_client.save_document("syllabi", syllabus_id, syllabus_data)
        
        return {
            "id": syllabus_id,
            "message": "Syllabus uploaded and parsed successfully",
            "data": syllabus_data
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse syllabus structure")
    except Exception as e:
        logger.error(f"Error uploading syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{syllabus_id}")
async def get_syllabus(syllabus_id: str):
    """Get parsed syllabus data"""
    try:
        syllabus = firebase_client.get_document("syllabi", syllabus_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        return syllabus
    except Exception as e:
        logger.error(f"Error retrieving syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{syllabus_id}/topics")
async def get_syllabus_topics(syllabus_id: str):
    """Get list of all topics from syllabus"""
    try:
        syllabus = firebase_client.get_document("syllabi", syllabus_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        
        topics = []
        for unit in syllabus.get("units", []):
            topics.extend(unit.get("topics", []))
        
        return {
            "syllabus_id": syllabus_id,
            "course_name": syllabus.get("course_name", ""),
            "topics": topics,
            "total_units": len(syllabus.get("units", []))
        }
        
    except Exception as e:
        logger.error(f"Error retrieving topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{syllabus_id}/units/{unit_number}")
async def get_unit_details(syllabus_id: str, unit_number: int):
    """Get detailed information about a specific unit"""
    try:
        syllabus = firebase_client.get_document("syllabi", syllabus_id)
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found")
        
        units = syllabus.get("units", [])
        unit = next((u for u in units if u.get("unit_number") == unit_number), None)
        
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        
        return unit
        
    except Exception as e:
        logger.error(f"Error retrieving unit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_syllabi(limit: int = 20):
    """List all uploaded syllabi"""
    try:
        syllabi = firebase_client.query_documents("syllabi", {}, limit=limit)
        return {
            "syllabi": [
                {
                    "id": s.get("id"),
                    "course_name": s.get("course_name"),
                    "course_code": s.get("course_code"),
                    "uploaded_at": s.get("uploaded_at")
                }
                for s in syllabi
            ],
            "count": len(syllabi)
        }
    except Exception as e:
        logger.error(f"Error listing syllabi: {e}")
        raise HTTPException(status_code=500, detail=str(e))