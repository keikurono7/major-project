// src/pages/TeacherHome.jsx
import React, { useContext, useState, useEffect } from "react";
import { AuthContext } from "../contexts/AuthContext";
import Navbar from "../components/common/Navbar";
import Sidebar from "../components/common/Sidebar";
import { paperApi } from "../services/api";
import PaperGenerator from "../components/teacher/PaperGenerator";
import Analytics from "../components/teacher/Analytics";
import { useForm } from 'react-hook-form';
import '../dashboard.css';
import StudentMonitoring from '../components/teacher/StudentMonitoring';
import { createClass, getClassesForUser } from '../services/class';
import ProjectsManagement from "../components/teacher/ProjectsManagement";
import { db, collection, getDocs, query, where } from '../services/firebase';
import { ClassHeatmap } from '../components/teacher/ClassHeatmap';
import { MarksUpload } from '../components/teacher/MarksUpload';

// Using string icons to match your existing sidebar structure
const sidebarItems = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "content", label: "Content Upload", icon: "📁" },
  { id: "projects", label: "Projects", icon: "📂" },
  { id: "papers", label: "Question Papers", icon: "📝" },
  { id: "analytics", label: "Analytics", icon: "📈" },
  { id: "students", label: "Students", icon: "👥" }
];

const TeacherHome = () => {
  const { currentUser } = useContext(AuthContext);
  const { user } = useContext(AuthContext) || {};
  const ctx = useContext(AuthContext) || {};
  const { setCurrentClassId, setClasses } = ctx;
  const [activeTab, setActiveTab] = useState("dashboard");
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState(null);
  
  // Dashboard data states
  const [dashboardStats, setDashboardStats] = useState({
    totalStudents: 0,
    totalProjects: 0,
    totalSubjects: 0,
    totalContent: 0
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [studentsList, setStudentsList] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('subject_1');

  const { register, handleSubmit, reset } = useForm();

  useEffect(() => {
    fetchDashboardData();
  }, [currentUser]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      if (!currentUser || !currentUser.id) {
        setLoading(false);
        return;
      }

      const teacherId = currentUser.id || currentUser.uid;

      // Fetch all students
      const studentsRef = collection(db, 'users');
      const studentsQuery = query(studentsRef, where('role', '==', 'student'));
      const studentsSnapshot = await getDocs(studentsQuery);
      const students = studentsSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setStudentsList(students);

      // Fetch teacher's subjects
      const subjectsRef = collection(db, 'subjects');
      const subjectsQuery = query(subjectsRef, where('teacherId', '==', teacherId));
      const subjectsSnapshot = await getDocs(subjectsQuery);
      const subjects = subjectsSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      // Fetch teacher's projects
      const projectsRef = collection(db, 'projects');
      const projectsQuery = query(projectsRef, where('creatorId', '==', teacherId));
      const projectsSnapshot = await getDocs(projectsQuery);
      const projects = projectsSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      // Fetch content/files
      const contentRef = collection(db, 'content');
      const contentQuery = query(contentRef, where('uploadedBy', '==', teacherId));
      const contentSnapshot = await getDocs(contentQuery);
      const content = contentSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      // Build recent activity
      const activity = [];
      
      // Add recent content uploads
      content.slice(-3).reverse().forEach(item => {
        activity.push({
          type: 'Upload',
          desc: `Uploaded ${item.fileName || 'file'}`,
          time: formatTimeAgo(item.createdAt)
        });
      });

      // Add recent projects
      projects.slice(-2).reverse().forEach(item => {
        activity.push({
          type: 'Project',
          desc: `Created project: ${item.title}`,
          time: formatTimeAgo(item.createdAt)
        });
      });

      // Add recent subjects
      subjects.slice(-2).reverse().forEach(item => {
        activity.push({
          type: 'Subject',
          desc: `Created subject: ${item.name}`,
          time: formatTimeAgo(item.createdAt)
        });
      });

      setRecentActivity(activity.slice(0, 5));

      // Update dashboard stats
      setDashboardStats({
        totalStudents: students.length,
        totalProjects: projects.length,
        totalSubjects: subjects.length,
        totalContent: content.length
      });

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Recently';
    
    try {
      let date;
      if (timestamp.seconds) {
        // Firebase timestamp
        date = new Date(timestamp.seconds * 1000);
      } else if (typeof timestamp === 'string') {
        date = new Date(timestamp);
      } else {
        return 'Recently';
      }

      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} minutes ago`;
      if (diffHours < 24) return `${diffHours} hours ago`;
      if (diffDays < 7) return `${diffDays} days ago`;
      return date.toLocaleDateString();
    } catch (error) {
      console.error('Error formatting time:', error);
      return 'Recently';
    }
  };

  const onSubmit = async (data) => {
    try {
      if (!file) {
        alert('Please select a PDF file');
        return;
      }
      
      // Create form data
      const formData = new FormData();
      formData.append('subjectName', data.subjectName);
      formData.append('teacherId', data.teacherId);
      formData.append('pdfFile', file);
      
      // Handle the upload
      await handlePdfUpload(formData);
      
      // Reset form
      reset();
      setFile(null);
      fetchDashboardData(); // Refresh dashboard
    } catch (error) {
      console.error('Error creating subject:', error);
      alert('Failed to create subject');
    }
  };

  const handlePdfUpload = async (file) => {
    try {
      await paperApi.uploadPdf(file);
      alert("PDF uploaded successfully");
    } catch (error) {
      console.error("Error uploading PDF:", error);
      alert("Failed to upload PDF");
    }
  };

  const handleGeneratePaper = async (data) => {
    try {
      const response = await paperApi.generatePaper(data);
      setPapers([...papers, response.data]);
      alert("Question paper generation started");
    } catch (error) {
      console.error("Error generating paper:", error);
      alert("Failed to generate question paper");
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      alert('Please select a valid PDF file');
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="loading">
          <div>Loading...</div>
        </div>
      );
    }

    switch (activeTab) {
      case "dashboard":
        return (
          <>
            {/* Welcome Card */}
            <div className="card">
              <h2>Welcome back, {currentUser.fullName}!</h2>
              <p>Here's what's happening with your classes today.</p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">👥</div>
                <div className="stat-info">
                  <div className="stat-value">{dashboardStats.totalStudents}</div>
                  <div className="stat-label">Total Students</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📝</div>
                <div className="stat-info">
                  <div className="stat-value">{dashboardStats.totalProjects}</div>
                  <div className="stat-label">Projects Created</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📁</div>
                <div className="stat-info">
                  <div className="stat-value">{dashboardStats.totalContent}</div>
                  <div className="stat-label">Content Files</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📚</div>
                <div className="stat-info">
                  <div className="stat-value">{dashboardStats.totalSubjects}</div>
                  <div className="stat-label">Subjects</div>
                </div>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="content-grid">
              {/* Recent Activity */}
              <div className="card">
                <h3 className="mb-4">Recent Activity</h3>
                <div className="activity-list">
                  {recentActivity.length > 0 ? (
                    recentActivity.map((item, idx) => (
                      <div key={idx} className="activity-item">
                        <div className="activity-icon">
                          {item.type === "Upload" ? "⬆️" : item.type === "Project" ? "📂" : "📚"}
                        </div>
                        <div className="activity-content">
                          <div className="activity-title">{item.desc}</div>
                          <div className="activity-time">{item.time}</div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: '#6b7280', textAlign: 'center', padding: '2rem' }}>
                      No recent activity
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="card">
                <h3 className="mb-4">Quick Actions</h3>
                <div className="quick-actions">
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("content")}
                  >
                    <span>📁</span>
                    Upload Content
                  </button>
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("papers")}
                  >
                    <span>📝</span>
                    Generate Paper
                  </button>
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("analytics")}
                  >
                    <span>📈</span>
                    View Analytics
                  </button>
                  <button 
                    className="btn btn-primary action-btn"
                    onClick={() => setActiveTab("projects")}
                  >
                    <span>📂</span>
                    Manage Projects
                  </button>
                </div>
              </div>
            </div>

            {/* Top Students */}
            {studentsList.length > 0 && (
              <div className="card">
                <h3 className="mb-4">Students Overview</h3>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', 
                  gap: '1rem' 
                }}>
                  {studentsList.slice(0, 6).map((student) => (
                    <div key={student.id} className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-10 h-10 rounded-full bg-blue-200 flex items-center justify-center text-sm font-bold">
                          {(student.full_name || student.fullName || 'S').split(' ')[0][0].toUpperCase()}
                        </div>
                        <div>
                          <h4 className="font-medium text-sm">{student.full_name || student.fullName || 'Unknown'}</h4>
                          <p className="text-xs text-gray-500">{student.email}</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600">Status: <span className="text-green-600">Active</span></p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        );

      case "content":
        return (
          <div className="card p-6 max-w-4xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">Create New Subject</h2>
            
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="form-group">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject Name
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter subject name"
                  required
                  {...register('subjectName')}
                />
              </div>

              <div className="form-group">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Teacher ID
                </label>
                <input
                  {...register('teacherId')}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={currentUser.id}
                  disabled
                />
              </div>

              <div className="form-group">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Study Material (PDF)
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg">
                  <div className="space-y-1 text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500">
                        <span>Upload a file</span>
                        <input 
                          {...register('pdfFile')}
                          type="file" 
                          className="sr-only" 
                          accept=".pdf" 
                          onChange={(e) => {
                            handleFileChange(e);
                            register('pdfFile').onChange(e);
                          }} 
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">PDF up to 10MB</p>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Create Subject
              </button>
            </form>
          </div>
        );
        
      case "papers":
        return <PaperGenerator onGenerate={handleGeneratePaper} />;
        
      case "analytics":
        return <Analytics />;
        
      case "students":
        return (
          <div className="space-y-6">
            <div className="card p-6">
              <h2 className="text-2xl font-semibold mb-6">All Students</h2>
              
              {studentsList.length === 0 ? (
                <div className="text-center p-8 text-gray-500">
                  <p>No students available yet</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {studentsList.map((student) => (
                    <div key={student.id} className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                      <div className="flex items-center space-x-4 mb-4">
                        <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-lg font-bold">
                          {(student.full_name || student.fullName || 'S').split(' ')[0][0].toUpperCase()}
                        </div>
                        <div>
                          <h3 className="font-medium">{student.full_name || student.fullName || 'Unknown'}</h3>
                          <p className="text-sm text-gray-500">{student.email}</p>
                        </div>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Status:</span>
                          <span className="text-green-600 font-medium">Active</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Role:</span>
                          <span className="text-gray-600">{student.role || 'Student'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Joined:</span>
                          <span className="text-gray-600">{formatTimeAgo(student.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 'projects':
        return <ProjectsManagement teacherId={currentUser.id} />;
        
      case 'overview':
        return (
          <ClassHeatmap subjectId={selectedSubject} />
        );
        
      case 'marks':
        return (
          <MarksUpload subjectId={selectedSubject} />
        );
        
      default:
        return (
          <div className="card">
            <p>Select an option from the sidebar</p>
          </div>
        );
    }
  };

  return (
    <div className="page">
      <Navbar user={currentUser} />
      
      <div className="dashboard">
        <Sidebar 
          items={sidebarItems}
          activeTab={activeTab}
          onItemClick={setActiveTab}
        />
        
        <div className="main-content">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default TeacherHome;