// src/components/student/QuizInterface.jsx
import React, { useState, useEffect } from 'react';
import api, { quizApi } from '../../services/api';
import { computeAllSubjectsProgress } from '../../services/progress';
import '../../dashboard.css';

const QuizInterface = ({ studentId }) => {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(localStorage.getItem('currentSubjectId') || null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [numQuestions, setNumQuestions] = useState(5);
  const [quiz, setQuiz] = useState(null);
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
        // Reset quiz state when subject changes
        setSelectedModule(null);
        setSelectedTopic(null);
        setQuiz(null);
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

  const handleGenerateQuiz = async () => {
    if (!selectedTopic) {
      alert('Please select a topic');
      return;
    }

    setLoading(true);
    try {
      const response = await quizApi.generateQuiz({
        scope: 'topic',
        topic_id: selectedTopic.id,
        student_id: studentId,
        num_questions: numQuestions
      });

      if (response.data.quiz && response.data.quiz.questions) {
        setQuiz(response.data.quiz);
        setCurrentQuestionIndex(0);
        setUserAnswers({});
        setShowResults(false);
        setStep('quiz');
      } else {
        alert('Failed to generate quiz. Please try again.');
      }
    } catch (error) {
      console.error('Error generating quiz:', error);
      alert('Failed to generate quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (answer) => {
    setUserAnswers({
      ...userAnswers,
      [currentQuestionIndex]: answer
    });
  };

  const handleNext = async () => {
    const currentQuestion = quiz.questions[currentQuestionIndex];
    const userAnswer = userAnswers[currentQuestionIndex];
    const isCorrect = userAnswer === currentQuestion.answer;

    // Submit answer to backend for BKT update
    try {
      await quizApi.submitQuizResponse({
        student_id: studentId,
        topic_id: quiz.topic_id,
        is_correct: isCorrect
      });
    } catch (error) {
      console.error('Error submitting quiz response:', error);
    }

    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      setShowResults(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleRetakeQuiz = () => {
    setQuiz(null);
    setCurrentQuestionIndex(0);
    setUserAnswers({});
    setShowResults(false);
    setStep('module');
    setSelectedModule(null);
    setSelectedTopic(null);
  };

  const calculateScore = () => {
    let correct = 0;
    quiz.questions.forEach((question, index) => {
      if (userAnswers[index] === question.answer) {
        correct++;
      }
    });
    return { correct, total: quiz.questions.length };
  };

  const renderModuleSelection = () => {
    const currentSubject = subjects.find(s => s.id === selectedSubjectId);
    
    if (!currentSubject) {
      return (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: '#6b7280', fontSize: '1.1rem' }}>
            Please select a subject from the header to start a quiz
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
            <h4 style={{ marginBottom: '1rem', color: '#1f2937' }}>Quiz Settings</h4>
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
              onClick={handleGenerateQuiz}
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
              {loading ? 'Generating Quiz...' : 'Start Quiz'}
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderQuiz = () => {
    if (!quiz || !quiz.questions || quiz.questions.length === 0) {
      return <div>No questions available</div>;
    }

    const currentQuestion = quiz.questions[currentQuestionIndex];
    const userAnswer = userAnswers[currentQuestionIndex];

    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ color: '#1f2937' }}>
            Question {currentQuestionIndex + 1} of {quiz.questions.length}
          </h3>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            {quiz.topic}
          </div>
        </div>

        <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
          <p style={{ fontSize: '1.125rem', color: '#1f2937', lineHeight: '1.6' }}>
            {currentQuestion.question}
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
          {currentQuestion.options.map((option, index) => {
            const label = String.fromCharCode(65 + index); // A, B, C, D
            const isSelected = userAnswer === label;

            return (
              <div
                key={index}
                onClick={() => handleAnswerSelect(label)}
                style={{
                  padding: '1rem',
                  border: isSelected ? '2px solid #ca404f' : '2px solid #e5e7eb',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: isSelected ? '#fff5f7' : 'white'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#ca404f';
                  e.currentTarget.style.backgroundColor = '#fff5f7';
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.backgroundColor = 'white';
                  }
                }}
              >
                <span style={{ fontWeight: '600', marginRight: '0.75rem', color: '#ca404f' }}>
                  {label})
                </span>
                <span style={{ color: '#1f2937' }}>{option}</span>
              </div>
            );
          })}
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
            disabled={!userAnswer}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: !userAnswer ? '#d1d5db' : '#ca404f',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: !userAnswer ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (userAnswer) e.currentTarget.style.backgroundColor = '#b0303f';
            }}
            onMouseLeave={(e) => {
              if (userAnswer) e.currentTarget.style.backgroundColor = '#ca404f';
            }}
          >
            {currentQuestionIndex === quiz.questions.length - 1 ? 'Submit' : 'Next'}
          </button>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    const { correct, total } = calculateScore();
    const percentage = Math.round((correct / total) * 100);

    return (
      <div>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ color: '#1f2937', marginBottom: '1rem' }}>Quiz Completed!</h2>
          <div style={{ 
            fontSize: '3rem', 
            fontWeight: '700', 
            color: percentage >= 70 ? '#10b981' : percentage >= 50 ? '#f59e0b' : '#ef4444',
            marginBottom: '0.5rem'
          }}>
            {percentage}%
          </div>
          <p style={{ color: '#6b7280', fontSize: '1.125rem' }}>
            You got {correct} out of {total} questions correct
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>Review Answers</h3>
          {quiz.questions.map((question, index) => {
            const userAnswer = userAnswers[index];
            const isCorrect = userAnswer === question.answer;

            return (
              <div key={index} style={{ 
                padding: '1.5rem', 
                backgroundColor: isCorrect ? '#f0fdf4' : '#fef2f2',
                borderRadius: '8px',
                marginBottom: '1rem',
                border: `2px solid ${isCorrect ? '#86efac' : '#fca5a5'}`
              }}>
                <div style={{ marginBottom: '1rem' }}>
                  <span style={{ fontWeight: '600', color: '#1f2937' }}>Q{index + 1}: </span>
                  <span style={{ color: '#374151' }}>{question.question}</span>
                </div>
                
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '600', color: '#374151' }}>Your answer: </span>
                  <span style={{ color: isCorrect ? '#059669' : '#dc2626' }}>
                    {userAnswer}) {question.options[userAnswer?.charCodeAt(0) - 65]}
                  </span>
                </div>
                
                {!isCorrect && (
                  <div style={{ marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: '600', color: '#374151' }}>Correct answer: </span>
                    <span style={{ color: '#059669' }}>
                      {question.answer}) {question.options[question.answer.charCodeAt(0) - 65]}
                    </span>
                  </div>
                )}
                
                {question.explanation && (
                  <div style={{ 
                    marginTop: '0.75rem', 
                    padding: '0.75rem', 
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    color: '#6b7280'
                  }}>
                    <span style={{ fontWeight: '600', color: '#374151' }}>Explanation: </span>
                    {question.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <button
          onClick={handleRetakeQuiz}
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
          Take Another Quiz
        </button>
      </div>
    );
  };

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1.5rem', color: '#1f2937' }}>Take a Quiz</h2>
      
      {step === 'module' && renderModuleSelection()}
      {step === 'topic' && renderTopicSelection()}
      {step === 'quiz' && !showResults && renderQuiz()}
      {showResults && renderResults()}
    </div>
  );
};

export default QuizInterface;