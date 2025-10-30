import os
import json
import re
import nltk
import difflib
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
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

# Download NLTK resources (only need to run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

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
        print(f"📚 Loading existing vector database from {persist_directory}")
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
    print(f"📚 Processing PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at {pdf_path}")
        return None
        
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
    print("✅ Created ml_syllabus.json file")
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
            "confidence_scores": {},
            "topic_mistakes": {},
            "learning_history": []
        }
        for topic in SYLLABUS_TOPICS:
            progress["confidence_scores"][topic] = 0.5
            progress["topic_mistakes"][topic] = []
        
        save_student_progress(progress)
        return progress

def save_student_progress(progress):
    """Save student progress to file"""
    with open(PROGRESS_FILE_PATH, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"✅ Progress saved to {PROGRESS_FILE_PATH}")

def update_confidence_score(progress, topic_name, is_correct):
    """Update confidence score based on assignment performance"""
    score = progress["confidence_scores"].get(topic_name, 0.5)
    if is_correct:
        score = min(1.0, score + 0.1)
    else:
        score = max(0.0, score - 0.05)
    progress["confidence_scores"][topic_name] = score
    
    # Add to learning history
    timestamp = import_datetime().now().isoformat()
    progress["learning_history"].append({
        "timestamp": timestamp,
        "topic": topic_name,
        "result": "correct" if is_correct else "incorrect",
        "confidence": score
    })
    
    save_student_progress(progress)
    return progress

def import_datetime():
    """Import datetime module on demand"""
    import datetime
    return datetime.datetime

def get_weakest_topics(progress, num=3):
    """Identify topics with lowest confidence scores"""
    sorted_topics = sorted(
        progress["confidence_scores"].items(),
        key=lambda x: x[1]
    )
    return sorted_topics[:num]

# --- Assignment Generation ---
def generate_assignment(vectordb, topic):
    """Generate assignment questions for a specific topic"""
    prompt_template = """
    You are an AI tutor specializing in Machine Learning, specifically working with Tom Mitchell's textbook.
    
    Based on the following context from the textbook, create 3 practice questions about {question}.
    
    Context information:
    {context}
    
    For each question:
    1. Create a clear, specific question that tests understanding of {question}
    2. Provide a detailed model answer that would be considered excellent
    3. Include common misconceptions or mistakes students might make
    4. Specify the difficulty level (easy, medium, or hard)
    
    Format your response as a JSON array:
    [
      {{
        "question": "Question text here",
        "model_answer": "Detailed ideal answer",
        "common_mistakes": ["Mistake 1", "Mistake 2", "Mistake 3"],
        "difficulty": "easy|medium|hard",
        "keywords": ["keyword1", "keyword2", "keyword3"]
      }}
    ]
    
    Ensure the JSON is properly formatted and parse-able.
    """

    # Change input_variables to use "question" instead of "topic"
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    llm = OllamaLLM(model=OLLAMA_MODEL)
    
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6}
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    print(f"📝 Generating questions for topic: {topic}")
    
    try:
        # The key fix: use "question" parameter instead of "topic"
        # RetrievalQA expects "query" for retrieval and "question" for prompt template
        response = qa_chain.invoke({
            "query": topic,
            "question": topic
        })
        
        result = response["result"]
        source_docs = response.get("source_documents", [])
        print(f"📚 Found {len(source_docs)} relevant sections from the textbook")
        
        # Extract JSON from response
        json_match = re.search(r'\[[\s\S]*\]', result)
        if not json_match:
            print("❌ Could not find JSON in response")
            return None
            
        json_str = json_match.group(0)
        questions = json.loads(json_str)
        
        # Add topic to each question
        for q in questions:
            q["topic"] = topic
            
        return questions
        
    except Exception as e:
        print(f"❌ Error generating questions: {str(e)}")
        return None

def generate_multi_topic_assignment(vectordb, progress):
    """Generate comprehensive assignment across multiple topics"""
    # Get weakest topics
    weak_topics = get_weakest_topics(progress, 1)
    
    print("\n🎯 Focusing on your weakest topics:")
    for topic, score in weak_topics:
        print(f"  • {topic} (Confidence: {score:.2f})")
    
    # Generate questions for each topic
    all_questions = []
    
    for topic, score in weak_topics:
        topic_questions = generate_assignment(vectordb, topic)
        if topic_questions:
            all_questions.extend(topic_questions)
        else:
            print(f"⚠️ Could not generate questions for {topic}")
    
    return all_questions

# --- Answer Analysis ---
def clean_text(text):
    """Clean and normalize text for comparison"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    
    return ' '.join(tokens)

def calculate_similarity(text1, text2):
    """Calculate text similarity using multiple methods"""
    # Clean texts
    clean_text1 = clean_text(text1)
    clean_text2 = clean_text(text2)
    
    # Sequence matcher
    sequence_ratio = difflib.SequenceMatcher(None, clean_text1, clean_text2).ratio()
    
    # Word overlap
    words1 = set(clean_text1.split())
    words2 = set(clean_text2.split())
    
    if not words1 or not words2:
        overlap = 0
    else:
        overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
    
    # Combine scores
    return (sequence_ratio + overlap) / 2

def analyze_answer(user_answer, question_data):
    """Analyze user answer against model answer"""
    model_answer = question_data["model_answer"]
    keywords = question_data.get("keywords", [])
    common_mistakes = question_data.get("common_mistakes", [])
    
    # Calculate similarity score
    similarity = calculate_similarity(user_answer, model_answer)
    
    # Check for keywords
    keyword_matches = []
    keyword_misses = []
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', user_answer.lower()):
            keyword_matches.append(keyword)
        else:
            keyword_misses.append(keyword)
    
    # Check for common mistakes
    detected_mistakes = []
    for mistake in common_mistakes:
        mistake_similarity = calculate_similarity(user_answer, mistake)
        if mistake_similarity > 0.7:  # Threshold for mistake detection
            detected_mistakes.append(mistake)
    
    # Calculate score
    if similarity > 0.8:
        score = "excellent"
        is_correct = True
    elif similarity > 0.6:
        score = "good"
        is_correct = True
    elif similarity > 0.4:
        score = "fair"
        is_correct = False
    else:
        score = "needs_improvement"
        is_correct = False
    
    # Generate feedback
    feedback = generate_feedback(
        user_answer, 
        model_answer, 
        keyword_matches, 
        keyword_misses, 
        detected_mistakes,
        score
    )
    
    return {
        "similarity": similarity,
        "score": score,
        "is_correct": is_correct,
        "keyword_matches": keyword_matches,
        "keyword_misses": keyword_misses,
        "detected_mistakes": detected_mistakes,
        "feedback": feedback
    }

def generate_feedback(user_answer, model_answer, keyword_matches, keyword_misses, detected_mistakes, score):
    """Generate personalized feedback based on answer analysis"""
    feedback = []
    
    # Add score-based general feedback
    if score == "excellent":
        feedback.append("Excellent! Your answer matches the key concepts very well.")
    elif score == "good":
        feedback.append("Good answer! You've covered most of the important points.")
    elif score == "fair":
        feedback.append("Fair attempt. There are some key concepts that could be improved.")
    else:
        feedback.append("This answer needs more development. Let's focus on the key concepts.")
    
    # Add keyword feedback
    if keyword_matches:
        feedback.append(f"✓ You correctly included these key concepts: {', '.join(keyword_matches)}")
    
    if keyword_misses:
        feedback.append(f"⚠️ Consider including these important concepts: {', '.join(keyword_misses)}")
    
    # Add mistake feedback
    if detected_mistakes:
        feedback.append("⚠️ Your answer contains some common misconceptions:")
        for mistake in detected_mistakes:
            feedback.append(f"  • {mistake}")
    
    # Suggest improvements if not excellent
    if score != "excellent":
        # Find key differences
        user_words = set(clean_text(user_answer).split())
        model_words = set(clean_text(model_answer).split())
        missing_words = model_words - user_words
        
        important_missing = [w for w in missing_words if w in ' '.join(keyword_misses).lower().split()]
        if important_missing:
            feedback.append("💡 Try to incorporate more specific terminology related to this topic.")
    
    return "\n".join(feedback)

# --- Main Program ---
def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("🎓 MACHINE LEARNING ASSIGNMENT GENERATOR & ANALYZER")
    print("Based on Tom Mitchell's 'Machine Learning' textbook")
    print("=" * 80)
    
    # Create syllabus if it doesn't exist
    if not os.path.exists("ml_syllabus.json"):
        create_ml_syllabus()
        
    # Check for PDF
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: PDF file '{PDF_PATH}' not found!")
        print("Please ensure the textbook file is in the current directory.")
        return
    
    # Load vector database
    vectordb = ingest_pdf()
    if not vectordb:
        print("❌ Failed to create or load vector database")
        return
    
    # Load student progress
    progress = load_student_progress()
    
    print("\n📊 CURRENT TOPIC CONFIDENCE SCORES:")
    for topic, score in sorted(progress["confidence_scores"].items(), key=lambda x: x[1]):
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"{topic}: {bar} {score:.2f}")
    
    # Generate multi-topic assignment
    print("\n📝 Generating your personalized assignment...")
    questions = generate_multi_topic_assignment(vectordb, progress)
    
    if not questions or len(questions) == 0:
        print("❌ Failed to generate assignment questions")
        return
    
    # Display and process questions
    print("\n" + "=" * 80)
    print(f"📚 YOUR MACHINE LEARNING ASSIGNMENT ({len(questions)} questions)")
    print("=" * 80)
    
    results = []
    
    for i, question_data in enumerate(questions, 1):
        topic = question_data["topic"]
        difficulty = question_data.get("difficulty", "medium")
        
        print(f"\n[Question {i} | {topic} | {difficulty}]\n")
        print(question_data["question"])
        print("\nYour answer (type below, press Enter twice when done):")
        
        # Collect multi-line answer
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        
        user_answer = "\n".join(lines)
        
        # Analyze answer
        print("\n📊 Analyzing your answer...")
        analysis = analyze_answer(user_answer, question_data)
        
        # Display feedback
        print("\n" + "-" * 60)
        print(f"FEEDBACK ({analysis['score']})")
        print("-" * 60)
        print(analysis["feedback"])
        print("\n📝 Model Answer:")
        print(question_data["model_answer"])
        print("-" * 60)
        
        # Update progress
        topic = question_data["topic"]
        is_correct = analysis["is_correct"]
        
        # Store answer data
        answer_data = {
            "question": question_data["question"],
            "topic": topic,
            "user_answer": user_answer,
            "model_answer": question_data["model_answer"],
            "analysis": analysis,
            "is_correct": is_correct
        }
        
        results.append(answer_data)
        
        # Update confidence score
        progress = update_confidence_score(progress, topic, is_correct)
        print(f"✅ Updated confidence for {topic}: {progress['confidence_scores'][topic]:.2f}")
        
        input("\nPress Enter to continue to the next question...")
    
    # Display summary
    correct_count = sum(1 for r in results if r["is_correct"])
    print("\n" + "=" * 80)
    print("📋 ASSIGNMENT SUMMARY")
    print(f"Score: {correct_count}/{len(results)} ({correct_count/len(results)*100:.1f}%)")
    print("=" * 80)
    
    # Summarize by topic
    topic_results = {}
    for r in results:
        topic = r["topic"]
        if topic not in topic_results:
            topic_results[topic] = {"correct": 0, "total": 0}
        topic_results[topic]["total"] += 1
        if r["is_correct"]:
            topic_results[topic]["correct"] += 1
    
    print("\nPerformance by topic:")
    for topic, data in topic_results.items():
        correct = data["correct"]
        total = data["total"]
        current_confidence = progress["confidence_scores"][topic]
        print(f"• {topic}: {correct}/{total} correct | Confidence: {current_confidence:.2f}")
    
    # Generate improvement recommendations
    print("\n💡 RECOMMENDATIONS FOR IMPROVEMENT:")
    weak_topics = [t for t, s in progress["confidence_scores"].items() if s < 0.6]
    
    if weak_topics:
        print("Focus on these topics for further study:")
        for topic in weak_topics[:3]:
            print(f"• {topic}")
    else:
        print("Great job! Consider exploring more advanced topics.")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Review the model answers for questions you missed")
    print("2. Study the recommended topics in the textbook")
    print("3. Take another assignment to improve your confidence scores")
    print("\nKeep learning! 📚")

if __name__ == "__main__":
    main()