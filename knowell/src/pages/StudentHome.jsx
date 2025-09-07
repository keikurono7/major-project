// src/pages/StudentHome.jsx
import React, { useContext, useState, useEffect } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import ProgressTracker from '../components/student/ProgressTracker';
import QuizInterface from '../components/student/QuizInterface';
import AssignmentInterface from '../components/student/AssignmentInterface';
import { topicsApi, progressApi } from '../services/api';

const StudentHome = () => {
  const { currentUser } = useContext(AuthContext);
  const [topics, setTopics] = useState([]);
  const [progress, setProgress] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [topicsResponse, progressResponse] = await Promise.all([
          topicsApi.getAll(),
          progressApi.getProgress(currentUser.id)
        ]);
        
        setTopics(topicsResponse.data);
        setProgress(progressResponse.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
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

  const renderContent = () => {
    if (loading) return <div className="loading">Loading...</div>;
    
    switch (activeTab) {
      case 'dashboard':
        return (
          <>
            <div className="card">
              <h2>Welcome back, {currentUser.fullName}</h2>
              <p>Continue your learning journey where you left off.</p>
            </div>
            
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-title">Topics</div>
                <div className="stat-value">{topics.length}</div>
                <div className="stat-desc">Available for learning</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-title">Average Confidence</div>
                <div className="stat-value">
                  {progress ? 
                    `${(Object.values(progress.confidence_scores).reduce((a, b) => a + b, 0) / 
                    Object.values(progress.confidence_scores).length * 100).toFixed(0)}%` : 
                    'N/A'}
                </div>
                <div className="stat-desc">Across all topics</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-title">Focus Area</div>
                <div className="stat-value" style={{ fontSize: '1.25rem' }}>
                  {progress ? 
                    Object.entries(progress.confidence_scores).sort((a, b) => a[1] - b[1])[0][0] : 
                    'N/A'}
                </div>
                <div className="stat-desc">Needs improvement</div>
              </div>
            </div>
            
            <div className="card">
              <h3 className="mb-4">Your Progress</h3>
              {progress && <ProgressTracker progress={progress.confidence_scores} />}
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
              <p>No question papers available yet.</p>
            </div>
          </div>
        );
      case 'profile':
        return (
          <div className="card">
            <h2>Profile</h2>
            <div className="mb-4">
              <div className="flex items-center gap-4">
                <div className="avatar" style={{ width: '80px', height: '80px', fontSize: '2rem' }}>
                  {currentUser.fullName.split(' ').map(part => part[0]).join('').toUpperCase()}
                </div>
                <div>
                  <h3 style={{ marginBottom: '0.25rem' }}>{currentUser.fullName}</h3>
                  <p style={{ color: 'var(--secondary)' }}>Student</p>
                </div>
              </div>
            </div>
            <hr className="mb-4" style={{ border: 'none', height: '1px', backgroundColor: '#E2E8F0' }} />
            <div>
              <h4 className="mb-2">Account Information</h4>
              <div>
                <strong>Username:</strong> {currentUser.username}
              </div>
              <div>
                <strong>ID:</strong> {currentUser.id}
              </div>
            </div>
          </div>
        );
      default:
        return <div>Select an option from the sidebar</div>;
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