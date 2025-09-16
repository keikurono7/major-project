# syllabus_parser.py

import re
import io
from typing import Dict, Any
import fitz  # PyMuPDF

def extract_syllabus_structure(syllabus_text: str, title: str = "Untitled Subject") -> Dict[str, Any]:
    """
    Extracts a clean, structured dictionary from syllabus text.
    
    Args:
        syllabus_text: Text content of the syllabus
        title: Subject title to use (will be used if name not found in text)
        
    Returns:
        Dictionary containing the structured syllabus
    """
    try:
        # Try multiple patterns to extract the subject name
        subject_name = title  # Initialize with the provided title
        
        # Pattern 1: Look for text before "Semester"
        subject_match = re.search(r"^(.*?)\nSemester", syllabus_text, re.MULTILINE)
        if subject_match:
            extracted_title = subject_match.group(1).strip()
            if extracted_title and len(extracted_title) > 3:  # Ensure we got a meaningful name
                subject_name = extracted_title
        
        # Pattern 2: Look for "Course Title:" or "Subject:"
        if subject_name == "Untitled Subject":
            title_match = re.search(r"(?:Course|Subject)(?:\s+Title)?[:]\s*(.*?)(?:\n|$)", syllabus_text, re.IGNORECASE)
            if title_match:
                extracted_title = title_match.group(1).strip()
                if extracted_title and len(extracted_title) > 3:
                    subject_name = extracted_title
        
        # Pattern 3: First line if it's all caps and looks like a title
        if subject_name == "Untitled Subject":
            first_line = syllabus_text.strip().split('\n')[0].strip()
            if first_line.isupper() and 10 < len(first_line) < 100:
                subject_name = first_line

        # Split text by modules
        module_text_blocks = re.split(r"(MODULE-\d+)", syllabus_text, flags=re.IGNORECASE)[1:]
        modules = []

        # If no modules found with MODULE-X pattern, try UNIT-X pattern
        if len(module_text_blocks) < 2:
            module_text_blocks = re.split(r"(UNIT-\d+|UNIT\s+\d+)", syllabus_text, flags=re.IGNORECASE)[1:]

        # If still no modules, create a generic module structure
        if len(module_text_blocks) < 2:
            # Try to find topics by looking for numbered lines or bullet points
            topic_matches = re.findall(r"^(\d+\.\d*\s+.+?)$|^[\u2022\u25CF•-]\s+(.+?)$", 
                                     syllabus_text, re.MULTILINE)
            
            topics = []
            for match in topic_matches:
                topic_name = match[0] if match[0] else match[1]
                if len(topic_name.strip()) > 5:  # Filter out short/empty lines
                    topics.append({"name": topic_name.strip(), "content": ""})
            
            if topics:
                modules = [{"name": "Module 1", "topics": topics}]
            else:
                # Last resort: just split by newlines and treat substantial lines as topics
                lines = [line.strip() for line in syllabus_text.split('\n') if len(line.strip()) > 20]
                topics = [{"name": line, "content": ""} for line in lines[:10]]  # Take first 10 substantial lines
                modules = [{"name": "Module 1", "topics": topics}]
        else:
            # Process module_text_blocks
            for i in range(0, len(module_text_blocks), 2):
                if i+1 >= len(module_text_blocks):
                    break
                    
                module_header = module_text_blocks[i]
                module_content = module_text_blocks[i+1]
                module_name = module_header.replace("-", " ").title()

                # Clean the content and stop at the next major section
                stop_phrases = ["PRACTICAL COMPONENT", "Course outcomes", "Text Book:", "MODULE-", "UNIT-", "UNIT "]
                for phrase in stop_phrases:
                    if phrase in module_content:
                        module_content = module_content.split(phrase, 1)[0]
                
                # Updated Logic: Join lines to create a single string, then split by delimiters
                cleaned_content = module_content.replace('\n', ' ').strip()
                cleaned_content = re.sub(r'\s{2,}', ' ', cleaned_content)
                
                topics = []
                # Split the cleaned content by commas and colons to get individual topics
                raw_topic_list = re.split(r'[,]', cleaned_content)
                
                for topic_name in raw_topic_list:
                    cleaned_topic = topic_name.strip()
                    if len(cleaned_topic) > 5:  # Ensure the topic is meaningful
                        topics.append({"name": cleaned_topic, "content": ""})

                if topics:
                    modules.append({"name": module_name, "topics": topics})
            
        return {"name": subject_name, "modules": modules}

    except Exception as e:
        print(f"Error extracting syllabus structure: {e}")
        # Even on error, use the provided title instead of default
        return {"name": title, "modules": []}

# Add function for PDF extraction if needed
def extract_text_from_pdf(pdf_bytes):
    """
    Extract text content from PDF bytes
    
    Args:
        pdf_bytes: Raw bytes of PDF file or BytesIO object
        
    Returns:
        Extracted text as string
    """
    try:
        if isinstance(pdf_bytes, bytes):
            pdf_bytes = io.BytesIO(pdf_bytes)
            
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")