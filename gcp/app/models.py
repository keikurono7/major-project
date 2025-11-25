from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============= Request Models =============

class AssignmentRequest(BaseModel):
    topics: List[str] = Field(..., description="Topics to cover")
    difficulty: str = Field(default="medium")
    num_questions: int = Field(default=5, ge=1, le=20)
    include_coding: bool = Field(default=False)

class QuizRequest(BaseModel):
    topics: List[str]
    num_questions: int = Field(default=10, ge=1, le=50)
    difficulty: str = Field(default="medium")
    question_types: Optional[List[str]] = ["mcq", "true_false", "short_answer"]

class QuestionPaperRequest(BaseModel):
    syllabus_content: str
    exam_type: str = Field(default="midterm")
    duration: int = Field(default=180, description="Duration in minutes")
    total_marks: int = Field(default=100)

class ProjectRequest(BaseModel):
    topic: str
    difficulty: str = Field(default="medium")
    project_type: str = Field(default="implementation")
    duration_weeks: int = Field(default=4, ge=1, le=16)

class ProjectEvaluationRequest(BaseModel):
    project_id: str
    submission_text: str
    code_files: Optional[Dict[str, str]] = None

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

# ============= Response Models =============

class GeneratedContent(BaseModel):
    id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class EvaluationResponse(BaseModel):
    score: float
    feedback: str
    strengths: List[str]
    improvements: List[str]
    details: Optional[Dict[str, Any]] = None