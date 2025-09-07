import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import { assignmentApi, topicsApi } from '../../services/api';
import ParallaxSection from '../common/ParallaxSection';
import Card from '../common/Card';
import Button from '../common/Button';

const AssignmentInterface = () => {
  const { currentUser } = useContext(AuthContext);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [assignment, setAssignment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [isMultiTopic, setIsMultiTopic] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeQuestion, setActiveQuestion] = useState(0);

  // Fetch available topics
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

  const generateAssignment = async () => {
    setIsLoading(true);
    try {
      const response = await assignmentApi.generateAssignment({
        student_id: currentUser.id,
        topic: selectedTopic,
        use_weakest: !selectedTopic,
        multi_topic: isMultiTopic
      });
      
      setAssignment(response.data.questions);
      setAnswers({}); // Reset answers
      setFeedback({}); // Reset feedback
    } catch (error) {
      console.error('Error generating assignment:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerChange = (questionIndex, value) => {
    setAnswers({
      ...answers,
      [questionIndex]: value
    });
  };

  const submitAnswer = async (questionIndex) => {
    if (!answers[questionIndex] || answers[questionIndex].trim() === '') return;
    
    setIsSubmitting(true);
    try {
      const question = assignment[questionIndex];
      const response = await assignmentApi.evaluateAnswer(
        currentUser.id,
        questionIndex,
        answers[questionIndex]
      );
      
      setFeedback({
        ...feedback,
        [questionIndex]: response.data
      });
    } catch (error) {
      console.error('Error submitting answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = () => {
    if (activeQuestion < assignment.length - 1) {
      setActiveQuestion(activeQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (activeQuestion > 0) {
      setActiveQuestion(activeQuestion - 1);
    }
  };

  // Assignment generation form
  if (!assignment) {
    return (
      <div className="assignment-interface">
        <ParallaxSection className="assignment-header">
          <h2 className="text-2xl font-bold mb-4">Practice Assignments</h2>
          <p>Complete assignments to deepen your understanding of key concepts</p>
        </ParallaxSection>
        
        <Card title="Generate New Assignment">
          <div className="mb-4">
            <label className="block mb-1 font-medium">Assignment Type:</label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  checked={!isMultiTopic}
                  onChange={() => setIsMultiTopic(false)}
                  className="mr-2"
                />
                Single Topic
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  checked={isMultiTopic}
                  onChange={() => setIsMultiTopic(true)}
                  className="mr-2"
                />
                Multiple Topics (Covers your weakest areas)
              </label>
            </div>
          </div>
          
          {!isMultiTopic && (
            <div className="mb-4">
              <label className="block mb-1 font-medium">Select Topic:</label>
              <select
                value={selectedTopic || ''}
                onChange={e => setSelectedTopic(e.target.value || null)}
                className="w-full p-2 border border-gray-300"
              >
                <option value="">Use my weakest topic</option>
                {topics.map(topic => (
                  <option key={topic} value={topic}>{topic}</option>
                ))}
              </select>
            </div>
          )}
          
          <Button
            onClick={generateAssignment}
            disabled={isLoading}
            fullWidth
          >
            {isLoading ? 'Generating...' : 'Generate Assignment'}
          </Button>
        </Card>
      </div>
    );
  }

  // Assignment display
  const currentQuestion = assignment[activeQuestion];
  const hasFeedback = feedback[activeQuestion];

  return (
    <div className="assignment-interface">
      <div className="assignment-progress mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-bold">Assignment Progress</h3>
          <span>{activeQuestion + 1} of {assignment.length}</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${((activeQuestion + 1) / assignment.length) * 100}%` }}
          ></div>
        </div>
      </div>
      
      <Card>
        <div className="topic-tag mb-2 inline-block bg-gray-100 px-2 py-1">
          {currentQuestion.topic}
        </div>
        <h3 className="text-xl font-medium mb-4">{currentQuestion.question}</h3>
        
        <div className="mb-4">
          <label className="block mb-2 font-medium">Your Answer:</label>
          <textarea
            value={answers[activeQuestion] || ''}
            onChange={(e) => handleAnswerChange(activeQuestion, e.target.value)}
            placeholder="Type your answer here..."
            className="w-full p-2 border border-gray-300 h-32"
            disabled={hasFeedback}
          />
        </div>
        
        {!hasFeedback ? (
          <Button 
            onClick={() => submitAnswer(activeQuestion)}
            disabled={isSubmitting || !answers[activeQuestion]}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Answer'}
          </Button>
        ) : (
          <div className="feedback-section border-t border-gray-300 pt-4 mt-4">
            <h4 className="font-medium mb-2">Feedback:</h4>
            <div className="score-indicator mb-2">
              Score: {Math.round(feedback[activeQuestion].score * 100)}%
            </div>
            <p>{feedback[activeQuestion].feedback}</p>
            
            {feedback[activeQuestion].keyword_matches.length > 0 && (
              <div className="mt-2">
                <h5 className="font-medium">Key concepts covered:</h5>
                <ul className="list-disc pl-5">
                  {feedback[activeQuestion].keyword_matches.map((keyword, i) => (
                    <li key={i}>{keyword}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {feedback[activeQuestion].keyword_misses.length > 0 && (
              <div className="mt-2">
                <h5 className="font-medium">Missing key concepts:</h5>
                <ul className="list-disc pl-5 text-red-600">
                  {feedback[activeQuestion].keyword_misses.map((keyword, i) => (
                    <li key={i}>{keyword}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        <div className="navigation-buttons mt-6 flex justify-between">
          <Button 
            type="secondary" 
            onClick={handlePrevious}
            disabled={activeQuestion === 0}
          >
            Previous
          </Button>
          
          <Button 
            onClick={handleNext}
            disabled={activeQuestion === assignment.length - 1}
          >
            Next Question
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AssignmentInterface;