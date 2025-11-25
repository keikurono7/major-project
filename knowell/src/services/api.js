// src/services/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication headers
api.interceptors.request.use(
  (config) => {
    const user = localStorage.getItem('user');
    if (user) {
      const { id } = JSON.parse(user);
      config.headers['user-id'] = id; 
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const quizApi = {
  // main.py expects POST /quizzes with { scope: 'topic', topic_id, student_id, num_questions }
  generateQuiz: (data) => api.post('/quizzes', data),

  // legacy endpoint kept (if still used elsewhere)
  submitAnswer: (studentId, data) => api.post(`/quiz/${studentId}/submit`, data),

  // main.py submit endpoint is POST /quizzes/submit
  submitQuizResponse: (data) => api.post('/quizzes/submit', data),
};

export const assignmentApi = {
  generateAssignment: (data) => api.post('/generate-topic-assignment', {
    subject_id: data.subject_id,
    topic_ids: data.topic_ids,
    num_questions: data.num_questions,
    student_id: data.student_id
  }),
  evaluateAnswer: (data) => 
    api.post('/evaluate-assignment-answer', data),
};

export const paperApi = {
  generatePaper: (data) => api.post('/question-paper', data),
  getPaper: (filename) => api.get(`/question-papers/${filename}`),
  getLatestPaper: () => api.get('/question-papers/latest'),
  uploadPdf: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/pdf/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export const chatWithAssistant = async (studentId, subjectId, message, studentName, conversationHistory = []) => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        student_id: studentId,
        subject_id: subjectId,
        message: message,
        student_name: studentName,
        conversation_history: conversationHistory
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error Response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error chatting with assistant:', error);
    throw error;
  }
};

// New endpoint for teacher analytics insights
export const teacherAnalyticsApi = {
  getBKTInsights: async (teacherId, subjectId, bktData, totalStudents, subjectName) => {
    try {
      const response = await fetch(`${API_URL}/teacher-analytics/insights`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          teacher_id: teacherId,
          subject_id: subjectId,
          bkt_data: bktData,
          total_students: totalStudents,
          subject_name: subjectName
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching BKT insights:', error);
      throw error;
    }
  },

  chatWithTeacherAssistant: async (teacherId, subjectId, message, bktContext = null, conversationHistory = []) => {
    try {
      const response = await fetch(`${API_URL}/teacher-analytics/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          teacher_id: teacherId,
          subject_id: subjectId,
          message: message,
          bkt_context: bktContext,
          conversation_history: conversationHistory
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error chatting with teacher assistant:', error);
      throw error;
    }
  }
};

// Add project evaluation API function
export const evaluateSubmissionApi = {
  evaluateSubmission: async (projectId, submissionId, studentId, files, projectDescription, projectInstructions) => {
    try {
      const response = await fetch(`${API_URL}/evaluate-submission`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectId: projectId,
          submissionId: submissionId,
          studentId: studentId,
          files: files,
          projectDescription: projectDescription,
          projectInstructions: projectInstructions
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error evaluating submission:', error);
      throw error;
    }
  }
};

export async function generateQuestions({ text, maxQuestions = 50 }) {
  const resp = await fetch("/api/generate_questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, maxQuestions }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function finalizeQuestions({ selectedQuestions, maxMarks }) {
  const resp = await fetch("/api/finalize_questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selectedQuestions, maxMarks }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export default api;
