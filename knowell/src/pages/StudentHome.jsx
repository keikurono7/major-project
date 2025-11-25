// src/pages/StudentHome.jsx
import React, { useContext, useState, useEffect, useRef } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import QuizInterface from '../components/student/QuizInterface';
import AssignmentInterface from '../components/student/AssignmentInterface';
import ProjectsFeed from '../components/student/ProjectsFeed';
import { computeAllSubjectsProgress } from '../services/progress';
import { chatWithAssistant } from '../services/api';
import '../dashboard.css';

const StudentHome = () => {
  const { currentUser, loading: authLoading } = useContext(AuthContext);
  const [topics, setTopics] = useState([]);
  const [subjectsData, setSubjectsData] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(localStorage.getItem('currentSubjectId') || null);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  
  // Chat states
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatMessagesRef = useRef(null);

  // Listen for subject changes from Navbar
  useEffect(() => {
    const handleSubjectChange = () => {
      const newSubjectId = localStorage.getItem('currentSubjectId');
      if (newSubjectId !== selectedSubjectId) {
        setSelectedSubjectId(newSubjectId);
        // Clear chat when subject changes
        setChatMessages([]);
      }
    };
    window.addEventListener('subjectChanged', handleSubjectChange);
    window.addEventListener('storage', handleSubjectChange);
    
    // Poll for same-tab changes
    const interval = setInterval(handleSubjectChange, 500);
    
    return () => {
      window.removeEventListener('subjectChanged', handleSubjectChange);
      window.removeEventListener('storage', handleSubjectChange);
      clearInterval(interval);
    };
  }, [selectedSubjectId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatMessages]);

  useEffect(() => {
    const fetchHierarchyWithBKT = async () => {
      try {
        if (!currentUser || !currentUser.id) {
          console.error("Invalid user data");
          setLoadingSubjects(false);
          return;
        }

        setLoadingSubjects(true);
        const subjectsWithProgress = await computeAllSubjectsProgress(currentUser.id);
        setSubjectsData(subjectsWithProgress || []);

        const flatTopics = (subjectsWithProgress || []).flatMap(s => (s.modules || []).flatMap(m => (m.topics || [])));
        setTopics(flatTopics);
        
        // If no subject is selected but we have subjects, select the first one
        if (!selectedSubjectId && subjectsWithProgress && subjectsWithProgress.length > 0) {
          const firstSubjectId = subjectsWithProgress[0].id;
          setSelectedSubjectId(firstSubjectId);
          localStorage.setItem('currentSubjectId', firstSubjectId);
        }
      } catch (error) {
        console.error("Error building subject/module/topic hierarchy:", error);
      } finally {
        setLoadingSubjects(false);
      }
    };

    if (!authLoading && currentUser) {
      fetchHierarchyWithBKT();
    }
  }, [currentUser, authLoading]);

  const sidebarItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'projects', label: 'Projects', icon: '🗂️' },
    { id: 'quizzes', label: 'Take Quiz', icon: '❓' },
    { id: 'assignments', label: 'Assignments', icon: '📝' },
    { id: 'papers', label: 'Question Papers', icon: '📚' },
    { id: 'profile', label: 'Profile', icon: '👤' }
  ];

  // active tab state required by renderContent and Sidebar
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Helper function to generate YouTube search query
  const getYouTubeSearchUrl = (topicName, subjectName) => {
    const query = encodeURIComponent(`${subjectName} ${topicName} tutorial`);
    return `https://www.youtube.com/results?search_query=${query}`;
  };

  const handleSendMessage = async (message = chatInput) => {
    if (!message.trim() || !selectedSubjectId) {
      console.log('Cannot send - missing message or subject');
      return;
    }

    const studentName = currentUser.full_name || currentUser.fullName;

    const userMessage = {
      role: 'user',
      content: message
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      console.log('Sending message with params:', {
        studentId: currentUser.id,
        subjectId: selectedSubjectId,
        message: message,
        studentName: studentName,
        historyLength: chatMessages.length
      });

      // Filter out weakTopics and isError from conversation history
      const cleanHistory = chatMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await chatWithAssistant(
        currentUser.id,
        selectedSubjectId,
        message,
        studentName,
        cleanHistory
      );

      console.log('Received response:', response);

      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        weakTopics: response.knowledge_context
      };

      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message}`
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const renderContent = () => {
    if (authLoading || loadingSubjects) return <div className="loading">Loading...</div>;
    
    switch (activeTab) {
      case 'dashboard':
        // Filter subjectsData by selected subject
        const currentSubject = selectedSubjectId 
          ? subjectsData.find(s => s.id === selectedSubjectId)
          : null;

        // Only show "please select" if data is loaded and truly no subject
        if (subjectsData.length === 0) {
          return (
            <div className="card">
              <h2>Welcome back, {currentUser.fullName}</h2>
              <p>No subjects available yet. Please contact your teacher.</p>
            </div>
          );
        }

        if (!currentSubject) {
          return (
            <div className="card">
              <h2>Welcome back, {currentUser.fullName}</h2>
              <p>Please select a subject from the header to view your progress.</p>
            </div>
          );
        }

        // Use only the selected subject's data
        const modules = currentSubject.modules || [];
        const flatFromSubject = modules.flatMap(m => (m.topics || []));
        
        const seen = new Set();
        const uniqueTopics = [];
        for (const t of flatFromSubject) {
          if (!t || !t.id) continue;
          if (!seen.has(t.id)) {
            seen.add(t.id);
            uniqueTopics.push(t);
          }
        }

        const validScores = uniqueTopics
          .map(t => Number(t.bkt_score ?? 0))
          .filter(v => !Number.isNaN(v));

        const avgBKT = validScores.length > 0
          ? Math.round((validScores.reduce((s, v) => s + v, 0) / validScores.length) * 100)
          : 0;

        // Get first topic below 70% (not sorted, just first occurrence)
        const worstTopic = uniqueTopics.find(t => Number(t.bkt_score ?? 0) < 0.7);
        const focusArea = worstTopic ? worstTopic.name : 'N/A';

        // Get topics that need improvement (BKT score < 0.7) - keep original order
        const topicsNeedingHelp = uniqueTopics
          .filter(t => Number(t.bkt_score ?? 0) < 0.7)
          .slice(0, 3);

        // Get weak topics for chat display - keep original order
        const weakTopics = uniqueTopics
          .filter(t => Number(t.bkt_score ?? 0) < 0.7)
          .slice(0, 5);
        
        return (
          <>
            {/* Welcome Card */}
            <div className="card">
              <h2>Welcome back, {currentUser.full_name || currentUser.fullName || currentUser.email}</h2>
              <p>Continue your learning journey in {currentSubject.name}.</p>
            </div>
            
            {/* Stats Grid */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">📚</div>
                <div className="stat-info">
                  <div className="stat-value">{uniqueTopics.length}</div>
                  <div className="stat-label">Topics</div>
                  <div className="stat-desc">In {currentSubject.name}</div>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-info">
                  <div className="stat-value">{avgBKT}%</div>
                  <div className="stat-label">Average Confidence</div>
                  <div className="stat-desc">In this subject</div>
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

              {/* YouTube Recommendations Card */}
              <div className="stat-card" style={{ gridColumn: 'span 1' }}>
                <div className="stat-icon">📺</div>
                <div className="stat-info">
                  <div className="stat-label" style={{ marginBottom: 8 }}>Recommended Videos</div>
                  {topicsNeedingHelp.length === 0 ? (
                    <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>All topics mastered! 🎉</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {topicsNeedingHelp.map((topic, idx) => {
                        const pct = Math.round((topic.bkt_score || 0) * 100);
                        return (
                          <a
                            key={topic.id}
                            href={getYouTubeSearchUrl(topic.name, currentSubject.name)}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: '0.75rem',
                              color: '#ca404f',
                              textDecoration: 'none',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                            onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                          >
                            <span>🎥</span>
                            <span>{topic.name} ({pct}%)</span>
                          </a>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Two Column Layout: Progress and Chat */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '1.5rem', 
              marginTop: '1.5rem',
              height: 'calc(100vh - 400px)', // Fixed height based on viewport
              minHeight: '500px',
              maxHeight: '700px'
            }}>
              {/* Progress Section */}
              <div className="card" style={{ 
                display: 'flex', 
                flexDirection: 'column',
                height: '100%',
                overflow: 'hidden'
              }}>
                <h3 style={{ marginBottom: '1rem', flexShrink: 0 }}>Your Progress in {currentSubject.name}</h3>
                <div style={{ 
                  flex: 1,
                  overflowY: 'auto',
                  paddingRight: '0.5rem'
                }}>
                  {modules.length === 0 && <div>No modules available in this subject.</div>}

                  {modules.map((module) => (
                    <details key={module.id} style={{ marginBottom: 12, border: '1px solid #e6e6e6', borderRadius: 6, padding: 8 }}>
                      <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
                        {module.name} ({module.topics?.length || 0} topics)
                      </summary>

                      <div style={{ marginTop: 8, paddingLeft: 12 }}>
                        {(!module.topics || module.topics.length === 0) && <div style={{ color: '#6b7280' }}>No topics</div>}

                        {(module.topics || []).map((topic) => {
                          const pct = Math.round((topic.bkt_score || 0) * 100);
                          const color = (topic.bkt_score || 0) > 0.8 ? '#10b981' : (topic.bkt_score || 0) > 0.6 ? '#f59e0b' : '#ef4444';
                          return (
                            <div key={topic.id} style={{ marginBottom: 10 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                <div style={{ fontSize: 14 }}>{topic.name}</div>
                                <div style={{ fontSize: 13, color: '#374151' }}>{pct}%</div>
                              </div>
                              <div style={{ backgroundColor: '#e5e7eb', borderRadius: 6, height: 12 }}>
                                <div style={{ width: `${pct}%`, backgroundColor: color, height: '100%', borderRadius: 6 }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </details>
                  ))}
                </div>
              </div>

              {/* AI Assistant Chat */}
              <div className="card" style={{ 
                display: 'flex', 
                flexDirection: 'column',
                height: '100%',
                overflow: 'hidden'
              }}>
                <div style={{ flexShrink: 0 }}>
                  <h3 style={{ marginBottom: '0.5rem' }}>🤖 AI Learning Assistant</h3>
                  <p style={{ color: '#6b7280', fontSize: '0.85rem', marginBottom: '1rem' }}>
                    Ask questions about {currentSubject.name}
                  </p>

                  {/* Weak Topics Display */}
                  {weakTopics.length > 0 && (
                    <div style={{ 
                      marginBottom: '1rem',
                      padding: '0.75rem',
                      backgroundColor: '#fef3f2',
                      borderRadius: '8px',
                      border: '1px solid #fca5a5',
                      maxHeight: '100px',
                      overflowY: 'auto'
                    }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '0.5rem', color: '#991b1b' }}>
                        🎯 Focus Areas:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                        {weakTopics.map(topic => {
                          const pct = Math.round((topic.bkt_score || 0) * 100);
                          return (
                            <span
                              key={topic.id}
                              style={{
                                padding: '0.125rem 0.5rem',
                                backgroundColor: 'white',
                                border: '1px solid #fca5a5',
                                borderRadius: '10px',
                                fontSize: '0.7rem',
                                color: '#991b1b'
                              }}
                            >
                              {topic.name} ({pct}%)
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Chat Interface */}
                <div style={{ 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '8px', 
                  flex: 1,
                  display: 'flex', 
                  flexDirection: 'column',
                  backgroundColor: '#f9fafb',
                  minHeight: 0 // Important for flex child scrolling
                }}>
                  {/* Chat Messages Area */}
                  <div style={{ 
                    flex: 1, 
                    padding: '1rem', 
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    minHeight: 0 // Important for flex child scrolling
                  }} ref={chatMessagesRef}>
                    {/* Welcome Message */}
                    {chatMessages.length === 0 && (
                      <div style={{ 
                        backgroundColor: 'white', 
                        padding: '0.75rem', 
                        borderRadius: '8px',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                      }}>
                        <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#ca404f', fontSize: '0.85rem' }}>
                          AI Assistant
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#374151', lineHeight: '1.5' }}>
                          Hi {currentUser.full_name || currentUser.fullName || 'there'}! I can see you're working on {currentSubject.name}. 
                          Your average confidence is {avgBKT}%. 
                          {focusArea !== 'N/A' && ` I notice ${focusArea} needs some attention. `}
                          How can I help you today?
                        </div>
                      </div>
                    )}
                    
                    {/* Chat Messages */}
                    {chatMessages.map((msg, idx) => (
                      <div key={idx} style={{ 
                        backgroundColor: msg.role === 'user' ? '#e1f5fe' : 'white', 
                        padding: '0.75rem', 
                        borderRadius: '8px',
                        border: '1px solid #e5e7eb',
                        maxWidth: '90%',
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                      }}>
                        <div style={{ 
                          fontSize: '0.7rem', 
                          fontWeight: 600, 
                          marginBottom: '0.25rem', 
                          color: msg.role === 'user' ? '#01579b' : '#ca404f' 
                        }}>
                          {msg.role === 'user' ? 'You' : 'AI Assistant'}
                        </div>
                        <div style={{ fontSize: '0.85rem', lineHeight: '1.5', color: '#1f2937' }}>
                          {msg.content}
                        </div>
                        {msg.weakTopics && msg.weakTopics.length > 0 && (
                          <div style={{ 
                            marginTop: '0.5rem', 
                            paddingTop: '0.5rem',
                            borderTop: '1px solid #e5e7eb'
                          }}>
                            <div style={{ fontSize: '0.7rem', fontWeight: '600', marginBottom: '0.25rem', color: '#6b7280' }}>
                              Suggested topics:
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                              {msg.weakTopics.map((topic, i) => (
                                <span
                                  key={i}
                                  style={{
                                    padding: '0.125rem 0.5rem',
                                    backgroundColor: '#fef3f2',
                                    border: '1px solid #fca5a5',
                                    borderRadius: '10px',
                                    fontSize: '0.65rem',
                                    color: '#991b1b'
                                  }}
                                >
                                  {topic.topic} ({topic.mastery}%)
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Loading indicator */}
                    {isChatLoading && (
                      <div style={{ 
                        backgroundColor: 'white', 
                        padding: '0.75rem', 
                        borderRadius: '8px',
                        border: '1px solid #e5e7eb',
                        alignSelf: 'flex-start',
                        maxWidth: '90%',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <div style={{ 
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: '#ca404f',
                          animation: 'pulse 1.5s ease-in-out infinite'
                        }} />
                        <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                          Thinking...
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Chat Input Area */}
                  <div style={{ 
                    padding: '0.75rem', 
                    borderTop: '1px solid #e5e7eb',
                    backgroundColor: 'white',
                    flexShrink: 0
                  }}>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <input
                        type="text"
                        placeholder="Ask me anything..."
                        style={{
                          flex: 1,
                          padding: '0.5rem',
                          border: '1px solid #e5e7eb',
                          borderRadius: '6px',
                          fontSize: '0.85rem',
                          outline: 'none'
                        }}
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !isChatLoading && chatInput.trim()) {
                            handleSendMessage();
                          }
                        }}
                        disabled={isChatLoading}
                        onFocus={(e) => e.currentTarget.style.borderColor = '#ca404f'}
                        onBlur={(e) => e.currentTarget.style.borderColor = '#e5e7eb'}
                      />
                      <button
                        onClick={() => handleSendMessage()}
                        disabled={isChatLoading || !chatInput.trim()}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: (isChatLoading || !chatInput.trim()) ? '#d1d5db' : '#ca404f',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '0.85rem',
                          cursor: (isChatLoading || !chatInput.trim()) ? 'not-allowed' : 'pointer',
                          fontWeight: 600,
                          transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          if (!isChatLoading && chatInput.trim()) {
                            e.currentTarget.style.backgroundColor = '#b0303f';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isChatLoading && chatInput.trim()) {
                            e.currentTarget.style.backgroundColor = '#ca404f';
                          }
                        }}
                      >
                        Send
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        );

      case 'quizzes':
        return <QuizInterface studentId={currentUser.id} />;

      case 'projects':
        return <ProjectsFeed studentId={currentUser.id} />;

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
                  {(currentUser.full_name || currentUser.fullName || 'U').split(' ').map(part => part[0]).join('').toUpperCase()}
                </div>
                <div className="profile-info">
                  <h3>{currentUser.full_name || currentUser.fullName}</h3>
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

  // minimal render: provide sidebarItems so Sidebar.map won't fail
  return (
    <div className="flex min-h-screen">
      <Sidebar items={sidebarItems} activeItem={activeTab} onItemClick={setActiveTab} />
      <div className="flex-1">
        <Navbar user={currentUser} />
        <main className="flex-1 bg-gray-100 p-6">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default StudentHome;