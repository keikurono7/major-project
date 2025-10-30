import os
import re
import json
import nltk
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# --- Configuration ---
PDF_PATH = "MachineLearningTomMitchell.pdf"
OLLAMA_MODEL = "phi3:mini"  # Lightweight model for quiz generation
EMBEDDING_MODEL = "nomic-embed-text"  # Lightweight embedding model
PROGRESS_FILE_PATH = "progress_user123.json"

# ML Syllabus Topics from Tom Mitchell's book
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

# ------------------ PDF Ingestion ------------------
def ingest_pdf(pdf_path, persist_directory="./db"):
    """Process PDF and create a vector database for retrieval"""
    if os.path.exists(persist_directory):
        print("Vector database already exists. Loading existing database...")
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
    print(f"📚 Processing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
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

# ------------------ Student Progress Functions ------------------
def load_student_progress(student_id="user123"):
    """Load student progress or initialize if it doesn't exist"""
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
    """Save student progress to file"""
    with open(PROGRESS_FILE_PATH, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"✅ Progress saved to {PROGRESS_FILE_PATH}")

def update_confidence_score(progress, topic_name, is_correct):
    """Update confidence score based on quiz performance"""
    score = progress["confidence_scores"].get(topic_name, 0.5)
    if is_correct:
        score = min(1.0, score + 0.1)
    else:
        score = max(0.0, score - 0.1)
    progress["confidence_scores"][topic_name] = score
    save_student_progress(progress)
    return progress

def get_weakest_topic(progress):
    """Get the topic with the lowest confidence score"""
    return min(progress["confidence_scores"], key=progress["confidence_scores"].get)

# ------------------ Parser ------------------
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

# ------------------ Enhanced Quiz Generator ------------------
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

# ------------------ Main Program ------------------
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 Machine Learning Quiz System")
    print("=" * 60)
    
    # Load vector database
    try:
        vectordb = ingest_pdf(PDF_PATH)
    except FileNotFoundError:
        print(f"Error: PDF file not found at {PDF_PATH}")
        print("Please ensure 'MachineLearningTomMitchell.pdf' is in the project directory.")
        exit()
        
    # Load student progress
    student_id = "user123"
    progress = load_student_progress(student_id)
    print(f"\n📊 Student Progress: {json.dumps(progress['confidence_scores'], indent=2)}")
    
    # Determine topic for quiz
    weakest_topic = get_weakest_topic(progress)
    confidence = progress["confidence_scores"][weakest_topic]
    
    print(f"\n📋 Recommended topic: {weakest_topic}")
    print(f"Current confidence level: {confidence:.2f}\n")
    
    # Let user select a topic or use recommendation
    print("Topics:")
    for i, topic in enumerate(SYLLABUS_TOPICS, 1):
        print(f"{i}. {topic} (Confidence: {progress['confidence_scores'][topic]:.2f})")
        
    while True:
        choice = input("\nSelect topic number or press Enter for recommendation: ")
        if not choice.strip():
            selected_topic = weakest_topic
            break
        try:
            topic_num = int(choice)
            if 1 <= topic_num <= len(SYLLABUS_TOPICS):
                selected_topic = SYLLABUS_TOPICS[topic_num-1]
                break
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Please enter a number or press Enter.")
    
    print(f"\n🚀 Generating quiz for: {selected_topic}")
    
    # Generate quiz
    quiz = generate_quiz_with_context(vectordb, selected_topic, progress["confidence_scores"][selected_topic])
    
    if quiz:
        print("=" * 60)
        print(f"MACHINE LEARNING QUIZ: {selected_topic}")
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
                
            # Update confidence after each answer
            progress = update_confidence_score(progress, selected_topic, is_correct)
            print("-" * 60)

        print(f"\n🎉 Quiz Complete!")
        print(f"📊 Score: {correct_answers}/{len(quiz)} ({correct_answers/len(quiz)*100:.1f}%)")
        print(f"📈 Updated confidence for {selected_topic}: {progress['confidence_scores'][selected_topic]:.2f}")
    else:
        print("❌ Unable to generate quiz. Please try running the program again.")
