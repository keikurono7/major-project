// src/pages/StudentHome.jsx
import React, { useContext, useState, useEffect } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import ProgressTracker from '../components/student/ProgressTracker';
import QuizInterface from '../components/student/QuizInterface';
import AssignmentInterface from '../components/student/AssignmentInterface';
import { topicsApi, progressApi } from '../services/api';
import '../dashboard.css';

const StudentHome = () => {
  const { currentUser } = useContext(AuthContext);
  const [topics, setTopics] = useState([
    { id: 1, name: "Machine Learning", confidence: 0.85 },
    { id: 2, name: "Data Structures", confidence: 0.72 },
    { id: 3, name: "Algorithms", confidence: 0.68 },
    { id: 4, name: "Database Systems", confidence: 0.91 },
    { id: 5, name: "Web Development", confidence: 0.79 },
    { id: 6, name: "AI Fundamentals", confidence: 0.63 }
  ]);
  const [progress, setProgress] = useState({
    confidence_scores: {
      "Machine Learning": 0.85,
      "Data Structures": 0.72,
      "Algorithms": 0.68,
      "Database Systems": 0.91,
      "Web Development": 0.79,
      "AI Fundamentals": 0.63
    }
  });
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate API calls
        setTimeout(() => {
          setLoading(false);
        }, 500);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };
    
    fetchData();
  }, [currentUser.id]);

  const sidebarItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'quizzes', label: 'Take Quiz', icon: '❓' },
    { id: 'assignments', label: 'Assignments', icon: '📝' },
    { id: 'papers', label: 'Question Papers', icon: '📚' },
    { id: 'profile', label: 'Profile', icon: '👤' }
  ];

  const recentActivity = [
    { type: "quiz", title: "ML Quiz - Linear Regression", score: 85, time: "2 hours ago" },
    { type: "assignment", title: "Data Structures Assignment", score: 78, time: "1 day ago" },
    { type: "quiz", title: "Algorithm Analysis Quiz", score: 92, time: "2 days ago" },
    { type: "assignment", title: "Database Design Project", score: 88, time: "3 days ago" }
  ];

  const renderContent = () => {
    if (loading) return <div className="loading">Loading...</div>;
    
    switch (activeTab) {
      case 'dashboard':
        const avgConfidence = progress ? 
          (Object.values(progress.confidence_scores).reduce((a, b) => a + b, 0) / 
          Object.values(progress.confidence_scores).length * 100).toFixed(0) : 0;
        
        const focusArea = progress ? 
          Object.entries(progress.confidence_scores).sort((a, b) => a[1] - b[1])[0][0] : 'N/A';

        return (
          <>
            {/* Welcome Card */}
            <div className="card">
              <h2>Welcome back, {currentUser.fullName}</h2>
              <p>Continue your learning journey where you left off.</p>
            </div>
            
            {/* Stats Grid */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">📚</div>
                <div className="stat-info">
                  <div className="stat-value">{topics.length}</div>
                  <div className="stat-label">Topics</div>
                  <div className="stat-desc">Available for learning</div>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-info">
                  <div className="stat-value">{avgConfidence}%</div>
                  <div className="stat-label">Average Confidence</div>
                  <div className="stat-desc">Across all topics</div>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-info">
                  <div className="stat-value" style={{ fontSize: '1rem' }}>{focusArea}</div>
                  <div className="stat-label">Focus Area</div>
                  <div className="stat-desc">Needs improvement</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">📈</div>
                <div className="stat-info">
                  <div className="stat-value">{recentActivity.length}</div>
                  <div className="stat-label">Recent Activity</div>
                  <div className="stat-desc">This week</div>
                </div>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="content-grid">
              {/* Progress Section */}
              <div className="card">
                <h3 className="mb-4">Your Progress</h3>
                <div className="progress-overview">
                  {Object.entries(progress.confidence_scores).map(([topic, confidence]) => (
                    <div key={topic} className="progress-item">
                      <div className="progress-header">
                        <span className="progress-topic">{topic}</span>
                        <span className="progress-score">{Math.round(confidence * 100)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ 
                            width: `${confidence * 100}%`,
                            backgroundColor: confidence > 0.8 ? '#10b981' : confidence > 0.6 ? '#f59e0b' : '#ef4444'
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Actions & Recent Activity */}
              <div className="card">
                <h3 className="mb-4">Quick Actions</h3>
                <div className="quick-actions">
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("quizzes")}
                  >
                    <span>❓</span>
                    Take a Quiz
                  </button>
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("assignments")}
                  >
                    <span>📝</span>
                    View Assignments
                  </button>
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("papers")}
                  >
                    <span>📚</span>
                    Question Papers
                  </button>
                </div>

                <h4 className="mb-3 mt-4">Recent Activity</h4>
                <div className="activity-list">
                  {recentActivity.slice(0, 3).map((activity, idx) => (
                    <div key={idx} className="activity-item">
                      <div className="activity-icon">
                        {activity.type === "quiz" ? "❓" : "📝"}
                      </div>
                      <div className="activity-content">
                        <div className="activity-title">{activity.title}</div>
                        <div className="activity-meta">
                          <span className="activity-time">{activity.time}</span>
                          <span className={`activity-score ${
                            activity.score >= 85 ? 'score-excellent' : 
                            activity.score >= 70 ? 'score-good' : 'score-needs-work'
                          }`}>
                            {activity.score}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        );

      case 'quizzes':
        return (
          <div className="card">
            <h2>Available Quizzes</h2>
            <div className="quiz-grid">
              {topics.map((topic, idx) => (
                <div key={idx} className="quiz-card">
                  <div className="quiz-header">
                    <h3>{topic.name}</h3>
                    <div className={`confidence-badge ${
                      topic.confidence > 0.8 ? 'confidence-high' : 
                      topic.confidence > 0.6 ? 'confidence-medium' : 'confidence-low'
                    }`}>
                      {Math.round(topic.confidence * 100)}%
                    </div>
                  </div>
                  <p>Test your knowledge in {topic.name.toLowerCase()}</p>
                  <button className="btn btn-primary">Start Quiz</button>
                </div>
              ))}
            </div>
          </div>
        );

      case 'assignments':
        return (
          <div className="card">
            <h2>Your Assignments</h2>
            <div className="assignment-list">
              {recentActivity.filter(item => item.type === 'assignment').map((assignment, idx) => (
                <div key={idx} className="assignment-card">
                  <div className="assignment-header">
                    <h3>{assignment.title}</h3>
                    <span className={`assignment-score ${
                      assignment.score >= 85 ? 'score-excellent' : 
                      assignment.score >= 70 ? 'score-good' : 'score-needs-work'
                    }`}>
                      {assignment.score}%
                    </span>
                  </div>
                  <div className="assignment-meta">
                    <span>Submitted {assignment.time}</span>
                    <span className={`status-badge ${
                      assignment.score >= 85 ? 'status-excellent' : 
                      assignment.score >= 70 ? 'status-good' : 'status-needs-improvement'
                    }`}>
                      {assignment.score >= 85 ? 'Excellent' : assignment.score >= 70 ? 'Good' : 'Needs Improvement'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'papers':
        return (
          <div className="card">
            <h2>Question Papers</h2>
            <p>View and download question papers</p>
            
            <div className="mt-4">
              <div className="empty-state">
                <span style={{ fontSize: '3rem' }}>📄</span>
                <p>No question papers available yet.</p>
              </div>
            </div>
          </div>
        );

      case 'profile':
        return (
          <div className="card">
            <h2>Profile</h2>
            <div className="profile-section">
              <div className="profile-header">
                <div className="avatar" style={{ width: '80px', height: '80px', fontSize: '2rem' }}>
                  {currentUser.fullName.split(' ').map(part => part[0]).join('').toUpperCase()}
                </div>
                <div className="profile-info">
                  <h3>{currentUser.fullName}</h3>
                  <p style={{ color: 'var(--secondary)' }}>Student</p>
                </div>
              </div>
            </div>
            
            <hr className="mb-4" style={{ border: 'none', height: '1px', backgroundColor: '#E2E8F0' }} />
            
            <div className="account-info">
              <h4 className="mb-2">Account Information</h4>
              <div className="info-grid">
                <div><strong>Username:</strong> {currentUser.username}</div>
                <div><strong>ID:</strong> {currentUser.id}</div>
                <div><strong>Role:</strong> Student</div>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="card">
            <p>Select an option from the sidebar</p>
          </div>
        );
    }
  };

  return (
    <div className="page">
      <Navbar user={currentUser} />
      <div className="dashboard">
        <Sidebar 
          items={sidebarItems}
          activeItem={activeTab}
          onItemClick={setActiveTab}
        />
        <div className="main-content">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default StudentHome;