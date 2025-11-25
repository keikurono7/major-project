import React, { useState, useEffect } from 'react';
import { getStudentProjects, getStudentSubmission } from '../../services/projectService';
import ProjectCard from './ProjectCard';
import ProjectSubmission from './ProjectSubmission';

const ProjectsFeed = ({ studentId }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [submissions, setSubmissions] = useState({});

  useEffect(() => {
    fetchProjects();
  }, [studentId]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await getStudentProjects(studentId);
      setProjects(data);

      // Fetch submissions for each project
      const subs = {};
      for (const project of data) {
        const projectSubs = await getStudentSubmission(project.id, studentId);
        subs[project.id] = projectSubs;
      }
      setSubmissions(subs);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
        <div style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</div>
        <p style={{ marginTop: '0.5rem' }}>Loading projects...</p>
      </div>
    );
  }

  if (selectedProject) {
    return (
      <ProjectSubmission
        project={selectedProject}
        studentId={studentId}
        existingSubmission={submissions[selectedProject.id]?.[0]}
        onBack={() => setSelectedProject(null)}
        onSubmit={() => fetchProjects()}
      />
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '1.5rem', color: '#1f2937' }}>
        📚 Projects
      </h2>

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
          <p style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📭</p>
          <p style={{ color: '#6b7280', fontWeight: '500' }}>No projects assigned yet</p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '1.5rem'
        }}>
          {projects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              submission={submissions[project.id]?.[0]}
              onSelect={() => setSelectedProject(project)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectsFeed;