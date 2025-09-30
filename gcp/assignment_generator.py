import os
import re
import nltk
from typing import List, Dict, Any, Optional
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from firebase_ops import get_student_bkt_params

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
    num_questions: int = 3,
    student_id: Optional[str] = None,
    bkt_params: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Generate an assignment for a specific topic, using BKT params if provided.
    """
    # Use bkt_params to adjust difficulty or focus
    difficulty = "medium"
    if bkt_params:
        p_L = bkt_params.get("mastery_probability", 0.0)
        if p_L < 0.3:
            difficulty = "basic"
        elif p_L < 0.7:
            difficulty = "intermediate"
        else:
            difficulty = "advanced"
        
        print(f"Student mastery level: {p_L:.2f}, setting assignment difficulty to: {difficulty}")
    
    print(f"Generating assignment for topic: {topic_name} in {module_name} ({subject_name})")
    
    # Create the prompt
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
            print(f"⚠️ Failed to generate assignment for {topic_name}, using backup method")
            # Fallback to simpler generation
            assignment_questions = generate_backup_questions(topic_name, difficulty)
        
        # Add topic to each question
        for question in assignment_questions:
            question["topic"] = topic_name
        
        print(f"✅ Successfully generated {len(assignment_questions)} questions for {topic_name}")
        
        return {
            "topic": topic_name,
            "questions": assignment_questions,
            "question_count": len(assignment_questions)
        }
    
    except Exception as e:
        print(f"❌ Error generating assignment: {str(e)}")
        # Return empty assignment with error message
        return {
            "topic": topic_name,
            "questions": generate_backup_questions(topic_name, difficulty),
            "question_count": 1,
            "error": str(e)
        }


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


def generate_backup_questions(topic_name: str, difficulty: str = "medium") -> List[Dict[str, Any]]:
    """Generate a simple backup question if main generation fails"""
    return [{
        "question": f"Explain the key concepts of {topic_name} and discuss its importance in the field.",
        "model_answer": f"{topic_name} encompasses several important principles and methodologies. A comprehensive understanding includes recognizing its foundational elements and practical applications.",
        "key_concepts": ["Definition", "Core principles", "Applications", "Historical context", "Recent developments"],
        "common_misconceptions": ["Oversimplification", "Confusion with related concepts"],
        "difficulty": difficulty,
        "topic": topic_name
    }]


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