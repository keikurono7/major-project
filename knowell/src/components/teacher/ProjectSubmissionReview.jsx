import React, { useState } from 'react';
import { getSubmissionFiles, updateSubmissionFeedback } from '../../services/projectService';
import { evaluateSubmissionApi } from '../../services/api';

const ProjectSubmissionReview = ({ project, submissions, onBack }) => {
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [submissionFiles, setSubmissionFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [score, setScore] = useState('');
  const [viewingFile, setViewingFile] = useState(null);
  const [aiEvaluation, setAiEvaluation] = useState(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);

  const handleSelectSubmission = async (submission) => {
    try {
      setLoading(true);
      setSelectedSubmission(submission);
      const files = await getSubmissionFiles(
        project.id,
        submission.studentId,
        submission.submissionId
      );
      
      const processedFiles = files.map(file => ({
        ...file,
        name: file.name || file.fileName || file.originalName || 'Unknown',
        fullPath: file.fullPath || file.url || file.downloadUrl || ''
      }));
      
      setSubmissionFiles(processedFiles);
      setFeedback(submission.feedback || '');
      setScore(submission.score || '');
      setAiEvaluation(submission.aiEvaluation || null);
    } catch (err) {
      console.error('Error loading submission:', err);
      alert('Error loading submission files');
    } finally {
      setLoading(false);
    }
  };

  const handleViewFile = async (file) => {
    try {
      if (!file || !file.name) {
        alert('Error: File information missing');
        return;
      }

      const firebaseUrl = "https://firebasestorage.googleapis.com/v0/b/atomic-lens-471613-m4.firebasestorage.app/o/"+encodeURIComponent(file.fullPath)+"?alt=media";
      
      window.open(firebaseUrl, '_blank');
      setViewingFile(file.name);
      
    } catch (err) {
      console.error('Error viewing file:', err);
      alert('Error: ' + err.message);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!selectedSubmission) return;

    try {
      setLoading(true);
      await updateSubmissionFeedback(selectedSubmission.id, {
        text: feedback,
        score: parseInt(score),
        reviewedBy: 'teacher'
      });
      alert('Feedback submitted successfully!');
      setSelectedSubmission({ ...selectedSubmission, feedback: { text: feedback, score: parseInt(score) } });
    } catch (err) {
      console.error('Error submitting feedback:', err);
      alert('Error submitting feedback');
    } finally {
      setLoading(false);
    }
  };

  const handleSendToAI = async () => {
    if (!selectedSubmission || submissionFiles.length === 0) {
      alert('No files to evaluate');
      return;
    }

    try {
      setEvaluationLoading(true);

      const evaluation = await evaluateSubmissionApi.evaluateSubmission(
        project.id,
        selectedSubmission.submissionId,
        selectedSubmission.studentId,
        submissionFiles,
        project.description,
        project.instructions
      );

      if (evaluation.success) {
        setAiEvaluation(evaluation.evaluation);
      } else {
        alert('AI evaluation failed');
      }
    } catch (err) {
      console.error('Error sending to AI:', err);
      alert('Error processing AI evaluation: ' + err.message);
    } finally {
      setEvaluationLoading(false);
    }
  };

  if (!selectedSubmission) {
    return (
      <div style={{ padding: '1.5rem' }}>
        <button
          onClick={onBack}
          style={{
            marginBottom: '1.5rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#f3f4f6',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            color: '#6b7280',
            fontSize: '0.875rem',
            fontWeight: '500',
            transition: 'all 0.2s'
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

        <h2 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '1.5rem', color: '#1f2937' }}>
          {project.title} - Submissions
        </h2>

        {submissions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
            <p style={{ color: '#6b7280', fontSize: '1rem' }}>No submissions yet</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {submissions.map(submission => (
              <div 
                key={submission.id} 
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
                <p style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#1f2937' }}>
                  Student ID: {submission.studentId}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                  Files: {submission.fileCount || submissionFiles.length}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem' }}>
                  Status: <span style={{
                    fontWeight: '600',
                    color: submission.status === 'reviewed' ? '#10b981' : '#f59e0b'
                  }}>
                    {submission.status}
                  </span>
                </p>
                <button
                  onClick={() => handleSelectSubmission(submission)}
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
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Review Submission'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <button
        onClick={() => setSelectedSubmission(null)}
        style={{
          marginBottom: '1.5rem',
          padding: '0.5rem 1rem',
          backgroundColor: '#f3f4f6',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          color: '#6b7280',
          fontSize: '0.875rem',
          fontWeight: '500',
          transition: 'all 0.2s'
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
        ← Back to Submissions
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Files Panel */}
        <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '2px solid #e5e7eb', padding: '1.5rem' }}>
          <h3 style={{ fontWeight: '700', marginBottom: '1rem', color: '#1f2937' }}>
            Submitted Files ({submissionFiles.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '24rem', overflowY: 'auto' }}>
            {submissionFiles.map((file, idx) => (
              <button
                key={idx}
                onClick={() => handleViewFile(file)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  textAlign: 'left',
                  border: viewingFile === file.name ? '2px solid #ca404f' : '2px solid #e5e7eb',
                  backgroundColor: viewingFile === file.name ? '#fff5f7' : 'white',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  fontSize: '0.875rem'
                }}
                onMouseEnter={(e) => {
                  if (viewingFile !== file.name) {
                    e.currentTarget.style.borderColor = '#ca404f';
                    e.currentTarget.style.backgroundColor = '#fff5f7';
                  }
                }}
                onMouseLeave={(e) => {
                  if (viewingFile !== file.name) {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.backgroundColor = 'white';
                  }
                }}
              >
                <p style={{ fontWeight: '600', color: '#1f2937', marginBottom: '0.25rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {file.name}
                </p>
                <p style={{ color: '#6b7280', fontSize: '0.75rem' }}>
                  {file.size ? (file.size / 1024).toFixed(2) : '?'} KB
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* File Viewer */}
        <div style={{
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '2px solid #e5e7eb',
          padding: '1.5rem',
          maxHeight: '24rem',
          overflowY: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
              Click on a file to view it in a new tab
            </p>
          </div>
        </div>
      </div>

      {/* Feedback Section */}
      <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '2px solid #e5e7eb', padding: '1.5rem' }}>
        <h3 style={{ fontWeight: '700', marginBottom: '1.5rem', color: '#1f2937' }}>
          Provide Feedback & Evaluation
        </h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
              Score
            </label>
            <input
              type="number"
              value={score}
              onChange={(e) => setScore(e.target.value)}
              max={project.maxScore || 100}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '2px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '0.875rem',
                transition: 'border-color 0.2s'
              }}
              onFocus={(e) => e.target.style.borderColor = '#ca404f'}
              onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              placeholder={`0 - ${project.maxScore || 100}`}
            />
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
              Status
            </p>
            <p style={{
              padding: '0.75rem',
              backgroundColor: '#f3f4f6',
              borderRadius: '6px',
              fontSize: '0.875rem',
              color: '#1f2937',
              fontWeight: '500',
              textTransform: 'capitalize'
            }}>
              {selectedSubmission.status}
            </p>
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
            Feedback
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontFamily: 'inherit',
              transition: 'border-color 0.2s',
              minHeight: '8rem',
              resize: 'vertical'
            }}
            onFocus={(e) => e.target.style.borderColor = '#ca404f'}
            onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
            placeholder="Enter your feedback for the student"
          />
        </div>

        {aiEvaluation && (
          <div style={{
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: '#f0fdf4',
            border: '2px solid #86efac',
            borderRadius: '8px'
          }}>
            <h4 style={{ fontWeight: '700', color: '#059669', marginBottom: '0.5rem' }}>
              🤖 AI Evaluation
            </h4>
            <div style={{
              fontSize: '0.875rem',
              color: '#047857',
              whiteSpace: 'pre-wrap',
              maxHeight: '16rem',
              overflowY: 'auto',
              lineHeight: '1.6'
            }}>
              {typeof aiEvaluation === 'string' 
                ? aiEvaluation 
                : JSON.stringify(aiEvaluation, null, 2)
              }
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={handleSubmitFeedback}
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              backgroundColor: loading ? '#d1d5db' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: '600',
              fontSize: '0.875rem',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = '#059669';
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = '#10b981';
            }}
          >
            {loading ? 'Saving...' : '✓ Submit Feedback'}
          </button>
          <button
            onClick={handleSendToAI}
            disabled={evaluationLoading || submissionFiles.length === 0}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              backgroundColor: evaluationLoading || submissionFiles.length === 0 ? '#d1d5db' : '#ca404f',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: evaluationLoading || submissionFiles.length === 0 ? 'not-allowed' : 'pointer',
              fontWeight: '600',
              fontSize: '0.875rem',
              transition: 'background-color 0.2s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}
            onMouseEnter={(e) => {
              if (!evaluationLoading && submissionFiles.length > 0) {
                e.currentTarget.style.backgroundColor = '#b0303f';
              }
            }}
            onMouseLeave={(e) => {
              if (!evaluationLoading && submissionFiles.length > 0) {
                e.currentTarget.style.backgroundColor = '#ca404f';
              }
            }}
          >
            {evaluationLoading ? (
              <>
                <span style={{ animation: 'spin 1s linear infinite' }}>⏳</span>
                Processing...
              </>
            ) : (
              '🤖 AI Evaluate'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProjectSubmissionReview;