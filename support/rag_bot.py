import os
import re
import json
import shutil
import nltk
import uuid
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
OLLAMA_MODEL = "tinyllama"
EMBEDDING_MODEL = "nomic-embed-text"
DATA_DIR = "./knowledge_base"
BOOKS_DIR = os.path.join(DATA_DIR, "books")
DB_DIR = os.path.join(DATA_DIR, "vector_db")
SUBJECTS_DIR = os.path.join(DATA_DIR, "subjects")
PROGRESS_DIR = os.path.join(DATA_DIR, "progress")

# Ensure directories exist
os.makedirs(BOOKS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(SUBJECTS_DIR, exist_ok=True)
os.makedirs(PROGRESS_DIR, exist_ok=True)

# Initialize NLTK if needed
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# --- Pydantic Models ---
class Subject(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    books: List[str] = []

class Book(BaseModel):
    id: str
    title: str
    author: Optional[str] = None
    subject_id: Optional[str] = None
    file_path: str
    topics: List[str] = []
    vector_db_path: Optional[str] = None
    upload_date: str

class Topic(BaseModel):
    name: str
    subject_id: str
    book_id: str
    confidence: float = 0.5

class QuizRequest(BaseModel):
    student_id: str
    subject_id: Optional[str] = None
    book_id: Optional[str] = None
    topic: Optional[str] = None
    num_questions: int = 5

class Question(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str

class RAGQueryRequest(BaseModel):
    query: str
    subject_id: Optional[str] = None
    book_id: Optional[str] = None
    student_id: Optional[str] = None

# --- Helper Functions ---
def get_book_path(book_id: str) -> str:
    return os.path.join(BOOKS_DIR, f"{book_id}.pdf")

def get_vector_db_path(book_id: str) -> str:
    return os.path.join(DB_DIR, book_id)

def get_subject_path(subject_id: str) -> str:
    return os.path.join(SUBJECTS_DIR, f"{subject_id}.json")

def get_student_progress_path(student_id: str) -> str:
    return os.path.join(PROGRESS_DIR, f"{student_id}.json")

def save_subject(subject: Subject):
    with open(get_subject_path(subject.id), "w") as f:
        json.dump(subject.dict(), f, indent=2)

def load_subject(subject_id: str) -> Subject:
    try:
        with open(get_subject_path(subject_id), "r") as f:
            data = json.load(f)
        return Subject(**data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Subject {subject_id} not found")

def get_all_subjects() -> List[Subject]:
    subjects = []
    for file in os.listdir(SUBJECTS_DIR):
        if file.endswith(".json"):
            with open(os.path.join(SUBJECTS_DIR, file), "r") as f:
                data = json.load(f)
            subjects.append(Subject(**data))
    return subjects

def save_book_metadata(book: Book):
    book_metadata_path = os.path.join(BOOKS_DIR, f"{book.id}_metadata.json")
    with open(book_metadata_path, "w") as f:
        json.dump(book.dict(), f, indent=2)

def load_book_metadata(book_id: str) -> Book:
    book_metadata_path = os.path.join(BOOKS_DIR, f"{book_id}_metadata.json")
    try:
        with open(book_metadata_path, "r") as f:
            data = json.load(f)
        return Book(**data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")

def get_all_books() -> List[Book]:
    books = []
    for file in os.listdir(BOOKS_DIR):
        if file.endswith("_metadata.json"):
            with open(os.path.join(BOOKS_DIR, file), "r") as f:
                data = json.load(f)
            books.append(Book(**data))
    return books

def get_books_by_subject(subject_id: str) -> List[Book]:
    return [book for book in get_all_books() if book.subject_id == subject_id]

def load_student_progress(student_id: str, create_if_missing: bool = True):
    progress_path = get_student_progress_path(student_id)
    try:
        with open(progress_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if create_if_missing:
            # Create new progress file with default confidence for all topics
            progress = {
                "student_id": student_id,
                "subjects": {}
            }
            
            # Set default confidence for all subjects and topics
            for subject in get_all_subjects():
                subject_progress = {
                    "confidence": 0.5,
                    "topics": {}
                }
                
                books = get_books_by_subject(subject.id)
                for book in books:
                    for topic in book.topics:
                        subject_progress["topics"][topic] = {
                            "confidence": 0.5,
                            "book_id": book.id
                        }
                
                progress["subjects"][subject.id] = subject_progress
            
            save_student_progress(progress)
            return progress
        else:
            raise HTTPException(status_code=404, detail=f"Student progress for {student_id} not found")

def save_student_progress(progress):
    progress_path = get_student_progress_path(progress["student_id"])
    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)

def extract_topics_from_book(book_path: str, book_id: str) -> List[str]:
    """Extract potential topics from a book using LLM"""
    try:
        # Create a temporary vector database for topic extraction
        loader = PyPDFLoader(book_path)
        documents = loader.load()
        
        # We'll just take the first few pages to extract high-level topics
        # Adjust based on your needs
        if len(documents) > 10:
            documents = documents[:10]
        
        text_content = "\n".join([doc.page_content for doc in documents])
        
        # Use LLM to extract topics
        llm = OllamaLLM(model=OLLAMA_MODEL)
        
        prompt = f"""
        Please analyze the following text from a textbook and extract 10-15 main topics that are covered in this book.
        Return the topics as a Python list of strings, formatted exactly like this: ["Topic 1", "Topic 2", "Topic 3"]
        
        TEXT:
        {text_content[:5000]}  # Limit text length
        """
        
        response = llm.invoke(prompt)
        
        # Parse the response to extract the list
        import ast
        try:
            # Find anything that looks like a list using regex
            list_pattern = r'\[(.*?)\]'
            match = re.search(list_pattern, response, re.DOTALL)
            if match:
                topics_str = match.group(0)
                topics = ast.literal_eval(topics_str)
                return topics
            else:
                # Fallback: try to find topics line by line
                topics = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line.startswith('"') and line.endswith('"'):
                        topics.append(line.strip('"'))
                    elif line.startswith("'") and line.endswith("'"):
                        topics.append(line.strip("'"))
                return topics[:15]  # Limit to 15 topics
        except:
            # If parsing fails, return a default topic
            return ["General Knowledge"]
    except Exception as e:
        print(f"Error extracting topics: {str(e)}")
        return ["General Knowledge"]

def create_vector_db_for_book(book_id: str) -> str:
    """Create a vector database for a book and return its path"""
    book = load_book_metadata(book_id)
    book_path = book.file_path
    vector_db_path = get_vector_db_path(book_id)
    
    # Check if database already exists
    if os.path.exists(vector_db_path) and os.listdir(vector_db_path):
        return vector_db_path
    
    # Load the PDF
    loader = PyPDFLoader(book_path)
    documents = loader.load()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    # Create embeddings
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    # Create and persist vector database
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=vector_db_path
    )
    vectordb.persist()
    
    # Update book metadata
    book.vector_db_path = vector_db_path
    save_book_metadata(book)
    
    return vector_db_path

def get_rag_chain(book_ids: List[str] = None, subject_id: str = None):
    """
    Get a retrieval chain that can answer questions from multiple books
    Optionally filter by subject or specific books
    """
    # Get all books or filter by subject
    if subject_id and not book_ids:
        books = get_books_by_subject(subject_id)
        book_ids = [book.id for book in books]
    
    # If no filters, get all books
    if not book_ids:
        books = get_all_books()
        book_ids = [book.id for book in books]
    
    # Ensure vector DBs exist for all books
    for book_id in book_ids:
        create_vector_db_for_book(book_id)
    
    # Create retriever that combines all the vector DBs
    if len(book_ids) == 1:
        # Single book case
        vector_db_path = get_vector_db_path(book_ids[0])
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vectordb = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
        retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    else:
        # Multiple books case - we create a multi-retriever
        # Note: In a production system, you might want to use a more sophisticated 
        # approach like langchain's MultiVectorRetriever
        retrievers = []
        for book_id in book_ids:
            vector_db_path = get_vector_db_path(book_id)
            embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
            vectordb = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
            retrievers.append(vectordb.as_retriever(search_kwargs={"k": 2}))
        
        # Create a combined retriever function
        def multi_retriever(query):
            all_docs = []
            for retriever in retrievers:
                all_docs.extend(retriever.get_relevant_documents(query))
            # Sort by relevance (if available) and limit
            return all_docs[:4]
        
        # Create a retriever object
        from langchain.schema.retriever import BaseRetriever
        
        class CustomRetriever(BaseRetriever):
            def get_relevant_documents(self, query):
                return multi_retriever(query)
            
            async def aget_relevant_documents(self, query):
                return multi_retriever(query)
        
        retriever = CustomRetriever()
    
    # Create the QA chain
    llm = OllamaLLM(model=OLLAMA_MODEL)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    return qa_chain

def update_student_topic_confidence(student_id: str, subject_id: str, topic: str, is_correct: bool):
    """Update a student's confidence score for a topic based on quiz performance"""
    progress = load_student_progress(student_id)
    
    # Ensure subject exists
    if subject_id not in progress["subjects"]:
        progress["subjects"][subject_id] = {
            "confidence": 0.5,
            "topics": {}
        }
    
    # Ensure topic exists
    subject_progress = progress["subjects"][subject_id]
    if topic not in subject_progress["topics"]:
        # Find which book this topic belongs to
        for book in get_books_by_subject(subject_id):
            if topic in book.topics:
                subject_progress["topics"][topic] = {
                    "confidence": 0.5,
                    "book_id": book.id
                }
                break
        # If topic isn't found in any book, create it anyway
        if topic not in subject_progress["topics"]:
            subject_progress["topics"][topic] = {
                "confidence": 0.5,
                "book_id": "unknown"
            }
    
    # Update confidence
    confidence = subject_progress["topics"][topic]["confidence"]
    if is_correct:
        confidence = min(1.0, confidence + 0.1)
    else:
        confidence = max(0.0, confidence - 0.1)
    subject_progress["topics"][topic]["confidence"] = confidence
    
    # Update overall subject confidence (average of topics)
    topic_confidences = [t["confidence"] for t in subject_progress["topics"].values()]
    if topic_confidences:
        subject_progress["confidence"] = sum(topic_confidences) / len(topic_confidences)
    
    # Save updated progress
    save_student_progress(progress)
    return confidence

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

def generate_quiz_for_topic(topic: str, subject_id: str = None, book_id: str = None, num_questions: int = 5):
    """Generate a quiz for a specific topic"""
    # Get the right retrieval chain
    if book_id:
        book_ids = [book_id]
    else:
        book_ids = None
    
    qa_chain = get_rag_chain(book_ids, subject_id)
    
    # Get content for the topic
    topic_query = f"What is {topic}? Explain in detail."
    topic_result = qa_chain({"query": topic_query})
    
    context = topic_result["result"]
    if "source_documents" in topic_result:
        for doc in topic_result["source_documents"][:2]:  # Add first two documents
            context += "\n" + doc.page_content
    
    # Limit context length
    context = context[:3000]
    
    # Create quiz prompt
    prompt = f"""
    Based on the following content about {topic}:
    
    {context}
    
    Create exactly {num_questions} multiple-choice questions about {topic}.
    
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
    
    # Generate quiz
    llm = OllamaLLM(model=OLLAMA_MODEL)
    raw_output = llm.invoke(prompt)
    
    # Parse output
    questions = parse_quiz_to_json(raw_output)
    return questions

# --- RAG Bot Application ---
rag_bot_app = FastAPI(
    title="Knowell RAG Bot",
    description="Multi-subject Retrieval Augmented Generation for educational content",
    version="1.0.0"
)

rag_bot_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routes ---
@rag_bot_app.get("/")
async def root():
    return {"message": "Welcome to Knowell RAG Bot. See /docs for API documentation."}

# --- Subject Management ---
@rag_bot_app.post("/subjects", response_model=Subject)
async def create_subject(name: str = Body(...), description: str = Body(None)):
    """Create a new subject"""
    subject_id = str(uuid.uuid4())
    subject = Subject(id=subject_id, name=name, description=description, books=[])
    save_subject(subject)
    return subject

@rag_bot_app.get("/subjects", response_model=List[Subject])
async def get_subjects():
    """Get all subjects"""
    return get_all_subjects()

@rag_bot_app.get("/subjects/{subject_id}", response_model=Subject)
async def get_subject(subject_id: str):
    """Get a specific subject"""
    return load_subject(subject_id)

@rag_bot_app.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: str):
    """Delete a subject"""
    subject_path = get_subject_path(subject_id)
    if not os.path.exists(subject_path):
        raise HTTPException(status_code=404, detail=f"Subject {subject_id} not found")
    
    # Remove subject from books
    for book in get_books_by_subject(subject_id):
        book.subject_id = None
        save_book_metadata(book)
    
    # Delete subject file
    os.remove(subject_path)
    return {"message": f"Subject {subject_id} deleted"}

# --- Book Management ---
@rag_bot_app.post("/books", response_model=Book)
async def upload_book(
    file: UploadFile = File(...),
    title: str = Query(...),
    author: str = Query(None),
    subject_id: str = Query(None)
):
    """Upload a new book"""
    # Verify subject exists if provided
    if subject_id:
        try:
            load_subject(subject_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Subject {subject_id} not found")
    
    # Generate book ID
    book_id = str(uuid.uuid4())
    book_path = get_book_path(book_id)
    
    # Save the PDF file
    with open(book_path, "wb") as f:
        f.write(await file.read())
    
    # Extract topics
    topics = extract_topics_from_book(book_path, book_id)
    
    # Create book metadata
    book = Book(
        id=book_id,
        title=title,
        author=author,
        subject_id=subject_id,
        file_path=book_path,
        topics=topics,
        upload_date=datetime.now().isoformat()
    )
    
    # Save book metadata
    save_book_metadata(book)
    
    # Update subject if provided
    if subject_id:
        subject = load_subject(subject_id)
        if book_id not in subject.books:
            subject.books.append(book_id)
            save_subject(subject)
    
    # Create vector database for the book in the background
    # In a real application, you might want to use a background task for this
    # But for simplicity, we'll do it synchronously
    vector_db_path = create_vector_db_for_book(book_id)
    book.vector_db_path = vector_db_path
    save_book_metadata(book)
    
    return book

@rag_bot_app.get("/books", response_model=List[Book])
async def get_books(subject_id: Optional[str] = None):
    """Get all books, optionally filtered by subject"""
    if subject_id:
        return get_books_by_subject(subject_id)
    else:
        return get_all_books()

@rag_bot_app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    """Get a specific book"""
    return load_book_metadata(book_id)

@rag_bot_app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    """Delete a book"""
    try:
        book = load_book_metadata(book_id)
    except HTTPException:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    
    # Remove from subject if associated
    if book.subject_id:
        try:
            subject = load_subject(book.subject_id)
            if book_id in subject.books:
                subject.books.remove(book_id)
                save_subject(subject)
        except HTTPException:
            pass  # Subject doesn't exist, continue with deletion
    
    # Delete book file
    if os.path.exists(book.file_path):
        os.remove(book.file_path)
    
    # Delete vector database if it exists
    if book.vector_db_path and os.path.exists(book.vector_db_path):
        shutil.rmtree(book.vector_db_path)
    
    # Delete metadata file
    metadata_path = os.path.join(BOOKS_DIR, f"{book_id}_metadata.json")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    return {"message": f"Book {book_id} deleted"}

@rag_bot_app.get("/topics", response_model=Dict[str, List[str]])
async def get_all_topics(subject_id: Optional[str] = None):
    """Get all topics, optionally filtered by subject"""
    if subject_id:
        books = get_books_by_subject(subject_id)
        topics = {}
        for book in books:
            topics[book.title] = book.topics
        return topics
    else:
        all_topics = {}
        for book in get_all_books():
            all_topics[book.title] = book.topics
        return all_topics

# --- RAG Functionality ---
@rag_bot_app.post("/query")
async def query_rag(request: RAGQueryRequest):
    """Query the RAG system with a question"""
    book_ids = None
    if request.book_id:
        book_ids = [request.book_id]
    
    qa_chain = get_rag_chain(book_ids, request.subject_id)
    result = qa_chain({"query": request.query})
    
    # Format the response
    response = {
        "answer": result["result"],
        "sources": []
    }
    
    if "source_documents" in result:
        for doc in result["source_documents"]:
            # Find which book this document came from
            doc_book_id = None
            for book in get_all_books():
                if book.vector_db_path and book.vector_db_path in str(doc.metadata.get("source", "")):
                    doc_book_id = book.id
                    break
            
            source = {
                "content": doc.page_content[:200] + "...",
                "book_id": doc_book_id,
                "book_title": load_book_metadata(doc_book_id).title if doc_book_id else "Unknown"
            }
            response["sources"].append(source)
    
    # Track this interaction in student progress if student_id is provided
    if request.student_id:
        # For simplicity, we won't implement detailed tracking here
        pass
    
    return response

# --- Quiz Generation ---
@rag_bot_app.post("/generate-quiz")
async def generate_quiz(request: QuizRequest):
    """Generate a quiz for a topic"""
    # If topic not specified, get the weakest topic for the student in this subject
    if not request.topic and request.student_id and request.subject_id:
        progress = load_student_progress(request.student_id)
        if request.subject_id in progress["subjects"]:
            subject_progress = progress["subjects"][request.subject_id]
            if subject_progress["topics"]:
                # Find weakest topic
                weakest_topic = min(
                    subject_progress["topics"].items(),
                    key=lambda x: x[1]["confidence"]
                )[0]
                request.topic = weakest_topic
    
    # If still no topic, pick a random one from the subject or book
    if not request.topic:
        if request.book_id:
            book = load_book_metadata(request.book_id)
            if book.topics:
                import random
                request.topic = random.choice(book.topics)
        elif request.subject_id:
            topics = []
            for book in get_books_by_subject(request.subject_id):
                topics.extend(book.topics)
            if topics:
                import random
                request.topic = random.choice(topics)
    
    # If still no topic, return error
    if not request.topic:
        raise HTTPException(status_code=400, detail="No topic specified or available")
    
    # Generate quiz
    questions = generate_quiz_for_topic(
        topic=request.topic,
        subject_id=request.subject_id,
        book_id=request.book_id,
        num_questions=min(request.num_questions, 10)  # Limit to 10 questions
    )
    
    return {
        "topic": request.topic,
        "subject_id": request.subject_id,
        "book_id": request.book_id,
        "questions": questions
    }

@rag_bot_app.post("/submit-quiz-answer")
async def submit_quiz_answer(
    student_id: str,
    subject_id: str,
    topic: str,
    is_correct: bool
):
    """Submit a quiz answer and update student progress"""
    new_confidence = update_student_topic_confidence(
        student_id=student_id,
        subject_id=subject_id,
        topic=topic,
        is_correct=is_correct
    )
    
    return {
        "student_id": student_id,
        "subject_id": subject_id,
        "topic": topic,
        "is_correct": is_correct,
        "new_confidence": new_confidence
    }

@rag_bot_app.get("/student-progress/{student_id}")
async def get_student_progress(student_id: str):
    """Get progress for a specific student"""
    try:
        return load_student_progress(student_id, create_if_missing=False)
    except HTTPException:
        raise HTTPException(status_code=404, detail=f"No progress found for student {student_id}")

# --- Run the application ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(rag_bot_app, host="127.0.0.1", port=8001)