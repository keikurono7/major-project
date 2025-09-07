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
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const topicsApi = {
  getAll: () => api.get('/topics'),
};

export const progressApi = {
  getProgress: (studentId) => api.get(`/progress/${studentId}`),
  resetProgress: (studentId) => api.post(`/progress/${studentId}/reset`),
};

export const quizApi = {
  generateQuiz: (data) => api.post('/quiz', data),
  submitAnswer: (studentId, data) => api.post(`/quiz/${studentId}/submit`, data),
};

export const assignmentApi = {
  generateAssignment: (data) => api.post('/assignment', data),
  evaluateAnswer: (studentId, questionId, answer) => 
    api.post(`/assignment/${studentId}/evaluate?question_id=${questionId}`, { answer }),
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

export default api;