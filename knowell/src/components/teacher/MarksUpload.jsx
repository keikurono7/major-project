import React, { useState } from 'react';
import { marksApi } from '../../services/api';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';

export const MarksUpload = ({ subjectId }) => {
  const [activeTab, setActiveTab] = useState('ia');
  const [file, setFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [marksData, setMarksData] = useState([]);

  // Handle file upload for question paper analysis
  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setAnalyzing(true);

    try {
      const result = await marksApi.analyzeQuestionPaper(uploadedFile, subjectId);
      setAnalysisResult(result);
      
      // Pre-fill marks data with analyzed questions
      const initialMarks = result.questions.map(q => ({
        question_id: q.question_id,
        topic: q.topic,
        marks_allocated: q.marks,
        difficulty: q.difficulty,
      }));
      setMarksData(initialMarks);
    } catch (error) {
      console.error('Error analyzing question paper:', error);
      alert('Failed to analyze question paper. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Handle IA marks submission
  const handleIASubmit = async (students) => {
    try {
      const entries = students.map(student => ({
        student_id: student.id,
        subject_id: subjectId,
        test_number: parseInt(student.testNumber),
        marks: parseFloat(student.marks),
        max_marks: 50,
        question_topic_mapping: marksData.map(q => ({
          question_id: q.question_id,
          topic_id: q.topic,
          marks_allocated: parseFloat(q.marks_allocated),
          difficulty_level: q.difficulty,
        })),
        uploaded_by: 'teacher_id', // Get from auth context
        uploaded_at: new Date().toISOString(),
      }));

      await marksApi.uploadIAMarks(entries);
      alert(`Successfully uploaded marks for ${entries.length} students!`);
      
      // Reset form
      setMarksData([]);
      setAnalysisResult(null);
      setFile(null);
    } catch (error) {
      console.error('Error uploading IA marks:', error);
      alert('Failed to upload marks. Please try again.');
    }
  };

  // Handle semester marks submission
  const handleSemesterSubmit = async (students) => {
    try {
      const entries = students.map(student => ({
        student_id: student.id,
        subject_id: subjectId,
        semester: parseInt(student.semester),
        year: parseInt(student.year),
        marks: parseFloat(student.marks),
        max_marks: 100,
        question_topic_mapping: marksData.map(q => ({
          question_id: q.question_id,
          topic_id: q.topic,
          marks_allocated: parseFloat(q.marks_allocated),
          difficulty_level: q.difficulty,
        })),
        fetched_from: 'manual',
        fetched_at: new Date().toISOString(),
      }));

      await marksApi.uploadSemesterMarks(entries);
      alert(`Successfully uploaded semester marks for ${entries.length} students!`);
      
      // Reset form
      setMarksData([]);
      setAnalysisResult(null);
      setFile(null);
    } catch (error) {
      console.error('Error uploading semester marks:', error);
      alert('Failed to upload marks. Please try again.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Selection */}
      <Card className="p-4">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('ia')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              activeTab === 'ia'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            IA Test Marks
          </button>
          <button
            onClick={() => setActiveTab('semester')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              activeTab === 'semester'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Semester Exam Marks
          </button>
          <button
            onClick={() => setActiveTab('vtu')}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              activeTab === 'vtu'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            VTU Auto-Fetch
          </button>
        </div>
      </Card>

      {/* Step 1: Upload Question Paper */}
      {(activeTab === 'ia' || activeTab === 'semester') && (
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Step 1: Upload Question Paper for AI Analysis
          </h3>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={handleFileUpload}
              className="hidden"
              id="question-paper-upload"
            />
            <label htmlFor="question-paper-upload" className="cursor-pointer">
              <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-semibold mb-2">
                {file ? file.name : 'Click to upload question paper'}
              </p>
              <p className="text-sm text-gray-600">
                Supports PDF, TXT, DOCX • AI will map questions to topics
              </p>
            </label>
          </div>

          {analyzing && (
            <div className="mt-4 text-center text-blue-600">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              Analyzing question paper with AI...
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Review AI Analysis */}
      {analysisResult && (
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Step 2: Review AI-Mapped Questions
          </h3>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <p className="text-green-800">
              ✓ Successfully analyzed {analysisResult.total_questions} questions
            </p>
          </div>

          <div className="space-y-2">
            {analysisResult.questions.map((q, idx) => (
              <div key={idx} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0 font-bold text-gray-600">
                  {q.question_id}
                </div>
                <div className="flex-1">
                  <p className="font-semibold">{q.question_text}</p>
                  <div className="flex gap-4 text-sm text-gray-600 mt-1">
                    <span>Topic: <strong>{q.topic}</strong></span>
                    <span>Marks: <strong>{q.marks}</strong></span>
                    <span>Difficulty: <strong>{q.difficulty}</strong></span>
                  </div>
                </div>
                <button className="text-blue-600 text-sm hover:underline">
                  Edit
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Step 3: Enter Student Marks */}
      {analysisResult && (
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">
            Step 3: Enter Student Marks
          </h3>
          
          {activeTab === 'ia' && (
            <IAMarksEntry 
              questions={analysisResult.questions}
              onSubmit={handleIASubmit}
            />
          )}
          
          {activeTab === 'semester' && (
            <SemesterMarksEntry
              questions={analysisResult.questions}
              onSubmit={handleSemesterSubmit}
            />
          )}
        </Card>
      )}

      {/* VTU Auto-Fetch */}
      {activeTab === 'vtu' && (
        <Card className="p-6">
          <h3 className="text-xl font-bold mb-4">VTU Auto-Fetch</h3>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <AlertCircle className="w-12 h-12 mx-auto text-blue-500 mb-4" />
            <p className="text-lg font-semibold mb-2">Coming Soon!</p>
            <p className="text-gray-600">
              Automatic fetching from VTU portal will be available in the next update.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              For now, please use manual upload for semester exam marks.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

// IA Marks Entry Component
const IAMarksEntry = ({ questions, onSubmit }) => {
  const [students, setStudents] = useState([
    { id: '', testNumber: '1', marks: '' }
  ]);

  const addStudent = () => {
    setStudents([...students, { id: '', testNumber: '1', marks: '' }]);
  };

  const updateStudent = (index, field, value) => {
    const updated = [...students];
    updated[index][field] = value;
    setStudents(updated);
  };

  const removeStudent = (index) => {
    setStudents(students.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-12 gap-4 text-sm font-semibold text-gray-700 px-2">
        <div className="col-span-5">Student ID / USN</div>
        <div className="col-span-2">IA Test</div>
        <div className="col-span-3">Marks (out of 50)</div>
        <div className="col-span-2">Actions</div>
      </div>

      {students.map((student, idx) => (
        <div key={idx} className="grid grid-cols-12 gap-4 items-center">
          <input
            type="text"
            placeholder="Enter USN"
            value={student.id}
            onChange={(e) => updateStudent(idx, 'id', e.target.value)}
            className="col-span-5 px-3 py-2 border rounded-lg"
          />
          <select
            value={student.testNumber}
            onChange={(e) => updateStudent(idx, 'testNumber', e.target.value)}
            className="col-span-2 px-3 py-2 border rounded-lg"
          >
            <option value="1">IA 1</option>
            <option value="2">IA 2</option>
            <option value="3">IA 3</option>
          </select>
          <input
            type="number"
            placeholder="0-50"
            value={student.marks}
            onChange={(e) => updateStudent(idx, 'marks', e.target.value)}
            className="col-span-3 px-3 py-2 border rounded-lg"
          />
          <button
            onClick={() => removeStudent(idx)}
            className="col-span-2 text-red-600 hover:text-red-800"
          >
            Remove
          </button>
        </div>
      ))}

      <div className="flex gap-4">
        <Button onClick={addStudent} variant="outline">
          + Add Another Student
        </Button>
        <Button
          onClick={() => onSubmit(students)}
          disabled={students.some(s => !s.id || !s.marks)}
        >
          Upload Marks & Update BKT
        </Button>
      </div>
    </div>
  );
};

// Semester Marks Entry Component
const SemesterMarksEntry = ({ questions, onSubmit }) => {
  const [students, setStudents] = useState([
    { id: '', semester: '1', year: '2024', marks: '' }
  ]);

  const addStudent = () => {
    setStudents([...students, { id: '', semester: '1', year: '2024', marks: '' }]);
  };

  const updateStudent = (index, field, value) => {
    const updated = [...students];
    updated[index][field] = value;
    setStudents(updated);
  };

  const removeStudent = (index) => {
    setStudents(students.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-12 gap-4 text-sm font-semibold text-gray-700 px-2">
        <div className="col-span-4">Student ID / USN</div>
        <div className="col-span-2">Semester</div>
        <div className="col-span-2">Year</div>
        <div className="col-span-2">Marks (100)</div>
        <div className="col-span-2">Actions</div>
      </div>

      {students.map((student, idx) => (
        <div key={idx} className="grid grid-cols-12 gap-4 items-center">
          <input
            type="text"
            placeholder="Enter USN"
            value={student.id}
            onChange={(e) => updateStudent(idx, 'id', e.target.value)}
            className="col-span-4 px-3 py-2 border rounded-lg"
          />
          <input
            type="number"
            placeholder="1-8"
            value={student.semester}
            onChange={(e) => updateStudent(idx, 'semester', e.target.value)}
            className="col-span-2 px-3 py-2 border rounded-lg"
          />
          <input
            type="number"
            placeholder="2024"
            value={student.year}
            onChange={(e) => updateStudent(idx, 'year', e.target.value)}
            className="col-span-2 px-3 py-2 border rounded-lg"
          />
          <input
            type="number"
            placeholder="0-100"
            value={student.marks}
            onChange={(e) => updateStudent(idx, 'marks', e.target.value)}
            className="col-span-2 px-3 py-2 border rounded-lg"
          />
          <button
            onClick={() => removeStudent(idx)}
            className="col-span-2 text-red-600 hover:text-red-800"
          >
            Remove
          </button>
        </div>
      ))}

      <div className="flex gap-4">
        <Button onClick={addStudent} variant="outline">
          + Add Another Student
        </Button>
        <Button
          onClick={() => onSubmit(students)}
          disabled={students.some(s => !s.id || !s.marks)}
        >
          Upload Marks & Update BKT
        </Button>
      </div>
    </div>
  );
};