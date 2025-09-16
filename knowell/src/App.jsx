import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './pages/Login';
import TeacherHome from './pages/TeacherHome';
import StudentHome from './pages/StudentHome';
// Remove the App.css import if it's causing issues
// import './App.css'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/teacher" element={<TeacherHome />} />
            <Route path="/student" element={<StudentHome />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;