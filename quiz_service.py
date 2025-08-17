from content_service import ContentService
from database import EducationDB
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import json
import os
import datetime

class QuizService:
    def __init__(self):
        self.db = EducationDB()
        self.content_service = ContentService()
        self.embedding_model = "nomic-embed-text"
        self.llm_model = "mistral:7b"
    
    def get_vector_db_for_subject(self, subject_id: int):
        """Get or create vector database for a subject"""
        db_path = f"./vector_db/subject_{subject_id}"
        
        if os.path.exists(db_path):
            # Check if we need to update the vector database
            last_update_file = os.path.join(db_path, "last_update.txt")
            
            # Get all books for this subject
            books = self.content_service.get_books_by_subject(subject_id)
            
            # If there are no books, we can't create a vector DB
            if not books:
                raise ValueError("No books available for this subject. Please add at least one book.")
                
            embeddings = OllamaEmbeddings(model=self.embedding_model)
            return Chroma(persist_directory=db_path, embedding_function=embeddings)
        
        # Create new vector database from subject books
        books = self.content_service.get_books_by_subject(subject_id)
        
        if not books:
            raise ValueError("No books available for this subject. Please add at least one book.")
        
        all_docs = []
        for book in books:
            if os.path.exists(book.file_path):
                try:
                    loader = PyPDFLoader(book.file_path)
                    documents = loader.load()
                    
                    # Add book metadata to documents
                    for doc in documents:
                        doc.metadata['book_title'] = book.title
                        doc.metadata['book_author'] = book.author
                        doc.metadata['subject_id'] = subject_id
                    
                    all_docs.extend(documents)
                except Exception as e:
                    print(f"Error loading book '{book.title}': {e}")
        
        if not all_docs:
            raise ValueError("Could not load any content from the books. Please check the PDF files.")
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        docs = text_splitter.split_documents(all_docs)
        
        # Create vector database
        os.makedirs(db_path, exist_ok=True)
        embeddings = OllamaEmbeddings(model=self.embedding_model)
        vectordb = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=db_path
        )
        
        # Record last update time
        with open(os.path.join(db_path, "last_update.txt"), "w") as f:
            f.write(datetime.datetime.now().isoformat())
        
        return vectordb
    
    def generate_quiz(self, subject_id: int, topic_id: int, student_confidence: float = 0.5):
        """Generate quiz for a specific topic"""
        # Get topic details
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.name, t.description, m.name as module_name, s.name as subject_name
            FROM topics t
            JOIN modules m ON t.module_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE t.id = ? AND s.id = ?
        """, (topic_id, subject_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError("Topic not found or doesn't belong to subject")
        
        topic_name, topic_desc, module_name, subject_name = result
        
        # Get vector database
        vectordb = self.get_vector_db_for_subject(subject_id)
        
        # Generate quiz using the same logic as before but with topic context
        prompt_template = """
        You are creating quiz questions based on the provided academic content.

        Context from textbooks: {context}

        Subject: {subject_name}
        Module: {module_name}
        Topic: {topic_name}
        Topic Description: {topic_description}

        Create exactly 3 multiple-choice questions about "{topic_name}" based on the context provided.
        Focus specifically on the topic within the context of the module and subject.

        Requirements:
        - Use the provided context to create relevant questions
        - Each question must have exactly 4 options (A, B, C, D)
        - Only one option should be correct
        - Provide clear explanations
        - Cover different aspects of the topic
        - Difficulty should match student confidence level (0.0-1.0): {confidence}

        Respond with valid JSON:
        [
          {{
            "question": "Question text here?",
            "options": [
              "A) First option",
              "B) Second option", 
              "C) Third option",
              "D) Fourth option"
            ],
            "answer": "A",
            "explanation": "Explanation of why this answer is correct."
          }}
        ]
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "subject_name", "module_name", "topic_name", "topic_description", "confidence"]
        )

        llm = OllamaLLM(model=self.llm_model)

        try:
            # Create a simplified chain that works directly with retrieval
            retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            
            # Get relevant documents first
            query = f"{subject_name} {module_name} {topic_name} {topic_desc}"
            docs = retriever.get_relevant_documents(query)
            
            # Combine documents into context
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Fill the prompt template
            filled_prompt = prompt.format(
                context=context,
                subject_name=subject_name,
                module_name=module_name,
                topic_name=topic_name,
                topic_description=topic_desc or "",
                confidence=student_confidence
            )
            
            # Generate response using LLM
            raw_response = llm.invoke(filled_prompt)
            
            # Parse JSON response
            json_start = raw_response.find("[")
            json_end = raw_response.rfind("]") + 1
            
            if json_start == -1 or json_end == 0:
                print("Failed to find JSON in response")
                return None
                
            json_string = raw_response[json_start:json_end]
            quiz_data = json.loads(json_string)
            
            if not isinstance(quiz_data, list) or len(quiz_data) == 0:
                print("Invalid quiz data format")
                return None
                
            return quiz_data
            
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return None