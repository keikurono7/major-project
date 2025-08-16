import streamlit as st
import json
from datetime import datetime
# Import your existing functions
from main_quiz import generate_quiz, load_student_progress, save_student_progress, update_confidence_score, get_next_quiz_topic, ingest_pdf

st.set_page_config(
    page_title="Machine Learning Quiz System",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Machine Learning Quiz System")
st.markdown("*Based on Tom Mitchell's Machine Learning Textbook*")

# Initialize session state
if 'student_id' not in st.session_state:
    st.session_state.student_id = "user123"
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = None

# Load vector database (cached)
@st.cache_resource
def load_vectordb():
    return ingest_pdf("MachineLearningTomMitchell.pdf")

# Sidebar - Student Progress
with st.sidebar:
    st.header("📊 Your Progress")
    progress = load_student_progress(st.session_state.student_id)
    
    # Progress visualization
    for topic, confidence in progress["confidence_scores"].items():
        st.metric(
            label=topic.replace(" ", "\n", 1),  # Break long topics
            value=f"{confidence:.1f}",
            help=f"Confidence level: {confidence:.2f}"
        )
        st.progress(confidence)

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Quiz Generation")
    
    # Only show quiz generation if no quiz is in progress
    if not st.session_state.get('quiz_started'):
        # Topic selection
        weakest_topic = get_next_quiz_topic(progress)
        st.info(f"**Recommended topic:** {weakest_topic} (Confidence: {progress['confidence_scores'][weakest_topic]:.2f})")
        
        # Manual topic selection
        selected_topic = st.selectbox(
            "Or choose a different topic:",
            options=list(progress["confidence_scores"].keys()),
            index=list(progress["confidence_scores"].keys()).index(weakest_topic)
        )
        
        # Generate quiz button
        if st.button("🚀 Generate Quiz", type="primary"):
            with st.spinner("Generating quiz from textbook..."):
                vectordb = load_vectordb()
                quiz = generate_quiz(vectordb, selected_topic, progress["confidence_scores"][selected_topic])
                
                if quiz:
                    st.session_state.current_quiz = quiz
                    st.session_state.current_topic = selected_topic
                    st.session_state.quiz_started = True
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_results = None
                    st.rerun()
                else:
                    st.error("Failed to generate quiz. Please try again.")

# Quiz Display
if st.session_state.get('quiz_started') and st.session_state.current_quiz and not st.session_state.get('quiz_completed'):
    st.header(f"📝 Quiz: {st.session_state.current_topic}")
    
    with st.form("quiz_form"):
        answers = {}
        
        for i, question in enumerate(st.session_state.current_quiz):
            st.subheader(f"Question {i+1}")
            st.write(question['question'])
            
            # Radio buttons for options
            answer = st.radio(
                "Select your answer:",
                options=question['options'],
                key=f"q_{i}",
                label_visibility="collapsed"
            )
            answers[i] = answer
        
        # Submit button
        submitted = st.form_submit_button("Submit Quiz", type="primary")
        
        if submitted:
            # Calculate results
            correct_count = 0
            results = []
            
            for i, question in enumerate(st.session_state.current_quiz):
                user_answer = answers[i]
                correct_answer = question['answer']
                is_correct = user_answer.startswith(correct_answer)
                
                if is_correct:
                    correct_count += 1
                
                results.append({
                    'question': question['question'],
                    'user_answer': user_answer,
                    'correct_answer': question['answer'],
                    'explanation': question.get('explanation', ''),
                    'is_correct': is_correct
                })
                
                # Update progress
                progress = update_confidence_score(progress, st.session_state.current_topic, is_correct)
            
            # Store results in session state
            st.session_state.quiz_results = {
                'correct_count': correct_count,
                'total_questions': len(results),
                'results': results,
                'updated_progress': progress
            }
            st.session_state.quiz_completed = True
            st.rerun()

# Results Display (outside of form)
if st.session_state.get('quiz_completed') and st.session_state.quiz_results:
    st.header("🎉 Quiz Results")
    
    results_data = st.session_state.quiz_results
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{results_data['correct_count']}/{results_data['total_questions']}")
    with col2:
        st.metric("Percentage", f"{results_data['correct_count']/results_data['total_questions']*100:.1f}%")
    with col3:
        st.metric("Updated Confidence", f"{results_data['updated_progress']['confidence_scores'][st.session_state.current_topic]:.2f}")
    
    # Detailed results
    for i, result in enumerate(results_data['results']):
        with st.expander(f"Question {i+1} - {'✅ Correct' if result['is_correct'] else '❌ Incorrect'}"):
            st.write(f"**Question:** {result['question']}")
            st.write(f"**Your Answer:** {result['user_answer']}")
            if not result['is_correct']:
                st.write(f"**Correct Answer:** {result['correct_answer']}")
            st.write(f"**Explanation:** {result['explanation']}")
    
    # Action buttons (outside form)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Take Another Quiz", type="primary"):
            st.session_state.quiz_started = False
            st.session_state.quiz_completed = False
            st.session_state.current_quiz = None
            st.session_state.quiz_results = None
            st.rerun()
    
    with col2:
        if st.button("📊 View Updated Progress"):
            st.session_state.quiz_started = False
            st.session_state.quiz_completed = False
            st.session_state.current_quiz = None
            st.session_state.quiz_results = None
            st.rerun()

with col2:
    st.header("📚 About")
    st.info("""
    This quiz system generates questions directly from Tom Mitchell's 
    "Machine Learning" textbook using:
    
    - **Vector Database**: ChromaDB with textbook content
    - **AI Generation**: Local Ollama (Mistral 7B)
    - **Adaptive Learning**: Progress tracking per topic
    """)
    
    # Study tips
    st.header("💡 Study Tips")
    st.success("Focus on topics with lower confidence scores for maximum learning impact!")
    
    # Quick stats
    if st.session_state.get('quiz_completed'):
        st.header("📈 Session Stats")
        total_topics = len(progress["confidence_scores"])
        avg_confidence = sum(progress["confidence_scores"].values()) / total_topics
        st.metric("Average Confidence", f"{avg_confidence:.2f}")
        st.metric("Topics Completed", f"1/{total_topics}")