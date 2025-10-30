import React, { useState, useEffect } from 'react';
import { assignmentApi } from '../../services/api';
import { computeAllSubjectsProgress } from '../../services/progress';
import '../../dashboard.css';

const AssignmentInterface = ({ studentId }) => {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(localStorage.getItem('currentSubjectId') || null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [numQuestions, setNumQuestions] = useState(5);
  const [assignment, setAssignment] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('module'); // Changed from 'subject' to 'module'

  useEffect(() => {
    fetchSubjects();
  }, []);

  // Listen for subject changes from header
  useEffect(() => {
    const handleSubjectChange = () => {
      const newSubjectId = localStorage.getItem('currentSubjectId');
      if (newSubjectId && newSubjectId !== selectedSubjectId) {
        setSelectedSubjectId(newSubjectId);
        // Reset assignment state when subject changes
        setSelectedModule(null);
        setSelectedTopic(null);
        setAssignment(null);
        setStep('module');
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

  const fetchSubjects = async () => {
    try {
      const subjectsWithProgress = await computeAllSubjectsProgress(studentId);
      setSubjects(subjectsWithProgress || []);
      
      // If we have a subject selected from header, use it
      const currentSubjectId = localStorage.getItem('currentSubjectId');
      if (currentSubjectId) {
        setSelectedSubjectId(currentSubjectId);
      }
    } catch (error) {
      console.error('Error fetching subjects:', error);
    }
  };

  const handleGenerateAssignment = async () => {
    if (!selectedTopic) {
      alert('Please select a topic');
      return;
    }

    setLoading(true);
    try {
      const response = await assignmentApi.createAssignment({
        topic_ids: [selectedTopic.id],
        student_id: studentId,
        num_questions: numQuestions
      });

      if (response.data.assignment && response.data.assignment.questions) {
        setAssignment(response.data.assignment);
        setCurrentQuestionIndex(0);
        setUserAnswers({});
        setShowResults(false);
        setStep('assignment');
      } else {
        alert('Failed to generate assignment. Please try again.');
      }
    } catch (error) {
      console.error('Error generating assignment:', error);
      alert('Failed to generate assignment');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (answer) => {
    setUserAnswers({
      ...userAnswers,
      [currentQuestionIndex]: answer
    });
  };

  const handleNext = () => {
    if (currentQuestionIndex < assignment.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      handleSubmitAssignment();
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmitAssignment = async () => {
    try {
      // In a real implementation, you would submit to backend here
      console.log('Submitting assignment with answers:', userAnswers);
      setShowResults(true);
    } catch (error) {
      console.error('Error submitting assignment:', error);
      alert('Failed to submit assignment');
    }
  };

  const handleRetakeAssignment = () => {
    setAssignment(null);
    setCurrentQuestionIndex(0);
    setUserAnswers({});
    setShowResults(false);
    setStep('module');
    setSelectedModule(null);
    setSelectedTopic(null);
  };

  const renderModuleSelection = () => {
    const currentSubject = subjects.find(s => s.id === selectedSubjectId);
    
    if (!currentSubject) {
      return (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: '#6b7280', fontSize: '1.1rem' }}>
            Please select a subject from the header to start an assignment
          </p>
        </div>
      );
    }

    return (
      <div>
        <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>
          Select Module ({currentSubject.name})
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
          {currentSubject.modules.map((module) => (
            <div
              key={module.id}
              onClick={() => {
                setSelectedModule(module);
                setStep('topic');
              }}
              style={{
                padding: '1.5rem',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: 'white'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#ca404f';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <h4 style={{ color: '#1f2937', marginBottom: '0.5rem' }}>{module.name}</h4>
              <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                {module.topics?.length || 0} topics
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderTopicSelection = () => {
    if (!selectedModule) return null;

    return (
      <div>
        <button
          onClick={() => {
            setSelectedModule(null);
            setStep('module');
          }}
          style={{
            marginBottom: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#f3f4f6',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.875rem'
          }}
        >
          ← Back to Modules
        </button>

        <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>
          Select Topic ({selectedModule.name})
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          {selectedModule.topics?.map((topic) => {
            const mastery = Math.round((topic.bkt_score || 0) * 100);
            const color = mastery > 80 ? '#10b981' : mastery > 60 ? '#f59e0b' : '#ef4444';
            
            return (
              <div
                key={topic.id}
                onClick={() => setSelectedTopic(topic)}
                style={{
                  padding: '1.5rem',
                  border: selectedTopic?.id === topic.id ? '2px solid #ca404f' : '2px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: selectedTopic?.id === topic.id ? '#fff5f7' : 'white'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#ca404f';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  if (selectedTopic?.id !== topic.id) {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                  }
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <h4 style={{ color: '#1f2937', marginBottom: '0.75rem', fontSize: '1rem' }}>
                  {topic.name}
                </h4>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ flex: 1, backgroundColor: '#e5e7eb', borderRadius: '4px', height: '8px' }}>
                    <div 
                      style={{ 
                        width: `${mastery}%`, 
                        backgroundColor: color, 
                        height: '100%', 
                        borderRadius: '4px',
                        transition: 'width 0.3s'
                      }} 
                    />
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '600' }}>
                    {mastery}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {selectedTopic && (
          <div style={{ marginTop: '1.5rem', padding: '1.5rem', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
            <h4 style={{ marginBottom: '1rem', color: '#1f2937' }}>Assignment Settings</h4>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
                Number of Questions:
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={numQuestions}
                onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
                style={{
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  width: '100px',
                  fontSize: '1rem'
                }}
              />
            </div>
            <button
              onClick={handleGenerateAssignment}
              disabled={loading}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: loading ? '#d1d5db' : '#ca404f',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!loading) e.currentTarget.style.backgroundColor = '#b0303f';
              }}
              onMouseLeave={(e) => {
                if (!loading) e.currentTarget.style.backgroundColor = '#ca404f';
              }}
            >
              {loading ? 'Generating Assignment...' : 'Start Assignment'}
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderAssignment = () => {
    if (!assignment || !assignment.questions || assignment.questions.length === 0) {
      return <div>No questions available</div>;
    }

    const currentQuestion = assignment.questions[currentQuestionIndex];
    const userAnswer = userAnswers[currentQuestionIndex] || '';

    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ color: '#1f2937' }}>
            Question {currentQuestionIndex + 1} of {assignment.questions.length}
          </h3>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            {selectedTopic?.name}
          </div>
        </div>

        <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          <p style={{ fontSize: '1.125rem', color: '#1f2937', lineHeight: '1.6', marginBottom: '1rem' }}>
            {currentQuestion.question}
          </p>
          {currentQuestion.hint && (
            <div style={{ 
              padding: '0.75rem', 
              backgroundColor: '#fef3c7', 
              borderRadius: '6px',
              fontSize: '0.875rem',
              color: '#92400e',
              marginTop: '0.75rem'
            }}>
              💡 <strong>Hint:</strong> {currentQuestion.hint}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
            Your Answer:
          </label>
          <textarea
            value={userAnswer}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Type your answer here..."
            style={{
              width: '100%',
              minHeight: '150px',
              padding: '1rem',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '1rem',
              fontFamily: 'inherit',
              resize: 'vertical',
              outline: 'none'
            }}
            onFocus={(e) => e.currentTarget.style.borderColor = '#ca404f'}
            onBlur={(e) => e.currentTarget.style.borderColor = '#e5e7eb'}
          />
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
            {userAnswer.length} characters
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: currentQuestionIndex === 0 ? '#e5e7eb' : '#f3f4f6',
              color: currentQuestionIndex === 0 ? '#9ca3af' : '#374151',
              border: 'none',
              borderRadius: '6px',
              cursor: currentQuestionIndex === 0 ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600'
            }}
          >
            Previous
          </button>

          <button
            onClick={handleNext}
            disabled={!userAnswer.trim()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: !userAnswer.trim() ? '#d1d5db' : '#ca404f',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: !userAnswer.trim() ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (userAnswer.trim()) e.currentTarget.style.backgroundColor = '#b0303f';
            }}
            onMouseLeave={(e) => {
              if (userAnswer.trim()) e.currentTarget.style.backgroundColor = '#ca404f';
            }}
          >
            {currentQuestionIndex === assignment.questions.length - 1 ? 'Submit Assignment' : 'Next'}
          </button>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    return (
      <div>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ color: '#1f2937', marginBottom: '1rem' }}>Assignment Submitted!</h2>
          <div style={{ 
            fontSize: '2.5rem', 
            marginBottom: '0.5rem'
          }}>
            ✅
          </div>
          <p style={{ color: '#6b7280', fontSize: '1.125rem' }}>
            Your assignment has been submitted successfully
          </p>
          <p style={{ color: '#9ca3af', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Your teacher will review and grade it soon
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>Your Responses</h3>
          {assignment.questions.map((question, index) => {
            const userAnswer = userAnswers[index] || '';

            return (
              <div key={index} style={{ 
                padding: '1.5rem', 
                backgroundColor: 'white',
                borderRadius: '8px',
                marginBottom: '1rem',
                border: '2px solid #e5e7eb'
              }}>
                <div style={{ marginBottom: '1rem' }}>
                  <span style={{ fontWeight: '600', color: '#1f2937' }}>Q{index + 1}: </span>
                  <span style={{ color: '#374151' }}>{question.question}</span>
                </div>
                
                <div style={{ 
                  padding: '1rem', 
                  backgroundColor: '#f9fafb',
                  borderRadius: '6px',
                  fontSize: '0.9rem',
                  color: '#374151'
                }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#6b7280' }}>
                    Your answer:
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {userAnswer || '(No answer provided)'}
                  </div>
                </div>
                
                {question.model_answer && (
                  <div style={{ 
                    marginTop: '0.75rem', 
                    padding: '0.75rem', 
                    backgroundColor: '#f0fdf4',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    color: '#166534',
                    border: '1px solid #86efac'
                  }}>
                    <span style={{ fontWeight: '600' }}>Model Answer: </span>
                    {question.model_answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <button
          onClick={handleRetakeAssignment}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#ca404f',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: '600',
            width: '100%',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#b0303f'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ca404f'}
        >
          Start New Assignment
        </button>
      </div>
    );
  };

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1.5rem', color: '#1f2937' }}>Assignments</h2>
      
      {step === 'module' && renderModuleSelection()}
      {step === 'topic' && renderTopicSelection()}
      {step === 'assignment' && !showResults && renderAssignment()}
      {showResults && renderResults()}
    </div>
  );
};

export default AssignmentInterface;