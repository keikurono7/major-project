import React, { useState, useEffect } from 'react';
import { getTeacherProjects, getProjectSubmissions, deleteProject } from '../../services/projectService';
import ProjectSubmissionReview from './ProjectSubmissionReview';
import ProjectCreation from './ProjectCreation';

const ProjectsManagement = ({ teacherId }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [viewingSubmissions, setViewingSubmissions] = useState(false);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchProjects();
  }, [teacherId]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await getTeacherProjects(teacherId);
      setProjects(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewSubmissions = async (project) => {
    try {
      setSelectedProject(project);
      const subs = await getProjectSubmissions(project.id);
      setSubmissions(subs);
      setViewingSubmissions(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        setDeletingId(projectId);
        await deleteProject(projectId);
        setProjects(projects.filter(p => p.id !== projectId));
      } catch (err) {
        setError(err.message);
      } finally {
        setDeletingId(null);
      }
    }
  };

  const handleProjectCreated = (newProject) => {
    setProjects([...projects, newProject]);
    setShowCreateProject(false);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
        <div style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</div>
        <p style={{ marginTop: '0.5rem' }}>Loading projects...</p>
      </div>
    );
  }

  if (viewingSubmissions && selectedProject) {
    return (
      <ProjectSubmissionReview
        project={selectedProject}
        submissions={submissions}
        onBack={() => setViewingSubmissions(false)}
      />
    );
  }

  if (showCreateProject) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <button
          onClick={() => setShowCreateProject(false)}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#f3f4f6',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            color: '#6b7280',
            fontSize: '0.875rem',
            fontWeight: '500',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            width: 'fit-content'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#e5e7eb';
            e.currentTarget.style.color = '#374151';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#f3f4f6';
            e.currentTarget.style.color = '#6b7280';
          }}
        >
          ← Back to Projects
        </button>
        <ProjectCreation 
          teacherId={teacherId} 
          onProjectCreated={handleProjectCreated}
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem'
      }}>
        <h2 style={{ fontSize: '1.875rem', fontWeight: '700', color: '#1f2937' }}>
          📚 My Projects
        </h2>
        <button
          onClick={() => setShowCreateProject(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            backgroundColor: '#ca404f',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '0.875rem',
            transition: 'all 0.2s',
            boxShadow: '0 4px 6px rgba(202, 64, 79, 0.2)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#b0303f';
            e.currentTarget.style.boxShadow = '0 8px 12px rgba(202, 64, 79, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#ca404f';
            e.currentTarget.style.boxShadow = '0 4px 6px rgba(202, 64, 79, 0.2)';
          }}
        >
          ➕ Create New Project
        </button>
      </div>

      {error && (
        <div style={{
          marginBottom: '1rem',
          padding: '1rem',
          backgroundColor: '#fee2e2',
          border: '2px solid #fca5a5',
          borderRadius: '8px',
          color: '#991b1b'
        }}>
          ⚠️ {error}
        </div>
      )}

      {projects.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '2rem',
          backgroundColor: '#f9fafb',
          border: '2px dashed #e5e7eb',
          borderRadius: '8px'
        }}>
          <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</p>
          <p style={{ color: '#6b7280', fontWeight: '500', marginBottom: '1rem' }}>
            No projects created yet
          </p>
          <button
            onClick={() => setShowCreateProject(true)}
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: '#ca404f',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.875rem',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#b0303f'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ca404f'}
          >
            Create your first project
          </button>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '1.5rem'
        }}>
          {projects.map(project => (
            <div
              key={project.id}
              style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '2px solid #e5e7eb',
                padding: '1.5rem',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#ca404f';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <h3 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: '0.5rem', color: '#1f2937' }}>
                {project.title}
              </h3>
              <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                {project.category}
              </p>
              <p style={{
                color: '#4b5563',
                marginBottom: '1rem',
                lineHeight: '1.5',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical'
              }}>
                {project.description}
              </p>
              
              <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <p>👥 <strong>Students:</strong> {project.assignedStudents?.length || 0}</p>
                <p>📅 <strong>Deadline:</strong> {new Date(project.deadline).toLocaleDateString()}</p>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={() => handleViewSubmissions(project)}
                  style={{
                    flex: 1,
                    backgroundColor: '#ca404f',
                    color: 'white',
                    padding: '0.75rem',
                    borderRadius: '6px',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#b0303f'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ca404f'}
                >
                  View Submissions
                </button>
                <button
                  onClick={() => handleDeleteProject(project.id)}
                  disabled={deletingId === project.id}
                  style={{
                    padding: '0.75rem 1rem',
                    backgroundColor: deletingId === project.id ? '#d1d5db' : '#fee2e2',
                    color: deletingId === project.id ? '#9ca3af' : '#991b1b',
                    border: '2px solid #fca5a5',
                    borderRadius: '6px',
                    cursor: deletingId === project.id ? 'not-allowed' : 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (deletingId !== project.id) {
                      e.currentTarget.style.backgroundColor = '#dc2626';
                      e.currentTarget.style.color = 'white';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (deletingId !== project.id) {
                      e.currentTarget.style.backgroundColor = '#fee2e2';
                      e.currentTarget.style.color = '#991b1b';
                    }
                  }}
                >
                  {deletingId === project.id ? '⏳...' : 'Delete'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectsManagement