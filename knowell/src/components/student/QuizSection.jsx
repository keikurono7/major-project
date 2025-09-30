import React, { useState } from 'react';
import { modulesApi, topicsApi } from '../../services/api';
import '../../dashboard.css';

const QuizSection = ({ currentUser }) => {
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [modules, setModules] = useState([]);
  const [topics, setTopics] = useState([]);

  // Fetch subjects when the component is mounted
  React.useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const subjectsRes = await modulesApi.getAll();
        setSubjects(subjectsRes.data.subjects || []);
      } catch (error) {
        console.error("Error fetching subjects:", error);
      }
    };

    fetchSubjects();
  }, []);

  const handleSubjectChange = async (subjectId) => {
    setSelectedSubject(subjectId);
    setSelectedModule(null);
    setSelectedTopic(null);
    setModules([]);
    setTopics([]);

    try {
      const modulesRes = await modulesApi.getBySubject(subjectId);
      setModules(modulesRes.data.modules || []);
    } catch (error) {
      console.error("Error fetching modules:", error);
    }
  };

  const handleModuleChange = async (moduleId) => {
    setSelectedModule(moduleId);
    setSelectedTopic(null);
    setTopics([]);

    try {
      const topicsRes = await topicsApi.getByModule(moduleId, currentUser.id);
      setTopics(topicsRes.data.topics || []);
    } catch (error) {
      console.error("Error fetching topics:", error);
    }
  };

  const handleStartQuiz = () => {
    if (!selectedTopic) {
      alert("Please select a topic to start the quiz.");
      return;
    }

    // Logic to start the quiz for the selected topic
    console.log(`Starting quiz for topic: ${selectedTopic}`);
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4">Take a Quiz</h2>
      <p className="text-gray-600 mb-6">Select a subject, module, and topic to start a quiz.</p>

      {/* Subject Selection */}
      <div className="form-group mb-4">
        <label className="form-label block text-sm font-medium text-gray-700 mb-2">Select Subject:</label>
        <select
          className="form-control w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
          value={selectedSubject || ''}
          onChange={(e) => handleSubjectChange(e.target.value)}
        >
          <option value="">-- Select a Subject --</option>
          {subjects.map((subject) => (
            <option key={subject.id} value={subject.id}>
              {subject.name}
            </option>
          ))}
        </select>
      </div>

      {/* Module Selection */}
      {selectedSubject && (
        <div className="form-group mb-4">
          <label className="form-label block text-sm font-medium text-gray-700 mb-2">Select Module:</label>
          <select
            className="form-control w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            value={selectedModule || ''}
            onChange={(e) => handleModuleChange(e.target.value)}
          >
            <option value="">-- Select a Module --</option>
            {modules.map((module) => (
              <option key={module.id} value={module.id}>
                {module.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Topic Selection */}
      {selectedModule && (
        <div className="form-group mb-4">
          <label className="form-label block text-sm font-medium text-gray-700 mb-2">Select Topic:</label>
          <select
            className="form-control w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            value={selectedTopic || ''}
            onChange={(e) => setSelectedTopic(e.target.value)}
          >
            <option value="">-- Select a Topic --</option>
            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
                {topic.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Start Quiz Button */}
      {selectedTopic && (
        <button
          className="btn btn-primary w-full py-2 px-4 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          onClick={handleStartQuiz}
        >
          Start Quiz
        </button>
      )}
    </div>
  );
};

export default QuizSection;