from flask import request, jsonify
import anthropic
import json

# Initialize Anthropic client
client = anthropic.Anthropic()

def evaluate_project_submission(project_data, submission_data, files_data):
    """
    Evaluate project submission using Claude AI
    """
    try:
        # Prepare the prompt for Claude
        prompt = f"""
You are an expert project evaluator. Please evaluate this student project submission based on the following criteria:

Project Title: {project_data['title']}
Project Description: {project_data['description']}
Project Instructions: {project_data['instructions']}
Max Score: {project_data['maxScore']}

Student Submission Files:
{json.dumps(files_data, indent=2)}

Please provide:
1. Overall assessment (2-3 sentences)
2. Strengths (3-5 points)
3. Areas for improvement (3-5 points)
4. Suggested score (0-{project_data['maxScore']})
5. Detailed feedback

Format the response as JSON.
"""

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Parse the response
        response_text = message.content[0].text
        
        # Try to extract JSON from the response
        try:
            evaluation = json.loads(response_text)
        except json.JSONDecodeError:
            evaluation = {
                "assessment": response_text,
                "status": "completed"
            }

        return evaluation

    except Exception as e:
        print(f"Error evaluating submission: {str(e)}")
        raise

# Add this to your Flask app
@app.route('/api/evaluate-submission', methods=['POST'])
def evaluate_submission():
    """
    Endpoint to evaluate project submission
    """
    try:
        data = request.json
        
        project_data = {
            'title': data.get('projectTitle'),
            'description': data.get('projectDescription'),
            'instructions': data.get('projectInstructions'),
            'maxScore': data.get('maxScore', 100)
        }
        
        submission_data = {
            'studentId': data.get('studentId'),
            'submissionId': data.get('submissionId')
        }
        
        files_data = data.get('files', [])
        
        # Evaluate submission
        evaluation = evaluate_project_submission(
            project_data,
            submission_data,
            files_data
        )
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500