import React, { useState, useEffect } from 'react';
import { paperApi } from '../../services/api';
import ParallaxSection from '../common/ParallaxSection';
import Card from '../common/Card';
import Button from '../common/Button';

const PaperGenerator = () => {
  const [topics, setTopics] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [includeAnswers, setIncludeAnswers] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPapers, setGeneratedPapers] = useState([]);
  const [latestPaperUrl, setLatestPaperUrl] = useState('');
  
  // Fetch available topics and previous papers
  useEffect(() => {
    const fetchData = async () => {
      try {
        const topicsResponse = await topicsApi.getAll();
        setTopics(topicsResponse.data);
        
        // You would need an API endpoint to get previously generated papers
        // This is a placeholder
        try {
          const latestPaper = await paperApi.getLatestPaper();
          if (latestPaper && latestPaper.data) {
            setLatestPaperUrl(`/question-papers/latest`);
          }
        } catch (e) {
          console.log('No previous papers found');
        }
      } catch (error) {
        console.error('Error fetching topics:', error);
      }
    };
    
    fetchData();
  }, []);
  
  const handleTopicSelect = (topic) => {
    if (selectedTopics.includes(topic)) {
      setSelectedTopics(selectedTopics.filter(t => t !== topic));
    } else {
      setSelectedTopics([...selectedTopics, topic]);
    }
  };
  
  const handleSelectAllTopics = () => {
    if (selectedTopics.length === topics.length) {
      setSelectedTopics([]);
    } else {
      setSelectedTopics([...topics]);
    }
  };
  
  const generatePaper = async () => {
    setIsGenerating(true);
    try {
      const response = await paperApi.generatePaper({
        topics: selectedTopics.length > 0 ? selectedTopics : null,
        include_answers: includeAnswers
      });
      
      setLatestPaperUrl(`/question-papers/${response.data.filename}`);
      setGeneratedPapers([
        response.data,
        ...generatedPapers
      ]);
      
    } catch (error) {
      console.error('Error generating paper:', error);
    } finally {
      setIsGenerating(false);
    }
  };
  
  return (
    <div className="paper-generator p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-2">Question Paper Generator</h2>
          <p className="text-gray-600">Create comprehensive examination papers with AI assistance</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="h-fit">
            <h3 className="text-lg font-semibold mb-4">Configure Paper</h3>
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <label className="font-medium">Select Topics:</label>
                <Button 
                  type="secondary" 
                  onClick={handleSelectAllTopics}
                >
                  {selectedTopics.length === topics.length ? 'Deselect All' : 'Select All'}
                </Button>
              </div>
              
              <div className="topics-selector mt-2 border border-gray-300 h-64 overflow-y-auto p-2">
                {topics.map(topic => (
                  <div key={topic} className="topic-item flex items-center p-1">
                    <input
                      type="checkbox"
                      id={`topic-${topic}`}
                      checked={selectedTopics.includes(topic)}
                      onChange={() => handleTopicSelect(topic)}
                      className="mr-2"
                    />
                    <label htmlFor={`topic-${topic}`}>{topic}</label>
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {selectedTopics.length === 0 
                  ? 'No selection will include all topics' 
                  : `${selectedTopics.length} topics selected`}
              </p>
            </div>
            
            <div className="mb-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeAnswers}
                  onChange={() => setIncludeAnswers(!includeAnswers)}
                  className="mr-2"
                />
                Include Answer Guidelines
              </label>
            </div>
            
            <Button
              onClick={generatePaper}
              disabled={isGenerating}
              fullWidth
            >
              {isGenerating ? 'Generating Paper...' : 'Generate Question Paper'}
            </Button>
          </Card>

          <Card className="h-fit">
            <h3 className="text-lg font-semibold mb-4">Generated Papers</h3>
            {latestPaperUrl && (
              <div className="latest-paper mb-4">
                <h4 className="font-medium mb-2">Latest Paper</h4>
                <div className="paper-preview border border-gray-300 p-3 mb-2 bg-gray-50">
                  <div className="flex justify-between">
                    <span>Question Paper</span>
                    <span className="text-gray-500">
                      {new Date().toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <Button 
                    onClick={() => window.open(latestPaperUrl, '_blank')}
                  >
                    Download Paper
                  </Button>
                </div>
              </div>
            )}
            
            <div className="previous-papers">
              <h4 className="font-medium mb-2">Previous Papers</h4>
              {generatedPapers.length > 0 ? (
                <div className="papers-list">
                  {generatedPapers.map((paper, index) => (
                    <div key={index} className="paper-item border-b border-gray-200 py-2 flex justify-between items-center">
                      <span>{paper.filename}</span>
                      <Button 
                        type="secondary"
                        onClick={() => window.open(`/question-papers/${paper.filename}`, '_blank')}
                      >
                        View
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No previously generated papers</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PaperGenerator;