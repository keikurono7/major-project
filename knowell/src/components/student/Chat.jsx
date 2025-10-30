import React, { useState, useEffect, useRef, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import { computeAllSubjectsProgress } from '../../services/progress';
import { chatWithAssistant } from '../../services/api';
import '../../dashboard.css';

const Chat = ({ studentId }) => {
  const { currentUser } = useContext(AuthContext);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(localStorage.getItem('currentSubjectId') || null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const chatMessagesRef = useRef(null);

  useEffect(() => {
    fetchSubjects();
  }, []);

  // Listen for subject changes from header
  useEffect(() => {
    const handleSubjectChange = () => {
      const newSubjectId = localStorage.getItem('currentSubjectId');
      if (newSubjectId && newSubjectId !== selectedSubjectId) {
        setSelectedSubjectId(newSubjectId);
        // Clear chat when subject changes
        setChatMessages([]);
      }
    };

    window.addEventListener('subjectChanged', handleSubjectChange);
    window.addEventListener('storage', handleSubjectChange);
    
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

  const fetchSubjects = async () => {
    try {
      const subjectsWithProgress = await computeAllSubjectsProgress(studentId);
      setSubjects(subjectsWithProgress || []);
      
      const currentSubjectId = localStorage.getItem('currentSubjectId');
      if (currentSubjectId) {
        setSelectedSubjectId(currentSubjectId);
      }
    } catch (error) {
      console.error('Error fetching subjects:', error);
    } finally {
      setLoadingSubjects(false);
    }
  };

  const handleSendMessage = async (message = chatInput) => {
    if (!message.trim() || !selectedSubjectId) {
      console.log('Cannot send - missing message or subject');
      return;
    }

    const studentName = currentUser.full_name;

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

  if (loadingSubjects) {
    return (
      <div className="card">
        <div className="loading">Loading chat...</div>
      </div>
    );
  }

  const currentSubject = subjects.find(s => s.id === selectedSubjectId);

  if (!currentSubject) {
    return (
      <div className="card">
        <h2>🤖 AI Learning Assistant</h2>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: '#6b7280', fontSize: '1.1rem' }}>
            Please select a subject from the header to start chatting
          </p>
        </div>
      </div>
    );
  }

  // Calculate stats for the current subject
  const modules = currentSubject.modules || [];
  const flatTopics = modules.flatMap(m => (m.topics || []));
  const uniqueTopics = [...new Map(flatTopics.map(t => [t.id, t])).values()];
  
  const validScores = uniqueTopics
    .map(t => Number(t.bkt_score ?? 0))
    .filter(v => !Number.isNaN(v));

  const avgBKT = validScores.length > 0
    ? Math.round((validScores.reduce((s, v) => s + v, 0) / validScores.length) * 100)
    : 0;

  const worstTopic = validScores.length > 0
    ? uniqueTopics.slice().sort((a, b) => (Number(a.bkt_score ?? 0) - Number(b.bkt_score ?? 0)))[0]
    : null;
  const focusArea = worstTopic ? worstTopic.name : 'N/A';

  // Get weak topics for display
  const weakTopics = uniqueTopics
    .filter(t => Number(t.bkt_score ?? 0) < 0.7)
    .sort((a, b) => (Number(a.bkt_score ?? 0) - Number(b.bkt_score ?? 0)))
    .slice(0, 5);

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1rem' }}>🤖 AI Learning Assistant</h2>
      <p style={{ color: '#6b7280', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Get personalized help for {currentSubject.name}
      </p>

      {/* Subject Stats Summary */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#f9fafb', 
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
            Average Mastery
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1f2937' }}>
            {avgBKT}%
          </div>
        </div>
        
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#f9fafb', 
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
            Focus Area
          </div>
          <div style={{ fontSize: '1rem', fontWeight: '600', color: '#1f2937' }}>
            {focusArea}
          </div>
        </div>

        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#f9fafb', 
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
            Topics
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1f2937' }}>
            {uniqueTopics.length}
          </div>
        </div>
      </div>

      {/* Weak Topics Display */}
      {weakTopics.length > 0 && (
        <div style={{ 
          marginBottom: '1.5rem',
          padding: '1rem',
          backgroundColor: '#fef3f2',
          borderRadius: '8px',
          border: '1px solid #fca5a5'
        }}>
          <div style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#991b1b' }}>
            🎯 Topics Needing Attention:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {weakTopics.map(topic => {
              const pct = Math.round((topic.bkt_score || 0) * 100);
              return (
                <span
                  key={topic.id}
                  style={{
                    padding: '0.25rem 0.75rem',
                    backgroundColor: 'white',
                    border: '1px solid #fca5a5',
                    borderRadius: '12px',
                    fontSize: '0.75rem',
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

      {/* Chat Interface */}
      <div style={{ 
        border: '1px solid #e5e7eb', 
        borderRadius: '8px', 
        height: '500px', 
        display: 'flex', 
        flexDirection: 'column',
        backgroundColor: '#f9fafb'
      }}>
        {/* Chat Messages Area */}
        <div style={{ 
          flex: 1, 
          padding: '1rem', 
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem'
        }} ref={chatMessagesRef}>
          {/* Welcome Message */}
          {chatMessages.length === 0 && (
            <div style={{ 
              backgroundColor: 'white', 
              padding: '1rem', 
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#ca404f' }}>
                AI Assistant
              </div>
              <div style={{ fontSize: '0.9rem', color: '#374151', lineHeight: '1.5' }}>
                Hi {currentUser.full_name || currentUser.fullName || 'there'}! I can see you're working on {currentSubject.name}. 
                {avgBKT < 70 && ` Your average mastery is ${avgBKT}%. `}
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
              maxWidth: '85%',
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}>
              <div style={{ 
                fontSize: '0.75rem', 
                fontWeight: 600, 
                marginBottom: '0.25rem', 
                color: msg.role === 'user' ? '#01579b' : '#ca404f' 
              }}>
                {msg.role === 'user' ? 'You' : 'AI Assistant'}
              </div>
              <div style={{ fontSize: '0.9rem', lineHeight: '1.5', color: '#1f2937' }}>
                {msg.content}
              </div>
              {msg.weakTopics && msg.weakTopics.length > 0 && (
                <div style={{ 
                  marginTop: '0.75rem', 
                  paddingTop: '0.75rem',
                  borderTop: '1px solid #e5e7eb'
                }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '0.5rem', color: '#6b7280' }}>
                    🎯 Focus Areas:
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
                          fontSize: '0.7rem',
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
              maxWidth: '85%',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <div style={{ 
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#ca404f',
                animation: 'pulse 1.5s ease-in-out infinite'
              }} />
              <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                Thinking...
              </div>
            </div>
          )}
        </div>
        
        {/* Chat Input Area */}
        <div style={{ 
          padding: '1rem', 
          borderTop: '1px solid #e5e7eb',
          backgroundColor: 'white'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="Ask me anything about your learning..."
              style={{
                flex: 1,
                padding: '0.75rem',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '0.9rem',
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
                padding: '0.75rem 1.5rem',
                backgroundColor: (isChatLoading || !chatInput.trim()) ? '#d1d5db' : '#ca404f',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.9rem',
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
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
            💡 I have context about your {uniqueTopics.length} topics and their mastery levels
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;