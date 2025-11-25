// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080/api';

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============= EXISTING APIs =============

export const paperApi = {
  uploadPdf: async (formData) => {
    return await api.post('/syllabus/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  generatePaper: async (data) => {
    return await api.post('/question-papers/generate', data);
  },

  listPapers: async () => {
    return await api.get('/question-papers/list');
  },

  getPaper: async (paperId) => {
    return await api.get(`/question-papers/${paperId}`);
  },
};

export const assignmentApi = {
  generate: async (data) => {
    return await api.post('/assignments/generate', data);
  },

  list: async () => {
    return await api.get('/assignments/list');
  },

  get: async (assignmentId) => {
    return await api.get(`/assignments/${assignmentId}`);
  },

  evaluate: async (assignmentId, data) => {
    return await api.post(`/assignments/${assignmentId}/evaluate`, data);
  },
};

export const quizApi = {
  generate: async (data) => {
    return await api.post('/quizzes/generate', data);
  },

  list: async () => {
    return await api.get('/quizzes/list');
  },

  get: async (quizId) => {
    return await api.get(`/quizzes/${quizId}`);
  },

  evaluate: async (quizId, answers) => {
    return await api.post(`/quizzes/${quizId}/evaluate`, { answers });
  },
};

export const projectApi = {
  generate: async (data) => {
    return await api.post('/projects/generate', data);
  },

  list: async () => {
    return await api.get('/projects/list');
  },

  get: async (projectId) => {
    return await api.get(`/projects/${projectId}`);
  },

  evaluate: async (projectId, data) => {
    return await api.post(`/projects/${projectId}/evaluate`, data);
  },
};

export const syllabusApi = {
  upload: async (formData) => {
    return await api.post('/syllabus/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  get: async (subjectId) => {
    return await api.get(`/syllabus/${subjectId}`);
  },

  list: async () => {
    return await api.get('/syllabus/list');
  },
};

export const chatApi = {
  send: async (message, context = null, sessionId = null) => {
    return await api.post('/chatbot/chat', {
      message,
      context,
      session_id: sessionId,
    });
  },

  clearHistory: async (sessionId) => {
    return await api.post(`/chatbot/clear/${sessionId}`);
  },
};

// ============= NEW: Schedule & Marks APIs =============

export const scheduleApi = {
  // Get student's schedule
  getStudentSchedule: async (studentId, subjectId) => {
    const response = await api.get(`/schedules/student/${studentId}/${subjectId}`);
    return response.data;
  },

  // Get today's tasks
  getTodayTasks: async (studentId, subjectId) => {
    const response = await api.get(`/schedules/student/${studentId}/${subjectId}/today`);
    return response.data;
  },

  // Get week tasks
  getWeekTasks: async (studentId, subjectId, weekNumber) => {
    const response = await api.get(`/schedules/student/${studentId}/${subjectId}/week/${weekNumber}`);
    return response.data;
  },

  // Complete a task
  completeTask: async (studentId, subjectId, taskId, timeSpent = null, notes = null) => {
    const response = await api.post(`/schedules/task/${taskId}/complete`, null, {
      params: { student_id: studentId, subject_id: subjectId, time_spent: timeSpent, notes }
    });
    return response.data;
  },

  // Skip a task
  skipTask: async (studentId, subjectId, taskId, reason) => {
    const response = await api.post(`/schedules/task/${taskId}/skip`, null, {
      params: { student_id: studentId, subject_id: subjectId, reason }
    });
    return response.data;
  },

  // Get AI insights
  getScheduleInsights: async (studentId, subjectId) => {
    const response = await api.get(`/schedules/insights/${studentId}/${subjectId}`);
    return response.data;
  },

  // Generate schedule
  generateSchedule: async (studentId, subjectId) => {
    const response = await api.post(`/schedules/generate/${studentId}/${subjectId}`);
    return response.data;
  },

  // Create/update schedule config (Teacher)
  createConfig: async (config) => {
    const response = await api.post('/schedules/config', config);
    return response.data;
  },

  // Get schedule config
  getConfig: async (subjectId) => {
    const response = await api.get(`/schedules/config/${subjectId}`);
    return response.data;
  },

  // Generate batch schedules
  generateBatch: async (subjectId, studentIds) => {
    const response = await api.post(`/schedules/generate-batch/${subjectId}`, {
      student_ids: studentIds
    });
    return response.data;
  },

  // Adjust schedule
  adjustSchedule: async (studentId, subjectId, reason, changes) => {
    const response = await api.post(`/schedules/adjust/${studentId}/${subjectId}`, {
      reason,
      changes
    });
    return response.data;
  },

  // Teacher override
  teacherOverride: async (studentId, subjectId, teacherId, topicId, action, reason) => {
    const response = await api.post(`/schedules/override/${studentId}/${subjectId}`, {
      teacher_id: teacherId,
      topic_id: topicId,
      action,
      reason
    });
    return response.data;
  },
};

export const marksApi = {
  // Upload IA marks
  uploadIAMarks: async (entries) => {
    const response = await api.post('/marks/ia/upload', entries);
    return response.data;
  },

  // Upload semester marks
  uploadSemesterMarks: async (entries) => {
    const response = await api.post('/marks/semester/upload', entries);
    return response.data;
  },

  // Analyze question paper
  analyzeQuestionPaper: async (file, subjectId) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/marks/question-paper/analyze?subject_id=${subjectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Get student marks
  getStudentMarks: async (studentId, subjectId = null) => {
    const response = await api.get(`/marks/student/${studentId}/marks`, {
      params: { subject_id: subjectId }
    });
    return response.data;
  },

  // Fetch from VTU (placeholder)
  fetchVTUMarks: async (usn, semester, year, subjectCodes) => {
    const response = await api.post('/marks/vtu/fetch', {
      student_usn: usn,
      semester,
      year,
      subject_codes: subjectCodes
    });
    return response.data;
  },

  // Fetch from ERP (placeholder)
  fetchERPMarks: async (studentIds, subjectId, testType) => {
    const response = await api.post('/marks/erp/fetch', {
      student_ids: studentIds,
      subject_id: subjectId,
      test_type: testType
    });
    return response.data;
  },
};

export const analyticsApi = {
  // ============= Student Analytics =============
  
  // Get student overview
  getStudentOverview: async (studentId) => {
    const response = await api.get(`/analytics/student/${studentId}/overview`);
    return response.data;
  },

  // Get knowledge graph
  getKnowledgeGraph: async (studentId, subjectId = null) => {
    const response = await api.get(`/analytics/student/${studentId}/knowledge-graph`, {
      params: { subject_id: subjectId }
    });
    return response.data;
  },

  // Get progress timeline
  getProgressTimeline: async (studentId, subjectId, days = 30) => {
    const response = await api.get(`/analytics/student/${studentId}/progress-timeline`, {
      params: { subject_id: subjectId, days }
    });
    return response.data;
  },

  // ============= Class Analytics =============
  
  // Get class overview
  getClassOverview: async (subjectId) => {
    const response = await api.get(`/analytics/class/${subjectId}/overview`);
    return response.data;
  },

  // Get class heatmap
  getClassHeatmap: async (subjectId) => {
    const response = await api.get(`/analytics/class/${subjectId}/heatmap`);
    return response.data;
  },

  // Get weak topics
  getWeakTopics: async (subjectId, threshold = 0.5) => {
    const response = await api.get(`/analytics/class/${subjectId}/weak-topics`, {
      params: { threshold }
    });
    return response.data;
  },

  // Get performance distribution
  getPerformanceDistribution: async (subjectId) => {
    const response = await api.get(`/analytics/class/${subjectId}/performance-distribution`);
    return response.data;
  },
};

// Export all as default as well
export default {
  paper: paperApi,
  assignment: assignmentApi,
  quiz: quizApi,
  project: projectApi,
  syllabus: syllabusApi,
  chat: chatApi,
  schedule: scheduleApi,
  marks: marksApi,
  analytics: analyticsApi,
};
