import json
import requests
from typing import Dict, Any, List, Optional
from firebase_ops import get_student_bkt_params, get_subject_structure

# Ollama configuration
OLLAMA_MODEL = "phi3:mini"  # Use a lightweight model for chatbot
OLLAMA_BASE_URL = "http://localhost:11434"  # Update to your Ollama server
OLLAMA_API_URL = f"{OLLAMA_BASE_URL}/api/generate"

def get_student_knowledge_context(student_id: str, subject_id: str) -> Dict[str, Any]:
    """
    Fetch student's knowledge state for a given subject.
    Returns a dictionary with topic names and their mastery levels.
    """
    try:
        print(f"Getting knowledge context for student {student_id}, subject {subject_id}")
        
        # Get subject structure
        subject = get_subject_structure(subject_id)
        if not subject:
            print(f"Subject {subject_id} not found")
            return {"topics": [], "error": "Subject not found"}
        
        print(f"Subject found: {subject.get('name')}")
        knowledge_context = []
        
        # Iterate through modules and topics
        for module in subject.get("modules", []):
            for topic in module.get("topics", []):
                topic_id = topic.get("id")
                topic_name = topic.get("name")
                
                if not topic_id:
                    continue
                
                # Get BKT parameters for this topic
                bkt_params = get_student_bkt_params(student_id, topic_id)
                
                # Use p_L (current mastery) instead of p_mastery
                # p_L is the actual current knowledge state
                mastery = bkt_params.get("p_L", bkt_params.get("p_mastery", 0.0))
                
                print(f"Topic: {topic_name}, ID: {topic_id}, Raw mastery value: {mastery}, BKT params: {bkt_params}")
                
                # Ensure mastery is converted to percentage (0-100 scale)
                mastery_pct = round(float(mastery) * 100, 2)
                
                knowledge_context.append({
                    "topic": topic_name,
                    "topic_id": topic_id,
                    "module": module.get("name"),
                    "mastery": mastery_pct,
                    "p_learn": bkt_params.get("p_learn", bkt_params.get("p_T", 0.0)),
                    "p_slip": bkt_params.get("p_slip", bkt_params.get("p_S", 0.0)),
                    "p_guess": bkt_params.get("p_guess", bkt_params.get("p_G", 0.0))
                })
        
        print(f"\n=== KNOWLEDGE CONTEXT SUMMARY ===")
        print(f"Total topics: {len(knowledge_context)}")
        if knowledge_context:
            print(f"First topic (lowest): {knowledge_context[0]['topic']} = {knowledge_context[0]['mastery']}%")
            print(f"Last topic (highest): {knowledge_context[-1]['topic']} = {knowledge_context[-1]['mastery']}%")
        
        avg_mastery = round(
            sum(t["mastery"] for t in knowledge_context) / len(knowledge_context)
            if knowledge_context else 0, 2
        )
        print(f"Average mastery: {avg_mastery}%")
        
        return {
            "subject_name": subject.get("name"),
            "total_topics": len(knowledge_context),
            "topics": knowledge_context,
            "average_mastery": avg_mastery
        }
    
    except Exception as e:
        print(f"Error fetching student knowledge context: {e}")
        import traceback
        traceback.print_exc()
        return {"topics": [], "error": str(e)}


def build_system_prompt(knowledge_context: Dict[str, Any], student_name: str) -> str:
    """
    Build a detailed system prompt with student's knowledge state.
    """
    subject_name = knowledge_context.get("subject_name", "Unknown Subject")
    avg_mastery = knowledge_context.get("average_mastery", 0)
    topics = knowledge_context.get("topics", [])
    
    # Get weakest topics (mastery < 70%)
    weak_topics = [t for t in topics if t["mastery"] < 70]
    
    # Get strongest topics (mastery > 80%)
    strong_topics = [t for t in topics if t["mastery"] > 80]
    
    # Build examples with actual data
    first_topic_name = topics[0]['topic'] if topics else 'N/A'
    first_topic_mastery = int(topics[0]['mastery']) if topics else 0
    focus_topic = weak_topics[0]['topic'] if weak_topics else 'practicing'
    
    prompt = f"""You are a concise AI learning assistant for {student_name} studying {subject_name}.

STUDENT'S KNOWLEDGE:
Average Mastery: {int(avg_mastery)}%
Total Topics: {knowledge_context.get('total_topics', 0)}

WEAK AREAS (< 70%):"""
    
    if weak_topics:
        for topic in weak_topics[:3]:
            prompt += f"\n- {topic['topic']}: {int(topic['mastery'])}%"
    else:
        prompt += "\n- None"
    
    prompt += "\n\nSTRONG AREAS (> 80%):"
    
    if strong_topics:
        for topic in strong_topics[:3]:
            prompt += f"\n- {topic['topic']}: {int(topic['mastery'])}%"
    else:
        prompt += "\n- None yet"
    
    prompt += f"""

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. Greetings (hi/hello/hey) = Respond with ONLY 1 short sentence. Example: "Hey {student_name}! 👋 How can I help with {subject_name}?"
2. Simple questions = Short direct answers (1-2 sentences max)
3. Complex questions = Detailed answers allowed
4. NEVER give long explanations unless specifically asked
5. Match response length to question complexity
6. ALL mastery percentages are already in 0-100 scale, use them as-is

EXAMPLES:
Student: "hey" 
Assistant: "Hey {student_name}! 👋 Need help with {subject_name}?"

Student: "what's my first topic"
Assistant: "Your first topic is {first_topic_name} ({first_topic_mastery}% mastery)."

Student: "why is my score low"
Assistant: "Your average is {int(avg_mastery)}%. Focus on {focus_topic} to improve."

Student: "explain neural networks in detail"
Assistant: [Give detailed explanation]

BE BRIEF UNLESS ASKED FOR DETAIL. USE MASTERY PERCENTAGES EXACTLY AS GIVEN."""
    
    return prompt


def chat_with_ollama(
    student_id: str,
    subject_id: str,
    message: str,
    student_name: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Send a message to Ollama with student context and get a response.
    """
    try:
        print(f"\n{'='*50}")
        print(f"Chat request - Student: {student_id}, Subject: {subject_id}")
        print(f"Message: {message}")
        print(f"{'='*50}")
        
        # Get student's knowledge context
        knowledge_context = get_student_knowledge_context(student_id, subject_id)
        
        if knowledge_context.get("error"):
            error_msg = f"Error getting knowledge context: {knowledge_context['error']}"
            print(error_msg)
            return {
                "response": "I'm having trouble accessing your learning data. Please try again.",
                "error": error_msg,
                "knowledge_context": []
            }
        
        print(f"\nKnowledge context retrieved successfully")
        
        # Build system prompt with context
        system_prompt = build_system_prompt(knowledge_context, student_name)
        
        print(f"\n--- SYSTEM PROMPT ---")
        print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
        print(f"--- END PROMPT ---\n")
        
        # Build conversation context
        full_prompt = system_prompt + "\n\n"
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-3:]:  # Last 3 messages only
                role = "Student" if msg.get("role") == "user" else "Assistant"
                full_prompt += f"{role}: {msg.get('content', '')}\n"
        
        # Add current message
        full_prompt += f"Student: {message}\nAssistant:"
        
        print(f"Calling Ollama at {OLLAMA_API_URL} with model {OLLAMA_MODEL}")
        
        # Call Ollama API
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more focused responses
                "top_p": 0.8,
                "num_predict": 150,  # Shorter max length
                "stop": ["\n\n", "Student:", "Assistant:"]  # Stop at double newline or role markers
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        ollama_response = response.json()
        assistant_message = ollama_response.get("response", "").strip()
        
        print(f"\n✅ Ollama response: {assistant_message}")
        
        # Get top 5 weakest topics for frontend display
        weak_topics = [
            {"topic": t["topic"], "mastery": int(t["mastery"])}
            for t in knowledge_context["topics"]
            if t["mastery"] < 70
        ][:5]
        
        print(f"Returning {len(weak_topics)} weak topics to frontend")
        
        return {
            "response": assistant_message,
            "knowledge_context": weak_topics,
            "average_mastery": int(knowledge_context.get("average_mastery", 0)),
            "total_topics": knowledge_context.get("total_topics", 0)
        }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API error: {str(e)}"
        print(error_msg)
        return {
            "response": "I'm having trouble connecting to my AI service. Please try again in a moment.",
            "error": error_msg,
            "knowledge_context": []
        }
    
    except Exception as e:
        error_msg = f"Error in chat_with_ollama: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "response": "An unexpected error occurred. Please try again.",
            "error": error_msg,
            "knowledge_context": []
        }


def get_teacher_bkt_insights(teacher_id, subject_id, bkt_data, total_students, subject_name):
    """
    Generate AI-powered insights for teacher analytics based on BKT data.
    
    Args:
        teacher_id (str): Teacher's ID
        subject_id (str): Subject ID
        bkt_data (dict): Raw BKT data with topic scores
        total_students (int): Total number of students
        subject_name (str): Name of the subject
    
    Returns:
        dict: Insights including key findings, recommendations, and interventions
    """
    try:
        print(f"Generating BKT insights for teacher {teacher_id}, subject {subject_name}")
        
        # Format BKT data for the prompt
        formatted_bkt = []
        for topic_id, topic_data in bkt_data.items():
            if topic_data.get('scores'):
                avg_score = sum(topic_data['scores']) / len(topic_data['scores'])
                
                formatted_bkt.append({
                    'topic': topic_data.get('topicName', 'Unknown'),
                    'avg_mastery': round(avg_score * 100, 1),  # Round to 1 decimal
                    'students': len(topic_data['scores'])
                })
        
        print(f"Formatted {len(formatted_bkt)} topics for analysis")
        
        # SIMPLIFIED PROMPT - much shorter and clearer
        prompt = f"""Analyze this class performance data for {subject_name}:

Class: {total_students} students, {len(formatted_bkt)} topics

Topic Performance:
"""
        
        for item in formatted_bkt:
            prompt += f"- {item['topic']}: {item['avg_mastery']}% average ({item['students']} students)\n"
        
        prompt += """

Provide brief insights:
1. Overall class performance (1 sentence)
2. Best performing topics
3. Topics needing help
4. 2-3 teaching recommendations

Keep it concise and actionable."""
        
        print(f"Simplified prompt length: {len(prompt)} characters")
        print(f"Prompt preview: {prompt[:300]}...")
        
        # Call Ollama with SIMPLIFIED options
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Very low for consistent responses
                "top_p": 0.7,        # Lower for more focused
                "num_predict": 300,  # Shorter responses
                "stop": ["\n\n", "###"]  # Simple stop conditions
            }
        }
        
        print(f"Calling Ollama with simplified payload")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)  # Shorter timeout
        response.raise_for_status()
        
        result = response.json()
        insights = result.get('response', '').strip()
        
        print(f"Ollama response received, length: {len(insights)}")
        print(f"Raw result keys: {list(result.keys())}")
        
        if 'error' in result:
            print(f"Ollama returned error: {result['error']}")
            return {
                "status": "error",
                "error": f"Ollama error: {result['error']}",
                "insights": "AI service returned an error. Please try again."
            }
        
        if not insights:
            print("Empty insights response")
            return {
                "status": "error",
                "error": "Empty response from AI",
                "insights": "Unable to generate insights. Please try again."
            }
        
        print(f"Success! Insights: {insights}...")
        
        return {
            "status": "success",
            "insights": insights,
            "bkt_summary": {
                "total_topics": len(formatted_bkt),
                "avg_class_mastery": round(sum([t['avg_mastery'] for t in formatted_bkt]) / len(formatted_bkt), 1) if formatted_bkt else 0,
                "topics_below_60": len([t for t in formatted_bkt if t['avg_mastery'] < 60]),
                "topics_above_85": len([t for t in formatted_bkt if t['avg_mastery'] > 85])
            }
        }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API error: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "insights": "Unable to connect to AI service. Please check if Ollama is running."
        }
    
    except Exception as e:
        error_msg = f"Error generating BKT insights: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "insights": "Unable to generate insights"
        }


def chat_with_teacher_assistant(teacher_id, subject_id, message, bkt_context=None, conversation_history=None):
    """
    Chat endpoint for teachers to discuss class performance and get recommendations.
    
    Args:
        teacher_id (str): Teacher's ID
        subject_id (str): Subject ID
        message (str): Teacher's question/message
        bkt_context (dict): Optional BKT data for context
        conversation_history (list): List of previous messages
    
    Returns:
        dict: Response from the AI assistant
    """
    try:
        print(f"Teacher chat request: {message[:50]}...")
        
        if not message or not isinstance(message, str):
            return {
                "status": "error",
                "error": "Invalid message",
                "response": "Please provide a valid message"
            }
        
        # Build context from BKT data if available
        context = ""
        if bkt_context:
            context = "\n\nClass Performance Context:\n"
            for topic_id, topic_data in bkt_context.items():
                if topic_data.get('scores'):
                    avg_score = sum(topic_data['scores']) / len(topic_data['scores'])
                    context += f"- {topic_data.get('topicName', 'Unknown')}: {round(avg_score * 100, 2)}% mastery\n"
        
        # Build conversation history
        history_text = ""
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n\nConversation History:\n"
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                role = "Teacher" if msg.get('role') == 'user' else "Assistant"
                history_text += f"{role}: {msg.get('content', '')}\n"
        
        # Build the prompt
        system_prompt = """You are an experienced educational AI assistant for teachers. You help teachers:
- Interpret student BKT (Bayesian Knowledge Tracing) data
- Develop targeted interventions
- Improve student learning outcomes
- Design differentiated instruction strategies
- Track progress and identify patterns

Be supportive, evidence-based, and practical in your recommendations."""
        
        full_prompt = f"""{system_prompt}{context}{history_text}

Teacher's Question: {message}

Provide a helpful, specific response that:
1. Answers the teacher's question directly
2. References the class performance data if relevant
3. Offers actionable suggestions
4. Is concise but comprehensive"""
        
        print(f"Calling Ollama API for teacher chat")
        
        # Call Ollama LLM using same config as student chat
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Slightly higher for conversational responses
                "top_p": 0.8,
                "num_predict": 400,  # Medium length for teacher chat
                "stop": ["\n\n", "Teacher:", "Assistant:"]  # Stop at double newline or role markers
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()  # This will raise an exception if status is not 2xx
        
        result = response.json()
        assistant_response = result.get('response', '').strip()
        
        print(f"Teacher chat response received, length: {len(assistant_response)}")
        
        if not assistant_response:
            return {
                "status": "error",
                "error": "Empty response from LLM",
                "response": "I'm having trouble processing your request. Please try again."
            }
        
        return {
            "status": "success",
            "response": assistant_response,
            "message": assistant_response
        }
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API error: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "response": "Unable to connect to AI service. Please check if Ollama is running."
        }
    
    except Exception as e:
        error_msg = f"Error in teacher assistant chat: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "response": "An error occurred. Please try again."
        }