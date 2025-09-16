// src/pages/TeacherHome.jsx
import React, { useContext, useState, useEffect } from "react";
import { AuthContext } from "../contexts/AuthContext";
import Navbar from "../components/common/Navbar";
import Sidebar from "../components/common/Sidebar";
import { paperApi } from "../services/api";
import ContentUpload from "../components/teacher/ContentUpload";
import PaperGenerator from "../components/teacher/PaperGenerator";
import Analytics from "../components/teacher/Analytics";
import { useForm } from 'react-hook-form'; // Add this import
import '../dashboard.css';

// Using string icons to match your existing sidebar structure
const sidebarItems = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "content", label: "Content Upload", icon: "📁" },
  { id: "papers", label: "Question Papers", icon: "📝" },
  { id: "analytics", label: "Analytics", icon: "📈" },
  { id: "students", label: "Students", icon: "👥" }
];

const summaryStats = [
  { label: "Total Students", value: 42, icon: "👥" },
  { label: "Assignments Generated", value: 128, icon: "📝" },
  { label: "Content Files", value: 7, icon: "📁" },
  { label: "Avg. Progress", value: "76%", icon: "📈" },
];

const recentActivity = [
  { type: "Upload", desc: "Uploaded syllabus.pdf", time: "2 hours ago" },
  { type: "Assignment", desc: "Generated Assignment for Module 2", time: "5 hours ago" },
  { type: "Upload", desc: "Uploaded ML_Chapter3.pdf", time: "1 day ago" },
  { type: "Assignment", desc: "Generated Assignment for Module 1", time: "2 days ago" },
  { type: "Upload", desc: "Uploaded DataMining.pdf", time: "3 days ago" },
];

const mockStudents = [
  {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    averageScore: 85,
    weakAreas: ['Neural Networks', 'Deep Learning'],
    strongAreas: ['Data Structures', 'Algorithms']
  },
  {
    id: 2,
    name: "Jane Smith",
    email: "jane.smith@example.com",
    averageScore: 85,
    weakAreas: ["Statistics"],
    strongAreas: ["Algebra", "Calculus", "Geometry"]
  },
  {
    id: 3,
    name: "Emily Johnson",
    email: "emily.johnson@example.com",
    averageScore: 65,
    weakAreas: ["Calculus", "Statistics"],
    strongAreas: ["Algebra", "Geometry"]
  }
];

const TeacherHome = () => {
  const { currentUser } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState(null);

  const { register, handleSubmit, reset } = useForm();
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
    } catch (error) {
      console.error('Error creating subject:', error);
      alert('Failed to create subject');
    }
  };

  useEffect(() => {
    setTimeout(() => setLoading(false), 500);
  }, []);

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
              {summaryStats.map((stat, idx) => (
                <div key={idx} className="stat-card">
                  <div className="stat-icon">{stat.icon}</div>
                  <div className="stat-info">
                    <div className="stat-value">{stat.value}</div>
                    <div className="stat-label">{stat.label}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Main Content Grid */}
            <div className="content-grid">
              {/* Recent Activity */}
              <div className="card">
                <h3 className="mb-4">Recent Activity</h3>
                <div className="activity-list">
                  {recentActivity.map((item, idx) => (
                    <div key={idx} className="activity-item">
                      <div className="activity-icon">
                        {item.type === "Upload" ? "⬆️" : "📄"}
                      </div>
                      <div className="activity-content">
                        <div className="activity-title">{item.desc}</div>
                        <div className="activity-time">{item.time}</div>
                      </div>
                    </div>
                  ))}
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
                </div>
              </div>
            </div>

            {/* Student Progress */}
            <div className="card">
              <h3 className="mb-4">Student Progress Overview</h3>
              <div className="progress-chart">
                <div className="chart-placeholder">
                  <p>📊 Progress chart will be displayed here</p>
                  <p>Install 'recharts' package to see interactive charts:</p>
                  <code>npm install recharts</code>
                </div>
              </div>
            </div>
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
              <h2 className="text-2xl font-semibold mb-6">Student Performance Overview</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {mockStudents.map((student) => (
                  <div key={student.id} className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                    <div className="flex items-center space-x-4 mb-4">
                      <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-xl">{student.name[0]}</span>
                      </div>
                      <div>
                        <h3 className="font-medium">{student.name}</h3>
                        <p className="text-sm text-gray-500">{student.email}</p>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Average Score:</span>
                        <span className="font-medium">{student.averageScore}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Weak Areas:</span>
                        <span className="text-red-500">{student.weakAreas.join(', ')}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Strong Areas:</span>
                        <span className="text-green-500">{student.strongAreas.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
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
          activeItem={activeTab}
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