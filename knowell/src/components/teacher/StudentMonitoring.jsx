import React, { useState, useEffect } from 'react';
import ParallaxSection from '../common/ParallaxSection';
import Card from '../common/Card';
import Button from '../common/Button';

// Note: Since the API doesn't have student monitoring endpoints, this is a mockup
// You'll need to extend the API to handle student data

const StudentMonitoring = () => {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentProgress, setStudentProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  // Mock data for demonstration
  useEffect(() => {
    // This would be replaced with an API call to get students
    const mockStudents = [
      { id: 's1', name: 'Alice Johnson', email: 'alice@example.com', lastActive: '2023-09-06' },
      { id: 's2', name: 'Bob Smith', email: 'bob@example.com', lastActive: '2023-09-05' },
      { id: 's3', name: 'Charlie Brown', email: 'charlie@example.com', lastActive: '2023-09-04' },
      { id: 's4', name: 'Diana Prince', email: 'diana@example.com', lastActive: '2023-09-03' },
    ];
    
    setTimeout(() => {
      setStudents(mockStudents);
      setLoading(false);
    }, 1000);
  }, []);

  const loadStudentProgress = (studentId) => {
    setSelectedStudent(studentId);
    setStudentProgress(null);
    
    // This would be replaced with an API call to get student progress
    setTimeout(() => {
      const mockProgress = {
        student: students.find(s => s.id === studentId),
        confidenceScores: {
          'Neural Networks': 0.8,
          'Decision Trees': 0.65,
          'Clustering': 0.4,
          'Linear Regression': 0.9,
          'Support Vector Machines': 0.3,
        },
        quizAttempts: 12,
        quizAverage: 76,
        weakestTopic: 'Support Vector Machines',
        strongestTopic: 'Linear Regression',
        recentAttempts: [
          { date: '2023-09-06', topic: 'Neural Networks', score: 85 },
          { date: '2023-09-04', topic: 'Support Vector Machines', score: 60 },
          { date: '2023-09-01', topic: 'Clustering', score: 75 },
        ]
      };
      
      setStudentProgress(mockProgress);
    }, 1000);
  };

  const filterStudents = (filterType) => {
    setFilter(filterType);
    // In a real application, you would apply filtering via API calls
  };

  return (
    <div className="student-monitoring">
      <ParallaxSection className="monitoring-header">
        <h2 className="text-2xl font-bold mb-2">Student Progress Monitoring</h2>
        <p>Track student performance and identify areas for improvement</p>
      </ParallaxSection>
      
      <div className="filter-controls mb-4 flex space-x-2">
        <Button
          type={filter === 'all' ? 'primary' : 'secondary'}
          onClick={() => filterStudents('all')}
        >
          All Students
        </Button>
        <Button
          type={filter === 'active' ? 'primary' : 'secondary'}
          onClick={() => filterStudents('active')}
        >
          Active Today
        </Button>
        <Button
          type={filter === 'struggling' ? 'primary' : 'secondary'}
          onClick={() => filterStudents('struggling')}
        >
          Needs Help
        </Button>
        <Button
          type={filter === 'excelling' ? 'primary' : 'secondary'}
          onClick={() => filterStudents('excelling')}
        >
          Excelling
        </Button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <Card title="Students">
            {loading ? (
              <p className="text-gray-500">Loading students...</p>
            ) : (
              <div className="students-list">
                {students.map(student => (
                  <div 
                    key={student.id} 
                    className={`student-item p-2 cursor-pointer border-b border-gray-200 hover:bg-gray-50 ${selectedStudent === student.id ? 'bg-blue-50' : ''}`}
                    onClick={() => loadStudentProgress(student.id)}
                  >
                    <div className="font-medium">{student.name}</div>
                    <div className="text-sm text-gray-600">{student.email}</div>
                    <div className="text-xs text-gray-500">Last active: {student.lastActive}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
        
        <div className="lg:col-span-2">
          {selectedStudent && studentProgress ? (
            <div className="grid grid-cols-1 gap-4">
              <Card title={`Progress: ${studentProgress.student.name}`}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="stat-card border border-gray-200 p-3">
                    <div className="stat-title text-gray-600 text-sm">Quiz Attempts</div>
                    <div className="stat-value text-2xl font-bold">{studentProgress.quizAttempts}</div>
                  </div>
                  <div className="stat-card border border-gray-200 p-3">
                    <div className="stat-title text-gray-600 text-sm">Average Score</div>
                    <div className="stat-value text-2xl font-bold">{studentProgress.quizAverage}%</div>
                  </div>
                  <div className="stat-card border border-gray-200 p-3">
                    <div className="stat-title text-gray-600 text-sm">Needs Help With</div>
                    <div className="stat-value text-lg font-medium">{studentProgress.weakestTopic}</div>
                  </div>
                </div>
              </Card>
              
              <Card title="Topic Confidence">
                <div className="confidence-scores">
                  {Object.entries(studentProgress.confidenceScores).map(([topic, score]) => (
                    <div key={topic} className="topic-progress mb-2">
                      <div className="flex justify-between mb-1">
                        <span>{topic}</span>
                        <span>{(score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ 
                            width: `${score * 100}%`,
                            backgroundColor: score < 0.4 ? '#e74c3c' : score < 0.7 ? '#f39c12' : '#2ecc71'
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
              
              <Card title="Recent Activity">
                <div className="recent-activity">
                  {studentProgress.recentAttempts.map((attempt, index) => (
                    <div key={index} className="activity-item border-b border-gray-200 py-2 flex justify-between">
                      <div>
                        <div className="font-medium">{attempt.topic}</div>
                        <div className="text-sm text-gray-500">{attempt.date}</div>
                      </div>
                      <div className={`score-badge ${
                        attempt.score < 60 ? 'text-red-600' : 
                        attempt.score < 80 ? 'text-yellow-600' : 
                        'text-green-600'
                      }`}>
                        {attempt.score}%
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
              
              <div className="action-buttons flex space-x-2">
                <Button fullWidth>Send Message</Button>
                <Button fullWidth type="secondary">Generate Report</Button>
              </div>
            </div>
          ) : (
            <Card>
              <div className="flex flex-col items-center justify-center p-8 text-center">
                <div className="text-gray-400 text-6xl mb-4">👨‍🎓</div>
                <h3 className="text-xl font-medium mb-2">Select a Student</h3>
                <p className="text-gray-500">
                  Click on a student from the list to view their detailed progress
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentMonitoring;