import os
import re
import json
import nltk
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
PDF_PATH = "MachineLearningTomMitchell.pdf"
OLLAMA_MODEL = "phi3:mini"
EMBEDDING_MODEL = "nomic-embed-text"
PROGRESS_DIR = "./progress"
OUTPUT_DIR = "./question_papers"
DB_DIR = "./db"

# Ensure directories exist
os.makedirs(PROGRESS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Educational Content API",
    description="API for generating quizzes, assignments, and question papers based on textbook content",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- ML Syllabus Topics ---
SYLLABUS_TOPICS = [
    "Well-Posed Learning Problems",
    "Designing a Learning System", 
    "Perspectives and Issues in Machine Learning",
    "Concept Learning Task",
    "Concept Learning as Search",
    "Find-S Algorithm",
    "Version Spaces and Candidate-Elimination Algorithm",
    "Inductive Bias",
    "Sequential Covering Algorithms",
    "Learning Rule Sets",
    "Learning First-Order Rules",
    "FOIL Algorithm",
    "Explanation-Based Learning",
    "Perfect Domain Theories",
    "Learning Search Control Knowledge",
    "Inductive-Analytical Approaches"
]

# --- Pydantic Models ---
class Topic(BaseModel):
    name: str
    confidence: float = Field(default=0.5)

class StudentProgress(BaseModel):
    student_id: str
    confidence_scores: Dict[str, float]

class QuizRequest(BaseModel):
    student_id: str
    topic: Optional[str] = None
    use_weakest: bool = True

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str

class Quiz(BaseModel):
    topic: str
    questions: List[QuizQuestion]
    confidence: float

class QuizResponse(BaseModel):
    question: str
    options: List[str]
    selected_answer: str
    is_correct: bool

class AssignmentRequest(BaseModel):
    student_id: str
    topic: Optional[str] = None
    use_weakest: bool = True
    multi_topic: bool = False

class AssignmentQuestion(BaseModel):
    topic: str
    question: str
    difficulty: str = "medium"
    type: str = "theoretical"
    model_answer: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    common_misconceptions: Optional[List[str]] = None

class Assignment(BaseModel):
    questions: List[AssignmentQuestion]

class AssignmentResponse(BaseModel):
    question_id: int
    answer: str

class AssignmentFeedback(BaseModel):
    score: float
    feedback: str
    keyword_matches: List[str]
    keyword_misses: List[str]
    detected_mistakes: List[str]

class QuestionPaperRequest(BaseModel):
    topics: Optional[List[str]] = None
    include_answers: bool = False

class QuestionPaper(BaseModel):
    filename: str
    url: str

# --- PDF Processing Functions ---
def ingest_pdf(pdf_path=PDF_PATH, persist_directory=DB_DIR):
    """Process PDF and create a vector database for retrieval"""
    if os.path.exists(persist_directory):
        print("Vector database already exists. Loading existing database...")
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
    print(f"📚 Processing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
        
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"📄 Split PDF into {len(chunks)} chunks")
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    print("🔍 Creating vector database...")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print("✅ Vector database created and persisted")
    return vectordb

# --- Student Progress Functions ---
def get_progress_file_path(student_id):
    """Generate progress file path for student"""
    return os.path.join(PROGRESS_DIR, f"progress_{student_id}.json")

def load_student_progress(student_id):
    """Load student progress or initialize if it doesn't exist"""
    progress_path = get_progress_file_path(student_id)
    
    try:
        with open(progress_path, "r") as f:
            existing_progress = json.load(f)
            
        ml_topics = set(SYLLABUS_TOPICS)
        existing_topics = set(existing_progress.get("confidence_scores", {}).keys())
        
        if ml_topics != existing_topics:
            print("Updating progress file to use Machine Learning topics...")
            progress = {
                "student_id": student_id,
                "confidence_scores": {topic: 0.5 for topic in SYLLABUS_TOPICS}
            }
            save_student_progress(progress)
            return progress
        else:
            return existing_progress
            
    except FileNotFoundError:
        progress = {
            "student_id": student_id,
            "confidence_scores": {topic: 0.5 for topic in SYLLABUS_TOPICS}
        }
        save_student_progress(progress)
        return progress

def save_student_progress(progress):
    """Save student progress to file"""
    student_id = progress["student_id"]
    progress_path = get_progress_file_path(student_id)
    
    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"✅ Progress saved to {progress_path}")

def update_quiz_confidence(progress, topic_name, is_correct):
    """Update confidence score based on quiz performance"""
    score = progress["confidence_scores"].get(topic_name, 0.5)
    if is_correct:
        score = min(1.0, score + 0.1)
    else:
        score = max(0.0, score - 0.1)
    progress["confidence_scores"][topic_name] = score
    save_student_progress(progress)
    return progress

def update_assignment_confidence(progress, topic_name, score_percentage):
    """Update confidence score based on assignment performance"""
    current_score = progress["confidence_scores"].get(topic_name, 0.5)
    
    # Calculate change based on performance (0 to 1.0)
    change = (score_percentage - 0.5) * 0.4  # Scale factor for confidence change
    
    # Update score with limits
    new_score = max(0.1, min(0.9, current_score + change))
    progress["confidence_scores"][topic_name] = new_score
    
    save_student_progress(progress)
    return progress

def get_weakest_topic(progress):
    """Get the topic with the lowest confidence score"""
    return min(progress["confidence_scores"], key=progress["confidence_scores"].get)

# --- Text Processing Utilities ---
def clean_text(text):
    """Clean and normalize text for comparison"""
    if not text:
        return []
        
    # Convert to lowercase and tokenize
    tokens = nltk.word_tokenize(text.lower())
    
    # Remove stopwords and punctuation
    stop_words = set(nltk.corpus.stopwords.words('english'))
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    
    return tokens

def clean_json_string(json_str):
    """Remove control characters and other problematic characters from JSON string"""
    # Remove control characters that break JSON parsing
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
    # Fix common JSON formatting issues
    cleaned = cleaned.replace('\\"', '"')  # Fix escaped quotes
    cleaned = cleaned.replace('\\n', ' ')  # Replace newlines with spaces
    return cleaned

# --- Quiz Generation Functions ---
def parse_quiz_to_json(raw_text):
    """
    Convert raw quiz text into structured JSON.
    Expected input format:
    Q1. What is 2+2?
    A) 3
    B) 4
    C) 5
    D) 6
    Answer: B
    Explanation: Because 2+2 = 4
    """
    quizzes = []
    blocks = re.split(r'Q\d+\.', raw_text, flags=re.IGNORECASE)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.splitlines()
        if len(lines) < 3:
            continue

        # Question = first line
        question = lines[0].strip()

        # Options = next 4 lines
        options = []
        for line in lines[1:5]:
            match = re.match(r'[A-D]\)\s*(.*)', line.strip())
            if match:
                options.append(f"{line.strip()}")

        # Extract Answer
        answer_match = re.search(r'Answer:\s*([A-D])', block, flags=re.IGNORECASE)
        answer = answer_match.group(1).upper() if answer_match else ""

        # Extract Explanation
        exp_match = re.search(r'Explanation:\s*(.*)', block, flags=re.IGNORECASE | re.DOTALL)
        explanation = exp_match.group(1).strip() if exp_match else ""

        if question and len(options) == 4 and answer:
            quizzes.append({
                "question": question,
                "options": options,
                "answer": answer,
                "explanation": explanation
            })

    return quizzes

def generate_quiz_with_context(vectordb, topic_name, student_confidence, model=OLLAMA_MODEL):
    """Generate quiz questions using context from the vector database"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"📝 Generating quiz for topic: {topic_name}")
    print(f"📚 Retrieved {len(docs)} relevant passages from textbook")
    
    # Create the prompt with context
    prompt = f"""
    Based on the following textbook content about {topic_name}:

    {context[:2000]}  # Limit context to 2000 chars
    
    Create exactly 3 multiple-choice questions about {topic_name} in Machine Learning.
    
    Format them exactly like this:

    Q1. <question text>
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4
    Answer: <A/B/C/D>
    Explanation: <short explanation>

    Only return the questions in this format, nothing else.
    """

    llm = OllamaLLM(model=model)
    raw_output = llm.invoke(prompt)

    quizzes = parse_quiz_to_json(raw_output)
    
    if not quizzes:
        print("❌ Failed to generate properly formatted questions")
        return None
    
    print(f"✅ Successfully generated {len(quizzes)} questions")
    return quizzes

# --- Assignment Generation Functions ---
def analyze_answer(user_answer, question_data):
    """Analyze user's answer against model answer"""
    model_answer = question_data.get("model_answer", "")
    
    # Clean texts
    clean_user = " ".join(clean_text(user_answer))
    clean_model = " ".join(clean_text(model_answer))
    
    # Calculate similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([clean_user, clean_model])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except:
        similarity = 0.0
    
    # Extract key concepts from model answer
    key_concepts = question_data.get("key_concepts", [])
    
    # Check which key concepts are present in user answer
    user_tokens = set(clean_text(user_answer.lower()))
    keyword_matches = []
    keyword_misses = []
    
    for concept in key_concepts:
        concept_tokens = set(clean_text(concept.lower()))
        if any(token in user_tokens for token in concept_tokens):
            keyword_matches.append(concept)
        else:
            keyword_misses.append(concept)
    
    # Check for common misconceptions
    misconceptions = question_data.get("common_misconceptions", [])
    detected_mistakes = []
    
    for misconception in misconceptions:
        misconception_tokens = set(clean_text(misconception.lower()))
        if any(token in user_tokens for token in misconception_tokens):
            detected_mistakes.append(misconception)
    
    # Calculate score based on similarity and keyword coverage
    keyword_coverage = len(keyword_matches) / max(1, len(key_concepts))
    misconception_penalty = len(detected_mistakes) * 0.1
    
    # Final score combining similarity and keyword coverage
    score = min(1.0, max(0.0, (similarity * 0.6) + (keyword_coverage * 0.4) - misconception_penalty))
    
    return {
        "similarity": similarity,
        "keyword_matches": keyword_matches,
        "keyword_misses": keyword_misses,
        "detected_mistakes": detected_mistakes,
        "score": score
    }

def parse_assignment_questions(raw_text, topic_name):
    """Parse assignment questions from raw text output"""
    questions = []
    
    # Split the text into question blocks
    # Look for patterns like "Question 1:" or "Q1." or "1."
    question_blocks = re.split(r'(?:Question\s*\d+[:.]|Q\d+[:.]|\n\d+[:.]\s)', raw_text)
    
    # Process each question block
    for block in question_blocks:
        block = block.strip()
        if not block:
            continue
            
        # Extract the question text (first paragraph or until "Answer Guidelines:")
        question_match = re.search(r'^(.*?)(?:(?:\n\n|\r\n\r\n|Answer Guidelines:)|\Z)', 
                                 block, re.DOTALL)
        question_text = question_match.group(1).strip() if question_match else ""
        
        # Extract answer guidelines if present
        guidelines_match = re.search(r'(?:Answer Guidelines:|Guidelines:)\s*(.*)', 
                                    block, re.DOTALL)
        answer_guidelines = guidelines_match.group(1).strip() if guidelines_match else ""
        
        # Extract key concepts if present
        key_concepts = []
        concepts_match = re.search(r'Key concepts:(.*?)(?:\n\n|\Z)', block, re.IGNORECASE | re.DOTALL)
        if concepts_match:
            concepts_text = concepts_match.group(1).strip()
            key_concepts = [c.strip() for c in concepts_text.split(',')]
        
        # Only add if we have a valid question
        if len(question_text) > 10:
            questions.append({
                "question": question_text,
                "model_answer": answer_guidelines,
                "key_concepts": key_concepts,
                "topic": topic_name,
                "type": "theoretical",
                "difficulty": "medium"
            })
    
    return questions

def generate_theoretical_question(vectordb, topic_name):
    """Generate a theoretical question about a topic"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"🧠 Generating theoretical question for: {topic_name}")
    
    # Create the prompt with context
    prompt = f"""
    Based on the following textbook content about {topic_name}:

    {context[:2500]}
    
    Create 1 comprehensive theoretical question that requires an essay-style response about {topic_name} in Machine Learning.
    
    The question should:
    - Require deep analysis and explanation of key concepts
    - Test comprehensive understanding rather than simple recall
    - Be appropriate for a university-level examination
    
    Format your response like this:
    
    Question: [Write your theoretical question here]
    
    Answer Guidelines: [Write detailed guidelines about what should be included in a complete answer]
    
    Key concepts: [List key concepts that should be addressed, separated by commas]
    
    Do not use JSON formatting. Just provide the text as specified above.
    """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    raw_output = llm.invoke(prompt)
    
    # Parse the raw text into a structured question
    questions = parse_assignment_questions(raw_output, topic_name)
    
    if questions and len(questions) > 0:
        questions[0]["type"] = "theoretical"
        return questions[0]
    
    # Fallback question if parsing fails
    return {
        "question": f"Explain the key concepts and significance of {topic_name} in Machine Learning.",
        "model_answer": f"A good answer should define {topic_name}, explain its importance in machine learning, and discuss its applications.",
        "key_concepts": [f"{topic_name}", "Machine Learning", "Applications"],
        "topic": topic_name,
        "type": "theoretical",
        "difficulty": "medium"
    }

def generate_practical_question(vectordb, topic_name):
    """Generate a practical question about a topic"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning application")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"⚙️ Generating practical question for: {topic_name}")
    
    # Create the prompt with context
    prompt = f"""
    Based on the following textbook content about {topic_name}:

    {context[:2500]}
    
    Create 1 practical application question that requires students to apply the concept of {topic_name} in Machine Learning to solve a problem.
    
    The question should:
    - Present a realistic scenario where {topic_name} concepts can be applied
    - Require problem-solving skills and critical thinking
    - Ask students to demonstrate how to implement or use {topic_name} in practice
    
    Format your response like this:
    
    Question: [Write your practical application question here]
    
    Answer Guidelines: [Write detailed guidelines about what should be included in a good solution]
    
    Key concepts: [List key concepts that should be addressed, separated by commas]
    
    Do not use JSON formatting. Just provide the text as specified above.
    """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    raw_output = llm.invoke(prompt)
    
    # Parse the raw text into a structured question
    questions = parse_assignment_questions(raw_output, topic_name)
    
    if questions and len(questions) > 0:
        questions[0]["type"] = "practical"
        return questions[0]
    
    # Fallback question if parsing fails
    return {
        "question": f"Apply the concept of {topic_name} to solve a real-world machine learning problem. Describe your approach in detail.",
        "model_answer": f"A good answer should demonstrate application of {topic_name} concepts to solve a specific problem, with clear methodology and expected outcomes.",
        "key_concepts": [f"{topic_name}", "Problem solving", "Implementation"],
        "topic": topic_name,
        "type": "practical",
        "difficulty": "medium"
    }

# --- Question Paper Generation Functions ---
def generate_question_paper(vectordb, topics=None):
    """Generate a complete question paper with equal coverage of all topics"""
    if topics is None:
        topics = SYLLABUS_TOPICS
    
    print(f"🏗️ Generating comprehensive long-answer question paper covering {len(topics)} topics")
    print(f"📊 Each topic will have 1 theoretical and 1 practical question")
    
    question_paper = {
        "title": "Machine Learning Comprehensive Examination",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_marks": 0,
        "duration_minutes": 180,
        "instructions": [
            "Answer ALL questions",
            "This paper contains theoretical and practical long-answer questions",
            "Write all answers in the answer booklet provided",
            "Each question carries marks as indicated",
            "Detailed explanations with relevant examples are expected for full marks"
        ],
        "sections": [
            {
                "name": "Section A: Theoretical Questions",
                "instructions": "Answer all theoretical questions. Focus on clear explanation of concepts.",
                "questions": []
            },
            {
                "name": "Section B: Practical Applications",
                "instructions": "Answer all practical questions. Show your approach and methodology.",
                "questions": []
            }
        ]
    }
    
    # Generate theoretical questions (1 per topic)
    for topic in topics:
        theo_q = generate_theoretical_question(vectordb, topic)
        theo_q["marks"] = 10
        question_paper["sections"][0]["questions"].append(theo_q)
        question_paper["total_marks"] += 10
    
    # Generate practical questions (1 per topic)
    for topic in topics:
        prac_q = generate_practical_question(vectordb, topic)
        prac_q["marks"] = 10
        question_paper["sections"][1]["questions"].append(prac_q)
        question_paper["total_marks"] += 10
    
    # Calculate estimated duration
    all_questions = (question_paper["sections"][0]["questions"] + 
                    question_paper["sections"][1]["questions"])
    
    # Each question takes about 15 minutes on average
    estimated_minutes = len(all_questions) * 15
    question_paper["duration_minutes"] = max(180, estimated_minutes)  # At least 3 hours
    
    return question_paper

def save_question_paper(question_paper, include_answers=False):
    """Save the question paper to a text file"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"question_paper_{timestamp}.txt"
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        # Write header
        f.write(f"{'='*80}\n")
        f.write(f"{question_paper['title'].upper():^80}\n")
        f.write(f"Date: {question_paper['date']}\n")
        f.write(f"Duration: {question_paper['duration_minutes'] // 60} hours {question_paper['duration_minutes'] % 60} minutes\n")
        f.write(f"Total Marks: {question_paper['total_marks']}\n")
        f.write(f"{'='*80}\n\n")
        
        # Write instructions
        f.write("INSTRUCTIONS:\n")
        for i, instruction in enumerate(question_paper["instructions"], 1):
            f.write(f"{i}. {instruction}\n")
        f.write("\n")
        
        # Write sections
        for section in question_paper["sections"]:
            f.write(f"{'-'*80}\n")
            f.write(f"{section['name'].upper()}\n")
            f.write(f"{'-'*80}\n")
            f.write(f"{section['instructions']}\n\n")
            
            # Write questions
            for i, q in enumerate(section["questions"], 1):
                f.write(f"Question {i} [{q.get('marks', 0)} marks]\n")
                f.write(f"Topic: {q.get('topic', 'Unknown')}\n")
                f.write(f"{q['question']}\n\n")
                
                if include_answers and "model_answer" in q:
                    f.write("Answer Guidelines:\n")
                    f.write(f"{q['model_answer']}\n\n")
                    if "key_concepts" in q:
                        f.write("Key concepts to address: ")
                        f.write(", ".join(q["key_concepts"]))
                        f.write("\n\n")
            
            f.write("\n")
    
    print(f"📄 Question paper saved to {file_path}")
    return filename

# --- API Routes ---
@app.get("/")
async def root():
    return {"message": "Welcome to the Educational Content API. See /docs for API documentation."}

# --- Topic Management ---
@app.get("/topics", response_model=List[str])
async def get_topics():
    """Get all available topics"""
    return SYLLABUS_TOPICS

# --- Student Progress ---
@app.get("/progress/{student_id}", response_model=StudentProgress)
async def get_student_progress(student_id: str):
    """Get progress for a specific student"""
    progress = load_student_progress(student_id)
    return progress

@app.post("/progress/{student_id}/reset")
async def reset_student_progress(student_id: str):
    """Reset progress for a specific student"""
    progress = {
        "student_id": student_id,
        "confidence_scores": {topic: 0.5 for topic in SYLLABUS_TOPICS}
    }
    save_student_progress(progress)
    return {"message": f"Progress reset for student {student_id}"}

# --- Quiz Generation ---
@app.post("/quiz", response_model=Quiz)
async def generate_quiz(request: QuizRequest):
    """Generate a quiz for a student"""
    try:
        # Load student progress
        progress = load_student_progress(request.student_id)
        
        # Determine topic
        selected_topic = request.topic
        if not selected_topic and request.use_weakest:
            selected_topic = get_weakest_topic(progress)
        elif not selected_topic:
            # Pick random topic if not specified and not using weakest
            import random
            selected_topic = random.choice(SYLLABUS_TOPICS)
        
        # Get current confidence
        confidence = progress["confidence_scores"].get(selected_topic, 0.5)
        
        # Generate quiz
        vectordb = ingest_pdf()
        quiz_questions = generate_quiz_with_context(vectordb, selected_topic, confidence)
        
        if not quiz_questions:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")
            
        # Convert to Pydantic model format
        quiz = Quiz(
            topic=selected_topic,
            questions=[
                QuizQuestion(
                    question=q["question"],
                    options=q["options"],
                    answer=q["answer"],
                    explanation=q["explanation"]
                ) for q in quiz_questions
            ],
            confidence=confidence
        )
        
        return quiz
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

@app.post("/quiz/{student_id}/submit")
async def submit_quiz_answer(student_id: str, response: QuizResponse):
    """Submit a quiz answer and update progress"""
    try:
        # Load student progress
        progress = load_student_progress(student_id)
        
        # Update confidence based on correctness
        progress = update_quiz_confidence(progress, response.topic, response.is_correct)
        
        # Return updated confidence
        return {
            "topic": response.topic,
            "is_correct": response.is_correct,
            "updated_confidence": progress["confidence_scores"][response.topic]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting quiz answer: {str(e)}")

# --- Assignment Generation ---
@app.post("/assignment", response_model=Assignment)
async def generate_assignment(request: AssignmentRequest):
    """Generate an assignment for a student"""
    try:
        # Load student progress
        progress = load_student_progress(request.student_id)
        
        # Determine topic(s)
        topics = []
        if request.multi_topic:
            # Select 3 weakest topics
            sorted_topics = sorted(progress["confidence_scores"].items(), key=lambda x: x[1])
            topics = [topic for topic, _ in sorted_topics[:3]]
        else:
            # Single topic
            selected_topic = request.topic
            if not selected_topic and request.use_weakest:
                selected_topic = get_weakest_topic(progress)
            elif not selected_topic:
                # Pick random topic if not specified and not using weakest
                import random
                selected_topic = random.choice(SYLLABUS_TOPICS)
            topics = [selected_topic]
        
        # Generate assignment
        vectordb = ingest_pdf()
        assignment_questions = []
        
        for topic in topics:
            # Generate one theoretical and one practical question per topic
            theo_q = generate_theoretical_question(vectordb, topic)
            prac_q = generate_practical_question(vectordb, topic)
            
            assignment_questions.append(theo_q)
            assignment_questions.append(prac_q)
        
        # Convert to Pydantic model format
        assignment = Assignment(questions=assignment_questions)
        
        return assignment
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating assignment: {str(e)}")

@app.post("/assignment/{student_id}/evaluate", response_model=AssignmentFeedback)
async def evaluate_assignment_answer(student_id: str, question_id: int, answer: str):
    """Evaluate an assignment answer"""
    try:
        # Load student progress
        progress = load_student_progress(student_id)
        
        # We'd need to store assignments somewhere to get question data
        # For now, assume the question data is passed in the request
        question_data = {
            "question": "Sample question",
            "model_answer": "Sample answer",
            "key_concepts": ["concept1", "concept2"],
            "common_misconceptions": ["misconception1"],
            "topic": "Sample Topic"
        }
        
        # Analyze the answer
        analysis = analyze_answer(answer, question_data)
        
        # Update student progress
        topic = question_data["topic"]
        progress = update_assignment_confidence(progress, topic, analysis["score"])
        
        # Generate feedback
        feedback = {
            "score": analysis["score"],
            "feedback": f"Your answer scored {analysis['score']*100:.1f}%.",
            "keyword_matches": analysis["keyword_matches"],
            "keyword_misses": analysis["keyword_misses"],
            "detected_mistakes": analysis["detected_mistakes"]
        }
        
        return feedback
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating assignment: {str(e)}")

# --- Question Paper Generation ---
@app.post("/question-paper", response_model=QuestionPaper)
async def create_question_paper(request: QuestionPaperRequest, background_tasks: BackgroundTasks):
    """Generate a question paper"""
    try:
        # Use requested topics or all topics
        topics = request.topics or SYLLABUS_TOPICS
        
        # Generate question paper
        vectordb = ingest_pdf()
        
        # This could be a long-running task, so run it in the background
        def generate_and_save():
            question_paper = generate_question_paper(vectordb, topics)
            filename = save_question_paper(question_paper, request.include_answers)
            return filename
            
        background_tasks.add_task(generate_and_save)
        
        # Return a placeholder response since the actual generation happens in the background
        return QuestionPaper(
            filename="question_paper_generating.txt",
            url="/question-papers/latest"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating question paper: {str(e)}")

@app.get("/question-papers/{filename}")
async def get_question_paper(filename: str):
    """Get a generated question paper by filename"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Question paper not found")
    return FileResponse(file_path, media_type="text/plain", filename=filename)

@app.get("/question-papers/latest")
async def get_latest_question_paper():
    """Get the most recently generated question paper"""
    if not os.path.exists(OUTPUT_DIR):
        raise HTTPException(status_code=404, detail="No question papers found")
        
    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("question_paper_")]
    if not files:
        raise HTTPException(status_code=404, detail="No question papers found")
        
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)))
    return FileResponse(os.path.join(OUTPUT_DIR, latest_file), media_type="text/plain", filename=latest_file)

# --- PDF Upload ---
@app.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file to use for content generation"""
    try:
        file_location = PDF_PATH
        with open(file_location, "wb") as file_object:
            file_object.write(await file.read())
            
        # Clear existing database to force regeneration with new PDF
        import shutil
        if os.path.exists(DB_DIR):
            shutil.rmtree(DB_DIR)
            
        return {"message": f"PDF file uploaded successfully as {file_location}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")

# --- Run the application ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)