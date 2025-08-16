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
OLLAMA_MODEL = "mistral:7b"  # Keep this for LLM generation
EMBEDDING_MODEL = "nomic-embed-text"  # Light embedding model
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
def ingest_pdf(pdf_path, persist_directory="./db"):
    if os.path.exists(persist_directory):
        print("Vector database already exists. Loading existing database...")
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)  # Use light model for embeddings
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    print("Ingesting Machine Learning PDF and creating vector database...")
    print("Using lightweight embedding model for faster processing...")
    
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    # Smaller chunks for faster processing
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Smaller chunks for faster embedding
        chunk_overlap=100,  # Less overlap
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    docs = text_splitter.split_documents(documents)

    print(f"Split PDF into {len(docs)} chunks...")
    print("Creating embeddings (this may take a few minutes)...")

    # Use lightweight embedding model
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    # Process in smaller batches to avoid memory issues
    batch_size = 50
    all_docs = docs
    
    if len(docs) > batch_size:
        print(f"Processing in batches of {batch_size} for better performance...")
        # Create vector database with first batch
        first_batch = docs[:batch_size]
        vectordb = Chroma.from_documents(
            documents=first_batch, 
            embedding=embeddings, 
            persist_directory=persist_directory
        )
        
        # Add remaining documents in batches
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
                    {
                        "name": "Well-Posed Learning Problems",
                        "sub_topics": [
                            "Definition of learning problems",
                            "Components of learning problems",
                            "Problem formulation"
                        ]
                    },
                    {
                        "name": "Designing a Learning System",
                        "sub_topics": [
                            "System architecture",
                            "Learning components",
                            "Performance metrics"
                        ]
                    },
                    {
                        "name": "Perspectives and Issues in Machine Learning",
                        "sub_topics": [
                            "Different learning paradigms",
                            "Key challenges",
                            "Evaluation methods"
                        ]
                    },
                    {
                        "name": "Concept Learning Task",
                        "sub_topics": [
                            "Concept definition",
                            "Training examples",
                            "Target concept"
                        ]
                    },
                    {
                        "name": "Concept Learning as Search",
                        "sub_topics": [
                            "Hypothesis space",
                            "Search strategies",
                            "General-to-specific ordering"
                        ]
                    },
                    {
                        "name": "Find-S Algorithm",
                        "sub_topics": [
                            "Algorithm steps",
                            "Maximally specific hypothesis",
                            "Limitations"
                        ]
                    },
                    {
                        "name": "Version Spaces and Candidate-Elimination Algorithm",
                        "sub_topics": [
                            "Version space definition",
                            "Candidate elimination",
                            "General and specific boundaries"
                        ]
                    },
                    {
                        "name": "Inductive Bias",
                        "sub_topics": [
                            "Bias definition",
                            "Types of bias",
                            "Role in learning"
                        ]
                    }
                ]
            },
            {
                "module": "MODULE-2", 
                "topics": [
                    {
                        "name": "Sequential Covering Algorithms",
                        "sub_topics": [
                            "Algorithm overview",
                            "Rule learning process",
                            "Coverage and accuracy"
                        ]
                    },
                    {
                        "name": "Learning Rule Sets",
                        "sub_topics": [
                            "Example-based methods",
                            "Rule representation",
                            "Rule evaluation"
                        ]
                    },
                    {
                        "name": "Learning First-Order Rules",
                        "sub_topics": [
                            "First-order logic",
                            "Rule induction",
                            "Predicate learning"
                        ]
                    },
                    {
                        "name": "FOIL Algorithm",
                        "sub_topics": [
                            "FOIL overview",
                            "First-order inductive learner",
                            "Algorithm implementation"
                        ]
                    },
                    {
                        "name": "Explanation-Based Learning",
                        "sub_topics": [
                            "EBL principles",
                            "Domain theories",
                            "Explanation construction"
                        ]
                    },
                    {
                        "name": "Perfect Domain Theories",
                        "sub_topics": [
                            "Complete domain knowledge",
                            "Deductive learning",
                            "Theory refinement"
                        ]
                    },
                    {
                        "name": "Learning Search Control Knowledge",
                        "sub_topics": [
                            "Search control strategies",
                            "Knowledge acquisition",
                            "Performance improvement"
                        ]
                    },
                    {
                        "name": "Inductive-Analytical Approaches",
                        "sub_topics": [
                            "Hybrid learning methods",
                            "Combining induction and analysis",
                            "Synergistic effects"
                        ]
                    }
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
    try:
        with open(PROGRESS_FILE_PATH, "r") as f:
            existing_progress = json.load(f)
            
        # Check if the existing progress has the correct ML topics
        ml_topics = set(SYLLABUS_TOPICS)
        existing_topics = set(existing_progress.get("confidence_scores", {}).keys())
        
        # If topics don't match, create new progress with ML topics
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
        # Create new progress file with ML topics
        progress = {
            "student_id": student_id,
            "confidence_scores": {topic: 0.5 for topic in SYLLABUS_TOPICS}
        }
        save_student_progress(progress)
        return progress

def save_student_progress(progress):
    with open(PROGRESS_FILE_PATH, "w") as f:
        json.dump(progress, f, indent=2)

def update_confidence_score(progress, topic_name, is_correct):
    score = progress["confidence_scores"].get(topic_name, 0.5)
    if is_correct:
        score = min(1.0, score + 0.1)
    else:
        score = max(0.0, score - 0.1)
    progress["confidence_scores"][topic_name] = score
    save_student_progress(progress)
    return progress

def get_next_quiz_topic(progress):
    return min(progress["confidence_scores"], key=progress["confidence_scores"].get)

# --- Enhanced Quiz Generation ---
def generate_quiz(vectordb, topic_name, student_confidence):
    """Generate quiz questions based on Machine Learning content from Tom Mitchell's book"""
    
    # Completely generalized prompt without bias
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

    print(f"Generating quiz for: {topic_name}")
    print("Searching textbook for relevant content...")

    try:
        query = f"{topic_name} machine learning"
        response = qa_chain.invoke({"query": query})
        
        raw_response = response["result"]
        source_docs = response.get("source_documents", [])
        
        print(f"Found {len(source_docs)} relevant sections from the textbook")
        
        # Parse JSON response
        json_start_index = raw_response.find("[")
        json_end_index = raw_response.rfind("]") + 1
        
        if json_start_index == -1 or json_end_index == 0:
            print("Could not parse response. Please try again.")
            return None
            
        json_string = raw_response[json_start_index:json_end_index]
        quiz_data = json.loads(json_string)
        
        if not isinstance(quiz_data, list) or len(quiz_data) == 0:
            print("Invalid quiz format generated. Please try again.")
            return None
            
        return quiz_data
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error generating quiz: {e}")
        print("Please try again.")
        return None

# --- Main Program Loop ---
if __name__ == "__main__":
    # Create ML syllabus file
    create_ml_syllabus()
    
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        print("Please ensure 'MachineLearningTomMitchell.pdf' is in the project directory.")
    else:
        print("Starting Machine Learning Quiz System...")
        print("Based on Tom Mitchell's 'Machine Learning' textbook")
        print("-" * 50)
        
        vectordb = ingest_pdf(PDF_PATH)

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
