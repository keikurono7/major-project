import os
import uuid
import json
import shutil
import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, firestore, initialize_app
import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# ==============================================================================
# 1. Configuration & Initialization
# ==============================================================================

SERVICE_ACCOUNT_FILE = 'serviceAccountKey.json'

try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"❌ FATAL: Failed to initialize Firebase. Ensure '{SERVICE_ACCOUNT_FILE}' is correct. Error: {e}")
    raise

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK 'punkt' model...")
    nltk.download('punkt')

OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://ollama:11434"
embedding_model = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
RAG_DATA_DIR = "./rag_data"
DB_DIR = os.path.join(RAG_DATA_DIR, "vector_db")
os.makedirs(DB_DIR, exist_ok=True)

app = FastAPI(title="AI-Powered Education Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# ==============================================================================
# 2. Core Processing Logic
# ==============================================================================

def extract_syllabus_structure(syllabus_path: str) -> Dict[str, Any]:
    """Extracts a clean structure from the syllabus PDF."""
    try:
        doc = fitz.open(syllabus_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()

        subject_match = re.search(r"Deep Learning", text, re.IGNORECASE)
        subject_name = subject_match.group(0).strip() if subject_match else "Untitled Subject"

        module_text_blocks = re.split(r"(MODULE-\d+)", text, flags=re.IGNORECASE)[1:]
        modules = []

        for i in range(0, len(module_text_blocks), 2):
            module_header = module_text_blocks[i]
            module_content = module_text_blocks[i+1]
            module_name = module_header.replace("-", " ").title()

            # Clean and split the content into topics.
            # Using tokenization to handle irregular formatting.
            stop_phrases = ["PRACTICAL COMPONENT", "Course outcomes", "Assessment Details", "Text Book:"]
            for phrase in stop_phrases:
                if phrase in module_content:
                    module_content = module_content.split(phrase, 1)[0].strip()

            topics_list = [t.strip() for t in module_content.split(',')]
            topics = []
            current_topic_text = ""
            for t in topics_list:
                if t and t[0].isupper() and len(current_topic_text) > 0:
                    topics.append({"name": current_topic_text.strip()})
                    current_topic_text = t
                else:
                    current_topic_text += " " + t
            if current_topic_text.strip():
                topics.append({"name": current_topic_text.strip()})
            
            # Additional cleanup for bullet points
            cleaned_topics = []
            for t in topics:
                t_name = re.sub(r'^\d+\.\s*', '', t['name']).strip()
                t_name = re.sub(r'^[\u2022\u25CF]\s*', '', t_name).strip()
                if t_name: cleaned_topics.append({"name": t_name})

            modules.append({"name": module_name, "topics": cleaned_topics})
            
        return {"subject_name": subject_name, "modules": modules}

    except Exception as e:
        print(f"Error extracting syllabus structure: {e}")
        return {"subject_name": "Untitled Subject", "modules": []}

def find_and_extract_content_for_topic(topic_name: str, all_text: str) -> Optional[str]:
    """
    Searches for a topic name in the text and extracts the full paragraph containing it.
    This version is more robust, handling variations in formatting.
    """
    try:
        # Use regex to find the topic name as a heading or within a paragraph
        pattern = r'\b' + re.escape(topic_name) + r'\b'
        match = re.search(pattern, all_text, re.IGNORECASE)

        if not match:
            # If the exact topic name is not found, try a more general search for the first few words
            first_words = topic_name.split()[:2]
            if len(first_words) > 1:
                pattern = r'\b' + re.escape(' '.join(first_words)) + r'\b'
                match = re.search(pattern, all_text, re.IGNORECASE)
        
        if not match:
            return None

        start_index = match.start()
        
        # Find the beginning of the paragraph (look for double newline before the match)
        para_start = all_text.rfind('\n\n', 0, start_index)
        if para_start == -1:
            para_start = 0
        else:
            para_start += 2
            
        # Find the end of the paragraph (look for double newline after the match)
        para_end = all_text.find('\n\n', start_index)
        if para_end == -1:
            para_end = len(all_text)

        return all_text[para_start:para_end].strip()
    except re.error:
        print(f"Warning: Could not compile regex for topic: {topic_name}")
        return None

def process_text_for_rag(text_content: str, topic_id: str):
    """Chunks text content, embeds it, and stores it in the Chroma vector database."""
    print(f"Processing RAG for topic ID: {topic_id}")
    if not text_content:
        print(f"Warning: No content provided for topic {topic_id}. Skipping.")
        return

    sentences = sent_tokenize(text_content)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > 1500:
            chunks.append(current_chunk.strip())
            current_chunk = ""
        current_chunk += " " + sentence
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    if not chunks: return

    documents = [Document(page_content=chunk) for chunk in chunks]
    db_path = os.path.join(DB_DIR, topic_id)
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    Chroma.from_documents(documents=documents, embedding=embedding_model, persist_directory=db_path)
    print(f"Created vector store for topic {topic_id} with {len(documents)} chunks.")

# ==============================================================================
# 3. API Endpoint
# ==============================================================================

@app.post("/syllabus-textbook-upload")
async def process_syllabus_and_textbook(
    request: str = Form(...),
    syllabus_file: UploadFile = File(...),
    textbook_files: List[UploadFile] = File(...)
):
    """
    Synchronously processes a syllabus and textbooks using the direct search method.
    """
    temp_files_to_clean = []
    try:
        # --- 1. Setup and File Handling ---
        request_data = json.loads(request)
        teacher_id = request_data["teacher_id"]
        
        syllabus_path = os.path.join(RAG_DATA_DIR, f"syllabus_{uuid.uuid4()}.pdf")
        with open(syllabus_path, "wb") as f:
            shutil.copyfileobj(syllabus_file.file, f)
        temp_files_to_clean.append(syllabus_path)

        textbook_paths = []
        for file in textbook_files:
            path = os.path.join(RAG_DATA_DIR, f"textbook_{uuid.uuid4()}.pdf")
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            textbook_paths.append(path)
            temp_files_to_clean.append(path)

        # --- 2. Syllabus Processing & DB Setup ---
        print("Extracting syllabus structure...")
        syllabus_structure = extract_syllabus_structure(syllabus_path)
        
        subject_ref = db.collection('subjects').document()
        subject_data = {"id": subject_ref.id, "name": syllabus_structure["subject_name"], "teacher_id": teacher_id}
        subject_ref.set(subject_data)
        
        topic_map = {} # {topic_name: topic_id}
        for module in syllabus_structure["modules"]:
            module_ref = db.collection('modules').document()
            module_ref.set({"id": module_ref.id, "name": module["name"], "subject_id": subject_ref.id})
            for topic in module["topics"]:
                topic_ref = db.collection('topics').document()
                topic_ref.set({"id": topic_ref.id, "name": topic["name"], "module_id": module_ref.id})
                topic_map[topic["name"]] = topic_ref.id # Use original case for keys

        # --- 3. NEW: Aggregate all text from textbooks ---
        print("Aggregating text from all provided textbooks...")
        all_textbook_text = ""
        for path in textbook_paths:
            doc = fitz.open(path)
            all_textbook_text += "".join(page.get_text() for page in doc)
            doc.close()
            all_textbook_text += "\n\n" # Add separator between books

        # --- 4. NEW: Direct Search for each topic ---
        print("Searching for topics directly in the aggregated text...")
        topics_with_content_count = 0
        for topic_name, topic_id in topic_map.items():
            # Find the paragraph(s) for the topic in the combined text
            content = find_and_extract_content_for_topic(topic_name, all_textbook_text)
            
            if content:
                try:
                    # Process content for RAG
                    process_text_for_rag(content, topic_id)
                    
                    # Update the topic document safely using set+merge
                    db.collection('topics').document(topic_id).set(
                        {"has_content": True}, 
                        merge=True
                    )
                    
                    topics_with_content_count += 1
                except Exception as e:
                    print(f"Error processing topic '{topic_name}': {e}")
            else:
                print(f"Warning: No content found for topic '{topic_name}'. Skipping.")

        # --- 5. Return Success Response ---
        print("Processing complete.")
        return {
            "subject": subject_data,
            "structure": syllabus_structure,
            "message": "Processing complete!",
            "modules_created_count": len(syllabus_structure["modules"]),
            "topics_created_count": len(topic_map),
            "topics_with_content_count": topics_with_content_count,
        }

    except Exception as e:
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # --- 6. Cleanup ---
        for path in temp_files_to_clean:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)