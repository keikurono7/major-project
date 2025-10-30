import React, { useState, useEffect } from 'react';
import { getProgressData } from '../../services/progress';

const ProgressTracker = () => {
  const [selectedSubject, setSelectedSubject] = useState(localStorage.getItem('currentSubjectId') || null);

  useEffect(() => {
    const handleSubjectChange = () => {
      setSelectedSubject(localStorage.getItem('currentSubjectId') || null);
    };
    window.addEventListener('subjectChanged', handleSubjectChange);
    window.addEventListener('storage', handleSubjectChange);
    return () => {
      window.removeEventListener('subjectChanged', handleSubjectChange);
      window.removeEventListener('storage', handleSubjectChange);
    };
  }, []);

  useEffect(() => {
    const fetchProgress = async () => {
      if (!selectedSubject) return;
      try {
        const data = await getProgressData(selectedSubject);
        // ...existing logic to set progress data, filtering by selectedSubject...
      } catch (err) {
        console.error('Failed to load progress', err);
      }
    };
    fetchProgress();
  }, [selectedSubject]);

  if (!selectedSubject) {
    return <div style={{ padding: 16 }}>Please select a subject from the header to view progress.</div>;
  }

  const progress = data || {};

  return (
    <div className="progress-tracker">
      <div className="flex mb-4" style={{ gap: '1rem' }}>
        <div className="flex items-center gap-2">
          <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--danger)' }}></span>
          <span>Needs attention</span>
        </div>
        <div className="flex items-center gap-2">
          <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--warning)' }}></span>
          <span>Improving</span>
        </div>
        <div className="flex items-center gap-2">
          <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--success)' }}></span>
          <span>Proficient</span>
        </div>
      </div>
      
      <div className="mt-4">
        {Object.entries(progress || {}).map(([topic, score]) => (
          <div key={topic} className="mb-3">
            <div className="flex justify-between mb-1">
              <span>{topic}</span>
              <span>{Math.round(score * 100)}%</span>
            </div>
            <div className="progress-container">
              <div 
                className="progress-bar" 
                style={{ width: `${score * 100}%`, backgroundColor: getColorForScore(score) }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressTracker;