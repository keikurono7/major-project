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
      const user = {
        id: isStudent ? 'student123' : 'teacher456',
        username: credentials.username,
        role: isStudent ? 'student' : 'teacher',
        fullName: isStudent ? 'John Doe' : 'Dr. Smith',
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
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        position: 'relative'
      }}>
        {/* Login Card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            background: '#ca404f',
            padding: '32px',
            textAlign: 'center',
            color: 'white'
          }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '64px',
              height: '64px',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '50%',
              marginBottom: '16px'
            }}>
              <BookOpen size={32} />
            </div>
            <h1 style={{
              fontSize: '1.875rem',
              fontWeight: 'bold',
              margin: '0 0 8px 0'
            }}>
              Knowell
            </h1>
            <p style={{
              opacity: 0.9,
              margin: 0
            }}>
              AI-Powered Learning Platform
            </p>
          </div>
          
          {/* Form Content */}
          <div style={{ padding: '32px' }}>
            {/* Error Message */}
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
            
            {/* Login Form */}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Username Field */}
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
              
              {/* Password Field */}
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
              
              {/* Submit Button */}
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
            
            {/* Demo Credentials */}
            <div style={{
              marginTop: '24px',
              padding: '16px',
              backgroundColor: '#f8fafc',
              borderRadius: '8px'
            }}>
              <p style={{
                fontSize: '0.75rem',
                fontWeight: '500',
                color: '#374151',
                margin: '0 0 8px 0'
              }}>
                Demo Credentials:
              </p>
              <div style={{
                fontSize: '0.75rem',
                color: '#6b7280',
                lineHeight: 1.5
              }}>
                <p style={{ margin: '2px 0' }}><strong>Student:</strong> demo_student / password123</p>
                <p style={{ margin: '2px 0' }}><strong>Teacher:</strong> demo_teacher / password123</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div style={{
          textAlign: 'center',
          marginTop: '32px'
        }}>
          <p style={{
            fontSize: '0.875rem',
            color: 'rgba(255, 255, 255, 0.8)'
          }}>
            Don't have an account?{' '}
            <button style={{
              color: 'white',
              fontWeight: '500',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}>
              Contact your administrator
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;