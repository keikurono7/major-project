import json
from transformers import pipeline
from huggingface_hub import login

# Load the syllabus from a JSON file
def load_syllabus(file_path="syllabus.json"):
    with open(file_path, "r") as f:
        return json.load(f)

# Initialize or load student progress
def load_student_progress(student_id):
    try:
        with open(f"progress_{student_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # If the progress file doesn't exist, create a new one.
        syllabus = load_syllabus()
        progress = {
            "student_id": student_id,
            "confidence_scores": {}
        }
        for topic in syllabus["topics"]:
            topic_name = topic["name"]
            progress["confidence_scores"][topic_name] = 0.5
        
        save_student_progress(progress)
        return progress

# Save student progress
def save_student_progress(progress):
    with open(f"progress_{progress['student_id']}.json", "w") as f:
        json.dump(progress, f, indent=2)

def generate_quiz(pipe, student_id, topic_name, difficulty_level):
    """
    Generates quiz questions for a specific topic and difficulty using Mistral.
    """
    prompt_text = f"""Generate a quiz with 5 multiple-choice questions on the topic: {topic_name}.
The difficulty level should be {difficulty_level}.
For each question, provide:
1. The question text
2. Four options (A, B, C, D)
3. The correct answer
4. A brief explanation

Format the response as a JSON array like this:
[
  {{
    "question": "What is a linked list?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option B",
    "explanation": "Brief explanation here"
  }}
]

Topic: {topic_name}
Difficulty: {difficulty_level}

JSON:"""

    # Generate response using Mistral
    response = pipe(prompt_text, 
                   max_length=2000, 
                   num_return_sequences=1, 
                   temperature=0.7,
                   do_sample=True,
                   pad_token_id=pipe.tokenizer.eos_token_id)
    
    generated_text = response[0]['generated_text']
    
    # Extract JSON from the generated text
    json_start = generated_text.find('[')
    json_end = generated_text.rfind(']') + 1
    
    json_text = generated_text[json_start:json_end]
    quiz_data = json.loads(json_text)
    
    return quiz_data

def update_confidence_score(progress, topic_name, quiz_results):
    """
    Updates the student's confidence score based on quiz results.
    """
    correct_answers = sum(1 for result in quiz_results if result["is_correct"])
    total_questions = len(quiz_results)
    
    current_score = progress["confidence_scores"][topic_name]
    
    # Simple algorithm to update the score
    if total_questions > 0:
        # This formula provides a smoothed update to the score
        new_score = (current_score * (total_questions - 1) + (correct_answers / total_questions)) / total_questions
        progress["confidence_scores"][topic_name] = new_score
    
    save_student_progress(progress)
    return progress

def get_next_quiz_topic(progress, syllabus):
    """
    Suggests the next topic for a quiz based on the lowest confidence score.
    """
    lowest_confidence_topic = min(
        progress["confidence_scores"],
        key=progress["confidence_scores"].get
    )
    return lowest_confidence_topic, progress["confidence_scores"][lowest_confidence_topic]

# --- Main Logic with User Input ---
def main():
    # Login to Hugging Face Hub
    HF_TOKEN = "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"
    login(token=HF_TOKEN)
    
    # Setup - Initialize Mistral pipeline
    print("Loading Mistral model... This may take a few minutes on first run.")
    
    pipe = pipeline("text-generation", model="google/gemma-2b")
    print("Model loaded successfully!\n")
    
    student_id = "user123"

    # --- Student's Initial State ---
    syllabus = load_syllabus()
    progress = load_student_progress(student_id)
    print(f"Student Progress for {student_id}: {progress}\n")
    
    weakest_topic, confidence = get_next_quiz_topic(progress, syllabus)
    print(f"Weakest topic for {student_id}: {weakest_topic} (Confidence: {confidence:.2f})\n")

    # --- Quiz Generation and Assessment ---
    difficulty = "easy" if confidence < 0.5 else "medium"
    
    print(f"Generating a {difficulty} quiz for {weakest_topic}...\n")
    
    quiz = generate_quiz(pipe, student_id, weakest_topic, difficulty)
    
    # --- User takes the quiz ---
    quiz_results = []
    for i, q in enumerate(quiz, 1):
        print(f"\nQuestion {i}: {q['question']}")
        # Create an option mapping (e.g., A, B, C, D)
        options_map = {chr(65 + j): option for j, option in enumerate(q['options'])}
        for letter, option_text in options_map.items():
            print(f"  {letter}) {option_text}")
        
        user_answer = input("Your answer (A, B, C, D): ").upper()
        
        # Check if the user's answer is correct
        is_correct = (options_map.get(user_answer) == q['answer'])
        print(f"Result: {'Correct!' if is_correct else 'Incorrect.'}")
        if not is_correct:
            print(f"Explanation: {q['explanation']}")
        
        quiz_results.append({
            "question": q["question"],
            "is_correct": is_correct
        })
        
    # Update the student's confidence score
    updated_progress = update_confidence_score(progress, weakest_topic, quiz_results)
    print(f"\nQuiz completed. Your updated progress is: {updated_progress}\n")

if __name__ == "__main__":
    main()