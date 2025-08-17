from database import EducationDB
from models import StudentProgress
import sqlite3
from datetime import datetime

class ProgressService:
    def __init__(self):
        self.db = EducationDB()
    
    def get_student_progress(self, student_id: int, topic_id: int):
        """Get student progress for a specific topic"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, student_id, topic_id, confidence_score, attempts, 
                   last_quiz_date, total_questions, correct_answers
            FROM student_progress 
            WHERE student_id = ? AND topic_id = ?
        """, (student_id, topic_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return StudentProgress(
                id=result[0], student_id=result[1], topic_id=result[2],
                confidence_score=result[3], attempts=result[4],
                last_quiz_date=result[5], total_questions=result[6],
                correct_answers=result[7]
            )
        return None
    
    def update_student_progress(self, student_id: int, topic_id: int, correct_answers: int, total_questions: int):
        """Update student progress after a quiz"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get existing progress
        existing = self.get_student_progress(student_id, topic_id)
        
        if existing:
            # Update existing record
            new_attempts = existing.attempts + 1
            new_total_questions = existing.total_questions + total_questions
            new_correct_answers = existing.correct_answers + correct_answers
            
            # Calculate new confidence score
            accuracy = new_correct_answers / new_total_questions if new_total_questions > 0 else 0.5
            confidence_adjustment = (accuracy - 0.5) * 0.1
            new_confidence = max(0.0, min(1.0, existing.confidence_score + confidence_adjustment))
            
            cursor.execute("""
                UPDATE student_progress 
                SET confidence_score = ?, attempts = ?, last_quiz_date = ?,
                    total_questions = ?, correct_answers = ?
                WHERE student_id = ? AND topic_id = ?
            """, (new_confidence, new_attempts, datetime.now(), 
                  new_total_questions, new_correct_answers, student_id, topic_id))
        else:
            # Create new record
            accuracy = correct_answers / total_questions if total_questions > 0 else 0.5
            confidence = max(0.0, min(1.0, 0.5 + (accuracy - 0.5) * 0.2))
            
            cursor.execute("""
                INSERT INTO student_progress 
                (student_id, topic_id, confidence_score, attempts, last_quiz_date, total_questions, correct_answers)
                VALUES (?, ?, ?, 1, ?, ?, ?)
            """, (student_id, topic_id, confidence, datetime.now(), total_questions, correct_answers))
        
        # Record quiz history
        cursor.execute("""
            INSERT INTO quiz_history (student_id, topic_id, score, total_questions)
            VALUES (?, ?, ?, ?)
        """, (student_id, topic_id, correct_answers, total_questions))
        
        conn.commit()
        conn.close()
    
    def get_student_subject_progress(self, student_id: int, subject_id: int):
        """Get all progress for a student in a subject"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sp.id, sp.student_id, sp.topic_id, sp.confidence_score, 
                   sp.attempts, sp.last_quiz_date, sp.total_questions, sp.correct_answers,
                   t.name as topic_name
            FROM student_progress sp
            JOIN topics t ON sp.topic_id = t.id
            JOIN modules m ON t.module_id = m.id
            WHERE sp.student_id = ? AND m.subject_id = ?
        """, (student_id, subject_id))
        
        progress_list = []
        for row in cursor.fetchall():
            progress = StudentProgress(
                id=row[0], student_id=row[1], topic_id=row[2],
                confidence_score=row[3], attempts=row[4],
                last_quiz_date=row[5], total_questions=row[6],
                correct_answers=row[7]
            )
            progress.topic_name = row[8]  # Add topic name
            progress_list.append(progress)
        
        conn.close()
        return progress_list
    
    def get_weakest_topics_for_teacher(self, teacher_id: int, limit: int = 10):
        """Get topics where students are struggling most (for teacher insights)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.name as topic_name, m.name as module_name, s.name as subject_name,
                   AVG(sp.confidence_score) as avg_confidence,
                   COUNT(sp.student_id) as student_count
            FROM student_progress sp
            JOIN topics t ON sp.topic_id = t.id
            JOIN modules m ON t.module_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE s.teacher_id = ?
            GROUP BY t.id
            HAVING student_count >= 3
            ORDER BY avg_confidence ASC
            LIMIT ?
        """, (teacher_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'topic_name': row[0],
                'module_name': row[1], 
                'subject_name': row[2],
                'avg_confidence': row[3],
                'student_count': row[4]
            })
        
        conn.close()
        return results