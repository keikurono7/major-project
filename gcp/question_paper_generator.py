# question_paper_generator.py (Final Version with Post-Processing)

import os
import re
import random
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from langchain_ollama import OllamaLLM

# Configuration
OUTPUT_DIR = "./question_papers"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OLLAMA_MODEL = "phi3:mini"
OLLAMA_URL = "http://localhost:11434"  # adjust if different

def clean_ocr_text(raw_text: str) -> str:
    # (This function remains the same)
    cleaned_lines = []
    lines = raw_text.split('\n')
    junk_keywords = [
        'vturesource', 'go green', 'usn', 'download this free',
        'branches', 'all semesters', 'notes', 'question papers', 'lab manuals'
    ]
    question_start_pattern = re.compile(r'^\s*(\d+\s*)?[a-zA-Z]\.\s|OR|Module-\d', re.IGNORECASE)
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in junk_keywords):
            continue
        if len(line.strip()) < 5:
            continue
        if cleaned_lines and not question_start_pattern.match(line.strip()):
            cleaned_lines[-1] = cleaned_lines[-1].strip() + " " + line.strip()
        else:
            cleaned_lines.append(line.strip())
    return "\n".join(cleaned_lines)

def analyze_past_paper_style(past_paper_text: str) -> str:
    # (This function remains the same)
    print("🔬 Stage 1: Analyzing past paper for style and topics...")
    prompt = f"""
    You are an expert educational analyst. Analyze the following examination paper text and extract its essential characteristics.
    Focus ONLY on the academic content. Describe the:
    1.  **Main Topics Tested:** List the 5-7 most important academic topics.
    2.  **Question Style:** Describe the typical style (e.g., definition-based, compare-contrast, derivations, applications).
    3.  **Cognitive Level:** Briefly assess the difficulty (e.g., tests recall, requires application, demands analysis).

    EXAMINATION PAPER TEXT:
    ```
    {past_paper_text}
    ```
    Provide a concise summary.
    """
    llm = OllamaLLM(model=OLLAMA_MODEL)
    analysis = llm.invoke(prompt)
    print("✅ Analysis complete.")
    return analysis

# --- NEW FUNCTION FOR POST-PROCESSING ---
def add_marking_variety(paper_content: str) -> str:
    """
    Finds pairs of (10 Marks) and randomly changes them to other valid distributions.
    This adds variety *after* the AI has generated a clean, structured paper.
    """
    print("🎨 Applying post-processing to add marking variety...")
    # Patterns that sum to 20
    distributions = [
        (8, 12), (12, 8),
        (7, 13), (13, 7),
        (6, 14), (14, 6)
    ]
    
    # This function is called for every pair of "(10 Marks)" found
    def replacer(match):
        # Decide whether to replace this pair or keep it as 10+10
        if random.random() > 0.5: # 50% chance to change it
            dist = random.choice(distributions)
            return f"({dist[0]} Marks)\n       b. [Question Text] ({dist[1]} Marks)"
        else:
            # Keep it as 10+10
            return match.group(0)

    # Use a regex that captures the full 'a' and 'b' lines to replace marks in pairs
    # This is a simplified regex; a more complex one could be used if needed.
    # For now, let's just replace the mark values.
    
    marks_tags = re.findall(r'\(10 Marks\)', paper_content)
    num_pairs = len(marks_tags) // 2
    
    new_content = paper_content
    for _ in range(num_pairs):
        if random.random() > 0.5: # 50% chance to vary a pair of marks
            dist = random.choice(distributions)
            # Replace the first two occurrences of (10 Marks) with the new distribution
            new_content = new_content.replace('(10 Marks)', f'({dist[0]} Marks)', 1)
            new_content = new_content.replace('(10 Marks)', f'({dist[1]} Marks)', 1)
            
    return new_content

def _call_ollama(prompt: str, max_tokens: int = 1000) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.2
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    # depends on Ollama response format — try to extract text field
    # adjust keys if your Ollama returns different structure
    return data.get("text") or data.get("output") or json.dumps(data)

def generate_questions_from_text(text: str, max_questions: int = 50) -> List[Dict]:
    prompt = f"""
You are a question generator. Given the following source text, generate up to {max_questions} candidate exam questions.
Return output as JSON array of objects with keys: text, type, default_marks, difficulty, notes.
Source text:
\"\"\"{text[:20000]}\"\"\"  # truncate if extremely long
Instructions:
- Produce many short clear questions, variety of types (MCQ, short answer, long answer).
- For MCQs include options field (array) and indicate correct_index.
- For each question include default_marks (suggested).
Return ONLY valid JSON.
"""
    out = _call_ollama(prompt, max_tokens=2000)
    try:
        # ensure JSON; Ollama may return raw text — attempt to parse
        questions = json.loads(out)
        return questions
    except Exception:
        # fallback: try to extract JSON substring
        # simple heuristic: find first '[' and last ']'
        try:
            start = out.index('[')
            end = out.rindex(']') + 1
            return json.loads(out[start:end])
        except Exception as e:
            raise RuntimeError("Failed to parse Ollama response: " + str(e))

def finalize_questions_with_ollama(selected_questions: List[Dict], max_marks: int = 100) -> List[Dict]:
    # Send selected questions and desired total max marks; task the model to pick a final set
    payload_json = json.dumps(selected_questions, ensure_ascii=False)
    prompt = f"""
You are an exam composer tool. You are given candidate questions (JSON array). Choose a subset or adjust marks so that the total marks equal {max_marks} (or as close as possible without exceeding).
Input questions:
{payload_json}
Instructions:
- Return a JSON array of final question objects with keys: text, marks, type, notes.
- Do not include any explanatory text.
"""
    out = _call_ollama(prompt, max_tokens=1000)
    try:
        final = json.loads(out)
        return final
    except Exception:
        # attempt heuristics as above
        try:
            start = out.index('[')
            end = out.rindex(']') + 1
            return json.loads(out[start:end])
        except Exception as e:
            raise RuntimeError("Failed to parse Ollama response: " + str(e))

def generate_question_paper(
    subject_data: Dict[str, Any], 
    past_paper_text: Optional[str] = None
) -> Dict[str, Any]:
    # (Topic extraction logic remains the same)
    subject_name = subject_data.get("name", "Examination Paper")
    all_topics = [
        topic.get("name", "").strip() for module in subject_data.get("modules", []) 
        for topic in module.get("topics", []) if topic.get("name", "").strip()
    ]
    print(f"🏗️ Generating question paper for {subject_name} covering {len(all_topics)} topics")
    
    # --- PROMPT IS NOW RADICALLY SIMPLIFIED AND RIGID ---
    base_prompt_instructions = f"""
    You are an expert professor creating a clean, well-structured examination paper for the subject: {subject_name}.

    ## INSTRUCTIONS (Follow These Rules Exactly)
    1.  **Structure:** Create exactly 5 modules (Module-1 to Module-5).
    2.  **Module Content:** Each module must contain two full, independent questions separated by an "OR".
    3.  **Numbering:** Questions must be numbered consecutively from 1 to 10. (Module-1 has Q1 OR Q2, Module-2 has Q3 OR Q4, etc.).
    4.  **Sub-questions:** **EACH** of the 10 questions must have exactly two sub-questions, labeled 'a' and 'b'.
    5.  **Marking:** Assign exactly **10 marks** to every sub-question. Do not vary this.
    6.  **Crucial Format Example for a Module:**
        ```
        Module-1
        1. a. [Text for sub-question 1a] (10 Marks)
           b. [Text for sub-question 1b] (10 Marks)
        OR
        2. a. [Text for sub-question 2a] (10 Marks)
           b. [Text for sub-question 2b] (10 Marks)
        ```
    7.  **Syllabus:** Base the questions on the provided syllabus topics.
    8.  **No Repetition:** Ensure all questions are unique.
    """

    if past_paper_text:
        cleaned_text = clean_ocr_text(past_paper_text)
        style_guidelines = analyze_past_paper_style(cleaned_text)
        print("✍️ Stage 2: Generating new paper using style guidelines...")
        prompt = f"""
        {base_prompt_instructions}

        ## SYLLABUS TO COVER
        {', '.join(all_topics)}

        ## STYLE GUIDELINES (from analysis of a past paper)
        Use the following analysis to influence the tone, topic focus, and difficulty of the new questions.
        <analysis>
        {style_guidelines}
        </analysis>

        ## GENERATE THE NEW QUESTION PAPER BELOW
        """
    else:
        print("📝 Generating paper without a past paper for reference.")
        prompt = f"""
        {base_prompt_instructions}

        ## SYLLABUS TO COVER
        {', '.join(all_topics)}

        ## GENERATE THE NEW QUESTION PAPER BELOW
        """

    llm = OllamaLLM(model=OLLAMA_MODEL)
    paper_content = llm.invoke(prompt)
    
    # --- APPLY POST-PROCESSING STEP ---
    processed_content = add_marking_variety(paper_content)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    question_paper = {
        "title": f"{subject_name} Examination",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": processed_content, # Use the processed content
        "filename": f"question_paper_{timestamp}.txt"
    }
    
    print("✅ Question paper generated and processed successfully.")
    return question_paper

def save_question_paper(question_paper: Dict[str, Any]) -> str:
    # (This function remains the same)
    filename = question_paper.get("filename", f"question_paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"{'='*80}\n")
        f.write(f"{question_paper['title'].upper():^80}\n")
        f.write(f"Date: {question_paper['date']}\n")
        f.write(f"{'='*80}\n\n")
        f.write(question_paper['content'])
    
    print(f"📄 Question paper saved to {file_path}")
    return filename