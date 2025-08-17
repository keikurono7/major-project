from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: str = ""  # 'teacher' or 'student'
    full_name: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Subject:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    teacher_id: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class Module:
    id: Optional[int] = None
    subject_id: int = 0
    name: str = ""
    description: str = ""
    order_index: int = 0
    created_at: Optional[datetime] = None

@dataclass
class Topic:
    id: Optional[int] = None
    module_id: int = 0
    name: str = ""
    description: str = ""
    order_index: int = 0
    created_at: Optional[datetime] = None

@dataclass
class Book:
    id: Optional[int] = None
    subject_id: int = 0
    title: str = ""
    author: str = ""
    file_path: str = ""
    is_active: bool = True
    uploaded_at: Optional[datetime] = None

@dataclass
class StudentProgress:
    id: Optional[int] = None
    student_id: int = 0
    topic_id: int = 0
    confidence_score: float = 0.5
    attempts: int = 0
    last_quiz_date: Optional[datetime] = None
    total_questions: int = 0
    correct_answers: int = 0