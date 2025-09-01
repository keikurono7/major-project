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
PROGRESS_FILE_PATH = "assignment_progress.json"

# ML Syllabus Topics
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
def ingest_pdf(pdf_path=PDF_PATH, persist_directory="./assignment_db"):
    """Process PDF and create a vector database for retrieval"""
    if os.path.exists(persist_directory):
        print(f"Loading existing vector database from {persist_directory}")
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
    print(f"Processing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None
        
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split PDF into {len(chunks)} chunks")
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    print("Creating vector database...")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print("Vector database created and persisted")
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
def load_student_progress(student_id="user123"):
    """Load student progress or initialize if it doesn't exist"""
    try:
        with open(PROGRESS_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        progress = {
            "student_id": student_id,
            "confidence_scores": {}
        }
        for topic in SYLLABUS_TOPICS:
            progress["confidence_scores"][topic] = 0.5
        
        save_student_progress(progress)
        return progress

def save_student_progress(progress):
    """Save student progress to file"""
    with open(PROGRESS_FILE_PATH, "w") as f:
        json.dump(progress, f, indent=2)

def update_confidence_score(progress, topic_name, is_correct):
    """Update confidence score based on assignment performance"""
    score = progress["confidence_scores"].get(topic_name, 0.5)
    if is_correct:
        score = min(1.0, score + 0.1)
    else:
        score = max(0.0, score - 0.05)
    progress["confidence_scores"][topic_name] = score
    save_student_progress(progress)
    return progress

def get_weakest_topic(progress):
    """Identify topic with lowest confidence score"""
    return min(progress["confidence_scores"], key=progress["confidence_scores"].get)

# --- Assignment Generation ---
def generate_assignment(vectordb, topic_name, student_confidence):
    """Generate assignment questions based on Machine Learning content"""
    # Template for assignment generation
    prompt_template = """
    You are an AI tutor specializing in Machine Learning, specifically working from Tom Mitchell's textbook.
    
    Based on the following context from the textbook, create 10 practice assignment questions about {question}.
    These should be designed to help a student improve their understanding of this topic.
    
    The student's current confidence in this topic is {confidence_level}/1.0, so adapt the difficulty accordingly.
    
    Context information:
    {context}
    
    Create 10 practice questions with the following characteristics:
    - A mix of question types (short answer, fill in the blank, etc.)
    - Each question should require the student to demonstrate understanding (not just memorization)
    - Include at least 2 questions that require application of concepts to new scenarios
    - Include at least 1 question that connects this topic to related Machine Learning concepts
    - Provide the correct answer or solution approach after each question
    
    Format your response as a JSON array:
    [
      {
        "question": "Question text here",
        "question_type": "short_answer|multiple_choice|fill_blank|conceptual|application",
        "answer": "Correct answer or solution approach",
        "difficulty": "easy|medium|hard"
      }
    ]
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question", "confidence_level"]
    )

    llm = OllamaLLM(model=OLLAMA_MODEL)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6}  # Retrieve more context for assignments
        ),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    print(f"📚 Generating assignments for: {topic_name}")
    print("🔍 Searching textbook for relevant content...")

    try:
        query = f"{topic_name} machine learning"
        response = qa_chain.invoke({"query": query, "confidence_level": student_confidence})
        
        raw_response = response["result"]
        source_docs = response.get("source_documents", [])
        
        print(f"📄 Found {len(source_docs)} relevant sections from the textbook")
        
        # Parse JSON response
        try:
            # Find JSON array in response
            json_start = raw_response.find("[")
            json_end = raw_response.rfind("]") + 1
            
            if json_start == -1 or json_end == 0:
                print("❌ Failed to find JSON in response")
                return None
                
            json_string = raw_response[json_start:json_end]
            assignment_data = json.loads(json_string)
            
            if not isinstance(assignment_data, list) or len(assignment_data) == 0:
                print("❌ Invalid assignment data format")
                return None
                
            return assignment_data
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating assignment: {e}")
        return None

# --- Main Program (for standalone execution) ---
def main():
    """Main function for standalone execution"""
    # Create ML syllabus file if it doesn't exist
    create_ml_syllabus()
    
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        print("Please ensure 'MachineLearningTomMitchell.pdf' is in the project directory.")
        return
        
    print("🎓 Starting Machine Learning Assignment Generator")
    print("📚 Based on Tom Mitchell's 'Machine Learning' textbook")
    print("-" * 60)
    
    vectordb = ingest_pdf()
    if not vectordb:
        print("Failed to create or load vector database")
        return

    student_id = "user123"
    progress = load_student_progress(student_id)
    print(f"\nStudent Progress: {progress}\n")

    weakest_topic = get_weakest_topic(progress)
    confidence = progress["confidence_scores"][weakest_topic]
    print(f"Generating assignments for your weakest topic: {weakest_topic}")
    print(f"Current confidence level: {confidence:.2f}\n")

    assignment = generate_assignment(vectordb, weakest_topic, confidence)

    if assignment:
        print("=" * 80)
        print(f"MACHINE LEARNING ASSIGNMENT: {weakest_topic.upper()}")
        print(f"This assignment contains 10 questions to help you improve on this topic.")
        print("=" * 80)
        
        completed = 0
        
        for i, q in enumerate(assignment, 1):
            print(f"\nQuestion {i} [{q.get('difficulty', 'medium')} - {q.get('question_type', 'practice')}]")
            print(f"{q['question']}")
            
            input("\nPress Enter when you are ready to see the answer...")
            
            print(f"\nAnswer/Solution: {q['answer']}")
            
            is_correct = input("\nDid you answer correctly? (y/n): ").lower().strip() == 'y'
            if is_correct:
                completed += 1
            
            progress = update_confidence_score(progress, weakest_topic, is_correct)
            print("-" * 40)

        print(f"\nAssignment Complete!")
        print(f"Score: {completed}/10 ({completed/10*100:.1f}%)")
        print(f"Updated confidence for {weakest_topic}: {progress['confidence_scores'][weakest_topic]:.2f}")
        print(f"\nKeep practicing to improve your confidence in this topic.")
        print("\nFull progress:", json.dumps(progress["confidence_scores"], indent=2))
    else:
        print("❌ Unable to generate assignment. Please try running the program again.")

if __name__ == "__main__":
    main()