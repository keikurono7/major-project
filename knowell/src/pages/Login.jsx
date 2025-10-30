// src/pages/Login.jsx
import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { User, Lock, GraduationCap, BookOpen } from 'lucide-react';

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
      const user = await login(credentials.username, credentials.password);
      navigate(isStudent ? '/student' : '/teacher');
    } catch (err) {
      // surface actual error message from backend/auth service
      setError(err?.message || 'Login failed. Please check your credentials.');
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="login-layout" style={{ minHeight: '100vh' }}>
      {/* Responsive styles */}
      <style>{`
        .login-layout {
          display: flex;
          flex-direction: column;
        }
        .login-left {
          background: linear-gradient(180deg, #ca404f 0%, #a7373f 100%);
          color: white;
          padding: 48px 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .login-left .brand {
          text-align: center;
        }
        .login-left .brand h1 {
          margin: 16px 0 8px;
          font-size: 2rem;
          font-weight: 700;
        }
        .login-left .brand p {
          margin: 0;
          opacity: 0.95;
        }
        .login-right {
          padding: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .login-card {
          width: 100%;
          max-width: 520px;
        }
        /* Desktop: two columns */
        @media (min-width: 768px) {
          .login-layout {
            flex-direction: row;
          }
          .login-left, .login-right {
            flex: 1 1 50%;
            min-height: 100vh;
          }
          .login-left {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 64px;
          }
          .login-right {
            align-items: center;
            justify-content: center;
            padding: 64px;
            background: #f3f4f6;
          }
          .login-card {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            overflow: hidden;
            padding: 0;
          }
        }
      `}</style>

      {/* Left / Branding */}
      <div className="login-left">
        <div className="brand" style={{ maxWidth: 360 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 96,
            height: 96,
            backgroundColor: 'rgba(255,255,255,0.12)',
            borderRadius: '50%',
            margin: '0 auto'
          }}>
            <BookOpen size={44} />
          </div>
          <h1>Knowell</h1>
          <p style={{ marginTop: 8 }}>AI-Powered Learning Platform</p>
          <p style={{ marginTop: 16, opacity: 0.95, fontSize: '0.95rem' }}>
            Personalized learning paths, assignments and insights for students and teachers.
          </p>
        </div>
      </div>

      {/* Right / Form */}
      <div className="login-right">
        <div className="login-card">
          {/* Header (mobile shows colored header inside card; desktop header is left panel) */}
          <div style={{
            background: '#ffffff',
            padding: '28px 32px',
            display: 'block'
          }}>
            {/* On mobile show small colored bar with icon to keep branding */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: '#ca404f',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white'
              }}>
                <BookOpen size={20} />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Welcome back</h2>
                <p style={{ margin: 0, color: '#6b7280', fontSize: '0.875rem' }}>Sign in to continue</p>
              </div>
            </div>
          </div>

          {/* Form Content */}
          <div style={{ padding: '28px 32px' }}>
            {error && (
              <div style={{
                marginBottom: '24px',
                padding: '12px',
                backgroundColor: '#fee2e2',
                border: '1px solid #fecaca',
                color: '#b91c1c',
                borderRadius: '8px',
                fontSize: '0.875rem'
              }}>
                {error}
              </div>
            )}

            {/* Role Selector */}
            <div style={{ marginBottom: '24px' }}>
              <div style={{
                display: 'flex',
                backgroundColor: '#f8fafc',
                borderRadius: '8px',
                padding: '4px',
                border: '1px solid #e2e8f0'
              }}>
                <button
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '12px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    backgroundColor: isStudent ? 'white' : 'transparent',
                    color: isStudent ? '#ca404f' : '#6b7280',
                    boxShadow: isStudent ? '0 1px 2px 0 rgba(0, 0, 0, 0.05)' : 'none'
                  }}
                  onClick={() => setIsStudent(true)}
                  type="button"
                >
                  <GraduationCap size={16} style={{ marginRight: '8px' }} />
                  Student
                </button>
                <button
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '12px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    backgroundColor: !isStudent ? 'white' : 'transparent',
                    color: !isStudent ? '#7c1d21' : '#6b7280',
                    boxShadow: !isStudent ? '0 1px 2px 0 rgba(0, 0, 0, 0.05)' : 'none'
                  }}
                  onClick={() => setIsStudent(false)}
                  type="button"
                >
                  <User size={16} style={{ marginRight: '8px' }} />
                  Teacher
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Username */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '8px'
                }}>
                  Username
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{
                    position: 'absolute',
                    inset: '0 auto 0 0',
                    padding: '0 12px',
                    display: 'flex',
                    alignItems: 'center',
                    pointerEvents: 'none'
                  }}>
                    <User size={18} color="#9ca3af" />
                  </div>
                  <input
                    type="text"
                    name="username"
                    style={{
                      width: '100%',
                      paddingLeft: '40px',
                      paddingRight: '12px',
                      paddingTop: '12px',
                      paddingBottom: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '0.875rem',
                      transition: 'all 0.2s',
                      outline: 'none'
                    }}
                    placeholder={`Enter your ${isStudent ? 'student' : 'teacher'} username`}
                    value={credentials.username}
                    onChange={handleChange}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#e89fba';
                      e.target.style.boxShadow = '0 0 0 3px rgba(255, 0, 0, 0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#d1d5db';
                      e.target.style.boxShadow = 'none';
                    }}
                    required
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '8px'
                }}>
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{
                    position: 'absolute',
                    inset: '0 auto 0 0',
                    padding: '0 12px',
                    display: 'flex',
                    alignItems: 'center',
                    pointerEvents: 'none'
                  }}>
                    <Lock size={18} color="#9ca3af" />
                  </div>
                  <input
                    type="password"
                    name="password"
                    style={{
                      width: '100%',
                      paddingLeft: '40px',
                      paddingRight: '12px',
                      paddingTop: '12px',
                      paddingBottom: '12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '0.875rem',
                      transition: 'all 0.2s',
                      outline: 'none'
                    }}
                    placeholder="Enter your password"
                    value={credentials.password}
                    onChange={handleChange}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#e89fba';
                      e.target.style.boxShadow = '0 0 0 3px rgba(246, 59, 59, 0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#d1d5db';
                      e.target.style.boxShadow = 'none';
                    }}
                    required
                  />
                </div>
              </div>

              <button 
                type="submit"
                style={{
                  width: '100%',
                  background: '#ca404f',
                  color: 'white',
                  fontWeight: '500',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
                }}
              >
                Login as {isStudent ? 'Student' : 'Teacher'}
              </button>
            </form>
          </div>

          {/* Footer */}
          <div style={{
            textAlign: 'center',
            marginTop: '12px',
            padding: '12px 32px 28px'
          }}>
            <p style={{
              fontSize: '0.875rem',
              color: '#6b7280'
            }}>
              Don't have an account?{' '}
              <button
                style={{
                  color: '#ca404f',
                  fontWeight: '500',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
                onClick={() => navigate('/register')}
                type="button"
              >
                Sign up
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;