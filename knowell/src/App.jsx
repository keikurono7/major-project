import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthContext } from './contexts/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import StudentHome from './pages/StudentHome';
import TeacherHome from './pages/TeacherHome';

const ProtectedRoute = ({ children, allowedRole }) => {
  const { currentUser, loading } = useContext(AuthContext);
  
  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      Loading...
    </div>;
  }
  
  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRole && currentUser.role !== allowedRole) {
    return <Navigate to={currentUser.role === 'teacher' ? '/teacher' : '/student'} replace />;
  }
  
  return children;
};

function App() {
  const { currentUser, loading } = useContext(AuthContext);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      Loading...
    </div>;
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={currentUser ? <Navigate to={currentUser.role === 'teacher' ? '/teacher' : '/student'} replace /> : <Login />} 
        />
        <Route 
          path="/register" 
          element={currentUser ? <Navigate to={currentUser.role === 'teacher' ? '/teacher' : '/student'} replace /> : <Register />} 
        />
        <Route 
          path="/student" 
          element={
            <ProtectedRoute allowedRole="student">
              <StudentHome />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/teacher" 
          element={
            <ProtectedRoute allowedRole="teacher">
              <TeacherHome />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/" 
          element={
            currentUser ? (
              <Navigate to={currentUser.role === 'teacher' ? '/teacher' : '/student'} replace />
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;