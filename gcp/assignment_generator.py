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
    student_id: Optional[str] = None,
    topic_ids: List[str] = None,
    num_questions: int = 5
) -> Dict[str, Any]:
    """
    Generate an assignment based on topic IDs.
    
    Args:
        student_id: Student ID for personalization
        topic_ids: List of topic IDs to include in assignment
        num_questions: Total number of questions to generate
        
    Returns:
        Dictionary containing the assignment data
    """
    try:
        topics_info = []
        subjects = get_all_subjects()
        subject_name = None
        
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
                        if not subject_name:
                            subject_name = subject["name"]
        
        if not topics_info:
            print(f"❌ No valid topics found for IDs: {topic_ids}")
            return {
                "title": "Assignment Error",
                "questions": [],
                "question_count": 0,
                "error": f"Topics not found for IDs: {topic_ids}"
            }
        
        # Build prompt with all topics
        topics_context = "\n".join([
            f"- {t['topic_name']} (from module: {t['module_name']})" 
            for t in topics_info
        ])
        
        # Get BKT params for topic difficulty adjustment
        topic_difficulties = {}
        for topic in topics_info:
            difficulty = "medium"
            if student_id:
                bkt_params = get_student_bkt_params(student_id, topic["topic_id"])
                p_L = bkt_params.get("p_L", 0.0)
                if p_L < 0.3:
                    difficulty = "basic"
                elif p_L < 0.7:
                    difficulty = "medium"
                else:
                    difficulty = "advanced"
                print(f"Topic '{topic['topic_name']}' - Mastery: {p_L:.2f}, Difficulty: {difficulty}")
            topic_difficulties[topic["topic_name"]] = difficulty
        
        # Create a prompt for all topics
        prompt = f"""
        Based on the following academic context:
        Subject: {subject_name}
        
        Topics to cover:
        {topics_context}
        
        Create exactly {num_questions} open-ended questions distributed across the topics listed above.
        
        Topic difficulties:
        {", ".join([f"{topic}: {diff}" for topic, diff in topic_difficulties.items()])}
        
        For each question:
        1. Create a clear, specific question that tests understanding of the associated topic
        2. Provide a detailed model answer that would be considered excellent
        3. List 5-8 key concepts that should be present in a good answer
        4. Include 2-3 common misconceptions students might have
        5. Specify which topic this question belongs to
        6. Specify the difficulty level (easy, medium, or hard)
        
        Format as valid JSON:
        [
          {{
            "question": "Detailed question text here?",
            "model_answer": "Comprehensive model answer here...",
            "key_concepts": ["Concept 1", "Concept 2", "Concept 3", "Concept 4", "Concept 5"],
            "common_misconceptions": ["Misconception 1", "Misconception 2"],
            "difficulty": "easy|medium|hard",
            "topic": "Topic name here"
          }}
        ]
        
        Ensure you create a total of exactly {num_questions} questions distributed reasonably across all topics.
        Only return the JSON format, nothing else.
        """
        
        # Call the model
        llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        raw_output = llm.invoke(prompt)
        
        # Parse the output
        assignment_questions = parse_assignment_to_json(raw_output)
        
        if not assignment_questions or len(assignment_questions) == 0:
            print(f"⚠️ Failed to generate assignment questions")
            return {
                "title": f"{subject_name} - Assignment",
                "questions": [],
                "question_count": 0,
                "error": "Failed to generate valid assignment questions"
            }
        
        # Add module info to each question
        topic_to_module = {t["topic_name"]: t["module_name"] for t in topics_info}
        for question in assignment_questions:
            topic_name = question.get("topic")
            if topic_name and topic_name in topic_to_module:
                question["module"] = topic_to_module[topic_name]
        
        # Create the final assignment
        topics_covered = list(set(q.get("topic") for q in assignment_questions if q.get("topic")))
        assignment = {
            "title": f"{subject_name} - Assignment",
            "topics_covered": topics_covered,
            "questions": assignment_questions,
            "question_count": len(assignment_questions)
        }
        
        print(f"✅ Generated {len(assignment_questions)} questions for {len(topics_covered)} topics")
        return assignment
        
    except Exception as e:
        print(f"❌ Error generating assignment: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "title": "Assignment Generation Error",
            "questions": [],
            "question_count": 0,
            "error": str(e)
        }

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
