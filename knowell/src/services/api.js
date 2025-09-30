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

export const topicsApi = {
  getByModule: (moduleId, userId) =>
    api.get(`/modules/${moduleId}/topics`, {
      headers: { 'user-id': userId },
    }),
};

export const progressApi = {
  getProgress: (studentId) => api.get(`/student/${studentId}/progress`),
  getBKTParams: (studentId, topicId) =>
    api.get(`/student/${studentId}/bkt/${topicId}`), 
};

export const modulesApi = {
  getAll: () => api.get('/subjects'),
  getBySubject: (subjectId) => api.get(`/subjects/${subjectId}/modules`),
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
