import React, { useState, useEffect } from 'react';
import { paperApi } from '../../services/api';
import ParallaxSection from '../common/ParallaxSection';
import Card from '../common/Card';
import Button from '../common/Button';
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf";
import { generateQuestions, finalizeQuestions } from "../../services/api";

pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const PaperGenerator = () => {
  const [topics, setTopics] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [includeAnswers, setIncludeAnswers] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPapers, setGeneratedPapers] = useState([]);
  const [latestPaperUrl, setLatestPaperUrl] = useState('');
  const [fileText, setFileText] = useState("");
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState([]);
  const [selected, setSelected] = useState({});
  const [maxMarks, setMaxMarks] = useState(100);
  
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
  
  async function extractTextFromPdf(file) {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let fullText = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const pageText = content.items.map(i => i.str).join(" ");
      fullText += "\n\n" + pageText;
    }
    return fullText;
  }

  async function handleUpload(e) {
    const f = e.target.files[0];
    if (!f) return;
    setLoading(true);
    try {
      const text = await extractTextFromPdf(f);
      setFileText(text);
    } catch (err) {
      console.error(err);
      alert("Failed to read PDF");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    if (!fileText) return alert("Upload a PDF first");
    setLoading(true);
    try {
      // ask backend to generate many questions from full text
      const resp = await generateQuestions({ text: fileText, maxQuestions: 50 });
      setGenerated(resp.questions || []);
      // init default marks & selection
      const sel = {};
      resp.questions?.forEach((q, idx) => (sel[idx] = { selected: true, marks: q.default_marks || 2 }));
      setSelected(sel);
    } catch (err) {
      console.error(err);
      alert("Generation failed: " + (err.message || err));
    } finally {
      setLoading(false);
    }
  }

  function toggleQuestion(i) {
    setSelected(s => ({ ...s, [i]: { ...s[i], selected: !s[i].selected } }));
  }

  function setMarks(i, m) {
    setSelected(s => ({ ...s, [i]: { ...s[i], marks: Number(m) } }));
  }

  async function handleFinalize() {
    const chosen = generated
      .map((q, i) => ({ index: i, question: q, ...selected[i] }))
      .filter(item => item.selected);
    if (!chosen.length) return alert("Select at least one question");
    setLoading(true);
    try {
      const resp = await finalizeQuestions({ selectedQuestions: chosen, maxMarks });
      // backend returns final paper or chosenQuestions
      alert("Finalized. Preview returned from server.");
      console.log("finalized:", resp);
    } catch (err) {
      console.error(err);
      alert("Finalize failed: " + (err.message || err));
    } finally {
      setLoading(false);
    }
  }

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

        <div className="mt-6">
          <h3 className="font-medium">Generated Questions ({generated.length})</h3>
          <div className="space-y-3 mt-3">
            {generated.map((q, i) => (
              <div key={i} className="p-2 border rounded">
                <div className="flex items-start justify-between">
                  <div>
                    <input type="checkbox" checked={!!selected[i]?.selected} onChange={() => toggleQuestion(i)} />
                    <strong className="ml-2">Q{i + 1}:</strong>
                    <span className="ml-2">{q.text}</span>
                  </div>
                  <div className="ml-4">
                    <label>Marks</label>
                    <input type="number" value={selected[i]?.marks || q.default_marks || 2} onChange={(e) => setMarks(i, e.target.value)} className="ml-2 w-20" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <label>Max total marks</label>
            <input type="number" value={maxMarks} onChange={(e) => setMaxMarks(Number(e.target.value))} className="ml-2 w-28" />
            <button onClick={handleFinalize} className="btn ml-4" disabled={loading}>Finalize</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaperGenerator;