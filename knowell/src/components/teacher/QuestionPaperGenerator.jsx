import React, { useState, useEffect } from 'react';
import { questionPaperApi } from '../../services/questionPaper';
import { computeAllSubjectsProgress } from '../../services/progress';
import '../../dashboard.css';

const QuestionPaperGenerator = ({ teacherId }) => {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);
  const [currentStep, setCurrentStep] = useState(1); // 1: Generate, 2: Filter, 3: Final
  const [loading, setLoading] = useState(false);
  const [generatedQuestions, setGeneratedQuestions] = useState({});
  const [filteredQuestions, setFilteredQuestions] = useState({});
  const [finalQuestionPaper, setFinalQuestionPaper] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    try {
      const subjectsData = await computeAllSubjectsProgress(teacherId);
      setSubjects(subjectsData || []);
    } catch (error) {
      console.error('Error fetching subjects:', error);
    }
  };

  const handleGenerateQuestions = async () => {
    if (!selectedSubjectId) return;
    
    setLoading(true);
    try {
      const response = await questionPaperApi.generateInitialQuestions(selectedSubjectId);
      setGeneratedQuestions(response.questions); // { moduleId: [25 questions] }
      setSessionId(response.session_id);
      setCurrentStep(2);
    } catch (error) {
      console.error('Error generating questions:', error);
      alert('Failed to generate questions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionSelect = (moduleId, questionId, isSelected) => {
    setFilteredQuestions(prev => {
      const moduleQuestions = prev[moduleId] || [];
      
      if (isSelected) {
        if (moduleQuestions.length >= 10) {
          alert('You can only select 10 questions per module');
          return prev;
        }
        return {
          ...prev,
          [moduleId]: [...moduleQuestions, questionId]
        };
      } else {
        return {
          ...prev,
          [moduleId]: moduleQuestions.filter(id => id !== questionId)
        };
      }
    });
  };

  const handleSubmitFiltered = async () => {
    // Validate 10 questions per module
    const moduleIds = Object.keys(generatedQuestions);
    const allValid = moduleIds.every(moduleId => {
      const count = (filteredQuestions[moduleId] || []).length;
      return count === 10;
    });

    if (!allValid) {
      alert('Please select exactly 10 questions for each module');
      return;
    }

    setLoading(true);
    try {
      const response = await questionPaperApi.submitFilteredQuestions(
        selectedSubjectId,
        filteredQuestions
      );
      setFinalQuestionPaper(response.question_paper);
      setCurrentStep(3);
    } catch (error) {
      console.error('Error submitting filtered questions:', error);
      alert('Failed to generate final question paper. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuestionPaper = async () => {
    setLoading(true);
    try {
      await questionPaperApi.saveQuestionPaper(selectedSubjectId, finalQuestionPaper);
      alert('Question paper saved successfully!');
      // Reset
      setCurrentStep(1);
      setGeneratedQuestions({});
      setFilteredQuestions({});
      setFinalQuestionPaper(null);
      setSessionId(null);
    } catch (error) {
      console.error('Error saving question paper:', error);
      alert('Failed to save question paper. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const currentSubject = subjects.find(s => s.id === selectedSubjectId);
  const modules = currentSubject?.modules || [];

  return (
    <div className="card">
      <h2 style={{ marginBottom: '1rem' }}>📝 Question Paper Generator</h2>
      
      {/* Step Indicator */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        marginBottom: '2rem',
        padding: '1rem',
        backgroundColor: '#f9fafb',
        borderRadius: '8px'
      }}>
        {[
          { num: 1, label: 'Generate Questions' },
          { num: 2, label: 'Filter & Select' },
          { num: 3, label: 'Final Paper' }
        ].map(step => (
          <div key={step.num} style={{ 
            textAlign: 'center', 
            flex: 1,
            opacity: currentStep >= step.num ? 1 : 0.5
          }}>
            <div style={{ 
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              backgroundColor: currentStep >= step.num ? '#ca404f' : '#d1d5db',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 0.5rem',
              fontWeight: 'bold'
            }}>
              {step.num}
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>
              {step.label}
            </div>
          </div>
        ))}
      </div>

      {/* Step 1: Subject Selection */}
      {currentStep === 1 && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
              Select Subject:
            </label>
            <select
              value={selectedSubjectId || ''}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '0.9rem'
              }}
            >
              <option value="">-- Select a Subject --</option>
              {subjects.map(subject => (
                <option key={subject.id} value={subject.id}>
                  {subject.name} ({subject.modules?.length || 0} modules)
                </option>
              ))}
            </select>
          </div>

          {currentSubject && (
            <div style={{ 
              padding: '1rem', 
              backgroundColor: '#f0f9ff', 
              borderRadius: '8px',
              marginBottom: '1rem',
              border: '1px solid #bae6fd'
            }}>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>
                <strong>{currentSubject.name}</strong> has <strong>{modules.length}</strong> modules.
                <br />
                This will generate <strong>{modules.length * 25}</strong> questions total 
                (25 per module).
              </p>
            </div>
          )}

          <button
            onClick={handleGenerateQuestions}
            disabled={!selectedSubjectId || loading}
            style={{
              width: '100%',
              padding: '1rem',
              backgroundColor: !selectedSubjectId || loading ? '#d1d5db' : '#ca404f',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: !selectedSubjectId || loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Generating Questions...' : 'Generate Questions'}
          </button>
        </div>
      )}

      {/* Step 2: Filter Questions */}
      {currentStep === 2 && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Filter Questions - Select 10 per Module
            </h3>
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
              Review and select exactly 10 questions from each module's generated 25 questions.
            </p>
          </div>

          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {modules.map(module => {
              const moduleQuestions = generatedQuestions[module.id] || [];
              const selectedCount = (filteredQuestions[module.id] || []).length;

              return (
                <div key={module.id} style={{ 
                  marginBottom: '2rem',
                  padding: '1rem',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  backgroundColor: selectedCount === 10 ? '#f0fdf4' : 'white'
                }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '1rem'
                  }}>
                    <h4 style={{ margin: 0, fontSize: '1rem' }}>{module.name}</h4>
                    <span style={{ 
                      padding: '0.25rem 0.75rem',
                      backgroundColor: selectedCount === 10 ? '#10b981' : '#ca404f',
                      color: 'white',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '600'
                    }}>
                      {selectedCount}/10 Selected
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {moduleQuestions.map((question, idx) => {
                      const isSelected = (filteredQuestions[module.id] || []).includes(question.id);
                      
                      return (
                        <div key={question.id} style={{ 
                          display: 'flex',
                          alignItems: 'flex-start',
                          padding: '0.75rem',
                          border: '1px solid #e5e7eb',
                          borderRadius: '6px',
                          backgroundColor: isSelected ? '#dbeafe' : 'white',
                          cursor: 'pointer'
                        }}
                        onClick={() => handleQuestionSelect(module.id, question.id, !isSelected)}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              e.stopPropagation();
                              handleQuestionSelect(module.id, question.id, e.target.checked);
                            }}
                            style={{ marginRight: '0.75rem', marginTop: '0.25rem' }}
                          />
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.25rem' }}>
                              Q{idx + 1}. {question.question_text}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              Topic: {question.topic} | Difficulty: {question.difficulty}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button
              onClick={() => setCurrentStep(1)}
              style={{
                flex: 1,
                padding: '1rem',
                backgroundColor: 'white',
                color: '#ca404f',
                border: '2px solid #ca404f',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Back
            </button>
            <button
              onClick={handleSubmitFiltered}
              disabled={loading || Object.keys(generatedQuestions).some(
                moduleId => (filteredQuestions[moduleId] || []).length !== 10
              )}
              style={{
                flex: 1,
                padding: '1rem',
                backgroundColor: loading ? '#d1d5db' : '#ca404f',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Generating Final Paper...' : 'Generate Final Paper'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Final Question Paper */}
      {currentStep === 3 && finalQuestionPaper && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Final Question Paper
            </h3>
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
              Total Marks: <strong>100</strong> | Modules: <strong>{modules.length}</strong> (20 marks each)
            </p>
          </div>

          <div style={{ maxHeight: '600px', overflowY: 'auto', padding: '1rem', backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
            {finalQuestionPaper.modules?.map((moduleData, moduleIdx) => (
              <div key={moduleData.module_id} style={{ marginBottom: '2rem' }}>
                <h4 style={{ 
                  fontSize: '1rem', 
                  marginBottom: '1rem',
                  padding: '0.75rem',
                  backgroundColor: '#f9fafb',
                  borderRadius: '6px'
                }}>
                  Module {moduleIdx + 1}: {moduleData.module_name} (20 Marks)
                </h4>

                {moduleData.questions?.map((question, qIdx) => (
                  <div key={qIdx} style={{ 
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      marginBottom: '0.5rem'
                    }}>
                      <strong>Question {qIdx + 1}:</strong>
                      <span style={{ 
                        backgroundColor: '#fef3f2',
                        color: '#ca404f',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '600'
                      }}>
                        {question.marks} marks
                      </span>
                    </div>
                    <div style={{ marginBottom: '0.75rem' }}>
                      {question.question_text}
                    </div>
                    
                    {question.sub_questions && question.sub_questions.length > 0 && (
                      <div style={{ paddingLeft: '1.5rem' }}>
                        {question.sub_questions.map((subQ, subIdx) => (
                          <div key={subIdx} style={{ 
                            marginBottom: '0.5rem',
                            padding: '0.5rem',
                            backgroundColor: '#f9fafb',
                            borderRadius: '4px'
                          }}>
                            <div style={{ fontSize: '0.875rem' }}>
                              <strong>({String.fromCharCode(97 + subIdx)})</strong> {subQ.text}
                              <span style={{ 
                                marginLeft: '0.5rem',
                                color: '#6b7280',
                                fontSize: '0.75rem'
                              }}>
                                [{subQ.marks} marks]
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button
              onClick={() => setCurrentStep(2)}
              style={{
                flex: 1,
                padding: '1rem',
                backgroundColor: 'white',
                color: '#ca404f',
                border: '2px solid #ca404f',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Back to Filter
            </button>
            <button
              onClick={handleSaveQuestionPaper}
              disabled={loading}
              style={{
                flex: 1,
                padding: '1rem',
                backgroundColor: loading ? '#d1d5db' : '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Saving...' : 'Save Question Paper'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuestionPaperGenerator;