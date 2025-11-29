

export const questionPaperApi = {
  // Generate initial 25 questions per module
  generateInitialQuestions: async (subjectId) => {
    return apiRequest('/api/question-paper/generate-initial', {
      method: 'POST',
      body: JSON.stringify({ subject_id: subjectId })
    });
  },

  // Submit teacher-filtered questions (10 per module)
  submitFilteredQuestions: async (subjectId, filteredQuestions) => {
    return apiRequest('/api/question-paper/submit-filtered', {
      method: 'POST',
      body: JSON.stringify({
        subject_id: subjectId,
        filtered_questions: filteredQuestions
      })
    });
  },

  // Get final question paper with optional questions
  getFinalQuestionPaper: async (subjectId, sessionId) => {
    return apiRequest(`/api/question-paper/final/${subjectId}/${sessionId}`);
  },

  // Save finalized question paper
  saveQuestionPaper: async (subjectId, questionPaper) => {
    return apiRequest('/api/question-paper/save', {
      method: 'POST',
      body: JSON.stringify({
        subject_id: subjectId,
        question_paper: questionPaper
      })
    });
  }
};