import axios from 'axios';

// console.log("REACT_APP_API_URL env:", process.env.REACT_APP_API_URL);
// Dynamic API URL - use REACT_APP_API_URL from .env (CRA format)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
// console.log("Using API Base URL:", API_BASE_URL);

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || '';
      const isAuthRequest = requestUrl.includes('/patients/login')
        || requestUrl.includes('/patients/register')
        || requestUrl.includes('/doctors/login')
        || requestUrl.includes('/doctors/register');

      if (!isAuthRequest) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        const role = localStorage.getItem('userRole');
        window.location.href = role === 'doctor' ? '/doctor-login' : '/login';
      }
    }
    return Promise.reject(error);
  }
);

// =====================
// Authentication APIs
// =====================

export const authAPI = {
  register: (data) => api.post('/patients/register', data),
  login: (credentials) => api.post('/patients/login', credentials),
  getCurrentPatient: () => api.get('/patients/me'),
};

export const doctorAuthAPI = {
  register: (data) => api.post('/doctors/register', data),
  login: (data) => api.post('/doctors/login', data),
  getProfile: () => api.get('/doctors/profile'),
};

// =====================
// Patient APIs
// =====================

export const patientAPI = {
  getProfile: () => api.get('/patients/me'),
  updateProfile: (data) => api.put('/patients/me', data),
  getDashboard: () => api.get('/patients/dashboard'),
  getTrends: (days = 30) => api.get('/patients/trends', { params: { days } }),
  getAppointmentRequests: () => api.get('/patients/appointment-requests'),
};

// =====================
// Analysis APIs
// =====================

export const analysisAPI = {
  uploadSession: (data) => api.post('/analysis/upload-session', data),
  uploadVideo: (formData) => api.post('/analysis/upload-video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getVideoHistory: (limit = 20) => api.get('/analysis/video-history', { params: { limit } }),
  getVideoHistoryForDoctor: (patientId, limit = 50) => api.get(`/analysis/video-history/${patientId}`, { params: { limit } }),
  getSession: (sessionId) => api.get(`/analysis/sessions/${sessionId}`),
  getSessions: (limit = 50) => api.get('/analysis/sessions', { params: { limit } }),
  getRiskAssessment: (sessionId) => api.get(`/analysis/risk/${sessionId}`),
};

export const doctorAPI = {
  getPatients: () => api.get('/doctors/patients'),
  assignPatient: (patientId) => api.post(`/doctors/assign-patient/${patientId}`),
  assignPatientByEmail: (email) => api.post('/doctors/assign-patient-by-email', null, { params: { email } }),
  getPatientTimeline: (patientId, days = 90) => api.get(`/doctors/patient/${patientId}/health-timeline`, { params: { days } }),
  addMedication: (patientId, data) => api.post(`/doctors/patient/${patientId}/medication`, data),
  getPatientMedications: (patientId) => api.get(`/doctors/patient/${patientId}/medications`),
  getHighRiskAlerts: (patientId) => api.get(`/doctors/patient/${patientId}/high-risk-alerts`),
  getDirectory: () => api.get('/doctors/directory'),
  createAppointmentRequest: (data) => api.post('/doctors/requests', data),
  getAppointmentRequests: () => api.get('/doctors/appointment-requests'),
  acceptAppointmentRequest: (requestId) => api.post(`/doctors/appointment-requests/${requestId}/accept`),
  rejectAppointmentRequest: (requestId) => api.post(`/doctors/appointment-requests/${requestId}/reject`),
  updateProfile: (data) => api.put('/doctors/profile', data),
  getNotifications: () => api.get('/doctors/notifications'),
  markNotificationsRead: () => api.post('/doctors/notifications/mark-read'),
};

export const healthAPI = {
  getRiskTimeline: (patientId, days = 90) => api.get(`/health/risk-timeline/${patientId}`, { params: { days } }),
  setMedicationReminder: (data) => api.post('/health/medication/reminder', data),
  getMedicationSchedule: (patientId) => api.get(`/health/medication/schedule/${patientId}`),
  recordMedicationTaken: (patientId, medicationName) => api.post(`/health/medication/record-taken/${patientId}`, null, { params: { medication_name: medicationName } }),
  generateReport: (patientId, reportType = 'Monthly Summary') => api.post('/health/report/generate', null, { params: { patient_id: patientId, report_type: reportType } }),
  getReports: (patientId, limit = 10) => api.get(`/health/reports/${patientId}`, { params: { limit } }),
  sendChatMessage: (patientId, message, conversationHistory = null) =>
    api.post('/health/chatbot/message', { message, conversation_history: conversationHistory }, { params: { patient_id: patientId } }),
  getMedicationRecommendations: (data) => api.post('/health/medication/recommendations', data),
  getNotifications: (patientId) => api.get(`/health/notifications/${patientId}`),
  markNotificationsRead: (patientId) => api.post(`/health/notifications/${patientId}/mark-read`),
  getHealthHistory: (patientId, limit = 50) => api.get(`/health/history/${patientId}`, { params: { limit } }),
  sendMedicationAlert: (patientId, medicationName, timeSlot) => api.post(`/health/medication/alert/${patientId}`, null, { params: { medication_name: medicationName, time_slot: timeSlot } }),
  // NEW: PDF Medical Report Analysis via Gemini AI
  uploadPDFReport: (formData) => api.post('/health/pdf-report/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  // NEW: Generate AI-powered chat suggestions based on conversation history
  generateChatSuggestions: (data) => api.post('/health/chat/generate-suggestions', data),
  // NEW: Get fitness records
  getFitnessRecords: (patientId) => api.get(`/health/fitness-records/${patientId}`),
  addFitnessRecord: (patientId, data) => api.post(`/health/fitness/records/${patientId}`, data),
  analyzeFitness: (data) => api.post('/health/fitness/analyze', data),
  // NEW: Video analysis access control
  unlockVideoAnalysis: (patientId) => api.post(`/health/video-analysis/unlock/${patientId}`),
  lockVideoAnalysis: (patientId) => api.post(`/health/video-analysis/lock/${patientId}`),
  getVideoAccessStatus: (patientId) => api.get(`/health/video-analysis/access-status/${patientId}`),
  // Video analysis with Gemini (sends video file)
  analyzeVideo: (formData) => api.post('/health/video-analysis/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getVideoAnalysis: (patientId) => api.get(`/health/video-analysis/${patientId}`),
  // SOS Emergency Alert
  sendSOSAlert: (data) => api.post('/health/sos-alert', data),
};

// =====================
// Health Check
// =====================

export const systemHealthAPI = {
  check: () => api.get('/health'),
};

export default api;
