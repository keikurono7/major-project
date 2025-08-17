import sqlite3
import hashlib
import streamlit as st
from database import EducationDB
from models import User

class AuthService:
    def __init__(self):
        self.db = EducationDB()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str, role: str, full_name: str) -> bool:
        """Create a new user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password_hash, role, full_name))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate(self, username: str, password: str) -> User:
        """Authenticate user and return User object"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, full_name, created_at
            FROM users WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return User(
                id=result[0],
                username=result[1],
                email=result[2],
                password_hash=result[3],
                role=result[4],
                full_name=result[5],
                created_at=result[6]
            )
        return None
    
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, full_name, created_at
            FROM users WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return User(
                id=result[0],
                username=result[1],
                email=result[2],
                password_hash=result[3],
                role=result[4],
                full_name=result[5],
                created_at=result[6]
            )
        return None