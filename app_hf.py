import streamlit as st
import json
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import PyPDF2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle

st.set_page_config(
    page_title="Machine Learning Quiz System",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Machine Learning Quiz System")
st.markdown("*Based on Tom Mitchell's Machine Learning Textbook*")

# Machine Learning Topics
SYLLABUS_TOPICS = [
    "Well-Posed Learning Problems",
    "Designing a Learning System", 
    "Concept Learning Task",
    "Find-S Algorithm",
    "Version Spaces and Candidate-Elimination Algorithm",
    "Inductive Bias"
]

# Cache models and embeddings
@st.cache_resource
def load_models():
    """Load lightweight models for HF Spaces"""
    try:
        # Use a smaller sentence transformer
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        # Use a smaller text generation model
        generator = pipeline('text-generation', 
                           model='microsoft/DialoGPT-small',
                           max_length=200)
        return encoder, generator
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None

@st.cache_data
def extract_pdf_content():
    """Extract content from PDF if available"""
    if os.path.exists("MachineLearningTomMitchell.pdf"):
        try:
            with open("MachineLearningTomMitchell.pdf", 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                # Extract first 20 pages to stay within limits
                for page_num in range(min(20, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.warning(f"Could not extract PDF: {e}")
    
    # Fallback content for each topic
    fallback_content = {
        "Well-Posed Learning Problems": """
        A learning problem is well-posed if it has three components:
        - Task T: The type of task to be performed
        - Performance measure P: How to measure success
        - Experience E: The training data or experience
        """,
        "Designing a Learning System": """
        Key design choices include:
        - Type of training experience
        - Target function to be learned  
        - Representation of the target function
        - Learning algorithm to use
        """,
        "Find-S Algorithm": """
        Find-S finds the most specific hypothesis consistent with positive examples.
        It ignores negative examples and generalizes only when necessary.
        """
    }
    return fallback_content

def generate_quiz_lightweight(topic_name, content):
    """Generate quiz using lightweight approach"""
    
    # Predefined quiz questions for reliability
    quiz_bank = {
        "Well-Posed Learning Problems": [
            {
                "question": "What are the three components of a well-posed learning problem?",
                "options": [
                    "A) Task, Performance, Experience",
                    "B) Data, Algorithm, Model", 
                    "C) Input, Output, Function",
                    "D) Training, Testing, Validation"
                ],
                "answer": "A",
                "explanation": "Mitchell defines well-posed learning problems with Task T, Performance measure P, and Experience E."
            },
            {
                "question": "What does the Performance measure (P) define in a learning problem?",
                "options": [
                    "A) The type of data to use",
                    "B) How to measure task performance", 
                    "C) The algorithm complexity",
                    "D) The training time required"
                ],
                "answer": "B",
                "explanation": "The Performance measure P quantifies how well the task is being performed."
            }
        ],
        "Find-S Algorithm": [
            {
                "question": "What does the Find-S algorithm find?",
                "options": [
                    "A) Most general hypothesis",
                    "B) Most specific hypothesis consistent with positive examples",
                    "C) All possible hypotheses", 
                    "D) Random hypothesis"
                ],
                "answer": "B",
                "explanation": "Find-S finds the most specific hypothesis consistent with positive training examples."
            },
            {
                "question": "How does Find-S handle negative examples?",
                "options": [
                    "A) Uses them to specialize",
                    "B) Ignores them completely",
                    "C) Creates separate rules",
                    "D) Generalizes based on them"
                ],
                "answer": "B", 
                "explanation": "Find-S algorithm ignores negative examples and only uses positive examples."
            }
        ]
    }
    
    # Return predefined questions if available, otherwise generate simple ones
    if topic_name in quiz_bank:
        return quiz_bank[topic_name][:2]  # Return 2 questions
    else:
        return [
            {
                "question": f"What is a key concept in {topic_name}?",
                "options": [
                    "A) Algorithm efficiency",
                    "B) Data preprocessing", 
                    "C) Model complexity",
                    "D) All of the above"
                ],
                "answer": "D",
                "explanation": f"{topic_name} involves multiple aspects of machine learning including algorithms, data, and models."
            }
        ]

# Initialize session state
if 'student_progress' not in st.session_state:
    st.session_state.student_progress = {topic: 0.5 for topic in SYLLABUS_TOPICS}

if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Quiz Generation")
    
    # Topic selection
    weakest_topic = min(st.session_state.student_progress, 
                       key=st.session_state.student_progress.get)
    
    st.info(f"Recommended: {weakest_topic} (Confidence: {st.session_state.student_progress[weakest_topic]:.2f})")
    
    selected_topic = st.selectbox("Choose topic:", SYLLABUS_TOPICS)
    
    if st.button("🚀 Generate Quiz"):
        with st.spinner("Generating quiz..."):
            content = extract_pdf_content()
            quiz = generate_quiz_lightweight(selected_topic, content)
            st.session_state.current_quiz = quiz
            st.session_state.current_topic = selected_topic

# Display quiz
if st.session_state.current_quiz:
    st.header(f"📝 Quiz: {st.session_state.current_topic}")
    
    answers = {}
    for i, question in enumerate(st.session_state.current_quiz):
        st.subheader(f"Question {i+1}")
        st.write(question['question'])
        
        answer = st.radio("Select:", question['options'], key=f"q_{i}")
        answers[i] = answer
    
    if st.button("Submit Quiz"):
        correct_count = 0
        for i, question in enumerate(st.session_state.current_quiz):
            is_correct = answers[i].startswith(question['answer'])
            if is_correct:
                correct_count += 1
            
            # Update progress
            current_score = st.session_state.student_progress[st.session_state.current_topic]
            if is_correct:
                st.session_state.student_progress[st.session_state.current_topic] = min(1.0, current_score + 0.1)
            else:
                st.session_state.student_progress[st.session_state.current_topic] = max(0.0, current_score - 0.1)
        
        # Show results
        st.success(f"Score: {correct_count}/{len(st.session_state.current_quiz)}")
        
        for i, question in enumerate(st.session_state.current_quiz):
            is_correct = answers[i].startswith(question['answer'])
            with st.expander(f"Q{i+1} - {'✓' if is_correct else '✗'}"):
                st.write(f"**Your answer:** {answers[i]}")
                if not is_correct:
                    st.write(f"**Correct:** {question['answer']}")
                st.write(f"**Explanation:** {question['explanation']}")

with col2:
    st.header("📊 Your Progress")
    for topic, confidence in st.session_state.student_progress.items():
        st.metric(topic.replace(" ", "\n", 1), f"{confidence:.1f}")
        st.progress(confidence)
    
    st.header("📚 About")
    st.info("Lightweight ML Quiz System for Hugging Face Spaces")