// src/components/teacher/ContentUpload.jsx
import React, { useState } from 'react';
import ParallaxSection from '../common/ParallaxSection';

const ContentUpload = ({ onUpload }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [fileSelected, setFileSelected] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setFileSelected(true);
    } else {
      alert('Please select a valid PDF file');
      setFileSelected(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      await onUpload(file);
      setFile(null);
      setFileSelected(false);
      // Reset file input
      document.getElementById('pdf-upload').value = '';
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="content-upload">
      <ParallaxSection className="upload-header">
        <h1>Upload Learning Content</h1>
        <p>Upload PDF textbooks or learning materials to generate quizzes and questions</p>
      </ParallaxSection>

      <div className="upload-container sharp-card">
        <h2>Upload New PDF</h2>
        <p>Select a PDF file to upload as educational content</p>

        <form onSubmit={handleUpload} className="upload-form">
          <div className="file-input-container">
            <input
              type="file"
              id="pdf-upload"
              accept="application/pdf"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <label htmlFor="pdf-upload" className="file-label sharp-button">
              {fileSelected ? file.name : 'Select PDF File'}
            </label>
          </div>

          <button 
            type="submit" 
            className="sharp-button"
            disabled={!fileSelected || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload PDF'}
          </button>
        </form>

        {uploading && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '50%' }}></div>
            </div>
            <p>Uploading PDF and processing content...</p>
          </div>
        )}
      </div>

      <div className="content-tips sharp-card">
        <h3>Tips for Best Results</h3>
        <ul>
          <li>Use clear, well-structured PDFs for better parsing</li>
          <li>Make sure the content is relevant to the subject</li>
          <li>Larger textbooks provide more context for question generation</li>
          <li>After uploading, the system will process the content automatically</li>
        </ul>
      </div>
    </div>
  );
};

export default ContentUpload;