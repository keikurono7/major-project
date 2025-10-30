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
    topic_ids: data.topic_ids,    num_questions: data.num_questions,
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
    const response = await fetch(`${API_URL}/chat`, {  // Changed from API_BASE_URL to API_URL
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

export default api;
