import os
import re
import nltk
from typing import List, Dict, Any, Optional
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from firebase_ops import get_student_bkt_params, get_all_subjects, get_subject_modules, get_module_topics

# Initialize NLTK for sentence tokenization
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Configuration
OLLAMA_MODEL = "phi3:mini"  # Use a lightweight model for assignment generation
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"  # Update to your Ollama server


def generate_topic_assignment(
    subject_name: str,
    module_name: str,
    topic_name: str,
    num_questions: int = 5,
    student_id: Optional[str] = None,
    topic_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an assignment for a single topic with difficulty adjusted based on student mastery level.
    Pass Firestore topic_id to align BKT tracking with DB IDs.
    
    Args:
        subject_name: Name of the subject
        module_name: Name of the module
        topic_name: Name of the topic
        num_questions: Number of questions to generate
        student_id: Optional student ID to personalize difficulty
        topic_id: Optional Firestore ID for the topic (preferred over generated key)
    
    Returns:
        Dictionary containing the assignment data
    """
    # Use Firestore topic_id if provided; otherwise derive a deterministic slug
    topic_key = topic_id or f"{subject_name}-{module_name}-{topic_name}".replace(" ", "_").lower()
    
    # Get BKT params for this student-topic pair if student_id provided
    difficulty = "medium"
    if student_id:
        bkt_params = get_student_bkt_params(student_id, topic_key)
        p_L = bkt_params.get("p_L", 0.0)
        if p_L < 0.3:
            difficulty = "basic"
        elif p_L < 0.7:
            difficulty = "medium"
        else:
            difficulty = "advanced"
        print(f"Student mastery level: {p_L:.2f}, setting difficulty to: {difficulty}")
    
    # Create context for the prompt
    context = f"Subject: {subject_name}\nModule: {module_name}\nTopic: {topic_name}"
    
    prompt = f"""
    Based on the following academic context:
    {context}
    
    Create exactly {num_questions} open-ended questions about "{topic_name}" at {difficulty} difficulty level.
    
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
        "difficulty": "{difficulty}"
      }}
    ]
    
    Only return the JSON format, nothing else.
    """
    
    try:
        # Call the model
        llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        raw_output = llm.invoke(prompt)
        
        # Parse the output
        assignment_questions = parse_assignment_to_json(raw_output)
        
        if not assignment_questions or len(assignment_questions) == 0:
            print(f"⚠️ Failed to generate assignment questions")
            raise ValueError("Failed to generate valid assignment questions. Please try again.")
        
        # Add topic and module info to each question
        for question in assignment_questions:
            question["topic"] = topic_name
            question["module"] = module_name
            
        print(f"✅ Generated {len(assignment_questions)} questions for topic: {topic_name}")
        
        return {
            "title": f"{topic_name} - Assignment",
            "topic": topic_name,
            "topic_id": topic_key,
            "subject": subject_name,
            "module": module_name,
            "questions": assignment_questions,
            "question_count": len(assignment_questions)
        }
    
    except Exception as e:
        print(f"❌ Error generating assignment: {str(e)}")
        # Return empty assignment with error message
        return {
            "title": f"{topic_name} - Assignment",
            "topic": topic_name,
            "topic_id": topic_key,
            "subject": subject_name,
            "module": module_name,
            "questions": [],
            "question_count": 0,
            "error": str(e)
        }


def generate_multi_topic_assignment(
    topics_info: List[Dict[str, Any]],
    num_questions: int = 5,
    student_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an assignment with questions from multiple topics.
    
    Args:
        topics_info: List of topic information including subject_name, module_name, topic_name, and topic_id
        num_questions: Total number of questions to distribute across topics
        student_id: Optional student ID to personalize difficulty
        
    Returns:
        Dictionary containing the assignment data
    """
    if not topics_info:
        raise ValueError("No topics provided")
        
    # Get the subject name from the first topic (assuming all topics are from the same subject)
    subject_name = topics_info[0]["subject_name"]
    
    print(f"🏗️ Generating multi-topic assignment for {subject_name} with {len(topics_info)} topics")
    
    # Distribute questions across topics
    questions_per_topic = max(1, num_questions // len(topics_info))
    remaining_questions = num_questions % len(topics_info)
    
    all_questions = []
    topics_covered = []
    
    for i, topic_info in enumerate(topics_info):
        # Calculate number of questions for this topic
        topic_question_count = questions_per_topic + (1 if i < remaining_questions else 0)
        
        if topic_question_count == 0:
            continue
            
        topic_name = topic_info["topic_name"]
        module_name = topic_info["module_name"]
        topic_id = topic_info["topic_id"]
        
        print(f"📝 Generating {topic_question_count} questions for topic: {topic_name}")
        
        # Generate questions for this topic
        topic_assignment = generate_topic_assignment(
            subject_name=subject_name,
            module_name=module_name,
            topic_name=topic_name,
            num_questions=topic_question_count,
            student_id=student_id,
            topic_id=topic_id
        )
        
        # Add questions to the collection
        all_questions.extend(topic_assignment.get("questions", []))
        topics_covered.append(topic_name)
    
    # Create the complete multi-topic assignment
    assignment = {
        "title": f"{subject_name} - Multi-Topic Assignment",
        "topics_covered": topics_covered,
        "questions": all_questions,
        "question_count": len(all_questions)
    }
    
    print(f"✅ Generated multi-topic assignment with {len(all_questions)} questions covering {len(topics_covered)} topics")
    
    return assignment


def generate_assignment_for_topics(
    student_id: str, 
    topic_ids: List[str], 
    num_questions: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Wrapper function: resolve subject/module/topic names for Firestore topic_ids,
    then call generate_multi_topic_assignment.
    
    Args:
        student_id: Student ID for personalization
        topic_ids: List of Firestore topic IDs to include in the assignment
        num_questions: Total number of questions to generate across all topics
        
    Returns:
        Dictionary containing the assignment data
    """
    try:
        topics_info = []
        subjects = get_all_subjects()
        
        # Resolve topic information from topic IDs
        for subject in subjects:
            modules = get_subject_modules(subject["id"])
            for module in modules:
                topics = get_module_topics(subject["id"], module["id"])
                for topic in topics:
                    if topic["id"] in topic_ids:
                        topics_info.append({
                            "subject_name": subject["name"],
                            "module_name": module["name"],
                            "topic_name": topic["name"],
                            "topic_id": topic["id"]
                        })
        
        if not topics_info:
            print(f"❌ No valid topics found for IDs: {topic_ids}")
            return None
            
        return generate_multi_topic_assignment(
            topics_info=topics_info,
            num_questions=num_questions,
            student_id=student_id
        )
        
    except Exception as e:
        print(f"❌ Error generating assignment for topics {topic_ids}: {e}")
        return None


# Keep these helper functions unchanged
def parse_assignment_to_json(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse the raw text from the LLM into a structured assignment format.
    """
    # Try to extract JSON from the response
    json_match = re.search(r'\[[\s\S]*\]', raw_text)
    if not json_match:
        return []
        
    json_str = json_match.group(0)
    
    try:
        import json
        questions = json.loads(json_str)
        
        # Validate each question has the required fields
        validated_questions = []
        for q in questions:
            if not all(key in q for key in ["question", "model_answer", "key_concepts", "common_misconceptions", "difficulty"]):
                continue
            validated_questions.append(q)
        
        return validated_questions
    except json.JSONDecodeError:
        return []


def evaluate_assignment_answer(
    student_answer: str, 
    question_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a student's answer against the model answer and key concepts.
    Returns an assessment with feedback.
    """
    # Check if student's answer is empty
    if not student_answer or student_answer.strip() == "":
        return {
            "score": 0.0,
            "keyword_matches": [],
            "keyword_misses": question_data.get("key_concepts", []),
            "detected_mistakes": ["No answer provided"],
            "feedback": "No answer was provided. Please attempt to answer the question."
        }

    # Create the evaluation prompt
    prompt = f"""
    You are an expert academic evaluator. Compare the student's answer to the model answer for the following question:
    
    QUESTION: {question_data["question"]}
    
    MODEL ANSWER: {question_data["model_answer"]}
    
    KEY CONCEPTS that should be included:
    {", ".join(question_data["key_concepts"])}
    
    COMMON MISCONCEPTIONS to watch for:
    {", ".join(question_data["common_misconceptions"])}
    
    STUDENT ANSWER: {student_answer}
    
    Evaluate the student's answer on a scale of 0.0 to 1.0 based on:
    1. Inclusion of key concepts (60% of score)
    2. Accuracy and avoidance of misconceptions (30% of score)
    3. Organization and clarity (10% of score)
    
    Format response as JSON:
    {{
      "score": 0.XX,
      "keyword_matches": ["matched concepts"],
      "keyword_misses": ["missing concepts"],
      "detected_mistakes": ["identified errors or misconceptions"]
    }}
    
    Only return the JSON object, nothing else.
    """

    try:
        # Call the model
        llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        raw_output = llm.invoke(prompt)
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', raw_output)
        if not json_match:
            raise ValueError("Failed to extract evaluation JSON")
            
        json_str = json_match.group(0)
        
        import json
        result = json.loads(json_str)
        
        # Validate the result
        if not all(key in result for key in ["score", "keyword_matches", "keyword_misses", "detected_mistakes"]):
            raise ValueError("Invalid evaluation result format")
        
        
        return result
        
    except Exception as e:
        print(f"❌ Error evaluating answer: {str(e)}")
        return {
            "score": 0.0,
            "keyword_matches": [],
            "keyword_misses": question_data.get("key_concepts", []),
            "detected_mistakes": ["Evaluation failed"],
            "feedback": "An error occurred during evaluation. Please try again."
        }

def generate_feedback(
    student_answer: str,
    model_answer: str,
    keyword_matches: List[str],
    keyword_misses: List[str],
    detected_mistakes: List[str],
    score: float
) -> str:
    """
    Generate detailed feedback for a student's answer.
    """
    prompt = f"""
    You are an educational feedback assistant. Based on the following information:
    
    STUDENT ANSWER: {student_answer}
    
    MODEL ANSWER: {model_answer}
    
    MATCHED CONCEPTS: {", ".join(keyword_matches)}
    
    MISSING CONCEPTS: {", ".join(keyword_misses)}
    
    DETECTED ISSUES: {", ".join(detected_mistakes)}
    
    SCORE: {score:.2f} out of 1.0
    
    Generate constructive feedback that:
    1. Acknowledges what the student did well
    2. Points out key concepts they missed
    3. Corrects any misconceptions
    4. Provides 2-3 specific suggestions for improvement
    5. Is encouraging and educational
    
    Keep the feedback concise (150-200 words max).
    """

    try:
        # Call the model
        llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        feedback = llm.invoke(prompt)
        
        return feedback.strip()
        
    except Exception as e:
        print(f"❌ Error generating feedback: {str(e)}")
        
        # Simple feedback fallback
        if score > 0.8:
            return "Excellent work! You covered most of the key concepts well. Keep up the good work!"
        elif score > 0.5:
            return f"Good attempt, but you missed some key concepts: {', '.join(keyword_misses[:3])}. Review these areas to improve."
        else:
            return f"Your answer needs improvement. Focus on understanding these key concepts: {', '.join(keyword_misses[:5])}"


def generate_multi_topic_assignment(
    subject_data: Dict[str, Any],
    student_id: Optional[str] = None,
    num_topics: int = 3,
    num_questions_per_topic: int = 2
) -> Dict[str, Any]:
    """
    Generate an assignment with questions from multiple topics.
    
    Args:
        subject_data: The complete subject structure from Firebase
        student_id: Optional student ID to personalize difficulty
        num_topics: Number of topics to include in the assignment
        num_questions_per_topic: Number of questions to generate per topic
        
    Returns:
        Dictionary containing the assignment data
    """
    subject_name = subject_data["name"]
    
    print(f"🏗️ Generating multi-topic assignment for {subject_name}")
    
    # Extract all topics from all modules
    all_topics = []
    for module in subject_data["modules"]:
        module_name = module["name"]
        for topic in module["topics"]:
            all_topics.append({
                "name": topic["name"],
                "module_name": module_name
            })
    
    # If we don't have enough topics, use what we have
    available_topic_count = len(all_topics)
    if available_topic_count < num_topics:
        print(f"⚠️ Only {available_topic_count} topics available. Using all of them.")
        num_topics = available_topic_count
    
    # If student_id is provided, we could fetch their weak topics
    # (This would require implementing topic weakness tracking)
    selected_topics = []
    if student_id:
        # TODO: Implement logic to select student's weakest topics
        # For now, we'll just randomly select
        import random
        selected_topics = random.sample(all_topics, num_topics)
    else:
        # Randomly select topics
        import random
        selected_topics = random.sample(all_topics, num_topics)
    
    # Generate questions for each selected topic
    all_questions = []
    for topic_info in selected_topics:
        topic_name = topic_info["name"]
        module_name = topic_info["module_name"]
        
        print(f"📝 Generating questions for topic: {topic_name}")
        
        # Generate questions for this topic
        topic_assignment = generate_topic_assignment(
            subject_name=subject_name,
            module_name=module_name,
            topic_name=topic_name,
            num_questions=num_questions_per_topic,
            student_id=student_id
        )
        
        # Add module and topic info to each question
        for question in topic_assignment.get("questions", []):
            question["module"] = module_name
            question["topic"] = topic_name
            all_questions.append(question)
    
    # Create the complete multi-topic assignment
    assignment = {
        "title": f"{subject_name} - Multi-Topic Assignment",
        "topics_covered": [t["name"] for t in selected_topics],
        "questions": all_questions,
        "total_questions": len(all_questions),
        "estimated_time_minutes": len(all_questions) * 10  # Estimate 10 minutes per question
    }
    
    print(f"✅ Generated multi-topic assignment with {len(all_questions)} questions covering {num_topics} topics")
    
    return assignment