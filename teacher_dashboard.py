import streamlit as st
import pandas as pd
import os
import datetime  # Add this import
from content_service import ContentService
from progress_service import ProgressService
from auth_service import AuthService
import datetime

def teacher_dashboard():
    if 'user' not in st.session_state or st.session_state.user.role != 'teacher':
        st.error("Access denied. Teacher login required.")
        return
    
    st.title(f"👨‍🏫 Teacher Dashboard - Welcome {st.session_state.user.full_name}")
    
    content_service = ContentService()
    progress_service = ProgressService()
    teacher_id = st.session_state.user.id
    
    tab1, tab2, tab3, tab4 = st.tabs(["My Subjects", "Student Progress", "Analytics", "Recommendations"])
    
    with tab1:
        st.header("📚 Subject Management")
        
        # Create new subject
        with st.expander("➕ Create New Subject"):
            with st.form("new_subject"):
                subject_name = st.text_input("Subject Name")
                subject_desc = st.text_area("Description")
                
                if st.form_submit_button("Create Subject"):
                    if subject_name:
                        subject_id = content_service.create_subject(subject_name, subject_desc, teacher_id)
                        st.success(f"Subject '{subject_name}' created successfully!")
                        st.rerun()
        
        # Display existing subjects
        st.subheader("📋 Your Subjects")
        subjects = content_service.get_subjects_by_teacher(teacher_id)
        
        if not subjects:
            st.info("No subjects created yet. Create your first subject above!")
        
        for subject in subjects:
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.subheader(subject.name)
                    st.write(subject.description)
                    
                    # Show quick stats
                    modules = content_service.get_modules_by_subject(subject.id)
                    total_topics = sum(len(content_service.get_topics_by_module(m.id)) for m in modules)
                    books = content_service.get_books_by_subject(subject.id)
                    
                    st.caption(f"📖 {len(modules)} modules • 📝 {total_topics} topics • 📚 {len(books)} books")
                
                with col2:
                    if st.button(f"📝 Manage", key=f"manage_{subject.id}"):
                        st.session_state.managing_subject = subject.id
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{subject.id}", type="secondary"):
                        if st.session_state.get(f'confirm_delete_{subject.id}'):
                            try:
                                content_service.delete_subject(subject.id, teacher_id)
                                st.success("Subject deleted!")
                                if f'confirm_delete_{subject.id}' in st.session_state:
                                    del st.session_state[f'confirm_delete_{subject.id}']
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting subject: {e}")
                        else:
                            st.session_state[f'confirm_delete_{subject.id}'] = True
                            st.warning("Click delete again to confirm")
                            st.rerun()
                
                # Subject management interface
                if st.session_state.get('managing_subject') == subject.id:
                    manage_subject_content(subject, content_service)
                
                st.divider()
    
    with tab2:
        st.header("📊 Student Progress Overview")
        display_student_progress(progress_service, teacher_id)
    
    with tab3:
        st.header("📈 Analytics & Insights")
        display_analytics(progress_service, teacher_id)
    
    with tab4:
        st.header("💡 Teaching Recommendations")
        display_recommendations(progress_service, teacher_id)

def manage_subject_content(subject, content_service):
    """Manage modules, topics, and books for a subject"""
    st.write(f"**Managing: {subject.name}**")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("✅ Done", key=f"done_{subject.id}"):
            st.session_state.pop('managing_subject', None)
            st.rerun()
    
    # Tabs for different management sections
    tab1, tab2, tab3 = st.tabs(["📖 Modules & Topics", "📚 Books", "🔧 Quick Add"])
    
    with tab1:
        # Display and manage existing modules
        modules = content_service.get_modules_by_subject(subject.id)
        
        if modules:
            for module in modules:
                with st.expander(f"📖 {module.name}", expanded=False):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**Module:** {module.name}")
                    
                    with col2:
                        if st.button("➕ Add Topic", key=f"add_topic_{module.id}"):
                            st.session_state[f'adding_topic_to_{module.id}'] = True
                    
                    with col3:
                        if st.button("🗑️ Delete Module", key=f"del_module_{module.id}", type="secondary"):
                            if st.session_state.get(f'confirm_delete_module_{module.id}'):
                                try:
                                    content_service.delete_module(module.id)
                                    st.success(f"Module '{module.name}' deleted!")
                                    if f'confirm_delete_module_{module.id}' in st.session_state:
                                        del st.session_state[f'confirm_delete_module_{module.id}']
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting module: {e}")
                            else:
                                st.session_state[f'confirm_delete_module_{module.id}'] = True
                                st.warning("Click delete again to confirm")
                                st.rerun()
                    
                    # Show topics
                    topics = content_service.get_topics_by_module(module.id)
                    if topics:
                        for topic in topics:
                            topic_col1, topic_col2 = st.columns([5, 1])
                            with topic_col1:
                                st.write(f"  • {topic.name}")
                            with topic_col2:
                                if st.button("🗑️", key=f"del_topic_{topic.id}", help="Delete topic"):
                                    if st.session_state.get(f'confirm_delete_topic_{topic.id}'):
                                        try:
                                            content_service.delete_topic(topic.id)
                                            st.success(f"Topic '{topic.name}' deleted!")
                                            if f'confirm_delete_topic_{topic.id}' in st.session_state:
                                                del st.session_state[f'confirm_delete_topic_{topic.id}']
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error deleting topic: {e}")
                                    else:
                                        st.session_state[f'confirm_delete_topic_{topic.id}'] = True
                                        st.warning("Click delete again to confirm")
                                        st.rerun()
                    else:
                        st.write("  No topics yet")
                    
                    # Add topic form
                    if st.session_state.get(f'adding_topic_to_{module.id}'):
                        with st.form(f"add_topic_form_{module.id}"):
                            new_topic = st.text_input("Topic Name")
                            topic_desc = st.text_input("Description (optional)")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Add Topic"):
                                    if new_topic:
                                        existing_topics = len(topics) if topics else 0
                                        content_service.add_topic(module.id, new_topic, topic_desc, existing_topics + 1)
                                        st.success(f"Topic '{new_topic}' added!")
                                        st.session_state.pop(f'adding_topic_to_{module.id}', None)
                                        st.rerun()
                            
                            with col2:
                                if st.form_submit_button("Cancel"):
                                    st.session_state.pop(f'adding_topic_to_{module.id}', None)
                                    st.rerun()
        
        # Add new module
        st.subheader("➕ Add New Module")
        with st.form(f"new_module_{subject.id}"):
            module_name = st.text_input("Module Name")
            module_desc = st.text_input("Module Description (optional)")
            
            if st.form_submit_button("Create Module"):
                if module_name:
                    existing_modules = len(modules) if modules else 0
                    content_service.add_module(subject.id, module_name, module_desc, existing_modules + 1)
                    st.success(f"Module '{module_name}' created!")
                    st.rerun()
    
    with tab2:
        manage_books(subject, content_service)
    
    with tab3:
        # Quick bulk add
        st.subheader("🚀 Quick Bulk Add")
        
        bulk_option = st.selectbox("What would you like to add?", 
                                  ["New Module with Topics", "Topics to Existing Module"])
        
        if bulk_option == "New Module with Topics":
            with st.form(f"bulk_module_{subject.id}"):
                module_name = st.text_input("Module Name")
                topics_text = st.text_area("Topics (one per line)", 
                                         placeholder="Topic 1\nTopic 2\nTopic 3\n...")
                
                if st.form_submit_button("Create Module with Topics"):
                    if module_name and topics_text:
                        # Create module
                        existing_modules = content_service.get_modules_by_subject(subject.id)
                        module_id = content_service.add_module(subject.id, module_name, "", len(existing_modules) + 1)
                        
                        # Add topics
                        topics = [t.strip() for t in topics_text.split('\n') if t.strip()]
                        for i, topic in enumerate(topics):
                            content_service.add_topic(module_id, topic, "", i + 1)
                        
                        st.success(f"Created module '{module_name}' with {len(topics)} topics!")
                        st.rerun()
        
        elif bulk_option == "Topics to Existing Module":
            modules = content_service.get_modules_by_subject(subject.id)
            if modules:
                with st.form(f"bulk_topics_{subject.id}"):
                    selected_module = st.selectbox("Select Module", modules, format_func=lambda x: x.name)
                    topics_text = st.text_area("Topics (one per line)", 
                                             placeholder="Topic 1\nTopic 2\nTopic 3\n...")
                    
                    if st.form_submit_button("Add Topics"):
                        if topics_text:
                            existing_topics = content_service.get_topics_by_module(selected_module.id)
                            start_order = len(existing_topics) + 1
                            
                            topics = [t.strip() for t in topics_text.split('\n') if t.strip()]
                            for i, topic in enumerate(topics):
                                content_service.add_topic(selected_module.id, topic, "", start_order + i)
                            
                            st.success(f"Added {len(topics)} topics to '{selected_module.name}'!")
                            st.rerun()
            else:
                st.info("Create a module first")

def manage_books(subject, content_service):
    """Book management"""
    st.subheader("📚 Books")
    
    # Upload new book
    with st.form(f"upload_book_{subject.id}"):
        uploaded_file = st.file_uploader("Upload PDF Book", type="pdf")
        
        col1, col2 = st.columns(2)
        with col1:
            book_title = st.text_input("Book Title")
        with col2:
            book_author = st.text_input("Author")
        
        if st.form_submit_button("📤 Upload Book"):
            if uploaded_file and book_title:
                try:
                    # Create books directory if it doesn't exist
                    books_dir = f"books/subject_{subject.id}"
                    os.makedirs(books_dir, exist_ok=True)
                    
                    # Generate a unique filename to avoid conflicts
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_filename = "".join([c if c.isalnum() else "_" for c in uploaded_file.name])
                    unique_filename = f"{timestamp}_{safe_filename}"
                    book_path = os.path.join(books_dir, unique_filename)
                    
                    # Save file with unique name
                    with open(book_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Add to database
                    content_service.add_book(subject.id, book_title, book_author, book_path)
                    st.success("Book uploaded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error uploading book: {str(e)}")
            else:
                st.error("Please select a file and enter a title")
    
    # Display existing books with refresh button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("Uploaded Books")
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get fresh list of books
    books = content_service.get_books_by_subject(subject.id)
    if books:
        for book in books:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📖 **{book.title}** by {book.author}")
                if os.path.exists(book.file_path):
                    st.caption(f"✅ File available: {os.path.basename(book.file_path)}")
                else:
                    st.caption(f"⚠️ File not found: {os.path.basename(book.file_path)}")
            with col2:
                if st.button(f"🗑️", key=f"remove_book_{book.id}", help="Remove book"):
                    content_service.remove_book(book.id)
                    st.success("Book removed!")
                    st.rerun()
    else:
        st.info("No books uploaded yet")

def display_student_progress(progress_service, teacher_id):
    """Display student progress for teacher's subjects"""
    st.info("Student progress tracking will show here once students start taking quizzes")

def display_analytics(progress_service, teacher_id):
    """Display analytics for teacher"""
    try:
        weakest_topics = progress_service.get_weakest_topics_for_teacher(teacher_id)
        
        if weakest_topics:
            st.subheader("Topics Where Students Struggle Most")
            df = pd.DataFrame(weakest_topics)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No student data available yet")
    except Exception as e:
        st.info("Analytics will be available once students start taking quizzes")

def display_recommendations(progress_service, teacher_id):
    """Display teaching recommendations"""
    st.info("AI-powered teaching recommendations will appear here based on student performance")