// src/pages/Login.jsx
import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [isStudent, setIsStudent] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      // For demo purposes, we'll just mock login
      const user = {
        id: isStudent ? 'student123' : 'teacher456',
        username: credentials.username,
        role: isStudent ? 'student' : 'teacher',
        fullName: isStudent ? 'Student User' : 'Teacher User',
      };
      
      login(user);
      navigate(isStudent ? '/student' : '/teacher');
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="page login-page">
      <div className="container">
        <div className="flex" style={{ height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: '100%', maxWidth: '400px' }}>
            <div className="card">
              <div className="text-center mb-6">
                <h1 className="mb-2">Knowell</h1>
                <p className="text-secondary">AI-Powered Learning Platform</p>
              </div>
              
              {error && (
                <div className="mb-4" style={{ padding: '0.75rem', backgroundColor: '#FEE2E2', color: '#B91C1C', borderRadius: '0.375rem' }}>
                  {error}
                </div>
              )}
              
              <div className="mb-4">
                <div className="flex" style={{ border: '1px solid #E2E8F0', borderRadius: '0.375rem', overflow: 'hidden' }}>
                  <button
                    className={`flex-1 py-2 text-center ${isStudent ? 'bg-primary text-white' : 'bg-white'}`}
                    onClick={() => setIsStudent(true)}
                    type="button"
                  >
                    Student
                  </button>
                  <button
                    className={`flex-1 py-2 text-center ${!isStudent ? 'bg-primary text-white' : 'bg-white'}`}
                    onClick={() => setIsStudent(false)}
                    type="button"
                  >
                    Teacher
                  </button>
                </div>
              </div>
              
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label className="form-label" htmlFor="username">Username</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    className="form-control"
                    value={credentials.username}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label" htmlFor="password">Password</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    className="form-control"
                    value={credentials.password}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <button type="submit" className="btn btn-primary w-full">
                  Login as {isStudent ? 'Student' : 'Teacher'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;