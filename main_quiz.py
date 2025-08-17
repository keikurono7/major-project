import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# --- Configuration ---
PDF_PATH = "MachineLearningTomMitchell.pdf"
OLLAMA_MODEL = "mistral:7b"
EMBEDDING_MODEL = "nomic-embed-text"
PROGRESS_FILE_PATH = "progress_user123.json"

# Updated syllabus based on Machine Learning by Tom Mitchell
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

# --- PDF Ingestion ---
def ingest_pdf(pdf_path=None, persist_directory="./db"):
    """
    Ingest PDF and create/load vector database
    
    Args:
        pdf_path (str): Path to PDF file (defaults to PDF_PATH)
        persist_directory (str): Directory to store vector database
    
    Returns:
        Chroma: Vector database instance
    """
    if pdf_path is None:
        pdf_path = PDF_PATH
        
    if os.path.exists(persist_directory):
        print("Vector database already exists. Loading existing database...")
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    print("Ingesting Machine Learning PDF and creating vector database...")
    print("Using lightweight embedding model for faster processing...")
    
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    docs = text_splitter.split_documents(documents)

    print(f"Split PDF into {len(docs)} chunks...")
    print("Creating embeddings (this may take a few minutes)...")

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    batch_size = 50
    if len(docs) > batch_size:
        print(f"Processing in batches of {batch_size} for better performance...")
        first_batch = docs[:batch_size]
        vectordb = Chroma.from_documents(
            documents=first_batch, 
            embedding=embeddings, 
            persist_directory=persist_directory
        )
        
        for i in range(batch_size, len(docs), batch_size):
            batch = docs[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1}...")
            vectordb.add_documents(batch)
    else:
        vectordb = Chroma.from_documents(
            documents=docs, 
            embedding=embeddings, 
            persist_directory=persist_directory
        )
    
    print("Vector database created successfully.")
    return vectordb

# --- Create ML Syllabus JSON ---
def create_ml_syllabus():
    """Create a syllabus.json file with Machine Learning topics"""
    ml_syllabus = {
        "subject": "Machine Learning",
        "modules": [
            {
                "module": "MODULE-1",
                "topics": [
                    {"name": topic, "sub_topics": []}
                    for topic in SYLLABUS_TOPICS[:8]
                ]
            },
            {
                "module": "MODULE-2", 
                "topics": [
                    {"name": topic, "sub_topics": []}
                    for topic in SYLLABUS_TOPICS[8:]
                ]
            }
        ]
    }
    
    with open("ml_syllabus.json", "w") as f:
        json.dump(ml_syllabus, f, indent=2)
    print("Created ml_syllabus.json file")
    return ml_syllabus

# --- Student Progress Functions ---
def load_student_progress(student_id):
    """
    Load student progress from file
    
    Args:
        student_id (str): Unique student identifier
    
    Returns:
        dict: Student progress data
    """
    try:
        with open(PROGRESS_FILE_PATH, "r") as f:
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
    """
    Save student progress to file
    
    Args:
        progress (dict): Student progress data
    """
    with open(PROGRESS_FILE_PATH, "w") as f:
        json.dump(progress, f, indent=2)

def update_confidence_score(progress, topic_name, is_correct):
    """
    Update confidence score for a topic based on quiz performance
    
    Args:
        progress (dict): Student progress data
        topic_name (str): Name of the topic
        is_correct (bool): Whether the answer was correct
    
    Returns:
        dict: Updated progress data
    """
    score = progress["confidence_scores"].get(topic_name, 0.5)
    if is_correct:
        score = min(1.0, score + 0.1)
    else:
        score = max(0.0, score - 0.1)
    progress["confidence_scores"][topic_name] = score
    save_student_progress(progress)
    return progress

def get_next_quiz_topic(progress):
    """
    Get the topic with the lowest confidence score
    
    Args:
        progress (dict): Student progress data
    
    Returns:
        str: Topic name with lowest confidence
    """
    return min(progress["confidence_scores"], key=progress["confidence_scores"].get)

# --- Quiz Generation ---
def wait_for_ollama():
    """Wait for Ollama to be ready"""
    import requests
    import time
    
    max_retries = 30  # 5 minutes
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama is ready!")
                
                # Check if models are available
                models_data = response.json()
                models = [model.get('name', '') for model in models_data.get('models', [])]
                
                required_models = ['mistral:7b', 'nomic-embed-text:latest']
                missing_models = [model for model in required_models 
                                if not any(model.split(':')[0] in existing for existing in models)]
                
                if missing_models:
                    print(f"⚠️ Missing models: {missing_models}")
                    print("Models are still downloading. This may take several minutes...")
                    time.sleep(30)  # Wait longer if models are missing
                    continue
                
                print(f"✅ Available models: {models}")
                return True
                
        except Exception as e:
            print(f"⏳ Waiting for Ollama... ({i+1}/{max_retries}) - {str(e)[:50]}...")
        
        time.sleep(10)
    
    print("❌ Ollama failed to start within timeout period")
    return False

def generate_quiz(vectordb, topic_name, student_confidence):
    """Generate quiz questions based on Machine Learning content from textbook"""
    
    # Ensure Ollama is ready
    print("Checking Ollama connection...")
    if not wait_for_ollama():
        print("❌ Ollama is not responding.")
        return None
    
    prompt_template = """
    You are creating quiz questions based on the provided academic content.

    Context from textbook: {context}

    Topic: {question}

    Create exactly 3 multiple-choice questions about "{question}" based on the context provided.

    Requirements:
    - Use the provided context to create relevant questions
    - Each question must have exactly 4 options (A, B, C, D)
    - Only one option should be correct
    - Provide clear explanations
    - Cover different aspects of the topic

    Respond with valid JSON:
    [
      {{
        "question": "Question text here?",
        "options": [
          "A) First option",
          "B) Second option", 
          "C) Third option",
          "D) Fourth option"
        ],
        "answer": "A",
        "explanation": "Explanation of why this answer is correct."
      }}
    ]

    Topic: {question}
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    llm = OllamaLLM(model=OLLAMA_MODEL)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        ),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    print(f"🎯 Generating quiz for: {topic_name}")
    print("📖 Searching textbook for relevant content...")

    try:
        query = f"{topic_name} machine learning"
        response = qa_chain.invoke({"query": query})
        
        raw_response = response["result"]
        source_docs = response.get("source_documents", [])
        
        print(f"📚 Found {len(source_docs)} relevant sections from the textbook")
        
        # Parse JSON response
        json_start_index = raw_response.find("[")
        json_end_index = raw_response.rfind("]") + 1
        
        if json_start_index == -1 or json_end_index == 0:
            print("❌ Could not parse AI response.")
            return None
            
        json_string = raw_response[json_start_index:json_end_index]
        quiz_data = json.loads(json_string)
        
        if not isinstance(quiz_data, list) or len(quiz_data) == 0:
            print("❌ Invalid quiz format generated.")
            return None
            
        print(f"✅ Successfully generated {len(quiz_data)} questions")
        return quiz_data
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"❌ Error generating quiz: {e}")
        return None

# --- Utility Functions ---
def get_all_topics():
    """
    Get all available topics
    
    Returns:
        list: List of all topic names
    """
    return SYLLABUS_TOPICS.copy()

def get_student_summary(student_id):
    """
    Get a summary of student progress
    
    Args:
        student_id (str): Student identifier
    
    Returns:
        dict: Summary including weakest topic, strongest topic, average confidence
    """
    progress = load_student_progress(student_id)
    confidence_scores = progress["confidence_scores"]
    
    weakest_topic = min(confidence_scores, key=confidence_scores.get)
    strongest_topic = max(confidence_scores, key=confidence_scores.get)
    avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
    
    return {
        "student_id": student_id,
        "weakest_topic": weakest_topic,
        "weakest_confidence": confidence_scores[weakest_topic],
        "strongest_topic": strongest_topic,
        "strongest_confidence": confidence_scores[strongest_topic],
        "average_confidence": avg_confidence,
        "total_topics": len(confidence_scores)
    }

def reset_student_progress(student_id):
    """
    Reset student progress to initial state
    
    Args:
        student_id (str): Student identifier
    
    Returns:
        dict: Reset progress data
    """
    progress = {
        "student_id": student_id,
        "confidence_scores": {topic: 0.5 for topic in SYLLABUS_TOPICS}
    }
    save_student_progress(progress)
    print(f"Progress reset for student {student_id}")
    return progress

# --- Main Program (for standalone execution) ---
def main():
    """Main function for standalone execution"""
    create_ml_syllabus()
    
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        print("Please ensure 'MachineLearningTomMitchell.pdf' is in the project directory.")
        return
        
    print("Starting Machine Learning Quiz System...")
    print("Based on Tom Mitchell's 'Machine Learning' textbook")
    print("-" * 50)
    
    vectordb = ingest_pdf()

    student_id = "user123"
    progress = load_student_progress(student_id)
    print(f"\nStudent Progress: {progress}\n")

    weakest_topic = get_next_quiz_topic(progress)
    confidence = progress["confidence_scores"][weakest_topic]
    print(f"Generating quiz for your weakest topic: {weakest_topic}")
    print(f"Current confidence level: {confidence:.2f}\n")

    quiz = generate_quiz(vectordb, weakest_topic, confidence)

    if quiz:
        print("=" * 60)
        print(f"MACHINE LEARNING QUIZ: {weakest_topic}")
        print("=" * 60)
        
        correct_answers = 0
        
        for i, q in enumerate(quiz, 1):
            print(f"\nQuestion {i}: {q['question']}")
            for option in q['options']:
                print(f"  {option}")

            user_answer = input("\nYour answer (A, B, C, D): ").upper().strip()
            
            is_correct = user_answer == q['answer']
            if is_correct:
                correct_answers += 1
                print("✓ Correct!")
            else:
                print(f"✗ Incorrect. The correct answer is {q['answer']}")
            
            if 'explanation' in q:
                print(f"Explanation: {q['explanation']}")
            
            progress = update_confidence_score(progress, weakest_topic, is_correct)
            print("-" * 40)

        print(f"\nQuiz Complete!")
        print(f"Score: {correct_answers}/{len(quiz)} ({correct_answers/len(quiz)*100:.1f}%)")
        print(f"Updated confidence for {weakest_topic}: {progress['confidence_scores'][weakest_topic]:.2f}")
        print(f"\nFull progress: {progress}")
    else:
        print("Unable to generate quiz. Please try running the program again.")

if __name__ == "__main__":
    main()