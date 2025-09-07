import os
import re
import json
import nltk
import random
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from datetime import datetime

# --- Configuration ---
PDF_PATH = "MachineLearningTomMitchell.pdf"
OLLAMA_MODEL = "phi3:mini"  # Lightweight model for question generation
EMBEDDING_MODEL = "nomic-embed-text"  # Lightweight embedding model
QUESTIONS_PER_TOPIC = 2  # Number of questions per topic (1 theory + 1 practical)
OUTPUT_DIR = "./question_papers"  # Directory to save question papers

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

# ------------------ Question Generation ------------------
def clean_json_string(json_str):
    """Remove control characters and other problematic characters from JSON string"""
    # Remove control characters that break JSON parsing
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
    # Fix common JSON formatting issues
    cleaned = cleaned.replace('\\"', '"')  # Fix escaped quotes
    cleaned = cleaned.replace('\\n', ' ')  # Replace newlines with spaces
    return cleaned

def generate_theoretical_question(vectordb, topic_name, max_retries=2):
    """Generate a theoretical question about a topic"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"🧠 Generating theoretical question for: {topic_name}")
    
    # Create the prompt with context
    prompt = f"""
    Based on the following textbook content about {topic_name}:

    {context[:2000]}
    
    Create 1 theoretical question that tests deep understanding of the concept of {topic_name} in Machine Learning.
    
    The question should:
    - Require explanation and discussion of key concepts
    - Test understanding rather than simple recall
    - Be appropriate for a university-level examination
    
    Format the response in JSON:
    {{
      "question": "The theoretical question text here?",
      "answer_guidelines": "Key points that should be covered in a complete answer",
      "type": "theoretical",
      "topic": "{topic_name}",
      "estimated_time_minutes": 15,
      "marks": 10
    }}

    Return ONLY the JSON with no additional text.
    """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    
    for attempt in range(max_retries + 1):
        try:
            raw_output = llm.invoke(prompt)
            
            # Extract JSON from the output
            json_start = raw_output.find("{")
            json_end = raw_output.rfind("}") + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = raw_output[json_start:json_end]
                # Clean the JSON string before parsing
                clean_str = clean_json_string(json_str)
                question_data = json.loads(clean_str)
                
                return question_data
            else:
                print(f"⚠️ Could not find valid JSON in theoretical question output (attempt {attempt+1})")
                if attempt < max_retries:
                    continue
        except Exception as e:
            print(f"❌ Error generating theoretical question: {e}")
            if attempt < max_retries:
                continue
    
    # Fallback question if all attempts fail
    return {
        "question": f"Explain the key concepts and significance of {topic_name} in Machine Learning.",
        "answer_guidelines": f"A good answer should define {topic_name}, explain its importance in machine learning, and discuss its applications.",
        "type": "theoretical",
        "topic": topic_name,
        "estimated_time_minutes": 15,
        "marks": 10
    }

def generate_practical_question(vectordb, topic_name, max_retries=2):
    """Generate a practical/application question about a topic"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning application")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"⚙️ Generating practical question for: {topic_name}")
    
    # Create the prompt with context
    prompt = f"""
    Based on the following textbook content about {topic_name}:

    {context[:2000]}
    
    Create 1 practical/application-based question related to {topic_name} in Machine Learning.
    
    The question should:
    - Involve applying the concept to a practical scenario
    - Require problem-solving skills
    - Test application rather than just theory
    - Be appropriate for a university-level examination
    
    Format the response in JSON:
    {{
      "question": "The practical/application question text here",
      "answer_guidelines": "Key points that should be covered in a complete answer",
      "type": "practical",
      "topic": "{topic_name}",
      "estimated_time_minutes": 15,
      "marks": 10
    }}

    Return ONLY the JSON with no additional text.
    """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    
    for attempt in range(max_retries + 1):
        try:
            raw_output = llm.invoke(prompt)
            
            # Extract JSON from the output
            json_start = raw_output.find("{")
            json_end = raw_output.rfind("}") + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = raw_output[json_start:json_end]
                # Clean the JSON string before parsing
                clean_str = clean_json_string(json_str)
                question_data = json.loads(clean_str)
                
                return question_data
            else:
                print(f"⚠️ Could not find valid JSON in practical question output (attempt {attempt+1})")
                if attempt < max_retries:
                    continue
        except Exception as e:
            print(f"❌ Error generating practical question: {e}")
            if attempt < max_retries:
                continue
    
    # Fallback question if all attempts fail
    return {
        "question": f"Apply the concept of {topic_name} to solve a real-world machine learning problem. Describe your approach in detail.",
        "answer_guidelines": f"A good answer should demonstrate application of {topic_name} concepts to solve a specific problem, with clear methodology and expected outcomes.",
        "type": "practical",
        "topic": topic_name,
        "estimated_time_minutes": 15,
        "marks": 10
    }

def generate_multiple_choice_question(vectordb, topic_name, max_retries=2):
    """Generate a multiple choice question about a topic"""
    # Get relevant content from vector database
    retriever = vectordb.as_retriever(search_kwargs={"k": 2})
    docs = retriever.get_relevant_documents(f"{topic_name} machine learning")
    context = "\n\n".join([doc.page_content for doc in docs])
    
    print(f"📝 Generating MCQ for: {topic_name}")
    
    # Create the prompt with context
    prompt = f"""
    Based on the following textbook content about {topic_name}:

    {context[:1500]}
    
    Create 1 challenging multiple-choice question about {topic_name} in Machine Learning.
    
    Format the response in JSON:
    {{
      "question": "The question text here?",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "correct_answer": "A",
      "explanation": "Why this is the correct answer",
      "type": "multiple_choice",
      "topic": "{topic_name}",
      "marks": 5
    }}

    Return ONLY the JSON with no additional text.
    """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    
    for attempt in range(max_retries + 1):
        try:
            raw_output = llm.invoke(prompt)
            
            # Extract JSON from the output
            json_start = raw_output.find("{")
            json_end = raw_output.rfind("}") + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = raw_output[json_start:json_end]
                # Clean the JSON string before parsing
                clean_str = clean_json_string(json_str)
                question_data = json.loads(clean_str)
                
                # Validate the MCQ data
                if (len(question_data.get("options", [])) == 4 and 
                    question_data.get("correct_answer") in ["A", "B", "C", "D"]):
                    return question_data
                else:
                    print("⚠️ Generated MCQ has invalid format")
            else:
                print(f"⚠️ Could not find valid JSON in MCQ output (attempt {attempt+1})")
            
            if attempt < max_retries:
                continue
        except Exception as e:
            print(f"❌ Error generating MCQ: {e}")
            if attempt < max_retries:
                continue
    
    # Fallback MCQ if all attempts fail
    return {
        "question": f"Which of the following best describes {topic_name}?",
        "options": [
            f"A) A fundamental concept in {topic_name}",
            "B) A machine learning algorithm from the 1990s",
            "C) A statistical method unrelated to machine learning",
            "D) A hardware optimization technique"
        ],
        "correct_answer": "A",
        "explanation": f"This is a fallback question. {topic_name} is indeed a fundamental concept in machine learning.",
        "type": "multiple_choice",
        "topic": topic_name,
        "marks": 5
    }

# ------------------ Question Paper Generation ------------------
def generate_question_paper(vectordb, topics=None, questions_per_topic=2):
    """Generate a complete question paper with equal coverage of all topics - LONG ANSWER ONLY"""
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
        question_paper["sections"][0]["questions"].append(theo_q)
        question_paper["total_marks"] += theo_q.get("marks", 10)
    
    # Generate practical questions (1 per topic)
    for topic in topics:
        prac_q = generate_practical_question(vectordb, topic)
        question_paper["sections"][1]["questions"].append(prac_q)
        question_paper["total_marks"] += prac_q.get("marks", 10)
    
    # Calculate estimated duration (long answers take more time)
    all_questions = (question_paper["sections"][0]["questions"] + 
                    question_paper["sections"][1]["questions"])
    
    # Increase time per question since they're all long-answer format now
    estimated_minutes = sum(q.get("estimated_time_minutes", 20) for q in all_questions)
    question_paper["duration_minutes"] = max(180, estimated_minutes)  # At least 3 hours
    
    print(f"✅ Question paper generated with {len(all_questions)} long-answer questions")
    print(f"📊 Total marks: {question_paper['total_marks']}")
    print(f"⏱️ Estimated duration: {question_paper['duration_minutes'] // 60} hours {question_paper['duration_minutes'] % 60} minutes")
    
    return question_paper

# ------------------ Export Functions ------------------
def save_question_paper(question_paper, include_answers=False):
    """Save the question paper to a text file"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/question_paper_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
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
                f.write(f"{q['question']}\n\n")
                
                if q["type"] == "multiple_choice":
                    for option in q["options"]:
                        f.write(f"  {option}\n")
                    f.write("\n")
                    
                    if include_answers:
                        f.write(f"Correct Answer: {q['correct_answer']}\n")
                        f.write(f"Explanation: {q['explanation']}\n\n")
                
                elif include_answers and "answer_guidelines" in q:
                    f.write("Answer Guidelines:\n")
                    f.write(f"{q['answer_guidelines']}\n\n")
            
            f.write("\n")
    
    print(f"📄 Question paper saved to {filename}")
    return filename

# ------------------ Main Program ------------------
if __name__ == "__main__":
    print("=" * 60)
    print("📝 Machine Learning Question Paper Generator")
    print("=" * 60)
    
    # Load vector database
    try:
        vectordb = ingest_pdf(PDF_PATH)
    except FileNotFoundError:
        print(f"Error: PDF file not found at {PDF_PATH}")
        print("Please ensure 'MachineLearningTomMitchell.pdf' is in the project directory.")
        exit()
    
    # Ask how many topics to include
    print(f"\nAvailable topics: {len(SYLLABUS_TOPICS)}")
    for i, topic in enumerate(SYLLABUS_TOPICS, 1):
        print(f"{i}. {topic}")
    
    # Get user input for question paper configuration
    while True:
        try:
            topic_count_input = input(f"\nHow many topics to include? (1-{len(SYLLABUS_TOPICS)}, default=all): ").strip()
            
            if not topic_count_input:  # Default to all topics
                selected_topics = SYLLABUS_TOPICS.copy()
                break
                
            topic_count = int(topic_count_input)
            if 1 <= topic_count <= len(SYLLABUS_TOPICS):
                # Option to select specific topics or random
                selection_mode = input("Select specific topics (s) or random (r)? ").strip().lower()
                
                if selection_mode == 's':
                    # Let user select specific topics
                    selected_indices = []
                    print("Enter topic numbers one by one (enter blank to finish):")
                    while len(selected_indices) < topic_count:
                        idx_input = input(f"Topic {len(selected_indices)+1}/{topic_count}: ").strip()
                        if not idx_input:
                            break
                        try:
                            idx = int(idx_input) - 1
                            if 0 <= idx < len(SYLLABUS_TOPICS) and idx not in selected_indices:
                                selected_indices.append(idx)
                            else:
                                print("Invalid or duplicate topic number.")
                        except ValueError:
                            print("Please enter a valid number.")
                    
                    selected_topics = [SYLLABUS_TOPICS[i] for i in selected_indices]
                    if len(selected_topics) == topic_count:
                        break
                else:
                    # Random selection
                    selected_topics = random.sample(SYLLABUS_TOPICS, topic_count)
                    print("Randomly selected topics:")
                    for i, topic in enumerate(selected_topics, 1):
                        print(f"{i}. {topic}")
                    break
            else:
                print(f"Please enter a number between 1 and {len(SYLLABUS_TOPICS)}.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Generate question paper
    question_paper = generate_question_paper(vectordb, selected_topics)
    
    # Ask if answers should be included
    include_answers = input("\nInclude answer guidelines in output? (y/n): ").strip().lower() == 'y'
    
    # Save question paper
    output_file = save_question_paper(question_paper, include_answers)
    
    print("\n" + "=" * 60)
    print(f"✅ Question paper generation complete!")
    print(f"📄 Output saved to: {output_file}")
    print("=" * 60)

# Add this function to parse theoretical questions from text

def parse_theoretical_question(raw_text, topic_name):
    """Parse a theoretical question from raw text output"""
    question = ""
    answer_guidelines = ""
    
    # Look for question pattern
    question_match = re.search(r'(?:Question|Q)[:\s]+(.*?)(?:Answer Guidelines|Guidelines|Answer|$)', 
                              raw_text, re.IGNORECASE | re.DOTALL)
    if question_match:
        question = question_match.group(1).strip()
    
    # Look for answer guidelines pattern
    answer_match = re.search(r'(?:Answer Guidelines|Guidelines|Answer)[:\s]+(.*?)(?:$)', 
                            raw_text, re.IGNORECASE | re.DOTALL)
    if answer_match:
        answer_guidelines = answer_match.group(1).strip()
    
    # Fallback if no question found
    if not question:
        # Try to find the first sentence that looks like a question
        sentences = re.split(r'(?<=[.!?])\s+', raw_text)
        for sentence in sentences:
            if '?' in sentence or re.search(r'\b(?:explain|describe|discuss|analyze|evaluate|compare)\b', 
                                          sentence, re.IGNORECASE):
                question = sentence.strip()
                break
    
    # Create structured data
    return {
        "question": question if question else f"Explain the key concepts of {topic_name} in Machine Learning.",
        "answer_guidelines": answer_guidelines if answer_guidelines else "Provide a comprehensive explanation of the topic.",
        "type": "theoretical",
        "topic": topic_name,
        "estimated_time_minutes": 15,
        "marks": 10
    }