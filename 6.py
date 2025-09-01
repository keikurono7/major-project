import os
import re
import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# --- Configuration ---
PDF_PATH = "MachineLearningTomMitchell.pdf"
OLLAMA_MODEL = "phi3:mini"  # Lightweight model for assignment generation
EMBEDDING_MODEL = "nomic-embed-text"  # Lightweight embedding model
PROGRESS_FILE_PATH = "progress_user123.json"

# Download NLTK resources (only need to run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

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

def update_confidence_score(progress, topic_name, score_percentage):
    """Update confidence score based on assignment performance"""
    current_score = progress["confidence_scores"].get(topic_name, 0.5)
    
    # Calculate change based on performance (0 to 1.0)
    # Performance below 0.5 decreases confidence, above 0.5 increases
    change = (score_percentage - 0.5) * 0.4  # Scale factor for confidence change
    
    # Update score with limits
    new_score = max(0.1, min(0.9, current_score + change))
    progress["confidence_scores"][topic_name] = new_score
    
    save_student_progress(progress)
    return progress

def get_weakest_topic(progress):
    """Get the topic with the lowest confidence score"""
    return min(progress["confidence_scores"], key=progress["confidence_scores"].get)

# ------------------ Text Processing for Answer Analysis ------------------
def clean_text(text):
    """Clean and normalize text for comparison"""
    if not text:
        return []
        
    # Convert to lowercase and tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    
    return tokens

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts using TF-IDF and cosine similarity"""
    if not text1 or not text2:
        return 0.0
        
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity
    except:
        return 0.0

# Add this function after your existing imports and before other functions
def clean_json_string(json_str):
    """Remove control characters and other problematic characters from JSON string"""
    # Remove control characters that break JSON parsing
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
    # Fix common JSON formatting issues
    cleaned = cleaned.replace('\\"', '"')  # Fix escaped quotes
    cleaned = cleaned.replace('\\n', ' ')  # Replace newlines with spaces
    return cleaned

# Add this new function for LLM-based answer analysis
def llm_analyze_answer(user_answer, question_data, model=OLLAMA_MODEL):
    """Use phi3:mini to semantically analyze student answers"""
    if not user_answer.strip():
        return {
            "score": 0.0,
            "concepts_covered": [],
            "concepts_missing": question_data.get("key_concepts", []),
            "misconceptions": [],
            "feedback": "No answer provided."
        }
    
    # Extract question components
    question = question_data.get("question", "")
    model_answer = question_data.get("model_answer", "")
    key_concepts = question_data.get("key_concepts", [])
    misconceptions = question_data.get("common_misconceptions", [])
    
    # Create evaluation prompt for the LLM
    prompt = f"""
    You are a Machine Learning professor grading a student's answer.
    
    QUESTION:
    {question}
    
    STUDENT'S ANSWER:
    {user_answer}
    
    MODEL ANSWER:
    {model_answer}
    
    KEY CONCEPTS THAT SHOULD BE COVERED:
    {", ".join(key_concepts)}
    
    COMMON MISCONCEPTIONS TO WATCH FOR:
    {", ".join(misconceptions)}
    
    Evaluate how well the student's answer demonstrates understanding. Focus on concepts, not exact wording.
    A perfect answer doesn't need to match the model answer word-for-word but should demonstrate understanding of all key concepts.
    
    Provide your evaluation in this JSON format ONLY:
    {{
      "score": 0.75, // Score from 0.0 to 1.0
      "concepts_covered": ["concept1", "concept2"], // List key concepts student covered well
      "concepts_missing": ["concept3"], // List key concepts student missed or didn't adequately explain
      "misconceptions": ["specific error in reasoning"], // List any misconceptions or errors
      "feedback": "Brief, specific feedback to help the student improve"
    }}
    """
    
    # Call the LLM for evaluation
    llm = OllamaLLM(model=model)
    
    try:
        # Get LLM evaluation
        response = llm.invoke(prompt)
        
        # Extract JSON from response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        
        if json_start >= 0 and json_end > 0:
            # Extract and clean JSON
            json_str = response[json_start:json_end]
            cleaned_json = clean_json_string(json_str)
            
            # Parse JSON
            analysis = json.loads(cleaned_json)
            
            # Ensure all required fields exist
            analysis.setdefault("score", 0.5)
            analysis.setdefault("concepts_covered", [])
            analysis.setdefault("concepts_missing", [])
            analysis.setdefault("misconceptions", [])
            analysis.setdefault("feedback", "No specific feedback provided.")
            
            return analysis
        else:
            # Fallback to traditional analysis if no JSON found
            print("⚠️ LLM didn't return proper JSON. Using fallback analysis.")
            return fallback_analyze(user_answer, question_data)
    except Exception as e:
        print(f"⚠️ Error in LLM analysis: {e}. Using fallback analysis.")
        return fallback_analyze(user_answer, question_data)

# Rename original analyze_answer to fallback_analyze
def fallback_analyze(user_answer, question_data):
    """Fallback analysis using traditional NLP methods"""
    model_answer = question_data.get("model_answer", "")
    
    # Clean texts
    clean_user = " ".join(clean_text(user_answer))
    clean_model = " ".join(clean_text(model_answer))
    
    # Calculate similarity
    similarity = calculate_similarity(clean_user, clean_model)
    
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
    
    # Return in the new format for compatibility
    return {
        "score": score,
        "concepts_covered": keyword_matches,
        "concepts_missing": keyword_misses,
        "misconceptions": detected_mistakes,
        "feedback": "Analysis performed using traditional NLP methods."
    }

# Create a new feedback generator for the LLM-based analysis
def generate_llm_feedback(analysis, model_answer):
    """Generate comprehensive feedback based on LLM analysis"""
    feedback = []
    
    # Score-based feedback
    score = analysis.get("score", 0)
    if score >= 0.8:
        feedback.append("✅ Excellent answer! You demonstrated strong understanding of the concept.")
    elif score >= 0.6:
        feedback.append("✓ Good answer with some room for improvement.")
    elif score >= 0.4:
        feedback.append("⚠️ Partial understanding shown, but some important concepts are missing.")
    else:
        feedback.append("❌ Your answer needs significant improvement.")
    
    # Add specific feedback from LLM
    if "feedback" in analysis and analysis["feedback"]:
        feedback.append(f"\n💬 Feedback: {analysis['feedback']}")
    
    # Concept coverage feedback
    concepts_covered = analysis.get("concepts_covered", [])
    if concepts_covered:
        feedback.append("\n✓ You correctly addressed these key concepts:")
        for concept in concepts_covered:
            feedback.append(f"   • {concept}")
    
    concepts_missing = analysis.get("concepts_missing", [])
    if concepts_missing:
        feedback.append("\n⚠️ Your answer should also address:")
        for concept in concepts_missing:
            feedback.append(f"   • {concept}")
    
    # Misconception feedback
    misconceptions = analysis.get("misconceptions", [])
    if misconceptions:
        feedback.append("\n❌ Your answer contains some misconceptions or errors:")
        for misconception in misconceptions:
            feedback.append(f"   • {misconception}")
    
    # Model answer
    feedback.append("\n📝 Sample answer:")
    feedback.append(model_answer)
    
    return "\n".join(feedback)

# ------------------ Assignment Generation ------------------
def generate_assignment_with_context(vectordb, topic_name):
    """Generate theory questions with model answers using context from the textbook"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"📝 Generating assignment for topic: {topic_name}")
    print(f"📚 Retrieved {len(docs)} relevant passages from textbook")
    
    # Create the prompt with context
    prompt = f"""
    You are an AI tutor specializing in Machine Learning. Generate 3 theory questions about "{topic_name}" based on the following textbook content:

    {context[:3000]}  # Using a larger context for better question generation

    For each question:
    1. Create a clear, specific question that tests understanding of {topic_name}
    2. Provide a detailed model answer that would be considered excellent
    3. List 5-8 key concepts that should be present in a good answer
    4. Include 2-3 common misconceptions students might have
    5. Specify the difficulty level (easy, medium, or hard)

    Format as valid JSON:
    [
      {{
        "question": "Detailed question text here?",
        "model_answer": "Comprehensive model answer here...",
        "key_concepts": ["Concept 1", "Concept 2", "Concept 3", "Concept 4", "Concept 5"],
        "common_misconceptions": ["Misconception 1", "Misconception 2"],
        "difficulty": "medium"
      }}
    ]
    """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    
    try:
        raw_output = llm.invoke(prompt)
        
        # Extract JSON from the output
        json_start = raw_output.find("[")
        json_end = raw_output.rfind("]") + 1
        
        if json_start >= 0 and json_end > 0:
            json_str = raw_output[json_start:json_end]
            assignment = json.loads(json_str)
            
            print(f"✅ Successfully generated {len(assignment)} questions")
            return assignment
        else:
            print("❌ Failed to extract valid JSON from model output")
            return None
    except Exception as e:
        print(f"❌ Error generating assignment: {e}")
        return None

def generate_multi_topic_assignment(vectordb, progress):
    """Generate an assignment with questions from multiple topics"""
    # Get the 3 weakest topics
    sorted_topics = sorted(progress["confidence_scores"].items(), key=lambda x: x[1])
    weakest_topics = [topic for topic, score in sorted_topics[:3]]
    
    print(f"🎯 Generating assignment covering your weakest topics: {', '.join(weakest_topics)}")
    
    all_questions = []
    for topic in weakest_topics:
        questions = generate_assignment_with_context(vectordb, topic)
        if questions:
            # Add topic to each question for reference
            for q in questions:
                q["topic"] = topic
            all_questions.extend(questions)
    
    return all_questions

# ------------------ Main Program ------------------
if __name__ == "__main__":
    print("=" * 60)
    print("📝 Machine Learning Assignment System")
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
    
    # Determine topic for assignment
    weakest_topic = get_weakest_topic(progress)
    confidence = progress["confidence_scores"][weakest_topic]
    
    print(f"\n📋 Recommended topic: {weakest_topic}")
    print(f"Current confidence level: {confidence:.2f}\n")
    
    # Let user select assignment type
    print("Assignment Options:")
    print("1. Single topic assignment (focused practice)")
    print("2. Multi-topic assignment (covers your weakest 3 areas)")
    
    while True:
        choice = input("\nSelect option (1-2): ")
        if choice == "1":
            # Let user select a topic or use recommendation
            print("\nTopics:")
            for i, topic in enumerate(SYLLABUS_TOPICS, 1):
                print(f"{i}. {topic} (Confidence: {progress['confidence_scores'][topic]:.2f})")
                
            while True:
                topic_choice = input("\nSelect topic number or press Enter for recommendation: ")
                if not topic_choice.strip():
                    selected_topic = weakest_topic
                    break
                try:
                    topic_num = int(topic_choice)
                    if 1 <= topic_num <= len(SYLLABUS_TOPICS):
                        selected_topic = SYLLABUS_TOPICS[topic_num-1]
                        break
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Please enter a number or press Enter.")
            
            print(f"\n🚀 Generating assignment for: {selected_topic}")
            assignment = generate_assignment_with_context(vectordb, selected_topic)
            single_topic_mode = True
            break
            
        elif choice == "2":
            print("\n🚀 Generating multi-topic assignment covering your weakest areas...")
            assignment = generate_multi_topic_assignment(vectordb, progress)
            single_topic_mode = False
            break
        else:
            print("Invalid option. Please select 1 or 2.")
    
    if assignment:
        print("=" * 60)
        print("📝 MACHINE LEARNING ASSIGNMENT")
        print("=" * 60)
        
        # Track scores for each topic
        topic_scores = {}
        
        # Display all questions first
        for i, q in enumerate(assignment, 1):
            topic = q.get("topic", selected_topic if single_topic_mode else "Unknown")
            difficulty = q.get("difficulty", "medium")
            
            print(f"\nQuestion {i}: [{topic}] - Difficulty: {difficulty}")
            print(q["question"])
            print("\n" + "-" * 60)
        
        # Now collect answers and provide feedback
        print("\n" + "=" * 60)
        print("Please answer each question. Type your answers carefully.")
        print("=" * 60)
        
        for i, q in enumerate(assignment, 1):
            topic = q.get("topic", selected_topic if single_topic_mode else "Unknown")
            
            print(f"\nQuestion {i}: [{topic}]")
            print(q["question"])
            
            print("\nYour answer (type below, press Enter twice when finished):")
            user_answer = ""
            while True:
                line = input()
                if line.strip() == "":
                    break
                user_answer += line + "\n"
            
            # Analyze answer
            analysis = analyze_answer(user_answer, q)
            
            # Generate feedback
            feedback = generate_feedback(
                user_answer,
                q["model_answer"],
                analysis["keyword_matches"],
                analysis["keyword_misses"],
                analysis["detected_mistakes"],
                analysis["score"]
            )
            
            print("\n" + "=" * 60)
            print(f"FEEDBACK FOR QUESTION {i}")
            print("-" * 60)
            print(feedback)
            print("-" * 60)
            print(f"Score: {analysis['score']*100:.1f}%")
            print("=" * 60)
            
            # Track topic scores
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(analysis["score"])
        
        # Update confidence scores for each topic
        print("\n📊 ASSIGNMENT RESULTS")
        print("-" * 60)
        
        for topic, scores in topic_scores.items():
            avg_score = sum(scores) / len(scores)
            progress = update_confidence_score(progress, topic, avg_score)
            print(f"Topic: {topic}")
            print(f"Average Score: {avg_score*100:.1f}%")
            print(f"Updated Confidence: {progress['confidence_scores'][topic]:.2f}")
            print("-" * 30)
        
        print("\n🎉 Assignment Complete!")
    else:
        print("❌ Unable to generate assignment. Please try running the program again.")