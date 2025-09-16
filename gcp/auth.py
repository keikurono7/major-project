from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr

from firebase_ops import db

# --- Pydantic Models for Auth ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str  # "student" or "teacher"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: Optional[datetime] = None

class Token(BaseModel):
    user_id: str
    role: str

# --- User Management Functions ---
def create_firebase_user(user_create: UserCreate) -> User:
    """Create a new user directly in Firestore"""
    try:
        # Check if user already exists
        existing_users = db.collection('users').where('email', '==', user_create.email).get()
        if len(existing_users) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Generate a unique user ID
        user_id = f"user_{int(datetime.now().timestamp())}"
        
        # Store user data in Firestore (including plain password)
        user_data = {
            "email": user_create.email,
            "password": user_create.password,  # Store plain password
            "full_name": user_create.full_name,
            "role": user_create.role,
            "created_at": datetime.now()
        }
        
        db.collection('users').document(user_id).set(user_data)
        
        # Return the created user (without password)
        return User(
            id=user_id,
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User creation failed: {str(e)}"
        )

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user by checking Firestore directly"""
    try:
        # Query for the user with the given email
        users = db.collection('users').where('email', '==', email).limit(1).get()
        
        if not users:
            return None
            
        user_doc = users[0]
        user_data = user_doc.to_dict()
        
        # Simple password check
        if user_data.get('password') != password:
            return None
            
        # Return the authenticated user
        return User(
            id=user_doc.id,
            email=user_data.get('email'),
            full_name=user_data.get('full_name', ''),
            role=user_data.get('role', 'student')
        )
    except Exception as e:
        print(f"Authentication error: {e}")
        return None