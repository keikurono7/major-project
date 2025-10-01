// src/pages/StudentHome.jsx
import React, { useContext, useState, useEffect } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import ProgressTracker from '../components/student/ProgressTracker';
import QuizInterface from '../components/student/QuizInterface';
import AssignmentInterface from '../components/student/AssignmentInterface';
import { topicsApi, progressApi, modulesApi } from '../services/api';
import '../dashboard.css';

const StudentHome = () => {
  const { currentUser, loading: authLoading } = useContext(AuthContext); // Use loading from AuthContext
  const [topics, setTopics] = useState([]);
  const [progress, setProgress] = useState({
    confidence_scores: {}
  });
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const fetchTopicsAndBKT = async () => {
      try {
        // Ensure currentUser is valid
        if (!currentUser || !currentUser.id) {
          console.error("Invalid user data");
          return;
        }

        // Step 1: Get all subjects
        const subjectsRes = await modulesApi.getAll();
        console.log("Subjects Response:", subjectsRes.data);
        const subjects = subjectsRes.data.subjects; // Access the subjects array
        if (!subjects || subjects.length === 0) {
          console.error("No subjects found");
          return;
        }

        // Loop through all subjects
        for (const subject of subjects) {
          console.log("Processing Subject:", subject);

          // Step 2: Get all modules for the current subject
          const modulesRes = await modulesApi.getBySubject(subject.id);
          const modules = modulesRes.data.modules; // Access the modules array
          if (!modules || modules.length === 0) {
            console.error(`No modules found for subject ${subject.name}`);
            continue;
          }

          // Loop through all modules
          for (const module of modules) {
            console.log("Processing Module:", module);

            // Step 3: Get all topics for the current module
            const topicsRes = await topicsApi.getByModule(module.id, currentUser.id);
            if (!topicsRes.data || !topicsRes.data.topics) {
              console.error(`No topics found for module ${module.name}`);
              continue;
            }

            // Fetch BKT parameters for each topic
            const topicsWithBKT = await Promise.all(
              topicsRes.data.topics.map(async (topic) => {
                try {
                  const bktRes = await progressApi.getBKTParams(currentUser.id, topic.id);
                  return {
                    ...topic,
                    bkt_score: bktRes.data.mastery_probability || 0, // Use mastery_probability from BKT API
                  };
                } catch (error) {
                  console.warn(`Failed to fetch BKT params for topic ${topic.name}:`, error);
                  return {
                    ...topic,
                    bkt_score: 0, // Default BKT score if API call fails
                  };
                }
              })
            );

            // Add topics with BKT scores to the state
            setTopics((prevTopics) => [...prevTopics, ...topicsWithBKT]);
          }
        }
      } catch (error) {
        console.error("Error fetching topics and BKT scores:", error);
      }
    };

    // Only fetch topics and BKT scores when AuthContext is done loading and currentUser is valid
    if (!authLoading && currentUser) {
      fetchTopicsAndBKT();
    }
  }, [currentUser, authLoading]);


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
    if (authLoading) return <div className="loading">Loading...</div>;
    
    switch (activeTab) {
      case 'dashboard':
        const avgBKT = topics.length > 0
        ? (topics.reduce((sum, topic) => sum + topic.bkt_score, 0) / topics.length * 100).toFixed(0)
        : 0;

      const focusArea = topics.length > 0
        ? topics.sort((a, b) => a.bkt_score - b.bkt_score)[0].name
        : 'N/A';

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
                  <div className="stat-value">{avgBKT}%</div>
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
                  {topics.filter(topic => topic.bkt_score > 0).map((topic) => (
                  <div key={topic.id} className="progress-item">
                    <div className="progress-header">
                      <span className="progress-topic">{topic.name}</span>
                      <span className="progress-score">{Math.round(topic.bkt_score * 100)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${topic.bkt_score * 100}%`,
                          backgroundColor: topic.bkt_score > 0.8 ? '#10b981' : topic.bkt_score > 0.6 ? '#f59e0b' : '#ef4444'
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
        return <QuizInterface studentId={currentUser.id} />;

      case 'assignments':
        return <AssignmentInterface studentId={currentUser.id} />;

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