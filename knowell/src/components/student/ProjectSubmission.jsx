import React, { useState } from 'react';
import { projectApi } from '../../services/api';
import { getStorage, ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { db, collection, addDoc } from '../../services/firebase';

const ProjectSubmission = ({ project, studentId, existingSubmission, onBack, onSubmit }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles]);
  };

  const handleRemoveFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Helper function to submit project files
  const submitProjectFiles = async (projectId, studentId, files) => {
    try {
      const storage = getStorage();
      const uploadedFiles = [];

      // Upload each file to Firebase Storage
      for (const file of files) {
        const storageRef = ref(storage, `projects/${projectId}/${studentId}/${file.name}`);
        await uploadBytes(storageRef, file);
        const downloadURL = await getDownloadURL(storageRef);
        
        uploadedFiles.push({
          name: file.name,
          url: downloadURL,
          fullPath: storageRef.fullPath,
          size: file.size,
          type: file.type
        });
      }

      // Create submission document
      const submissionRef = collection(db, 'project_submissions');
      await addDoc(submissionRef, {
        projectId,
        studentId,
        files: uploadedFiles,
        status: 'submitted',
        createdAt: new Date()
      });

      return true;
    } catch (error) {
      console.error('Error submitting files:', error);
      throw error;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await submitProjectFiles(project.id, studentId, files);

      setSuccess(true);
      setFiles([]);
      
      setTimeout(() => {
        setSuccess(false);
        onSubmit();
      }, 2000);
    } catch (err) {
      setError(err.message);
      console.error('Error submitting project:', err);
    } finally {
      setLoading(false);
    }
  };

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

      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '2px solid #e5e7eb',
        padding: '1.5rem',
        maxWidth: '56rem',
        marginLeft: 'auto',
        marginRight: 'auto'
      }}>
        <h2 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '0.5rem', color: '#1f2937' }}>
          {project.title}
        </h2>
        <p style={{ color: '#6b7280', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          {project.category}
        </p>

        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontWeight: '700', marginBottom: '0.5rem', color: '#1f2937' }}>Description</h3>
          <p style={{ color: '#4b5563', marginBottom: '1rem', lineHeight: '1.6' }}>
            {project.description}
          </p>

          <h3 style={{ fontWeight: '700', marginBottom: '0.5rem', color: '#1f2937' }}>Instructions</h3>
          <p style={{
            color: '#4b5563',
            marginBottom: '1rem',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.6',
            backgroundColor: '#f9fafb',
            padding: '1rem',
            borderRadius: '6px',
            border: '1px solid #e5e7eb'
          }}>
            {project.instructions}
          </p>

          <div style={{
            backgroundColor: '#f3f4f6',
            padding: '1rem',
            borderRadius: '6px',
            border: '1px solid #e5e7eb'
          }}>
            <p style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.5rem' }}>
              <strong>📅 Deadline:</strong> {new Date(project.deadline).toLocaleString()}
            </p>
            <p style={{ fontSize: '0.875rem', color: '#374151' }}>
              <strong>⭐ Max Score:</strong> {project.maxScore}
            </p>
          </div>
        </div>

        {existingSubmission && (
          <div style={{
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: '#f0fdf4',
            border: '2px solid #86efac',
            borderRadius: '8px'
          }}>
            <h3 style={{ fontWeight: '700', color: '#059669', marginBottom: '0.5rem' }}>✓ Submission Status</h3>
            <p style={{ fontSize: '0.875rem', color: '#047857', marginBottom: '0.25rem' }}>
              Status: <span style={{ fontWeight: '600', textTransform: 'capitalize' }}>{existingSubmission.status}</span>
            </p>
            <p style={{ fontSize: '0.875rem', color: '#047857', marginBottom: '0.5rem' }}>
              Submitted at: {new Date(existingSubmission.createdAt.toDate()).toLocaleString()}
            </p>
            {existingSubmission.feedback && (
              <div style={{
                marginTop: '0.75rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid #86efac'
              }}>
                <p style={{ fontSize: '0.875rem', color: '#047857', marginBottom: '0.25rem' }}>
                  <strong>Score:</strong> {existingSubmission.feedback.score}/{project.maxScore}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#047857', lineHeight: '1.4' }}>
                  {existingSubmission.feedback.text}
                </p>
              </div>
            )}
          </div>
        )}

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

        {success && (
          <div style={{
            marginBottom: '1rem',
            padding: '1rem',
            backgroundColor: '#f0fdf4',
            border: '2px solid #86efac',
            borderRadius: '8px',
            color: '#059669'
          }}>
            ✓ Project submitted successfully!
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
              Upload Project Files
            </label>
            <div
              style={{
                border: '2px dashed #e5e7eb',
                borderRadius: '8px',
                padding: '2rem',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: '#f9fafb'
              }}
              onDragOver={(e) => {
                e.preventDefault();
                e.currentTarget.style.borderColor = '#ca404f';
                e.currentTarget.style.backgroundColor = '#fff5f7';
              }}
              onDragLeave={(e) => {
                e.currentTarget.style.borderColor = '#e5e7eb';
                e.currentTarget.style.backgroundColor = '#f9fafb';
              }}
            >
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                id="file-input"
                disabled={loading}
              />
              <label htmlFor="file-input" style={{ cursor: 'pointer' }}>
                <p style={{ color: '#6b7280', marginBottom: '0.25rem', fontWeight: '500' }}>
                  📁 Click to upload or drag and drop
                </p>
                <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                  Supported: PDF, DOC, DOCX, TXT, CODE files
                </p>
              </label>
            </div>
          </div>

          {files.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontWeight: '600', marginBottom: '0.75rem', color: '#1f2937' }}>
                Selected Files ({files.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {files.map((file, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem',
                      backgroundColor: '#f3f4f6',
                      borderRadius: '6px'
                    }}
                  >
                    <span style={{ fontSize: '0.875rem', color: '#1f2937', fontWeight: '500' }}>
                      📄 {file.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      style={{
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: '#ca404f',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        transition: 'color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#b0303f'}
                      onMouseLeave={(e) => e.currentTarget.style.color = '#ca404f'}
                    >
                      ✕ Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || files.length === 0}
            style={{
              width: '100%',
              backgroundColor: loading || files.length === 0 ? '#d1d5db' : '#ca404f',
              color: 'white',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              border: 'none',
              cursor: loading || files.length === 0 ? 'not-allowed' : 'pointer',
              fontWeight: '600',
              fontSize: '1rem',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!loading && files.length > 0) {
                e.currentTarget.style.backgroundColor = '#b0303f';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading && files.length > 0) {
                e.currentTarget.style.backgroundColor = '#ca404f';
              }
            }}
          >
            {loading ? '⏳ Submitting...' : '🚀 Submit Project'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ProjectSubmission;