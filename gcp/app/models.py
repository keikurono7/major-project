from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum

# ============= Existing Models =============

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    session_id: Optional[str] = None

# ============= Assignment Models =============

class AssignmentRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    assignment_type: str = "mixed"  # mcq, short, long, problem, mixed

class GeneratedContent(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = {}

class EvaluationResponse(BaseModel):
    score: float
    feedback: str
    strengths: List[str] = []
    improvements: List[str] = []
    details: Dict[str, Any] = {}

# ============= Quiz Models =============

class QuizRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 10
    quiz_type: str = "mcq"

# ============= Question Paper Models =============

class QuestionPaperRequest(BaseModel):
    subject_id: str
    exam_type: str  # IA, Semester, Practice
    total_marks: int = 100
    duration_hours: float = 3.0
    num_questions: int = 10
    difficulty: str = "medium"
    teacher_id: str

class Question(BaseModel):
    question_id: str
    question_text: str
    question_type: str  # mcq, short, long, problem
    marks: int
    difficulty: str  # easy, medium, hard
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    module: str
    topic: str
    options: Optional[List[str]] = None  # for MCQ
    answer_key: Optional[str] = None

class QuestionPaper(BaseModel):
    paper_id: str
    subject_id: str
    exam_type: str
    total_marks: int
    duration_hours: float
    questions: List[Question]
    created_at: datetime
    created_by: str

# ============= Project Models =============

class ProjectRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    project_type: str = "implementation"  # implementation, research, analysis
    duration_weeks: int = 2

class ProjectEvaluationRequest(BaseModel):
    project_id: str
    submission_text: str
    code_files: Optional[Dict[str, str]] = None  # filename -> code

# ============= Syllabus Models =============

class Module(BaseModel):
    module_number: int
    module_name: str
    topics: List[str]
    learning_outcomes: List[str] = []
    hours: int = 0

class Textbook(BaseModel):
    title: str
    authors: List[str]
    edition: str = ""

class AssessmentScheme(BaseModel):
    ia_tests: int = 50
    semester_exam: int = 100
    assignments: int = 0
    projects: int = 0

class Syllabus(BaseModel):
    subject_id: str
    subject_name: str
    subject_code: str
    content: str  # Raw syllabus text
    modules: List[Module] = []
    textbooks: List[Textbook] = []
    reference_books: List[Textbook] = []
    assessment_scheme: AssessmentScheme = AssessmentScheme()
    total_hours: int = 0
    credits: int = 4
    uploaded_at: datetime

class SyllabusAnalysis(BaseModel):
    subject_id: str
    analysis: Dict[str, Any]

# ============= Marks & BKT Models =============

class QuestionTopicMapping(BaseModel):
    question_id: str
    topic_id: str
    marks_allocated: float
    difficulty_level: str  # easy, medium, hard

class IAMarkEntry(BaseModel):
    student_id: str
    subject_id: str
    test_number: int  # 1, 2, 3
    marks: float
    max_marks: float = 50
    question_topic_mapping: List[QuestionTopicMapping]
    uploaded_by: str
    uploaded_at: datetime

class SemesterExamMark(BaseModel):
    student_id: str
    subject_id: str
    semester: int
    year: int
    marks: float
    max_marks: float = 100
    question_topic_mapping: List[QuestionTopicMapping]
    fetched_from: str  # vtu, erp, manual
    fetched_at: datetime

class StudentMark(BaseModel):
    student_id: str
    subject_id: str
    source: str  # quiz, assignment, pbl, ia_test, semester_exam
    source_id: str
    topic_id: str
    marks_obtained: float
    max_marks: float
    difficulty: str
    timestamp: datetime

class VTUFetchRequest(BaseModel):
    student_usn: str
    semester: int
    year: int
    subject_codes: List[str]

class ERPFetchRequest(BaseModel):
    student_ids: List[str]
    subject_id: str
    test_type: str  # IA1, IA2, IA3

# ============= Schedule Models =============

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    RESCHEDULED = "rescheduled"

class SchedulePriority(str, Enum):
    PREREQUISITE_GAP = "prerequisite_gap"
    EXAM_CRITICAL = "exam_critical"
    LOW_BKT = "low_bkt"
    SCHEDULED_REVIEW = "scheduled_review"
    NEW_TOPIC = "new_topic"

class ScheduleTask(BaseModel):
    task_id: str
    topic_id: str
    topic_name: str
    activity_type: str  # study, practice, review, project
    duration_hours: float
    priority: SchedulePriority
    reason: str
    scheduled_date: date
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None
    time_spent: Optional[float] = None
    notes: Optional[str] = None

class WeeklyPlan(BaseModel):
    week_number: int
    start_date: date
    end_date: date
    tasks: List[ScheduleTask]
    total_hours: float
    topics_covered: List[str]

class StudentSchedule(BaseModel):
    student_id: str
    subject_id: str
    schedule_id: str
    weeks: List[WeeklyPlan]
    total_topics: int
    topics_mastered: int
    topics_in_progress: int
    topics_not_started: int
    adherence_score: float  # 0-100
    last_updated: datetime
    exam_date: Optional[date] = None

class SubjectScheduleConfig(BaseModel):
    subject_id: str
    total_weeks: int
    hours_per_week: float
    exam_date: date
    topics: List[str]
    prerequisites: Dict[str, List[str]] = {}  # topic_id -> [prerequisite_topic_ids]
    created_by: str
    created_at: datetime

class ScheduleAdjustment(BaseModel):
    student_id: str
    subject_id: str
    reason: str
    changes: Dict[str, Any]
    adjusted_at: datetime

class TeacherOverride(BaseModel):
    student_id: str
    subject_id: str
    teacher_id: str
    topic_id: str
    action: str  # skip, prioritize, extend_time
    reason: str
    applied_at: datetime

class DataSourceScore(BaseModel):
    quiz: float = 0.0
    assignment: float = 0.0
    pbl: float = 0.0
    ia_test: float = 0.0
    semester_exam: float = 0.0

class StudentTopicPerformance(BaseModel):
    student_id: str
    subject_id: str
    topic_id: str
    topic_name: str
    weighted_bkt: float  # 0-1
    data_sources: DataSourceScore
    prerequisite_gaps: List[str] = []
    last_practiced: Optional[datetime] = None
    next_review_date: Optional[date] = None
    learning_velocity: float = 1.0  # multiplier for learning speed

class DailyTasksSummary(BaseModel):
    date: date
    tasks: List[ScheduleTask]
    total_hours: float
    completed: int
    pending: int
    progress_message: str

# ============= Analytics Models =============

class TopicStatistics(BaseModel):
    topic: str
    average: float
    weak_students: int
    strong_students: int

class StudentHeatmapData(BaseModel):
    student_id: str
    topics: Dict[str, Dict[str, float]]  # topic_name -> {bkt, source_scores}

class ClassHeatmap(BaseModel):
    subject_id: str
    students: List[StudentHeatmapData]
    topics: List[str]
    statistics: Dict[str, TopicStatistics]

class WeakTopic(BaseModel):
    topic: str
    average_score: float
    weak_students: int
    affected_student_ids: List[str]

class ClassOverview(BaseModel):
    total_students: int
    on_track: int
    behind: int
    average_adherence: float

# ============= Export all models =============

__all__ = [
    "ChatRequest",
    "AssignmentRequest",
    "GeneratedContent",
    "EvaluationResponse",
    "QuizRequest",
    "QuestionPaperRequest",
    "Question",
    "QuestionPaper",
    "ProjectRequest",
    "ProjectEvaluationRequest",
    "Syllabus",
    "Module",
    "Textbook",
    "AssessmentScheme",
    "SyllabusAnalysis",
    "QuestionTopicMapping",
    "IAMarkEntry",
    "SemesterExamMark",
    "StudentMark",
    "VTUFetchRequest",
    "ERPFetchRequest",
    "TaskStatus",
    "SchedulePriority",
    "ScheduleTask",
    "WeeklyPlan",
    "StudentSchedule",
    "SubjectScheduleConfig",
    "ScheduleAdjustment",
    "TeacherOverride",
    "DataSourceScore",
    "StudentTopicPerformance",
    "DailyTasksSummary",
    "TopicStatistics",
    "StudentHeatmapData",
    "ClassHeatmap",
    "WeakTopic",
    "ClassOverview",
]