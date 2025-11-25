import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import Card from '../common/Card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { db, collection, getDocs, query, where, doc, getDoc } from '../../services/firebase';
import { analyticsApi } from '../../services/api';

const Analytics = () => {
  const { currentUser } = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);
  const [allStudentsData, setAllStudentsData] = useState([]);
  const [llmInsights, setLlmInsights] = useState('');
  const [llmLoading, setLlmLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  
  useEffect(() => {
    if (currentUser && currentUser.id) {
      fetchSubjects();
    }
  }, [currentUser]);

  useEffect(() => {
    if (selectedSubjectId && allStudentsData.length > 0) {
      processAnalyticsForSubject(selectedSubjectId);
    }
  }, [selectedSubjectId, allStudentsData]);

  const fetchSubjects = async () => {
    try {
      setLoading(true);

      const teacherId = currentUser.id || currentUser.uid;
      
      if (!teacherId) {
        console.error('Teacher ID not found');
        setLoading(false);
        return;
      }

      // Fetch ALL subjects
      const subjectsRef = collection(db, 'subjects');
      const subjectsSnapshot = await getDocs(subjectsRef);
      const subjectsList = subjectsSnapshot.docs
        .map(doc => ({ id: doc.id, ...doc.data() }));

      console.log('All subjects fetched:', subjectsList.length);
      setSubjects(subjectsList);

      if (subjectsList.length > 0) {
        setSelectedSubjectId(subjectsList[0].id);
      }

      // Fetch all students
      const studentsRef = collection(db, 'users');
      const studentsQuery = query(studentsRef, where('role', '==', 'student'));
      const studentsSnapshot = await getDocs(studentsQuery);
      const studentsList = studentsSnapshot.docs
        .map(doc => ({ id: doc.id, ...doc.data() }));

      console.log('Students fetched:', studentsList.length);

      // Fetch mastery data for all students
      const studentsMasteryData = [];
      for (const student of studentsList) {
        try {
          const studentDocRef = doc(db, 'users', student.id);
          const studentDocSnap = await getDoc(studentDocRef);
          
          if (studentDocSnap.exists()) {
            const studentData = studentDocSnap.data();
            studentsMasteryData.push({
              id: student.id,
              mastery_summary: studentData.mastery_summary || {}
            });
          }
        } catch (error) {
          console.log(`Error fetching data for student ${student.id}:`, error);
        }
      }

      setAllStudentsData(studentsMasteryData);

    } catch (error) {
      console.error('Error fetching subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  const processAnalyticsForSubject = async (subjectId) => {
    try {
      // Fetch all projects
      const projectsRef = collection(db, 'projects');
      const projectsSnapshot = await getDocs(projectsRef);
      const projects = projectsSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      const submissionsRef = collection(db, 'project_submissions');
      const submissionsSnapshot = await getDocs(submissionsRef);
      const submissions = submissionsSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      // Collect raw BKT data for the subject
      const topicBKTData = {};
      let totalBKTDataPoints = 0;

      console.log('Processing subject:', subjectId);
      console.log('Total students with data:', allStudentsData.length);

      for (const studentData of allStudentsData) {
        try {
          const masterySummary = studentData.mastery_summary || {};
          const subjectTopics = masterySummary[subjectId] || {};

          if (typeof subjectTopics === 'object' && Object.keys(subjectTopics).length > 0) {
            Object.entries(subjectTopics).forEach(([topicKey, topicData]) => {
              const bktScore = Number(topicData.mastery || 0);

              if (!topicBKTData[topicKey]) {
                topicBKTData[topicKey] = {
                  topicName: topicData.topic_name || 'Unknown Topic',
                  subjectName: topicData.subject_name || 'Unknown Subject',
                  moduleName: topicData.module_name || 'Unknown Module',
                  scores: [],
                  students: []
                };
              }
              topicBKTData[topicKey].scores.push(bktScore);
              topicBKTData[topicKey].students.push(studentData.id);
              totalBKTDataPoints++;
            });
          }
        } catch (error) {
          console.log(`Error processing data for student ${studentData.id}:`, error);
        }
      }

      console.log('Raw BKT Data:', topicBKTData);
      console.log('Total BKT Data Points:', totalBKTDataPoints);

      // Prepare data for display (simple aggregation without insights)
      const topicPerformance = Object.entries(topicBKTData)
        .map(([topicId, topicData]) => {
          const avgBKT = topicData.scores.length > 0 
            ? topicData.scores.reduce((sum, score) => sum + score, 0) / topicData.scores.length
            : 0;
          
          return {
            id: topicId,
            topic: topicData.topicName.substring(0, 35),
            fullTopic: topicData.topicName,
            avgScore: Math.round(avgBKT * 100),
            studentCount: topicData.scores.length,
            subjectName: topicData.subjectName,
            moduleName: topicData.moduleName
          };
        })
        .sort((a, b) => a.avgScore - b.avgScore);

      // Calculate assignment completion
      const totalAssignments = projects.length > 0 ? projects.length * allStudentsData.length : 1;
      const completedAssignments = submissions.filter(s => s.status === 'submitted').length;
      const assignmentCompletionRate = totalAssignments > 0
        ? Math.round((completedAssignments / totalAssignments) * 100)
        : 0;

      const allBKTScores = Object.values(topicBKTData)
        .flatMap(t => t.scores);
      const avgBKT = allBKTScores.length > 0
        ? Math.round((allBKTScores.reduce((sum, score) => sum + score, 0) / allBKTScores.length) * 100)
        : 0;

      const selectedSubject = subjects.find(s => s.id === subjectId);

      setAnalyticsData({
        topicPerformance: topicPerformance,
        rawBKTData: topicBKTData,
        quizCompletionRate: avgBKT,
        assignmentCompletionRate,
        totalStudents: allStudentsData.length,
        totalProjects: projects.length,
        totalSubjects: subjects.length,
        totalBKTDataPoints,
        subjectName: selectedSubject?.name || 'Unknown Subject'
      });

      // Automatically fetch LLM insights
      fetchLLMInsights(topicBKTData, selectedSubject?.name || 'Unknown Subject', allStudentsData.length);

    } catch (error) {
      console.error('Error processing analytics:', error);
    }
  };

  const fetchLLMInsights = async (bktData, subjectName, totalStudents) => {
    try {
      setLlmLoading(true);

      // Call backend API directly
      const response = await teacherAnalyticsApi.getBKTInsights(
        currentUser.id,
        selectedSubjectId,
        bktData,
        totalStudents,
        subjectName
      );

      setLlmInsights(response.insights || response.response);
      setChatMessages([{
        role: 'assistant',
        content: response.insights || response.response
      }]);
    } catch (error) {
      console.error('Error fetching LLM insights:', error);
      setLlmInsights('Unable to fetch insights. Please try again.');
    } finally {
      setLlmLoading(false);
    }
  };

  const handleChatMessage = async (message = chatInput) => {
    if (!message.trim() || !selectedSubjectId) return;

    const userMessage = {
      role: 'user',
      content: message
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const cleanHistory = chatMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await teacherAnalyticsApi.chatWithTeacherAssistant(
        currentUser.id,
        selectedSubjectId,
        message,
        analyticsData?.rawBKTData,
        cleanHistory
      );

      const assistantMessage = {
        role: 'assistant',
        content: response.response || response.message
      };
      setChatMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const COLORS = ['#ca404f', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'];
  
  if (loading) {
    return (
      <div className="analytics-loading p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-primary-600"></div>
        <p className="mt-4 text-gray-600">Loading analytics data...</p>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-600">No analytics data available</p>
      </div>
    );
  }
  
  return (
    <div className="analytics p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold mb-2">Analytics Dashboard</h2>
            <p className="text-gray-600">Track student performance with AI-powered insights</p>
          </div>
          
          {/* Subject Dropdown */}
          <div className="flex items-center gap-3">
            <label className="font-semibold text-gray-700">Select Subject:</label>
            <select 
              value={selectedSubjectId || ''}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 bg-white cursor-pointer"
            >
              <option value="">-- Choose Subject --</option>
              {subjects.map(subject => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow-lg">
            <div className="text-4xl mb-2">👥</div>
            <div className="text-3xl font-bold">{analyticsData.totalStudents}</div>
            <div className="text-blue-100">Total Students</div>
          </div>
          
          <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow-lg">
            <div className="text-4xl mb-2">📚</div>
            <div className="text-3xl font-bold">{analyticsData.totalSubjects}</div>
            <div className="text-green-100">All Subjects</div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow-lg">
            <div className="text-4xl mb-2">📁</div>
            <div className="text-3xl font-bold">{analyticsData.totalProjects}</div>
            <div className="text-purple-100">Projects</div>
          </div>
          
          <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-6 rounded-lg shadow-lg">
            <div className="text-4xl mb-2">✅</div>
            <div className="text-3xl font-bold">{analyticsData.totalBKTDataPoints}</div>
            <div className="text-orange-100">Topics Evaluated</div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card title="Performance Metrics">
            <div className="completion-rates space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="font-medium">Avg BKT Score</span>
                  <span className="font-bold text-blue-600">{analyticsData.quizCompletionRate}%</span>
                </div>
                <div className="progress-bar bg-gray-200 h-4 rounded-full overflow-hidden">
                  <div 
                    className="progress-fill bg-blue-500 h-full transition-all duration-500" 
                    style={{ width: `${analyticsData.quizCompletionRate}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className="font-medium">Assignment Completion</span>
                  <span className="font-bold text-green-600">{analyticsData.assignmentCompletionRate}%</span>
                </div>
                <div className="progress-bar bg-gray-200 h-4 rounded-full overflow-hidden">
                  <div 
                    className="progress-fill bg-green-500 h-full transition-all duration-500" 
                    style={{ width: `${analyticsData.assignmentCompletionRate}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </Card>

          {/* AI Insights */}
          <Card title="🤖 AI Insights">
            {llmLoading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full"></div>
                <p className="text-gray-600">Analyzing BKT data...</p>
              </div>
            ) : (
              <div style={{ fontSize: '0.9rem', lineHeight: '1.6', color: '#374151', maxHeight: '300px', overflowY: 'auto' }}>
                {llmInsights ? (
                  llmInsights.split('\n').map((line, idx) => (
                    <p key={idx} style={{ marginBottom: '0.5rem' }}>{line}</p>
                  ))
                ) : (
                  <p>No insights available</p>
                )}
              </div>
            )}
          </Card>
        </div>

        {/* Topic Performance Chart */}
        <Card className="mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="text-2xl mr-2">📊</span>
            Topic Performance (BKT) - {analyticsData.subjectName}
          </h3>
          {analyticsData.topicPerformance && analyticsData.topicPerformance.length > 0 ? (
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={analyticsData.topicPerformance}
                  margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="topic" 
                    angle={-45} 
                    textAnchor="end" 
                    height={150}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis domain={[0, 100]} label={{ value: 'BKT Score (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Bar dataKey="avgScore" fill="#ca404f" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center p-8 text-gray-500">No topic data available</div>
          )}
        </Card>

        {/* Chat with AI Assistant */}
        <Card title="💬 Ask AI Assistant About Your Class">
          <div style={{ 
            border: '1px solid #e5e7eb', 
            borderRadius: '8px', 
            height: '400px', 
            display: 'flex', 
            flexDirection: 'column',
            backgroundColor: '#f9fafb'
          }}>
            {/* Chat Messages */}
            <div style={{ 
              flex: 1, 
              padding: '1rem', 
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem'
            }}>
              {chatMessages.map((msg, idx) => (
                <div key={idx} style={{ 
                  backgroundColor: msg.role === 'user' ? '#e1f5fe' : 'white', 
                  padding: '0.75rem', 
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  maxWidth: '85%',
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    fontWeight: 600, 
                    marginBottom: '0.25rem', 
                    color: msg.role === 'user' ? '#01579b' : '#ca404f' 
                  }}>
                    {msg.role === 'user' ? 'You' : 'AI Assistant'}
                  </div>
                  <div style={{ fontSize: '0.9rem', lineHeight: '1.5', color: '#1f2937', whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div style={{ alignSelf: 'flex-start', color: '#6b7280', fontSize: '0.9rem' }}>
                  ✍️ Thinking...
                </div>
              )}
            </div>
            
            {/* Chat Input */}
            <div style={{ 
              padding: '1rem', 
              borderTop: '1px solid #e5e7eb',
              backgroundColor: 'white',
              display: 'flex',
              gap: '0.5rem'
            }}>
              <input
                type="text"
                placeholder="Ask about class performance, recommendations, etc..."
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
                  if (e.key === 'Enter' && !isChatLoading) {
                    handleChatMessage();
                  }
                }}
                disabled={isChatLoading}
              />
              <button
                onClick={() => handleChatMessage()}
                disabled={isChatLoading || !chatInput.trim()}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: isChatLoading || !chatInput.trim() ? '#d1d5db' : '#ca404f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: isChatLoading ? 'not-allowed' : 'pointer',
                  fontWeight: 600
                }}
              >
                Send
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;