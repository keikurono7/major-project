# firebase_ops.py

from firebase_admin import firestore, credentials, initialize_app
import firebase_admin
from config import SERVICE_ACCOUNT_FILE
from typing import Dict, Any, Optional
from datetime import datetime

# --- Firebase Initialization ---
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase connection successful.")
except Exception as e:
    print(f"❌ FATAL: Failed to initialize Firebase. Error: {e}")
    db = None
    raise

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
            
            # Create topics for this module
            topics = module.get('topics', [])
            for j, topic in enumerate(topics):
                topic_id = f"topic_{j+1}"
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
    Retrieve BKT parameters for a specific student and topic.
    If no parameters exist, returns default values.
    """
    from firebase_admin import firestore
    
    db = firestore.client()
    doc_ref = db.collection('student_data').document(student_id).collection('bkt_params').document(topic_id)
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        # Return default BKT parameters
        return {
            "p_L0": 0.5,  # Initial probability of mastery
            "p_T": 0.1,   # Probability of learning if not mastered
            "p_G": 0.2,   # Probability of guessing correctly if not mastered
            "p_S": 0.1,   # Probability of making a mistake if mastered
            "p_L": 0.5    # Current probability of mastery (starts at p_L0)
        }

def update_student_bkt_params(student_id: str, topic_id: str, bkt_params: Dict[str, float]) -> None:
    """
    Update BKT parameters for a specific student and topic.
    """
    from firebase_admin import firestore
    
    db = firestore.client()
    doc_ref = db.collection('student_data').document(student_id).collection('bkt_params').document(topic_id)
    doc_ref.set(bkt_params, merge=True)

def get_all_subjects():
    """
    Get all subjects available in the database.
    
    Returns:
        List of dictionaries containing subject id and name
    """
    try:
        subjects_ref = db.collection('subjects')
        subjects = []
        for doc in subjects_ref.get():
            data = doc.to_dict() or {}
            subjects.append({"id": doc.id, "name": data.get("name", "Unnamed Subject")})
        print(f"Retrieved {len(subjects)} subjects")
        return subjects
    except Exception as e:
        print(f"Error retrieving subjects: {e}")
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
        p_L = bkt_params.get("p_L", 0.5)  # Current mastery probability
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
            "p_L0": bkt_params.get("p_L0", 0.5),
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