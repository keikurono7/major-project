import streamlit as st
import pandas as pd  # Add this missing import
from content_service import ContentService
from quiz_service import QuizService
from progress_service import ProgressService

def student_interface():
    if 'user' not in st.session_state or st.session_state.user.role != 'student':
        st.error("Access denied. Student login required.")
        return
    
    st.title(f"🎓 Student Dashboard - Welcome {st.session_state.user.full_name}")
    
    content_service = ContentService()
    quiz_service = QuizService()
    progress_service = ProgressService()
    student_id = st.session_state.user.id
    
    # Sidebar - Subject Selection
    with st.sidebar:
        st.header("📚 Available Subjects")
        subjects = content_service.get_all_subjects()
        
        if subjects:
            subject_options = {f"{s.name} (by {s.teacher_name})": s.id for s in subjects}
            selected_subject_name = st.selectbox("Choose Subject:", list(subject_options.keys()))
            selected_subject_id = subject_options[selected_subject_name]
            
            st.session_state.selected_subject_id = selected_subject_id
        else:
            st.info("No subjects available yet")
            return
    
    # Main content
    if 'selected_subject_id' in st.session_state:
        subject_id = st.session_state.selected_subject_id
        
        # Get subject details
        subject = next(s for s in subjects if s.id == subject_id)
        st.header(f"📖 {subject.name}")
        st.write(subject.description)
        
        # Module and Topic Selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            modules = content_service.get_modules_by_subject(subject_id)
            
            if modules:
                selected_module = st.selectbox(
                    "Select Module:",
                    modules,
                    format_func=lambda x: x.name
                )
                
                if selected_module:
                    topics = content_service.get_topics_by_module(selected_module.id)
                    
                    if topics:
                        selected_topic = st.selectbox(
                            "Select Topic:",
                            topics,
                            format_func=lambda x: x.name
                        )
                        
                        if selected_topic:
                            # Display topic details
                            st.subheader(f"📝 {selected_topic.name}")
                            if selected_topic.description:
                                st.write(selected_topic.description)
                            
                            # Get student progress for this topic
                            progress = progress_service.get_student_progress(student_id, selected_topic.id)
                            confidence = progress.confidence_score if progress else 0.5
                            
                            st.info(f"Your current confidence level: {confidence:.2f}")
                            
                            # Quiz Generation
                            if st.button("🚀 Generate Quiz", type="primary"):
                                with st.spinner("Generating quiz from textbooks..."):
                                    try:
                                        quiz = quiz_service.generate_quiz(subject_id, selected_topic.id, confidence)
                                        
                                        if quiz:
                                            st.session_state.current_quiz = quiz
                                            st.session_state.current_topic_id = selected_topic.id
                                            st.session_state.quiz_started = True
                                            st.rerun()
                                        else:
                                            st.error("Failed to generate quiz. Please try again.")
                                    except ValueError as e:
                                        if "No books available" in str(e):
                                            st.error("No books available for this subject. Ask your teacher to add study materials.")
                                        elif "Could not load any content" in str(e):
                                            st.error("Could not extract content from the books. Please contact your teacher.")
                                        else:
                                            st.error(f"Error generating quiz: {str(e)}")
                                    except Exception as e:
                                        st.error(f"Unexpected error: {str(e)}")
                    else:
                        st.info("No topics available in this module")
                else:
                    st.info("Please select a module")
            else:
                st.info("No modules available in this subject")
        
        with col2:
            # Progress Summary
            st.subheader("📊 Your Progress")
            student_progress = progress_service.get_student_subject_progress(student_id, subject_id)
            
            if student_progress:
                avg_confidence = sum(p.confidence_score for p in student_progress) / len(student_progress)
                st.metric("Average Confidence", f"{avg_confidence:.2f}")
                st.metric("Topics Attempted", len(student_progress))
                
                # Progress chart
                progress_df = pd.DataFrame([
                    {"Topic": p.topic_name, "Confidence": p.confidence_score}
                    for p in student_progress
                ])
                st.bar_chart(progress_df.set_index("Topic"))
            else:
                st.info("No progress data yet. Take a quiz to get started!")
    
    # Quiz Display
    if st.session_state.get('quiz_started') and 'current_quiz' in st.session_state:
        display_quiz()

def display_quiz():
    """Display and handle quiz interaction"""
    quiz = st.session_state.current_quiz
    topic_id = st.session_state.current_topic_id
    student_id = st.session_state.user.id
    
    st.header("📝 Quiz Time!")
    
    with st.form("quiz_form"):
        answers = {}
        
        for i, question in enumerate(quiz):
            st.subheader(f"Question {i+1}")
            st.write(question['question'])
            
            answer = st.radio(
                f"Select answer for question {i+1}:",
                question['options'],
                key=f"q_{i}",
                label_visibility="collapsed"
            )
            
            # Extract letter (A, B, C, D) from answer
            answers[i] = answer[0] if answer else None
        
        if st.form_submit_button("Submit Quiz", type="primary"):
            # Process quiz results
            correct_count = 0
            results = []
            
            for i, question in enumerate(quiz):
                is_correct = answers[i] == question['answer']
                if is_correct:
                    correct_count += 1
                
                results.append({
                    'question': question['question'],
                    'user_answer': answers[i],
                    'correct_answer': question['answer'],
                    'is_correct': is_correct,
                    'explanation': question.get('explanation', '')
                })
            
            # Update progress
            progress_service = ProgressService()
            progress_service.update_student_progress(
                student_id, topic_id, correct_count, len(quiz)
            )
            
            # Display results
            st.session_state.quiz_results = results
            st.session_state.quiz_score = correct_count
            st.session_state.quiz_total = len(quiz)
            st.session_state.quiz_completed = True
            st.session_state.quiz_started = False
            st.rerun()
    
    # Display quiz results
    if st.session_state.get('quiz_completed'):
        st.header("🎉 Quiz Results")
        
        score = st.session_state.quiz_score
        total = st.session_state.quiz_total
        percentage = (score / total) * 100
        
        st.success(f"You scored {score}/{total} ({percentage:.1f}%)")
        
        # Show detailed results
        for i, result in enumerate(st.session_state.quiz_results):
            with st.expander(f"Question {i+1} - {'✅ Correct' if result['is_correct'] else '❌ Incorrect'}"):
                st.write(f"**Question:** {result['question']}")
                st.write(f"**Your answer:** {result['user_answer']}")
                st.write(f"**Correct answer:** {result['correct_answer']}")
                if result['explanation']:
                    st.write(f"**Explanation:** {result['explanation']}")
        
        if st.button("Take Another Quiz"):
            # Clear quiz session
            for key in ['current_quiz', 'current_topic_id', 'quiz_started', 'quiz_completed', 'quiz_results']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()