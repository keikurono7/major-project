// src/components/student/QuizInterface.jsx
import React, { useEffect, useState } from 'react';
import { modulesApi, topicsApi, quizApi } from '../../services/api';
import '../../dashboard.css';

const QuizInterface = ({ studentId }) => {
  const [loading, setLoading] = useState(false);
  const [quiz, setQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [modules, setModules] = useState([]);
  const [topics, setTopics] = useState([]);
  const [results, setResults] = useState(null);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const response = await modulesApi.getAll();
        setSubjects(response.data.subjects || []);
      } catch (error) {
        console.error('Error fetching subjects:', error);
      }
    };

    fetchSubjects();
  }, []);

  const fetchModules = async (subjectId) => {
    try {
      const response = await modulesApi.getBySubject(subjectId);
      setModules(response.data.modules || []);
    } catch (error) {
      console.error('Error fetching modules:', error);
    }
  };

  const fetchTopics = async (moduleId) => {
    try {
      const response = await topicsApi.getByModule(moduleId, studentId);
      setTopics(response.data.topics || []);
    } catch (error) {
      console.error('Error fetching topics:', error);
    }
  };

  const generateQuiz = async () => {
    setLoading(true);
    try {
      const payload = {
        student_id: studentId,
        topic_id: selectedTopic,
        num_questions: 5,
      };
      const response = await quizApi.generateQuiz(payload);
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

  const submitQuiz = async () => {
    if (!quiz) return;

    try {
      setLoading(true);

      // Submit each answer individually
      const quizResults = [];
      for (const [questionIndex, answerData] of Object.entries(answers)) {
        const selectedAnswer = answerData.selected; // Selected answer (e.g., "A")
        const correctAnswer = quiz.questions[questionIndex].answer; // Correct answer (e.g., "A")

        // Compare only the answer labels (e.g., "A", "B", "C", "D")
        const isCorrect = selectedAnswer === correctAnswer;

        quizResults.push({
          question: quiz.questions[questionIndex].question,
          selectedAnswer,
          correctAnswer,
          isCorrect,
        });

        const payload = {
          student_id: studentId,
          topic_id: quiz.topic_id,
          is_correct: isCorrect,
        };

        // Submit the response for the current question
        await quizApi.submitQuizResponse(payload);
      }

      setResults(quizResults);
      setQuizCompleted(true);
    } catch (error) {
      console.error('Error submitting quiz:', error);
      alert(`Failed to submit quiz: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (questionIndex, answer) => {
    // Extract only the answer label (e.g., "A", "B", "C", "D")
    const answerLabel = answer.split(')')[0].trim();
    setAnswers({
      ...answers,
      [questionIndex]: { selected: answerLabel },
    });
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitQuiz();
    }
  };

  const resetQuiz = () => {
    setQuiz(null);
    setCurrentQuestion(0);
    setAnswers({});
    setQuizCompleted(false);
    setSelectedSubject(null);
    setSelectedModule(null);
    setSelectedTopic(null);
    setResults(null);
  };

  const goBack = () => {
    if (selectedTopic) {
      setSelectedTopic(null);
    } else if (selectedModule) {
      setSelectedModule(null);
      setTopics([]);
    } else if (selectedSubject) {
      setSelectedSubject(null);
      setModules([]);
    }
  };

  // Quiz topic selection view
  if (!quiz && !loading) {
    return (
      <div className="card">
        <h2>Start a Quiz</h2>
        <p className="mb-4">Test your knowledge and improve your understanding</p>

        <div className="tile-container">
          {!selectedSubject && (
            <>
              <h3>Select a Subject:</h3>
              <div className="tiles">
                {subjects.map((subject) => (
                  <div
                    key={subject.id}
                    className="tile"
                    onClick={() => {
                      setSelectedSubject(subject.id);
                      fetchModules(subject.id);
                    }}
                  >
                    {subject.name}
                  </div>
                ))}
              </div>
            </>
          )}

          {selectedSubject && !selectedModule && (
            <>
              <h3>Select a Module:</h3>
              <div className="tiles">
                {modules.map((module) => (
                  <div
                    key={module.id}
                    className="tile"
                    onClick={() => {
                      setSelectedModule(module.id);
                      fetchTopics(module.id);
                    }}
                  >
                    {module.name}
                  </div>
                ))}
              </div>
              <button onClick={goBack} className="btn btn-secondary">
                Back
              </button>
            </>
          )}

          {selectedModule && !selectedTopic && (
            <>
              <h3>Select a Topic:</h3>
              <div className="tiles">
                {topics.map((topic) => (
                  <div
                    key={topic.id}
                    className="tile"
                    onClick={() => setSelectedTopic(topic.id)}
                  >
                    {topic.name}
                  </div>
                ))}
              </div>
              <button onClick={goBack} className="btn btn-secondary">
                Back
              </button>
            </>
          )}

          {selectedTopic && (
            <>
              <button onClick={generateQuiz} className="btn btn-primary">
                Start Quiz
              </button>
              <button onClick={goBack} className="btn btn-secondary">
                Back
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="card">
        <div className="text-center">
          <p>Processing...</p>
          <div className="mt-4">
            <div className="loader"></div>
          </div>
        </div>
      </div>
    );
  }

  // Quiz completed with results
  if (quizCompleted && results) {
    const correctAnswers = results.filter((r) => r.isCorrect).length;
    const totalQuestions = results.length;
    const percentage = Math.round((correctAnswers / totalQuestions) * 100);

    return (
      <div className="card">
        <h2>Quiz Results</h2>
        <p>
          You got {correctAnswers} out of {totalQuestions} correct ({percentage}%).
        </p>
        <div>
          {results.map((result, index) => (
            <div key={index} className={`quiz-result ${result.isCorrect ? 'correct' : 'incorrect'}`}>
              <p>
                <strong>Q{index + 1}:</strong> {result.question}
              </p>
              <p>
                <strong>Your Answer:</strong> {result.selectedAnswer}
              </p>
              {!result.isCorrect && (
                <p>
                  <strong>Correct Answer:</strong> {result.correctAnswer}
                </p>
              )}
            </div>
          ))}
        </div>
        <button onClick={resetQuiz} className="btn btn-secondary">
          Go to Start
        </button>
      </div>
    );
  }

  // Active quiz
  if (quiz && quiz.questions && quiz.questions.length > 0) {
    const currentQ = quiz.questions[currentQuestion];

    return (
      <div className="card">
        <h2>Quiz: {quiz.topic}</h2>
        <p id="question-text">{currentQ.question}</p>
        <div id="options-container" className="options-list">
          {currentQ.options.map((option, index) => {
            const isSelected = answers[currentQuestion]?.selected === option.split(')')[0].trim();

            return (
              <div
                key={index}
                className={`quiz-option ${isSelected ? 'selected' : ''}`}
                onClick={() => handleAnswer(currentQuestion, option)}
              >
                <div className="option-letter">{String.fromCharCode(65 + index)}</div>
                <div className="option-text">{option}</div>
              </div>
            );
          })}
        </div>
        <button onClick={handleNext} className="btn btn-primary" disabled={!answers[currentQuestion]}>
          {currentQuestion < quiz.questions.length - 1 ? 'Next Question' : 'Submit Quiz'}
        </button>
      </div>
    );
  }

  return <div>Something went wrong with the quiz.</div>;
};

export default QuizInterface;