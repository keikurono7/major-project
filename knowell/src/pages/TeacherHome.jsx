// src/pages/TeacherHome.jsx
import React, { useContext, useState, useEffect } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import { paperApi } from '../services/api';
import ParallaxSection from '../components/common/ParallaxSection';
import ContentUpload from '../components/teacher/ContentUpload';
import PaperGenerator from '../components/teacher/PaperGenerator';
import Analytics from '../components/teacher/Analytics';

const TeacherHome = () => {
  const { currentUser } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, fetch question papers and other teacher data
    setLoading(false);
  }, []);

  const handlePdfUpload = async (file) => {
    try {
      await paperApi.uploadPdf(file);
      alert('PDF uploaded successfully');
    } catch (error) {
      console.error('Error uploading PDF:', error);
      alert('Failed to upload PDF');
    }
  };

  const handleGeneratePaper = async (data) => {
    try {
      const response = await paperApi.generatePaper(data);
      setPapers([...papers, response.data]);
      alert('Question paper generation started');
    } catch (error) {
      console.error('Error generating paper:', error);
      alert('Failed to generate question paper');
    }
  };

  const renderContent = () => {
    if (loading) return <div>Loading...</div>;
    
    switch (activeTab) {
      case 'dashboard':
        return (
          <>
            <ParallaxSection className="welcome-section">
              <h1>Welcome, {currentUser.fullName}</h1>
              <p>Manage your educational content and monitor student progress</p>
            </ParallaxSection>
            
            <div className="dashboard-overview">
              <div className="grid-container">
                <div className="sharp-card">
                  <h3>Question Papers</h3>
                  <div className="stat">{papers.length}</div>
                </div>
                
                <div className="sharp-card">
                  <h3>Students</h3>
                  <div className="stat">N/A</div>
                </div>
                
                <div className="sharp-card">
                  <h3>Content Files</h3>
                  <div className="stat">1</div>
                </div>
              </div>
            </div>
            
            <ParallaxSection className="quick-actions" speed={0.2}>
              <h2>Quick Actions</h2>
              <div className="actions-grid">
                <button onClick={() => setActiveTab('content')} className="sharp-button">
                  Upload Content
                </button>
                <button onClick={() => setActiveTab('papers')} className="sharp-button">
                  Generate Question Paper
                </button>
                <button onClick={() => setActiveTab('analytics')} className="sharp-button">
                  View Analytics
                </button>
              </div>
            </ParallaxSection>
          </>
        );
      case 'content':
        return <ContentUpload onUpload={handlePdfUpload} />;
      case 'papers':
        return <PaperGenerator onGenerate={handleGeneratePaper} />;
      case 'analytics':
        return <Analytics />;
      case 'students':
        return <div>Student monitoring interface here</div>;
      default:
        return <div>Select an option from the sidebar</div>;
    }
  };

  return (
    <div className="teacher-home">
      <Navbar user={currentUser} />
      <div className="main-container">
        <Sidebar 
          items={[
            { id: 'dashboard', label: 'Dashboard', icon: '📊' },
            { id: 'content', label: 'Content Upload', icon: '📁' },
            { id: 'papers', label: 'Question Papers', icon: '📝' },
            { id: 'analytics', label: 'Analytics', icon: '📈' },
            { id: 'students', label: 'Students', icon: '👨‍🎓' }
          ]}
          activeItem={activeTab}
          onItemClick={setActiveTab}
        />
        <div className="content">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default TeacherHome;