from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
import uuid
from datetime import datetime

from app.models import ChatRequest
from app.firebase import firebase_client
from app.gemini import gemini_client

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory session storage (in production, use Redis or database)
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat with AI tutor"""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Build context
        system_context = """
        You are an AI tutor assistant. Your role is to:
        1. Help students understand concepts clearly
        2. Answer questions about course material
        3. Provide examples and explanations
        4. Guide students through problem-solving
        5. Encourage critical thinking
        
        Be patient, encouraging, and educational in your responses.
        """
        
        # Add context if provided
        if request.context:
            system_context += f"\n\nCourse Context:\n{request.context}"
        
        # Prepare conversation history
        history = [
            {"role": "user", "parts": [system_context]},
            {"role": "model", "parts": ["I understand. I'm ready to help students learn."]}
        ]
        
        # Add previous messages
        for msg in chat_sessions[session_id]:
            history.append({"role": msg["role"], "parts": [msg["content"]]})
        
        # Add current message
        history.append({"role": "user", "parts": [request.message]})
        
        # Get response
        response = gemini_client.generate_with_context(request.message, history)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
        # Update session
        chat_sessions[session_id].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        chat_sessions[session_id].append({
            "role": "model",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages
        if len(chat_sessions[session_id]) > 20:
            chat_sessions[session_id] = chat_sessions[session_id][-20:]
        
        # Save to Firebase
        firebase_client.save_document("chat_sessions", session_id, {
            "session_id": session_id,
            "messages": chat_sessions[session_id],
            "updated_at": datetime.now()
        })
        
        return {
            "session_id": session_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear chat session history"""
    try:
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        
        # Delete from Firebase
        firebase_client.delete_document("chat_sessions", session_id)
        
        return {"message": "Session cleared successfully", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Get chat session history"""
    try:
        # Try memory first
        if session_id in chat_sessions:
            return {
                "session_id": session_id,
                "messages": chat_sessions[session_id]
            }
        
        # Try Firebase
        session = firebase_client.get_document("chat_sessions", session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
        
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/feedback")
async def submit_feedback(session_id: str, message_index: int, feedback: str, rating: int):
    """Submit feedback for a specific response"""
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if message_index >= len(chat_sessions[session_id]):
            raise HTTPException(status_code=400, detail="Invalid message index")
        
        # Save feedback
        feedback_id = str(uuid.uuid4())
        firebase_client.save_document("chat_feedback", feedback_id, {
            "session_id": session_id,
            "message_index": message_index,
            "feedback": feedback,
            "rating": rating,
            "created_at": datetime.now()
        })
        
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))