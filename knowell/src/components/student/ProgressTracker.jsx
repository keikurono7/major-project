import React from 'react';

const ProgressTracker = ({ progress }) => {
  // Convert confidence scores object to array for sorting
  const topicsArray = Object.entries(progress || {}).map(([topic, score]) => ({
    topic,
    score,
    color: getColorForScore(score)
  }));

  // Sort by confidence score (ascending)
  topicsArray.sort((a, b) => a.score - b.score);

  // Helper function to get color based on confidence score
  function getColorForScore(score) {
    if (score < 0.3) return 'var(--danger)';
    if (score < 0.6) return 'var(--warning)';
    return 'var(--success)';
  }

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
        {topicsArray.map(({ topic, score, color }) => (
          <div key={topic} className="mb-3">
            <div className="flex justify-between mb-1">
              <span>{topic}</span>
              <span>{Math.round(score * 100)}%</span>
            </div>
            <div className="progress-container">
              <div 
                className="progress-bar" 
                style={{ width: `${score * 100}%`, backgroundColor: color }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressTracker;