import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import { assignmentApi, topicsApi, modulesApi } from '../../services/api';
import ParallaxSection from '../common/ParallaxSection';
import Card from '../common/Card';
import Button from '../common/Button';

const AssignmentInterface = () => {
  const { currentUser } = useContext(AuthContext);
  // State for selection flow
  const [subjects, setSubjects] = useState([]);
  const [modules, setModules] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [selectedTopics, setSelectedTopics] = useState([]);
  
  // State for assignments
  const [assignment, setAssignment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeQuestion, setActiveQuestion] = useState(0);
  const [numQuestions, setNumQuestions] = useState(5);

  // Fetch subjects on component mount
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

  // Fetch modules when subject is selected
  const fetchModules = async (subjectId) => {
    try {
      const response = await modulesApi.getBySubject(subjectId);
      setModules(response.data.modules || []);
    } catch (error) {
      console.error('Error fetching modules:', error);
    }
  };

  // Fetch topics when module is selected
  const fetchTopics = async (moduleId) => {
    try {
      const response = await topicsApi.getByModule(moduleId, currentUser.id);
      setTopics(response.data.topics || []);
    } catch (error) {
      console.error('Error fetching topics:', error);
    }
  };

  // Handle topic selection/deselection - always handle as multi-select
  const handleTopicSelect = (topic) => {
    if (selectedTopics.includes(topic.name)) {
      setSelectedTopics(selectedTopics.filter(name => name !== topic.name));
    } else {
      setSelectedTopics([...selectedTopics, topic.name]);
    }
  };

  // Go back in the selection flow
  const goBack = () => {
    if (selectedTopics.length > 0) {
      setSelectedTopics([]);
    } else if (selectedModule) {
      setSelectedModule(null);
      setTopics([]);
    } else if (selectedSubject) {
      setSelectedSubject(null);
      setModules([]);
    }
  };

  // Generate assignment with selected topics
  const generateAssignment = async () => {
    if (selectedTopics.length === 0) {
      alert('Please select at least one topic');
      return;
    }

    setIsLoading(true);
    try {
      const response = await assignmentApi.generateAssignment({
        subject_id: selectedSubject,
        topics: selectedTopics,
        num_questions: numQuestions,
        student_id: currentUser.id
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

  // Reset assignment and selection
  const resetAssignment = () => {
    setAssignment(null);
    setSelectedSubject(null);
    setSelectedModule(null);
    setSelectedTopics([]);
    setAnswers({});
    setFeedback({});
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

  // Assignment generation form with tile-based selection
  if (!assignment) {
    return (
      <div className="assignment-interface">
        <ParallaxSection className="assignment-header">
          <h2 className="text-2xl font-bold mb-4">Practice Assignments</h2>
          <p>Complete assignments to deepen your understanding of key concepts</p>
        </ParallaxSection>
        
        <Card>
          <h2>Create Assignment</h2>
          <p className="mb-4">Select topics and generate questions to practice</p>
          
          <div className="mb-4">
            <label className="block mb-1 font-medium">Number of Questions:</label>
            <input
              type="number"
              min="1"
              max="10"
              value={numQuestions}
              onChange={(e) => setNumQuestions(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
              className="w-24 p-2 border border-gray-300"
            />
          </div>

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

            {selectedModule && (
              <>
                <h3>Select Topics:</h3>
                <div className="tiles">
                  {topics.map((topic) => (
                    <div
                      key={topic.id}
                      className={`tile ${selectedTopics.includes(topic.name) ? 'selected' : ''}`}
                      onClick={() => handleTopicSelect(topic)}
                    >
                      {selectedTopics.includes(topic.name) && (
                        <span className="checkmark">✓</span>
                      )}
                      {topic.name}
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <button onClick={generateAssignment} className="btn btn-primary" disabled={selectedTopics.length === 0}>
                    Generate Assignment
                  </button>
                  <button onClick={goBack} className="btn btn-secondary ml-2">
                    Back
                  </button>
                </div>
              </>
            )}
          </div>
        </Card>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="card">
        <div className="text-center">
          <p>Generating your assignment...</p>
          <div className="mt-4">
            <div className="loader"></div>
          </div>
        </div>
      </div>
    );
  }

  // Assignment display (existing code)
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
          
          {activeQuestion === assignment.length - 1 ? (
            <Button onClick={resetAssignment} type="secondary">
              Finish Assignment
            </Button>
          ) : (
            <Button 
              onClick={handleNext}
              disabled={activeQuestion === assignment.length - 1}
            >
              Next Question
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};

export default AssignmentInterface;