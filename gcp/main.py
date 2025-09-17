# main.py

import os
import uuid
import json
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Add this import
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks, Depends, status, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# Import from our modules
from syllabus_parser import extract_syllabus_structure, extract_syllabus_structure_from_pdf
from firebase_ops import (
    create_subject_with_nested_structure, update_topic_content, get_subject_structure,
    get_all_subjects, get_subject_modules, get_module_topics,
)
from quiz_generator import generate_topic_quiz, generate_quiz_for_topic, evaluate_quiz_response
from assignment_generator import generate_topic_assignment, generate_multi_topic_assignment
from question_paper_generator import generate_question_paper, save_question_paper
from auth import User, UserCreate, Token
from auth import authenticate_user, create_firebase_user

# --- App Initialization ---
app = FastAPI(title="AI-Powered Education Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

TEMP_DATA_DIR = "./temp_data"
os.makedirs(TEMP_DATA_DIR, exist_ok=True)

QUESTION_PAPERS_DIR = "./question_papers"
os.makedirs(QUESTION_PAPERS_DIR, exist_ok=True)

# --- Models for Question Paper APIs ---
class QuestionPaperRequest(BaseModel):
    subject_id: str
    topics: List[str] = None
    past_paper_text: Optional[str] = None  # New field for direct text input

class QuestionPaper(BaseModel):
    filename: str
    url: str

class QuizResponseSubmission(BaseModel):
    student_id: str
    topic_id: str
    is_correct: bool
    question_data: Optional[Dict[str, Any]] = None

class BktParams(BaseModel):
    p_L: float
    p_L0: float
    p_T: float
    p_G: float
    p_S: float

# Update the create_course_from_syllabus endpoint
@app.post("/create-course-from-syllabus")
async def create_course_structure(
    title: str = Form("Untitled Course"),
    teacher_id: str = Form("unknown"),
    file: UploadFile = File(...),  # Now required, not Optional
):
    """
    Create a course structure from a PDF syllabus file.
    """
    try:
        print(f"Received request to create course: '{title}' by teacher: {teacher_id}")
        
        # Validate file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
        # Read the contents of the uploaded PDF
        contents = await file.read()
        
        # Extract the syllabus structure from the PDF bytes
        syllabus_structure = extract_syllabus_structure_from_pdf(contents, title)
        
        # Ensure the name from the syllabus_structure is updated with the provided title
        if syllabus_structure:
            syllabus_structure["name"] = title
        
        print(f"Extracted structure with name: {syllabus_structure.get('name', 'None')}")
        
        # Create the subject with nested structure
        subject_id = create_subject_with_nested_structure(teacher_id, syllabus_structure)
        
        return {
            "status": "success",
            "message": "Course structure created successfully",
            "subject_id": subject_id,
            "structure": syllabus_structure
        }
        
    except Exception as e:
        print(f"Error creating course: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create course structure: {str(e)}"
        )


@app.post("/generate-course-quizzes")
async def generate_course_quizzes(
    subject_id: str,
    num_questions_per_topic: int = 3
):
    """
    Generates quizzes for all topics in an existing course.
    This should be called after creating the course structure.
    """
    try:
        # --- 1. Get the course structure from Firebase ---
        print(f"Fetching course structure for subject {subject_id}...")
        subject_data = get_subject_structure(subject_id)
        
        if not subject_data:
            raise HTTPException(status_code=404, detail=f"Subject with ID {subject_id} not found")
        
        # --- 2. Generate quiz for each topic ---
        print("Starting AI quiz generation for all topics...")
        subject_name = subject_data["name"]
        quiz_counts = {"total": 0, "success": 0}
        
        for mod_idx, module in enumerate(subject_data["modules"]):
            for top_idx, topic in enumerate(module["topics"]):
                quiz_counts["total"] += 1
                
                # Generate quiz
                topic_quiz = generate_topic_quiz(
                    subject_name=subject_name,
                    module_name=module["name"],
                    topic_name=topic["name"],
                    num_questions=num_questions_per_topic
                )
                
                # Update the specific topic in Firestore
                if topic_quiz and len(topic_quiz["questions"]) > 0:
                    update_topic_content(subject_id, mod_idx, top_idx, {
                        "quiz": topic_quiz
                    })
                    quiz_counts["success"] += 1
        
        # --- 3. Return success response ---
        return {
            "message": "Course quizzes generated successfully!",
            "subject_id": subject_id,
            "subject_name": subject_name,
            "topics_processed": quiz_counts["total"],
            "quizzes_generated": quiz_counts["success"]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@app.post("/generate-topic-quiz")
async def generate_single_topic_quiz(
    subject_name: str,
    module_name: str,
    topic_name: str,
    num_questions: int = 5,
    student_id: Optional[str] = None
):
    """
    Endpoint to generate a quiz for a single topic,
    with difficulty adjusted based on student mastery level.
    """
    try:
        quiz = generate_topic_quiz(
            subject_name=subject_name,
            module_name=module_name,
            topic_name=topic_name,
            num_questions=num_questions,
            student_id=student_id
        )
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@app.post("/generate-topic-assignment")
async def generate_single_topic_assignment(
    subject_name: str,
    module_name: str,
    topic_name: str,
    num_questions: int = 3,
    student_id: Optional[str] = None
):
    """
    Endpoint to generate an assignment for a single topic,
    with difficulty adjusted based on student mastery level.
    """
    try:
        assignment = generate_topic_assignment(
            subject_name=subject_name,
            module_name=module_name,
            topic_name=topic_name,
            num_questions=num_questions,
            student_id=student_id
        )
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assignment generation failed: {str(e)}")


@app.post("/generate-multi-topic-assignment")
async def generate_multi_topics_assignment(
    subject_id: str,
    student_id: str = None,
    num_topics: int = 3,
    num_questions_per_topic: int = 2
):
    """
    Generates an assignment covering multiple topics, focusing on the student's 
    weakest areas if a student_id is provided.
    """
    try:
        # Get the course structure from Firebase
        subject_data = get_subject_structure(subject_id)
        
        if not subject_data:
            raise HTTPException(status_code=404, detail=f"Subject with ID {subject_id} not found")
        
        # Generate the multi-topic assignment
        assignment = generate_multi_topic_assignment(
            subject_data=subject_data,
            student_id=student_id,
            num_topics=num_topics,
            num_questions_per_topic=num_questions_per_topic
        )
        
        return assignment
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Assignment generation failed: {str(e)}")


@app.post("/store-topic-assignment")
async def store_topic_assignment(
    subject_id: str,
    module_idx: int,
    topic_idx: int,
    assignment_data: dict
):
    """
    Stores a generated assignment in Firebase for a specific topic.
    """
    try:
        update_topic_content(subject_id, module_idx, topic_idx, {
            "assignment": assignment_data
        })
        return {"message": "Assignment stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store assignment: {str(e)}")


# --- Question Paper Generation Endpoints ---
@app.post("/generate-question-paper", response_model=QuestionPaper)
async def create_question_paper(request: QuestionPaperRequest, background_tasks: BackgroundTasks):
    """
    Generate a comprehensive question paper covering the entire syllabus.
    """
    try:
        # Get the subject structure from Firebase
        subject_data = get_subject_structure(request.subject_id)
        
        if not subject_data:
            raise HTTPException(status_code=404, detail=f"Subject with ID {request.subject_id} not found")
            
        print(f"📚 Retrieved subject: {subject_data.get('name')} with {sum(len(m.get('topics', [])) for m in subject_data.get('modules', []))} topics")
            
        # This could be a long-running task, so run it in the background
        def generate_and_save():
            try:
                question_paper = generate_question_paper(
                    subject_data=subject_data,
                    past_paper_text=request.past_paper_text
                )
                filename = save_question_paper(question_paper)
                print(f"✅ Successfully generated and saved question paper: {filename}")
                return filename
            except Exception as e:
                print(f"❌ Error in background task: {str(e)}")
                raise
        
        background_tasks.add_task(generate_and_save)
        
        # Return a placeholder response since the actual generation happens in the background
        return QuestionPaper(
            filename="question_paper_generating.txt",
            url="/question-papers/latest"
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating question paper: {str(e)}")

@app.get("/question-papers/{filename}")
async def get_question_paper(filename: str):
    """
    Get a generated question paper by filename.
    """
    file_path = os.path.join(QUESTION_PAPERS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Question paper not found")
    return FileResponse(file_path, media_type="text/plain", filename=filename)

@app.get("/question-papers/latest")
async def get_latest_question_paper():
    """
    Get the most recently generated question paper.
    """
    if not os.path.exists(QUESTION_PAPERS_DIR):
        raise HTTPException(status_code=404, detail="No question papers found")
        
    files = [f for f in os.listdir(QUESTION_PAPERS_DIR) if f.startswith("question_paper_")]
    if not files:
        raise HTTPException(status_code=404, detail="No question papers found")
        
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(QUESTION_PAPERS_DIR, x)))
    return FileResponse(os.path.join(QUESTION_PAPERS_DIR, latest_file), 
                       media_type="text/plain", 
                       filename=latest_file)

@app.get("/question-papers")
async def list_question_papers():
    """
    List all generated question papers
    """
    try:
        if not os.path.exists("./question_papers"):
            return {"question_papers": []}
            
        files = os.listdir("./question_papers")
        question_papers = []
        
        for file in files:
            if file.startswith("question_paper_"):
                stat = os.stat(os.path.join("./question_papers", file))
                question_papers.append({
                    "filename": file,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size
                })
                
        # Sort by creation time, newest first
        question_papers.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"question_papers": question_papers}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing question papers: {str(e)}")


# --- Authentication Routes ---
@app.post("/signup", response_model=User)
async def signup_user(user_create: UserCreate):
    """Register a new user"""
    user = create_firebase_user(user_create)
    return user

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Simple login that returns user data for caching"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }

@app.get("/users/me")
async def get_user_profile(user_id: str = Header(None)):
    """Get user profile by ID passed in header"""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_data = user_doc.to_dict()
        
        # Don't return the password!
        if "password" in user_data:
            del user_data["password"]
        
        return {
            "id": user_doc.id,
            **user_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )


@app.get("/subjects")
async def get_subjects(user_id: str = Header(None)):
    """Get all available subjects"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    subjects = get_all_subjects()
    return {"subjects": subjects}

@app.get("/subjects/{subject_id}/modules")
async def get_modules(subject_id: str, user_id: str = Header(None)):
    """Get modules for a specific subject"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    modules = get_subject_modules(subject_id)
    return {"modules": modules}

@app.get("/modules/{module_id}/topics")
async def get_topics(module_id: str, user_id: str = Header(None)):
    """Get topics for a specific module"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # The module ID is unique, so we need to find the subject that contains it
    # We'll need to scan all subjects to find the right module
    subjects = get_all_subjects()
    
    for subject in subjects:
        topics = get_module_topics(subject["id"], module_id)
        if topics:
            return {"topics": topics}
    
    return {"topics": []}

@app.post("/generate-quiz")
async def generate_quiz(
    quiz_request: dict = Body(...),
    user_id: str = Header(None)
):
    """Generate a quiz for a topic"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    student_id = quiz_request.get("student_id", user_id)
    topic_id = quiz_request.get("topic_id")
    num_questions = quiz_request.get("num_questions", 5)
    
    if not topic_id:
        raise HTTPException(status_code=400, detail="Topic ID is required")
    
    quiz = generate_quiz_for_topic(student_id, topic_id, num_questions)
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Failed to generate quiz")
    
    return quiz

@app.post("/submit-quiz-response")
async def submit_response(
    response_data: dict = Body(...),
    user_id: str = Header(None)
):
    """Submit a response to a quiz question and update BKT"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    student_id = response_data.get("student_id", user_id)
    topic_id = response_data.get("topic_id")
    is_correct = response_data.get("is_correct")
    
    if topic_id is None or is_correct is None:
        raise HTTPException(status_code=400, detail="Topic ID and response correctness are required")
    
    # Use evaluate_quiz_response from quiz_generator instead
    updated_params = evaluate_quiz_response(student_id, topic_id, is_correct)
    
    if not updated_params:
        raise HTTPException(status_code=500, detail="Failed to update student parameters")
    
    return {
        "updated": True,
        "mastery_probability": updated_params.get("p_L", 0),
        "learning_rate": updated_params.get("p_T", 0)
    }

@app.get("/student/{student_id}/bkt/{topic_id}")
async def get_bkt_params(
    student_id: str,
    topic_id: str,
    user_id: str = Header(None)
):
    """Get BKT parameters for a student on a topic"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # For security, only allow students to view their own BKT parameters
    # unless we implement proper admin/teacher access control later
    if student_id != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own data")
    
    from firebase_ops import get_student_bkt_params
    params = get_student_bkt_params(student_id, topic_id)
    
    return {
        "mastery_probability": params.get("p_L", 0.0),
        "learning_rate": params.get("p_T", 0.1),
        "last_updated": params.get("last_updated", None)
    }
    
@app.post("/upload-syllabus")
async def upload_syllabus(
    file: UploadFile = File(...),
    title: str = Form("Untitled Subject"),
    teacher_id: str = Header(None)
):
    """Upload a PDF syllabus and extract its structure"""
    if not teacher_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        # Read the contents of the uploaded PDF
        contents = await file.read()
        
        # Extract the syllabus structure from the PDF bytes
        syllabus_structure = extract_syllabus_structure_from_pdf(contents, title)
        
        # Create subject with nested structure in Firebase
        subject_id = create_subject_with_nested_structure(teacher_id, syllabus_structure)
        
        return {
            "status": "success",
            "subject_id": subject_id,
            "structure": syllabus_structure,
            "modules_created_count": len(syllabus_structure.get("modules", [])),
            "topics_created_count": sum(len(module.get("topics", [])) for module in syllabus_structure.get("modules", [])),
            "topics_with_content_count": 0  # Will be updated if content mapping is implemented
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing syllabus: {str(e)}")
    
@app.post("/generate-multi-topic-assignment-bkt")
async def generate_multi_topic_assignment_bkt(
    request: dict = Body(...),
    user_id: str = Header(None)
):
    """
    Generate an assignment for multiple topics, passing BKT params for each topic.
    """
    subject_id = request.get("subject_id")
    module_id = request.get("module_id")
    topic_ids = request.get("topic_ids", [])
    num_questions_per_topic = request.get("num_questions_per_topic", 3)
    bkt_params = request.get("bkt_params", {})

    if not subject_id or not topic_ids:
        raise HTTPException(status_code=400, detail="Subject and topics are required.")

    # Get subject/module/topic names for context
    subject_data = get_subject_structure(subject_id)
    module_name = None
    for mod in subject_data["modules"]:
        if mod["id"] == module_id:
            module_name = mod["name"]
            break

    # Gather topic names and BKT params
    topics_info = []
    for mod in subject_data["modules"]:
        for topic in mod["topics"]:
            if topic["id"] in topic_ids:
                topics_info.append({
                    "id": topic["id"],
                    "name": topic["name"],
                    "module_name": mod["name"],
                    "bkt": bkt_params.get(topic["id"], {})
                })

    # Generate assignment using the topics and their BKT params
    questions = []
    for topic in topics_info:
        # Pass BKT params to your assignment generator
        assignment = generate_topic_assignment(
            subject_name=subject_data["name"],
            module_name=topic["module_name"],
            topic_name=topic["name"],
            num_questions=num_questions_per_topic,
            student_id=user_id,
            bkt_params=topic["bkt"]  # You may need to update your assignment generator to accept this
        )
        questions.extend(assignment.get("questions", []))

    return {
        "subject": subject_data["name"],
        "module": module_name,
        "topics": [t["name"] for t in topics_info],
        "questions": questions
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)