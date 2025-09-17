# firebase_ops.py

from firebase_admin import firestore, credentials, initialize_app
import firebase_admin  # Add this import
from config import SERVICE_ACCOUNT_FILE
from typing import Dict, Any, Optional
from datetime import datetime
import os  # Add this import

# --- Firebase Initialization ---
try:
    if not firebase_admin._apps:
        # Check if file exists first
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Service account file not found at: {SERVICE_ACCOUNT_FILE}")
            
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        initialize_app(cred)
        
    db = firestore.client()
    print("✅ Firebase connection successful.")
except Exception as e:
    print(f"❌ FATAL: Failed to initialize Firebase. Error: {e}")
    db = None
    # Don't raise here - let the app continue but with limited functionality

def create_subject_with_nested_structure(teacher_id: str, syllabus_structure: dict) -> str:
    """
    Create a subject with nested modules and topics in Firebase.
    
    Args:
        teacher_id: The ID of the teacher creating the subject
        syllabus_structure: Structured syllabus dictionary
        
    Returns:
        ID of the created subject
    """
    try:
        db = firestore.client()
        
        # Print inputs for debugging
        print(f"Creating subject with teacher_id: {teacher_id}")
        print(f"Subject name: {syllabus_structure.get('name', 'No name provided')}")
        
        # Generate a unique subject ID
        subject_id = f"subject_{int(datetime.now().timestamp())}"
        
        # Create the subject document
        subject_ref = db.collection('subjects').document(subject_id)
        
        # Ensure we have a name for the subject, even if syllabus_structure is incomplete
        subject_name = syllabus_structure.get('name', 'Untitled Subject')
        if not subject_name or subject_name == "Untitled Subject":
            subject_name = f"Course {subject_id}"
        
        # Set the subject data - explicitly set name and teacher_id
        subject_ref.set({
            'name': subject_name,  # Use the name from syllabus_structure
            'teacher_id': teacher_id,  # Use the provided teacher_id
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        # Create modules
        modules = syllabus_structure.get('modules', [])
        for i, module in enumerate(modules):
            module_id = f"module_{i+1}"
            module_ref = subject_ref.collection('modules').document(module_id)
            
            module_ref.set({
                'name': module.get('name', f'Module {i+1}'),
                'position': i+1,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            
            # Create topics for this module with GLOBALLY UNIQUE IDs
            topics = module.get('topics', [])
            for j, topic in enumerate(topics):
                # Create a unique topic ID that includes subject and module context
                topic_id = f"{subject_id}_{module_id}_topic_{j+1}"
                
                topic_ref = module_ref.collection('topics').document(topic_id)
                
                topic_ref.set({
                    'name': topic.get('name', f'Topic {j+1}'),
                    'content': topic.get('content', ''),
                    'position': j+1,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
                
        print(f"Successfully created subject: {subject_name} with ID: {subject_id}")
        return subject_id
        
    except Exception as e:
        print(f"Error creating subject structure: {e}")
        raise e

def update_topic_content(subject_id: str, module_index: int, topic_index: int, content: str):
    """
    Updates the content of a specific topic within a subject's nested structure.
    """
    if not db:
        raise ConnectionError("Firestore client is not initialized.")

    try:
        subject_ref = db.collection('subjects').document(subject_id)
        
        # Use dot notation to update a specific field in the nested array
        update_field = f"modules.{module_index}.topics.{topic_index}.content"
        
        subject_ref.update({
            update_field: content
        })
        print(f"Updated content for module {module_index}, topic {topic_index} in subject {subject_id}.")
    except Exception as e:
        print(f"Error updating topic content for subject {subject_id}: {e}")
        # Continue silently or raise, depending on desired behavior

def get_subject_structure(subject_id: str) -> Dict[str, Any]:
    """
    Get the complete structure of a subject including modules and topics.
    
    Args:
        subject_id: The ID of the subject
        
    Returns:
        Complete subject structure dictionary
    """
    try:
        db = firestore.client()
        
        # Get the subject document
        subject_doc = db.collection('subjects').document(subject_id).get()
        
        if not subject_doc.exists:
            print(f"Subject with ID '{subject_id}' not found")
            return None
        
        # Get the basic subject data
        subject_data = subject_doc.to_dict()
        if not subject_data:
            print(f"Subject document exists but has no data")
            return None
            
        # Ensure subject has a name
        if "name" not in subject_data or not subject_data["name"]:
            print(f"Subject missing name, using ID as name")
            subject_data["name"] = f"Subject {subject_id}"
        
        # Get modules subcollection directly from the subject document
        modules_ref = db.collection('subjects').document(subject_id).collection('modules')
        modules = []
        
        for module_doc in modules_ref.get():
            module_data = module_doc.to_dict()
            module_data["id"] = module_doc.id
            
            # Get topics for this module
            topics_ref = modules_ref.document(module_doc.id).collection('topics')
            topics = []
            
            for topic_doc in topics_ref.get():
                topic_data = topic_doc.to_dict()
                topic_data["id"] = topic_doc.id
                topics.append(topic_data)
            
            module_data["topics"] = topics
            modules.append(module_data)
        
        # Add modules to subject data
        subject_data["modules"] = modules
        
        print(f"Retrieved subject: {subject_data['name']} with {sum(len(m.get('topics', [])) for m in modules)} topics across {len(modules)} modules")
        return subject_data
        
    except Exception as e:
        print(f"Error retrieving subject structure: {e}")
        return None

def get_student_bkt_params(student_id: str, topic_id: str) -> Dict[str, float]:
    """
    Get Bayesian Knowledge Tracing parameters for a student on a specific topic.
    Checks directly in the users/{student_id} document.
    
    Args:
        student_id: ID of the student
        topic_id: ID of the topic
        
    Returns:
        Dictionary containing BKT parameters
    """
    try:
        if not db:
            print(f"⚠️ Firebase unavailable, returning default BKT params for {student_id} on {topic_id}")
            return get_default_bkt_params()
        
        print(f"Retrieving BKT parameters for student {student_id} on topic {topic_id}")
        
        # Get the user document
        user_ref = db.collection('users').document(student_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            
            # First check if we have it in the mastery summary
            if "mastery_summary" in user_data:
                for subject_id, topics in user_data["mastery_summary"].items():
                    if topic_id in topics:
                        topic_data = topics[topic_id]
                        print(f"Found BKT params in mastery summary")
                        
                        # Convert summary to full BKT params
                        params = get_default_bkt_params()
                        params["p_L"] = topic_data.get("mastery", 0.0)
                        return params
            
            # If not in summary, search the full structure
            if "mastery" in user_data:
                mastery = user_data["mastery"]
                
                # Check unknown topics first (simpler path)
                if "unknown_topics" in mastery and topic_id in mastery["unknown_topics"]:
                    params = mastery["unknown_topics"][topic_id]
                    print(f"Found BKT parameters in unknown_topics")
                    return params
                    
                # Search through subjects structure
                if "subjects" in mastery:
                    for subject_id, subject_data in mastery["subjects"].items():
                        if "modules" in subject_data:
                            for module_id, module_data in subject_data["modules"].items():
                                if "topics" in module_data and topic_id in module_data["topics"]:
                                    params = module_data["topics"][topic_id]
                                    print(f"Found BKT parameters in user mastery structure")
                                    
                                    # Ensure all required fields exist
                                    default_params = get_default_bkt_params()
                                    for key, value in default_params.items():
                                        if key not in params:
                                            params[key] = value
                                            
                                    return params
        
        # If we got here, we didn't find the parameters in the user document
        # Create default parameters
        print(f"No BKT parameters found for {student_id} on {topic_id}, using defaults")
        return get_default_bkt_params()
            
    except Exception as e:
        print(f"Error retrieving BKT parameters: {e}")
        return get_default_bkt_params()


def update_student_bkt_params(student_id: str, topic_id: str, bkt_params: Dict[str, float]) -> None:
    """
    Update Bayesian Knowledge Tracing parameters for a student on a specific topic.
    Stores data directly in the users/{student_id} document.
    
    Args:
        student_id: ID of the student
        topic_id: ID of the topic
        bkt_params: Dictionary containing BKT parameters
    """
    try:
        if not db:
            print(f"⚠️ Firebase unavailable, cannot update BKT params for {student_id} on {topic_id}")
            return
        
        # Add timestamp to track when the parameters were last updated
        bkt_params["last_updated"] = firestore.SERVER_TIMESTAMP
        
        # Find the subject/module that contains this topic
        subjects = get_all_subjects()
        topic_path_found = False
        
        for subject in subjects:
            subject_id = subject["id"]
            modules = get_subject_modules(subject_id)
            
            for module in modules:
                module_id = module["id"]
                topics = get_module_topics(subject_id, module_id)
                
                for topic in topics:
                    if topic["id"] == topic_id:
                        # Found the topic, update in user's document
                        user_ref = db.collection('users').document(student_id)
                        
                        # Set the mastery data path
                        mastery_path = f"mastery.subjects.{subject_id}.modules.{module_id}.topics.{topic_id}"
                        
                        # Prepare update data
                        update_data = {
                            f"{mastery_path}.p_L": bkt_params.get("p_L", 0.0),
                            f"{mastery_path}.p_L0": bkt_params.get("p_L0", 0.0),
                            f"{mastery_path}.p_T": bkt_params.get("p_T", 0.1),
                            f"{mastery_path}.p_G": bkt_params.get("p_G", 0.2),
                            f"{mastery_path}.p_S": bkt_params.get("p_S", 0.1),
                            f"{mastery_path}.attempts": bkt_params.get("attempts", 0) + 1,
                            f"{mastery_path}.correct": bkt_params.get("correct", 0) + (1 if bkt_params.get("is_correct", False) else 0),
                            f"{mastery_path}.last_updated": firestore.SERVER_TIMESTAMP,
                            f"{mastery_path}.topic_name": topic.get("name", ""),
                            f"{mastery_path}.subject_name": subject.get("name", ""),
                            f"{mastery_path}.module_name": module.get("name", "")
                        }
                        
                        # Update user document directly
                        user_ref.update(update_data)
                        
                        # Also add a summary for quick access
                        user_ref.update({
                            f"mastery_summary.{subject_id}.{topic_id}": {
                                "mastery": bkt_params.get("p_L", 0.0),
                                "topic_name": topic.get("name", ""),
                                "module_name": module.get("name", ""),
                                "subject_name": subject.get("name", ""),
                                "last_updated": firestore.SERVER_TIMESTAMP
                            }
                        })
                        
                        print(f"✅ Updated student mastery in user document")
                        topic_path_found = True
                        break
                        
                if topic_path_found:
                    break
            if topic_path_found:
                break
        
        if not topic_path_found:
            print(f"⚠️ Could not find topic path for {topic_id}, saving direct reference only")
            # Save in the user document with minimal info
            user_ref = db.collection('users').document(student_id)
            user_ref.update({
                f"mastery.unknown_topics.{topic_id}": bkt_params
            })
            
        print(f"✅ Successfully updated BKT parameters for {student_id} on {topic_id}")
        
    except Exception as e:
        print(f"❌ Error updating BKT parameters: {e}")
        import traceback
        traceback.print_exc()


def get_default_bkt_params() -> Dict[str, float]:
    """Get default BKT parameters for a new student-topic combination"""
    return {
        "p_L0": 0.0,  # Initial mastery (prior)
        "p_L": 0.0,   # Current mastery estimate
        "p_T": 0.1,   # Learning rate (transition probability)
        "p_G": 0.2,   # Guess probability
        "p_S": 0.1,   # Slip probability
        "attempts": 0,
        "correct": 0
    }

def get_all_subjects():
    """
    Get all subjects available in the database.
    
    Returns:
        List of dictionaries containing subject id and name
    """
        
    try:
        print("Fetching all subjects from Firestore...")
        
        # Attempt to get collection reference - debug output
        subjects_ref = db.collection('subjects')
        print(f"Got collection reference: {subjects_ref}")
        
        # Get documents with increased timeout and debug
        print("Starting document fetch...")
        docs = subjects_ref.get(timeout=30)  # Increased timeout to 30 seconds
        print(f"Fetch completed, processing documents")
        
        subjects = []
        doc_count = 0
        for doc in docs:
            doc_count += 1
            data = doc.to_dict() or {}
            subjects.append({
                "id": doc.id,
                "name": data.get("name", "Unnamed Subject")
            })
            print(f"Processed document: {doc.id} - {data.get('name', 'Unnamed')}")
            
        print(f"Retrieved {len(subjects)} subjects from {doc_count} documents")
        return subjects
    except Exception as e:
        print(f"Error retrieving subjects: {e}")
        # Return empty list rather than failing completely
        return []

def get_subject_modules(subject_id):
    """
    Get all modules for a specific subject.
    """
    try:
        modules_ref = db.collection('subjects').document(subject_id).collection('modules')
        modules = []
        for doc in modules_ref.get():
            data = doc.to_dict() or {}
            modules.append({"id": doc.id, "name": data.get("name", "Unnamed Module")})
        print(f"Retrieved {len(modules)} modules for subject {subject_id}")
        return modules
    except Exception as e:
        print(f"Error retrieving modules for subject {subject_id}: {e}")
        return []

def get_module_topics(subject_id, module_id):
    """
    Get all topics for a specific module.
    """
    try:
        topics_ref = (
            db.collection('subjects')
              .document(subject_id)
              .collection('modules')
              .document(module_id)
              .collection('topics')
        )
        topics = []
        for doc in topics_ref.get():
            data = doc.to_dict() or {}
            topics.append({
                "id": doc.id,
                "name": data.get("name", "Unnamed Topic"),
                "subject_id": subject_id,
                "module_id": module_id,
            })
        print(f"Retrieved {len(topics)} topics for module {module_id} in subject {subject_id}")
        return topics
    except Exception as e:
        print(f"Error retrieving topics for module {module_id} in subject {subject_id}: {e}")
        return []

# Deprecated: quiz generation does not belong in firebase_ops
def generate_quiz_for_topic(student_id, topic_id, num_questions=5):
    raise NotImplementedError(
        "Quiz generation has moved to quiz_generator. "
        "Use quiz_generator.generate_topic_quiz from main.py after retrieving subject/module/topic via firebase_ops."
    )

def update_student_topic_response(student_id, topic_id, is_correct):
    """
    Update BKT parameters based on student's response to a question.
    
    Args:
        student_id: ID of the student
        topic_id: ID of the topic
        is_correct: Whether the student's response was correct
        
    Returns:
        Updated BKT parameters
    """
    try:
        # Get current BKT parameters
        bkt_params = get_student_bkt_params(student_id, topic_id)
        
        # Update mastery probability using BKT update rule
        p_L = bkt_params.get("p_L", 0.0)  # Current mastery probability
        p_T = bkt_params.get("p_T", 0.1)  # Learning probability
        p_G = bkt_params.get("p_G", 0.2)  # Guess probability
        p_S = bkt_params.get("p_S", 0.1)  # Slip probability
        
        if is_correct:
            # P(L|correct) = P(correct|L)P(L) / P(correct)
            # P(correct) = P(correct|L)P(L) + P(correct|~L)P(~L)
            p_correct_given_L = 1 - p_S
            p_correct_given_not_L = p_G
            p_correct = p_correct_given_L * p_L + p_correct_given_not_L * (1 - p_L)
            p_L_new = (p_correct_given_L * p_L) / p_correct
        else:
            # P(L|incorrect) = P(incorrect|L)P(L) / P(incorrect)
            # P(incorrect) = P(incorrect|L)P(L) + P(incorrect|~L)P(~L)
            p_incorrect_given_L = p_S
            p_incorrect_given_not_L = 1 - p_G
            p_incorrect = p_incorrect_given_L * p_L + p_incorrect_given_not_L * (1 - p_L)
            p_L_new = (p_incorrect_given_L * p_L) / p_incorrect
        
        # Apply learning effect
        p_L_final = p_L_new + (1 - p_L_new) * p_T
        
        # Update BKT parameters
        updated_params = {
            "p_L0": bkt_params.get("p_L0", 0.0),
            "p_T": p_T,
            "p_G": p_G,
            "p_S": p_S,
            "p_L": p_L_final,
            "mastery_probability": p_L_final,
            "learning_rate": p_T,
            "last_updated": firestore.SERVER_TIMESTAMP
        }
        
        # Save updated parameters
        update_student_bkt_params(student_id, topic_id, updated_params)
        
        return updated_params
        
    except Exception as e:
        print(f"Error updating BKT parameters for student {student_id}, topic {topic_id}: {e}")
        return None