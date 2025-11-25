from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid

# ============= Enums =============

class SourceType(str, Enum):
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    PBL = "pbl"
    IA_TEST = "ia_test"
    SEMESTER_EXAM = "semester_exam"
    QUESTION_PAPER = "question_paper"

class SchedulePriority(str, Enum):
    PREREQUISITE_GAP = "prerequisite_gap"
    EXAM_CRITICAL = "exam_critical"
    LOW_BKT = "low_bkt"
    NEW_TOPIC = "new_topic"
    REVIEW = "review"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

# ============= Existing Request Models =============

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

# ============= NEW: Multi-Source Mark Models =============

class QuestionTopicMapping(BaseModel):
    question_id: str
    topic_id: str
    marks_allocated: float
    difficulty_level: str = "medium"

class StudentMark(BaseModel):
    student_id: str
    subject_id: str
    source_type: SourceType
    assessment_id: str  # quiz_id, assignment_id, etc.
    marks_obtained: float
    max_marks: float
    question_topic_mapping: List[QuestionTopicMapping]
    fetched_from: str = Field(..., description="vtu/erp/manual")
    synced_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class IAMarkEntry(BaseModel):
    student_id: str
    subject_id: str
    test_number: int  # IA1, IA2, IA3
    marks: float
    max_marks: float = 50.0
    question_paper_id: Optional[str] = None
    question_topic_mapping: List[QuestionTopicMapping]
    uploaded_by: str  # teacher_id
    uploaded_at: datetime = Field(default_factory=datetime.now)

class SemesterExamMark(BaseModel):
    student_id: str
    subject_id: str
    semester: int
    year: int
    marks: float
    max_marks: float = 100.0
    question_paper_id: Optional[str] = None
    question_topic_mapping: List[QuestionTopicMapping]
    fetched_from: str = "vtu"  # or "manual"
    fetched_at: datetime = Field(default_factory=datetime.now)

# ============= NEW: BKT & Performance Models =============

class DataSourceScore(BaseModel):
    quiz: float = 0.0
    assignment: float = 0.0
    pbl: float = 0.0
    ia_test: float = 0.0
    semester_exam: float = 0.0

class StudentTopicPerformance(BaseModel):
    student_id: str
    topic_id: str
    topic_name: str
    weighted_bkt: float  # Final BKT score
    data_sources: DataSourceScore
    learning_velocity: float = 1.0  # How fast student learns this topic
    last_practiced: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    prerequisite_gaps: List[str] = []  # List of prerequisite topic_ids with gaps
    error_patterns: List[str] = []  # Common mistakes

# ============= NEW: Schedule Models =============

class ScheduleTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    topic_id: str
    topic_name: str
    duration_hours: float
    priority: SchedulePriority
    reason: str  # Why this task is scheduled
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None
    actual_time_spent: Optional[float] = None
    notes: Optional[str] = None

class WeeklyPlan(BaseModel):
    week_number: int
    start_date: date
    end_date: date
    tasks: List[ScheduleTask]
    total_hours: float
    topics_covered: List[str]

class ScheduleAdjustment(BaseModel):
    adjusted_at: datetime
    reason: str
    changes: Dict[str, Any]
    triggered_by: str  # "system"/"teacher"/"student"

class TeacherOverride(BaseModel):
    override_id: str
    teacher_id: str
    topic_id: str
    action: str  # "mark_covered"/"add_practice"/"skip_topic"
    reason: str
    applied_at: datetime

class StudentSchedule(BaseModel):
    student_id: str
    subject_id: str
    generated_at: datetime = Field(default_factory=datetime.now)
    deadline: date
    total_topics: int
    topics_mastered: int
    weekly_plans: List[WeeklyPlan]
    adjustment_history: List[ScheduleAdjustment] = []
    teacher_overrides: List[TeacherOverride] = []
    adherence_score: float = 0.0  # % of tasks completed on time
    status: str = "on_track"  # "on_track"/"behind"/"ahead"

# ============= NEW: Subject Schedule Config =============

class ExamDate(BaseModel):
    exam_type: str  # "midterm"/"final"
    date: date
    topics_covered: List[str]

class Holiday(BaseModel):
    date: date
    description: str

class SubjectScheduleConfig(BaseModel):
    subject_id: str
    subject_name: str
    teacher_id: str
    deadline: date  # Syllabus completion deadline
    weekly_hours: int  # Expected student study hours per week
    topic_coverage_order: List[str]  # Ordered list of topic_ids
    topic_complexity: Dict[str, int]  # topic_id -> complexity (1-5)
    recommended_hours: Dict[str, float]  # topic_id -> hours
    exam_dates: List[ExamDate]
    holidays: List[Holiday] = []
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

# ============= NEW: VTU/ERP Integration Models =============

class VTUFetchRequest(BaseModel):
    student_usn: str
    semester: int
    year: int
    subject_codes: List[str]

class ERPFetchRequest(BaseModel):
    student_ids: List[str]
    subject_id: str
    test_type: str  # "IA1"/"IA2"/"IA3"

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

# ============= NEW: Dashboard Response Models =============

class StudentKnowledgeGraph(BaseModel):
    student_id: str
    subject_id: str
    topics: List[StudentTopicPerformance]
    overall_progress: float
    weak_topics: List[str]  # BKT < 0.6
    strong_topics: List[str]  # BKT > 0.8
    data_completeness: Dict[str, bool]  # Which data sources are available

class DailyTasksSummary(BaseModel):
    date: date
    tasks: List[ScheduleTask]
    total_hours: float
    completed: int
    pending: int
    progress_message: str

class ClassHeatmap(BaseModel):
    subject_id: str
    students: List[Dict[str, Any]]  # student_id, name, topic_scores
    topics: List[str]
    statistics: Dict[str, Any]