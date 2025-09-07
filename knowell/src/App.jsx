import React from 'react';
import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import Login from './pages/Login';
import StudentHome from './pages/StudentHome';
import TeacherHome from './pages/TeacherHome';
import './assets/styles/global.css'

// Protected route component
const ProtectedRoute = ({ children, role }) => {
  const isAuthenticated = localStorage.getItem('user');
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  const user = JSON.parse(isAuthenticated);
  
  if (role && user.role !== role) {
    // Redirect to appropriate dashboard based on role
    return <Navigate to={user.role === 'student' ? '/student' : '/teacher'} replace />;
  }
  
  return children;
};

function App() {
  const [count, setCount] = useState(0)

  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/student" element={
            <ProtectedRoute role="student">
              <StudentHome />
            </ProtectedRoute>
          } />
          <Route path="/teacher" element={
            <ProtectedRoute role="teacher">
              <TeacherHome />
            </ProtectedRoute>
          } />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
