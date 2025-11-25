import React from 'react';

const ProjectCard = ({ project, submission, onSelect }) => {
  const isOverdue = new Date(project.deadline) < new Date();
  const isSubmitted = submission && submission.status === 'submitted';
  const isReviewed = submission && submission.status === 'reviewed';

  const getStatusColor = () => {
    if (isReviewed) return { bg: '#dbeafe', text: '#0c4a6e', label: 'Reviewed' };
    if (isSubmitted) return { bg: '#dbeafe', text: '#0c4a6e', label: 'Submitted' };
    if (isOverdue) return { bg: '#fee2e2', text: '#7f1d1d', label: 'Overdue' };
    return { bg: '#fef3c7', text: '#78350f', label: 'Pending' };
  };

  const status = getStatusColor();

  return (
    <div
      style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '2px solid #e5e7eb',
        padding: '1.5rem',
        cursor: 'pointer',
        transition: 'all 0.2s'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = '#ca404f';
        e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = '#e5e7eb';
        e.currentTarget.style.boxShadow = 'none';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: '700', color: '#1f2937' }}>
          {project.title}
        </h3>
        <span
          style={{
            padding: '0.375rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: '600',
            borderRadius: '9999px',
            backgroundColor: status.bg,
            color: status.text,
            whiteSpace: 'nowrap'
          }}
        >
          {status.label}
        </span>
      </div>

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
        <p>📅 <strong>Deadline:</strong> {new Date(project.deadline).toLocaleDateString()}</p>
        <p>⭐ <strong>Max Score:</strong> {project.maxScore}</p>
      </div>

      {submission && submission.feedback && (
        <div style={{
          marginBottom: '1rem',
          padding: '0.75rem',
          backgroundColor: '#f0fdf4',
          borderLeft: '4px solid #10b981',
          borderRadius: '4px'
        }}>
          <p style={{ fontSize: '0.875rem', fontWeight: '600', color: '#059669', marginBottom: '0.25rem' }}>
            Score: {submission.feedback.score}/{project.maxScore}
          </p>
          <p style={{ fontSize: '0.875rem', color: '#047857', lineHeight: '1.4' }}>
            {submission.feedback.text}
          </p>
        </div>
      )}

      <button
        onClick={onSelect}
        style={{
          width: '100%',
          backgroundColor: '#ca404f',
          color: 'white',
          padding: '0.75rem 1rem',
          borderRadius: '6px',
          border: 'none',
          cursor: 'pointer',
          fontWeight: '600',
          fontSize: '0.875rem',
          transition: 'background-color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#b0303f'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ca404f'}
      >
        {submission ? 'View Submission' : 'Submit Project'}
      </button>
    </div>
  );
};

export default ProjectCard;