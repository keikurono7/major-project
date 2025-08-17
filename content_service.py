from database import EducationDB
from models import Subject, Module, Topic, Book
import os
import shutil
from typing import List, Optional

class ContentService:
    def __init__(self):
        self.db = EducationDB()
    
    # Subject Management
    def create_subject(self, name: str, description: str, teacher_id: int) -> int:
        """Create a new subject"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO subjects (name, description, teacher_id)
            VALUES (?, ?, ?)
        """, (name, description, teacher_id))
        
        subject_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create directory for subject books
        os.makedirs(f"books/subject_{subject_id}", exist_ok=True)
        return subject_id
    
    def get_subjects_by_teacher(self, teacher_id: int) -> List[Subject]:
        """Get all subjects created by a teacher"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, teacher_id, created_at
            FROM subjects WHERE teacher_id = ?
        """, (teacher_id,))
        
        subjects = []
        for row in cursor.fetchall():
            subjects.append(Subject(
                id=row[0], name=row[1], description=row[2],
                teacher_id=row[3], created_at=row[4]
            ))
        
        conn.close()
        return subjects
    
    def get_all_subjects(self) -> List[Subject]:
        """Get all subjects for student view"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.id, s.name, s.description, s.teacher_id, s.created_at,
                   u.full_name as teacher_name
            FROM subjects s
            JOIN users u ON s.teacher_id = u.id
            ORDER BY s.name
        """)
        
        subjects = []
        for row in cursor.fetchall():
            subject = Subject(
                id=row[0], name=row[1], description=row[2],
                teacher_id=row[3], created_at=row[4]
            )
            subject.teacher_name = row[5]  # Additional field
            subjects.append(subject)
        
        conn.close()
        return subjects
    
    # Module Management
    def add_module(self, subject_id: int, name: str, description: str, order_index: int) -> int:
        """Add a module to a subject"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO modules (subject_id, name, description, order_index)
            VALUES (?, ?, ?, ?)
        """, (subject_id, name, description, order_index))
        
        module_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return module_id
    
    def get_modules_by_subject(self, subject_id: int) -> List[Module]:
        """Get all modules for a subject"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, subject_id, name, description, order_index, created_at
            FROM modules WHERE subject_id = ?
            ORDER BY order_index
        """, (subject_id,))
        
        modules = []
        for row in cursor.fetchall():
            modules.append(Module(
                id=row[0], subject_id=row[1], name=row[2],
                description=row[3], order_index=row[4], created_at=row[5]
            ))
        
        conn.close()
        return modules
    
    # Topic Management
    def add_topic(self, module_id: int, name: str, description: str, order_index: int) -> int:
        """Add a topic to a module"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO topics (module_id, name, description, order_index)
            VALUES (?, ?, ?, ?)
        """, (module_id, name, description, order_index))
        
        topic_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return topic_id
    
    def get_topics_by_module(self, module_id: int) -> List[Topic]:
        """Get all topics for a module"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, module_id, name, description, order_index, created_at
            FROM topics WHERE module_id = ?
            ORDER BY order_index
        """, (module_id,))
        
        topics = []
        for row in cursor.fetchall():
            topics.append(Topic(
                id=row[0], module_id=row[1], name=row[2],
                description=row[3], order_index=row[4], created_at=row[5]
            ))
        
        conn.close()
        return topics
    
    # Book Management
    def add_book(self, subject_id: int, title: str, author: str, file_path: str) -> int:
        """Add a book to a subject with duplicate handling"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if a book with the same title and subject already exists
            cursor.execute("""
                SELECT id, file_path FROM books 
                WHERE subject_id = ? AND title = ? AND is_active = 1
            """, (subject_id, title))
            
            existing_book = cursor.fetchone()
            
            if existing_book:
                # Update the existing book record with the new file
                book_id = existing_book[0]
                old_file_path = existing_book[1]
                
                # Only update if the file is different
                if old_file_path != file_path:
                    cursor.execute("""
                        UPDATE books 
                        SET file_path = ?, author = ?, uploaded_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (file_path, author, book_id))
                    
                    # If old file exists and is different, remove it to save space
                    if os.path.exists(old_file_path) and old_file_path != file_path:
                        try:
                            os.remove(old_file_path)
                        except:
                            pass  # Ignore if we can't remove the old file
                
                conn.commit()
                return book_id
            
            # Add new book
            cursor.execute("""
                INSERT INTO books (subject_id, title, author, file_path, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (subject_id, title, author, file_path))
            
            book_id = cursor.lastrowid
            conn.commit()
            return book_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_books_by_subject(self, subject_id: int) -> List[Book]:
        """Get all active books for a subject"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, subject_id, title, author, file_path, is_active, uploaded_at
                FROM books WHERE subject_id = ? AND is_active = 1
                ORDER BY title
            """, (subject_id,))
            
            books = []
            for row in cursor.fetchall():
                book = Book(
                    id=row[0], 
                    subject_id=row[1], 
                    title=row[2],
                    author=row[3], 
                    file_path=row[4], 
                    is_active=row[5], 
                    uploaded_at=row[6]
                )
                books.append(book)
            
            return books
        except Exception as e:
            print(f"Error fetching books: {e}")
            return []
        finally:
            conn.close()
    
    def remove_book(self, book_id: int):
        """Deactivate a book"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE books SET is_active = 0 WHERE id = ?
        """, (book_id,))
        
        conn.commit()
        conn.close()
    
    def delete_subject(self, subject_id: int, teacher_id: int):
        """Delete a subject and all its content (only by the teacher who created it)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("SELECT teacher_id FROM subjects WHERE id = ?", (subject_id,))
        result = cursor.fetchone()
        
        if not result or result[0] != teacher_id:
            raise PermissionError("Only the subject creator can delete it")
        
        # Delete in reverse order due to foreign key constraints
        cursor.execute("DELETE FROM student_progress WHERE topic_id IN (SELECT id FROM topics WHERE module_id IN (SELECT id FROM modules WHERE subject_id = ?))", (subject_id,))
        cursor.execute("DELETE FROM quiz_history WHERE topic_id IN (SELECT id FROM topics WHERE module_id IN (SELECT id FROM modules WHERE subject_id = ?))", (subject_id,))
        cursor.execute("DELETE FROM topics WHERE module_id IN (SELECT id FROM modules WHERE subject_id = ?)", (subject_id,))
        cursor.execute("DELETE FROM modules WHERE subject_id = ?", (subject_id,))
        cursor.execute("UPDATE books SET is_active = 0 WHERE subject_id = ?", (subject_id,))
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        
        conn.commit()
        conn.close()
    
    def delete_topic(self, topic_id: int):
        """Delete a topic by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # First get topic details for success message
            cursor.execute("SELECT name FROM topics WHERE id = ?", (topic_id,))
            topic_name = cursor.fetchone()[0]
            
            # Delete student progress records for this topic
            cursor.execute("DELETE FROM student_progress WHERE topic_id = ?", (topic_id,))
            
            # Delete quiz history for this topic
            cursor.execute("DELETE FROM quiz_history WHERE topic_id = ?", (topic_id,))
            
            # Delete the topic itself
            cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
            
            conn.commit()
            return topic_name
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_module(self, module_id: int):
        """Delete a module and all its topics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get module name for success message
            cursor.execute("SELECT name FROM modules WHERE id = ?", (module_id,))
            module_name = cursor.fetchone()[0]
            
            # Get all topics in this module
            cursor.execute("SELECT id FROM topics WHERE module_id = ?", (module_id,))
            topic_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete student progress for all topics in this module
            for topic_id in topic_ids:
                cursor.execute("DELETE FROM student_progress WHERE topic_id = ?", (topic_id,))
                cursor.execute("DELETE FROM quiz_history WHERE topic_id = ?", (topic_id,))
            
            # Delete all topics in this module
            cursor.execute("DELETE FROM topics WHERE module_id = ?", (module_id,))
            
            # Delete the module itself
            cursor.execute("DELETE FROM modules WHERE id = ?", (module_id,))
            
            conn.commit()
            return module_name
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()