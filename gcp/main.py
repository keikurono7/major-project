import os, json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import (
    FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks,
    status, Header, Body, Query, Path
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from syllabus_parser import extract_syllabus_structure_from_pdf
from firebase_ops import (
    create_subject_with_nested_structure, update_topic_content, get_subject_structure,
    get_all_subjects, get_subject_modules, 
    get_student_bkt_params
)
from quiz_generator import generate_topic_quiz, generate_quiz_for_topic, evaluate_quiz_response
from assignment_generator import generate_topic_assignment, evaluate_assignment_answer, generate_feedback
from question_paper_generator import generate_question_paper, save_question_paper
from auth import User, UserCreate, authenticate_user, create_firebase_user
from chatbot import chat_with_ollama, get_teacher_bkt_insights, chat_with_teacher_assistant

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

# --- Pydantic models for compact RESTful calls ---
class AuthRequest(BaseModel):
    action: str  # "signup" | "login"
    data: Dict[str, Any]

class QuizRequest(BaseModel):
    scope: str  # "subject" | "topic"
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    num_questions: int = 5
    student_id: Optional[str] = None

class AssignmentCreateRequest(BaseModel):
    topic_ids: List[str]
    num_questions: int = 5
    student_id: Optional[str] = None

class AssignmentSubmitRequest(BaseModel):
    subject_id: str
    module_idx: int
    topic_idx: int
    submission: Dict[str, Any]
    student_id: Optional[str] = None

class GradeRequest(BaseModel):
    submission_id: str
    grade: float
    feedback: Optional[str] = None

class PaperRequest(BaseModel):
    subject_id: str
    past_paper_text: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    student_id: str
    subject_id: str
    message: str
    student_name: str
    conversation_history: Optional[List[ChatMessage]] = None

# ---------------- AUTH ----------------
@app.post("/auth")
async def auth(req: AuthRequest):
    if req.action == "signup":
        payload = req.data
        user_create = UserCreate(
            email=payload.get("email"),
            password=payload.get("password"),
            full_name=payload.get("full_name"),
            role=payload.get("role", "student")
        )
        try:
            user = create_firebase_user(user_create)
            return {"status": "ok", "user": user.dict()}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
    elif req.action == "login":
        payload = req.data
        user = authenticate_user(payload.get("email"), payload.get("password"))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return {"status": "ok", "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}}
    else:
        raise HTTPException(status_code=400, detail="Unsupported auth action")

# ---------------- SUBJECTS (single resource) ----------------
@app.post("/subjects")
async def create_subject_from_syllabus(
    file: UploadFile = File(...),
    title: str = Form("Untitled Course"),
    teacher_id: str = Header(None)
):
    if not teacher_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF required")
    contents = await file.read()
    structure = extract_syllabus_structure_from_pdf(contents, title)
    structure["name"] = title
    subject_id = create_subject_with_nested_structure(teacher_id, structure)
    return {"status": "ok", "subject_id": subject_id, "structure": structure}

# ---------------- QUIZZES (single endpoint covers generate/submit at scope) ----------------
@app.post("/quizzes")
async def quizzes(req: QuizRequest = Body(...)):
    if req.scope == "subject":
        if not req.subject_id:
            raise HTTPException(status_code=400, detail="subject_id required for subject-level quiz generation")
        subject = get_subject_structure(req.subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        generated = []
        for mod_idx, module in enumerate(subject.get("modules", [])):
            for top_idx, topic in enumerate(module.get("topics", [])):
                qz = generate_topic_quiz(subject_name=subject.get("name"), module_name=module.get("name"), topic_name=topic.get("name"), num_questions=req.num_questions)
                if qz:
                    update_topic_content(req.subject_id, mod_idx, top_idx, {"quiz": qz})
                    generated.append({"module": module.get("name"), "topic": topic.get("name"), "questions": len(qz.get("questions", []))})
        return {"status": "ok", "generated_count": len(generated), "details": generated}
    elif req.scope == "topic":
        if not req.topic_id:
            raise HTTPException(status_code=400, detail="topic_id required for topic-level quiz generation")
        q = generate_quiz_for_topic(req.student_id, req.topic_id, req.num_questions)
        return {"quiz": q}
    else:
        raise HTTPException(status_code=400, detail="Unsupported scope")

@app.post("/quizzes/submit")
async def submit_quiz_response(payload: Dict[str, Any] = Body(...)):
    student_id = payload.get("student_id")
    topic_id = payload.get("topic_id")
    is_correct = payload.get("is_correct")
    if not all([student_id, topic_id]) or is_correct is None:
        raise HTTPException(status_code=400, detail="student_id, topic_id and is_correct required")
    updated = evaluate_quiz_response(student_id, topic_id, is_correct)
    return {"updated": True, "bkt": updated}

# ---------------- ASSIGNMENTS (single resource) ----------------
@app.post("/assignments")
async def create_assignment(req: AssignmentCreateRequest):
    assignment = generate_topic_assignment(student_id=req.student_id, topic_ids=req.topic_ids, num_questions=req.num_questions)
    return {"assignment": assignment}

@app.post("/assignments/submissions")
async def submit_assignment(req: AssignmentSubmitRequest):
    student = req.student_id
    if not student:
        raise HTTPException(status_code=401, detail="student_id required")
    subject = get_subject_structure(req.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    try:
        topic = subject["modules"][req.module_idx]["topics"][req.topic_idx]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid module_idx/topic_idx")
    subs = topic.get("content", {}).get("submissions", [])
    sub = {
        "submission_id": f"sub_{int(datetime.utcnow().timestamp())}",
        "student_id": student,
        "submitted_at": datetime.utcnow().isoformat(),
        "payload": req.submission,
        "graded": False
    }
    subs.append(sub)
    ok = update_topic_content(req.subject_id, req.module_idx, req.topic_idx, {"submissions": subs})
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to store submission")
    return {"status": "ok", "submission_id": sub["submission_id"]}

@app.get("/assignments/submissions")
async def list_submissions(subject_id: str = Query(...), module_idx: int = Query(...), topic_idx: int = Query(...)):
    subject = get_subject_structure(subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    try:
        topic = subject["modules"][module_idx]["topics"][topic_idx]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid module_idx/topic_idx")
    return {"submissions": topic.get("content", {}).get("submissions", [])}

@app.put("/assignments/submissions/{submission_id}/grade")
async def grade_submission(submission_id: str, subject_id: str = Query(...), module_idx: int = Query(...), topic_idx: int = Query(...), req: GradeRequest = Body(...), grader_id: str = Header(None)):
    if not grader_id:
        raise HTTPException(status_code=401, detail="grader_id required")
    subject = get_subject_structure(subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    try:
        topic = subject["modules"][module_idx]["topics"][topic_idx]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid module_idx/topic_idx")
    subs = topic.get("content", {}).get("submissions", [])
    found = False
    for s in subs:
        if s.get("submission_id") == submission_id:
            s["graded"] = True
            s["grade"] = req.grade
            s["feedback"] = req.feedback
            s["grader_id"] = grader_id
            s["graded_at"] = datetime.utcnow().isoformat()
            # optional auto-eval
            if isinstance(s.get("payload"), dict) and s["payload"].get("answers"):
                s["auto_evaluation"] = [evaluate_assignment_answer(a.get("answer"), a.get("question_data")) for a in s["payload"]["answers"]]
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Submission not found")
    ok = update_topic_content(subject_id, module_idx, topic_idx, {"submissions": subs})
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to persist grading")
    return {"status": "ok", "submission_id": submission_id, "graded": True}

# ---------------- QUESTION PAPERS ----------------
@app.post("/papers")
async def create_paper(req: PaperRequest, background_tasks: BackgroundTasks):
    subject = get_subject_structure(req.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    def job():
        qp = generate_question_paper(subject_data=subject, past_paper_text=req.past_paper_text)
        save_question_paper(qp)
    background_tasks.add_task(job)
    return {"status": "queued", "message": "Generation started"}

@app.get("/papers")
async def list_or_get_papers(filename: Optional[str] = Query(None)):
    if filename:
        if filename == "latest":
            files = [f for f in os.listdir(QUESTION_PAPERS_DIR) if f.startswith("question_paper_")]
            if not files:
                raise HTTPException(status_code=404, detail="No papers found")
            latest = max(files, key=lambda x: os.path.getmtime(os.path.join(QUESTION_PAPERS_DIR, x)))
            return FileResponse(os.path.join(QUESTION_PAPERS_DIR, latest), media_type="text/plain", filename=latest)
        path = os.path.join(QUESTION_PAPERS_DIR, filename)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Paper not found")
        return FileResponse(path, media_type="text/plain", filename=filename)
    files = [f for f in os.listdir(QUESTION_PAPERS_DIR) if f.startswith("question_paper_")]
    papers = []
    for f in files:
        st = os.stat(os.path.join(QUESTION_PAPERS_DIR, f))
        papers.append({"filename": f, "created_at": datetime.fromtimestamp(st.st_mtime).isoformat(), "size": st.st_size})
    papers.sort(key=lambda x: x["created_at"], reverse=True)
    return {"papers": papers}

# ---------------- BKT / EVALUATION ----------------
@app.get("/students/{student_id}/bkt/{topic_id}")
async def read_bkt(student_id: str, topic_id: str, requester: str = Header(None)):
    if requester != student_id:
        raise HTTPException(status_code=403, detail="Can only access own BKT data")
    params = get_student_bkt_params(student_id, topic_id)
    return params

@app.post("/evaluate-assignment-answer")
async def evaluate_answer(payload: Dict[str, Any] = Body(...)):
    student_id = payload.get("student_id")
    question_data = payload.get("question_data")
    answer = payload.get("answer")
    if not all([student_id, question_data, answer]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    evaluation = evaluate_assignment_answer(answer, question_data)
    feedback_text = generate_feedback(
        student_answer=answer,
        model_answer=question_data.get("model_answer", ""),
        keyword_matches=evaluation.get("keyword_matches", []),
        keyword_misses=evaluation.get("keyword_misses", []),
        detected_mistakes=evaluation.get("detected_mistakes", []),
        score=evaluation.get("score", 0.0)
    )
    evaluation["feedback"] = feedback_text
    return evaluation

@app.post("/chat")
async def chat_assistant(req: ChatRequest):
    """
    Chat endpoint that provides AI assistance with student's knowledge context.
    """
    print(f"Received chat request: student_id={req.student_id}, subject_id={req.subject_id}")
    print(f"Message: {req.message}")
    print(f"Student name: {req.student_name}")
    print(f"History length: {len(req.conversation_history) if req.conversation_history else 0}")
    
    if not all([req.student_id, req.subject_id, req.message, req.student_name]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    try:
        # Convert ChatMessage objects to dicts for the chatbot function
        history_dicts = []
        if req.conversation_history:
            for msg in req.conversation_history:
                history_dicts.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        result = chat_with_ollama(
            student_id=req.student_id,
            subject_id=req.subject_id,
            message=req.message,
            student_name=req.student_name,
            conversation_history=history_dicts
        )
        
        if result.get("error"):
            print(f"Chat error: {result['error']}")
        
        return result
    
    except Exception as e:
        print(f"Exception in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/teacher-analytics/insights")
async def get_bkt_insights(request: dict):
    """
    Get AI-powered insights on class BKT performance
    """
    teacher_id = request.get('teacher_id')
    subject_id = request.get('subject_id')
    bkt_data = request.get('bkt_data')
    total_students = request.get('total_students')
    subject_name = request.get('subject_name')
    
    if not all([teacher_id, subject_id, bkt_data, subject_name]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    result = get_teacher_bkt_insights(
        teacher_id=teacher_id,
        subject_id=subject_id,
        bkt_data=bkt_data,
        total_students=total_students,
        subject_name=subject_name
    )
    
    if result.get('status') == 'error':
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to generate insights'))
    
    return result


@app.post("/teacher-analytics/chat")
async def chat_with_teacher_assistant_endpoint(request: dict):
    """
    Chat with AI assistant about class performance
    """
    teacher_id = request.get('teacher_id')
    subject_id = request.get('subject_id')
    message = request.get('message')
    bkt_context = request.get('bkt_context')
    history = request.get('conversation_history', [])
    
    if not all([teacher_id, subject_id, message]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    result = chat_with_teacher_assistant(
        teacher_id=teacher_id,
        subject_id=subject_id,
        message=message,
        bkt_context=bkt_context,
        conversation_history=history
    )
    
    if result.get('status') == 'error':
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to process message'))
    
    return result

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)