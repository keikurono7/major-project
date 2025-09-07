// src/components/student/QuizInterface.jsx
import React, { useState, useEffect } from 'react';
import { quizApi, topicsApi } from '../../services/api';

const QuizInterface = ({ studentId }) => {
  const [loading, setLoading] = useState(false);
  const [quiz, setQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topics, setTopics] = useState([]);
  const [results, setResults] = useState(null);
  
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const response = await topicsApi.getAll();
        setTopics(response.data);
      } catch (error) {
        console.error('Error fetching topics:', error);
      }
    };
    
    fetchTopics();
  }, []);
  
  const generateQuiz = async () => {
    setLoading(true);
    try {
      const response = await quizApi.generateQuiz({
        student_id: studentId,
        topic: selectedTopic,
        use_weakest: !selectedTopic
      });
      
      setQuiz(response.data);
      setCurrentQuestion(0);
      setAnswers({});
      setQuizCompleted(false);
      setResults(null);
    } catch (error) {
      console.error('Error generating quiz:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAnswer = (questionIndex, answer) => {
    setAnswers({
      ...answers,
      [questionIndex]: answer
    });
  };
  
  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setQuizCompleted(true);
      submitQuiz();
    }
  };
  
  const submitQuiz = async () => {
    if (!quiz) return;
    
    try {
      const quizResults = await Promise.all(
        Object.entries(answers).map(async ([index, answer]) => {
          const question = quiz.questions[index];
          const isCorrect = question.answer === answer;
          
          await quizApi.submitAnswer(studentId, {
            topic: quiz.topic,
            question: question.question,
            selected_answer: answer,
            is_correct: isCorrect
          });
          
          return { question, selectedAnswer: answer, isCorrect };
        })
      );
      
      setResults(quizResults);
    } catch (error) {
      console.error('Error submitting quiz:', error);
    }
  };
  
  // Quiz topic selection view
  if (!quiz && !loading) {
    return (
      <div className="card">
        <h2>Start a Quiz</h2>
        <p className="mb-4">Test your knowledge and improve your understanding</p>
        
        <div className="form-group">
          <label className="form-label">Select Topic:</label>
          <select 
            className="form-control"
            value={selectedTopic || ''} 
            onChange={(e) => setSelectedTopic(e.target.value || null)}
          >
            <option value="">Use my weakest topic</option>
            {topics.map(topic => (
              <option key={topic} value={topic}>{topic}</option>
            ))}
          </select>
          <div className="text-secondary mt-1" style={{ fontSize: '0.875rem' }}>
            Leave empty to automatically focus on your weakest topic
          </div>
        </div>
        
        <button onClick={generateQuiz} className="btn btn-primary">
          Start Quiz
        </button>
      </div>
    );
  }
  
  // Loading state
  if (loading) {
    return (
      <div className="card">
        <div className="text-center">
          <p>Generating quiz questions...</p>
          <div className="mt-4">
            <div className="loader"></div>
          </div>
        </div>
      </div>
    );
  }
  
  // Quiz completed with results
  if (quizCompleted && results) {
    const correctAnswers = results.filter(r => r.isCorrect).length;
    const totalQuestions = results.length;
    const percentage = Math.round((correctAnswers / totalQuestions) * 100);
    
    return (
      <div className="card">
        <h2>Quiz Results</h2>
        
        <div className="text-center my-6">
          <div style={{ 
            width: '120px', 
            height: '120px', 
            borderRadius: '50%', 
            backgroundColor: percentage >= 70 ? 'var(--success)' : percentage >= 40 ? 'var(--warning)' : 'var(--danger)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            fontWeight: 'bold',
            margin: '0 auto'
          }}>
            {percentage}%
          </div>
          <p className="mt-2" style={{ fontSize: '1.25rem' }}>
            You got {correctAnswers} out of {totalQuestions} correct
          </p>
        </div>
        
        <div>
          <h3 className="mb-4">Question Review</h3>
          
          {results.map((result, index) => (
            <div key={index} className="mb-4 card" style={{ border: '1px solid #E2E8F0' }}>
              <div className="flex items-center gap-2 mb-2">
                <span style={{ 
                  display: 'inline-block', 
                  width: '24px', 
                  height: '24px', 
                  borderRadius: '50%', 
                  backgroundColor: result.isCorrect ? 'var(--success)' : 'var(--danger)',
                  color: 'white',
                  textAlign: 'center',
                  lineHeight: '24px'
                }}>
                  {result.isCorrect ? '✓' : '✗'}
                </span>
                <h4 style={{ margin: 0 }}>Question {index + 1}</h4>
              </div>
              
              <p className="mb-2" style={{ fontWeight: 500 }}>{result.question.question}</p>
              
              <div className="mb-2">
                <strong>Your answer:</strong> {result.selectedAnswer}
                {!result.isCorrect && (
                  <span> (Correct answer: {result.question.answer})</span>
                )}
              </div>
              
              {result.question.explanation && (
                <div style={{ backgroundColor: '#F8FAFC', padding: '0.75rem', borderRadius: '0.25rem' }}>
                  <strong>Explanation:</strong> {result.question.explanation}
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div className="text-center mt-4">
          <button onClick={() => setQuiz(null)} className="btn btn-primary">
            Take Another Quiz
          </button>
        </div>
      </div>
    );
  }
  
  // Active quiz
  if (quiz && quiz.questions && quiz.questions.length > 0) {
    const currentQ = quiz.questions[currentQuestion];
  
    return (
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2>Quiz: {quiz.topic}</h2>
          <div>
            Question {currentQuestion + 1} of {quiz.questions.length}
          </div>
        </div>
        
        <div className="progress-container mb-4">
          <div 
            className="progress-bar" 
            style={{ width: `${((currentQuestion + 1) / quiz.questions.length) * 100}%` }}
          ></div>
        </div>
        
        <div className="card mb-4" style={{ backgroundColor: '#F8FAFC' }}>
          <h3>{currentQ.question}</h3>
        </div>
        
        <div className="mb-4">
          {currentQ.options.map((option, index) => {
            const optionLetter = option.substring(0, 1);
            const optionText = option.substring(3);
            
            return (
              <div 
                key={index}
                onClick={() => handleAnswer(currentQuestion, optionLetter)}
                className="mb-2 p-3"
                style={{ 
                  border: `2px solid ${answers[currentQuestion] === optionLetter ? 'var(--primary)' : '#E2E8F0'}`,
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  backgroundColor: answers[currentQuestion] === optionLetter ? 'rgba(37, 99, 235, 0.1)' : 'transparent'
                }}
              >
                <div className="flex items-center gap-3">
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    border: `2px solid ${answers[currentQuestion] === optionLetter ? 'var(--primary)' : '#CBD5E1'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    color: answers[currentQuestion] === optionLetter ? 'var(--primary)' : '#64748B'
                  }}>
                    {optionLetter}
                  </div>
                  <div>{optionText}</div>
                </div>
              </div>
            );
          })}
        </div>
        
        <div className="text-right">
          <button 
            onClick={handleNext} 
            disabled={!answers[currentQuestion]}
            className="btn btn-primary"
          >
            {currentQuestion < quiz.questions.length - 1 ? 'Next Question' : 'Submit Quiz'}
          </button>
        </div>
      </div>
    );
  }
  
  return <div>Something went wrong with the quiz.</div>;
};

export default QuizInterface;