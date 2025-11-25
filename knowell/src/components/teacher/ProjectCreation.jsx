import React, { useState, useEffect } from 'react';
import { createProject, assignStudentsToProject } from '../../services/projectService';
import { db, collection, query, where, getDocs } from '../../services/firebase';

const ProjectCreation = ({ teacherId, onProjectCreated }) => {
  const [projectData, setProjectData] = useState({
    title: '',
    description: '',
    deadline: '',
    instructions: '',
    category: '',
    maxScore: 100
  });
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingStudents, setFetchingStudents] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        setFetchingStudents(true);
        const usersRef = collection(db, 'users');
        const q = query(usersRef, where('role', '==', 'student'));
        const querySnapshot = await getDocs(q);
        
        const studentsList = [];
        querySnapshot.forEach((doc) => {
          studentsList.push({
            id: doc.id,
            ...doc.data()
          });
        });
        
        setStudents(studentsList);
      } catch (err) {
        console.error('Error fetching students:', err);
        setError('Failed to fetch students');
      } finally {
        setFetchingStudents(false);
      }
    };

    fetchStudents();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setProjectData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleStudentToggle = (studentId) => {
    setSelectedStudents(prev => {
      if (prev.includes(studentId)) {
        return prev.filter(id => id !== studentId);
      } else {
        return [...prev, studentId];
      }
    });
  };

  const handleSelectAll = () => {
    const filtered = getFilteredStudents();
    const filteredIds = filtered.map(s => s.id);
    
    if (filteredIds.every(id => selectedStudents.includes(id))) {
      setSelectedStudents(prev => prev.filter(id => !filteredIds.includes(id)));
    } else {
      setSelectedStudents(prev => [...new Set([...prev, ...filteredIds])]);
    }
  };

  const getFilteredStudents = () => {
    if (!searchTerm.trim()) return students;
    
    const term = searchTerm.toLowerCase();
    return students.filter(student => 
      (student.fullName || student.full_name || '').toLowerCase().includes(term) ||
      (student.email || '').toLowerCase().includes(term) ||
      (student.id || '').toLowerCase().includes(term)
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const projectId = await createProject(projectData, teacherId);
      
      if (selectedStudents.length > 0) {
        await assignStudentsToProject(projectId, selectedStudents);
      }

      setSuccess(true);
      setProjectData({
        title: '',
        description: '',
        deadline: '',
        instructions: '',
        category: '',
        maxScore: 100
      });
      setSelectedStudents([]);
      setSearchTerm('');

      setTimeout(() => {
        setSuccess(false);
        if (onProjectCreated) {
          onProjectCreated(projectId);
        }
      }, 2000);
    } catch (err) {
      setError(err.message);
      console.error('Error creating project:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredStudents = getFilteredStudents();

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '2px solid #e5e7eb',
        padding: '1.5rem',
        maxWidth: '80rem',
        marginLeft: 'auto',
        marginRight: 'auto'
      }}>
        <div style={{
          borderBottom: '2px solid #e5e7eb',
          paddingBottom: '1rem',
          marginBottom: '1.5rem'
        }}>
          <h2 style={{ fontSize: '1.875rem', fontWeight: '700', color: '#1f2937' }}>
            📋 Create New Project
          </h2>
          <p style={{ color: '#6b7280', marginTop: '0.25rem', fontSize: '0.875rem' }}>
            Define project details and assign students
          </p>
        </div>

        {error && (
          <div style={{
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: '#fee2e2',
            borderLeft: '4px solid #dc2626',
            borderRadius: '4px'
          }}>
            <p style={{ fontWeight: '600', color: '#991b1b', marginBottom: '0.25rem' }}>⚠️ Error</p>
            <p style={{ fontSize: '0.875rem', color: '#7f1d1d' }}>{error}</p>
          </div>
        )}

        {success && (
          <div style={{
            marginBottom: '1.5rem',
            padding: '1rem',
            backgroundColor: '#f0fdf4',
            borderLeft: '4px solid #16a34a',
            borderRadius: '4px'
          }}>
            <p style={{ fontWeight: '600', color: '#15803d', marginBottom: '0.25rem' }}>✓ Success!</p>
            <p style={{ fontSize: '0.875rem', color: '#166534' }}>Project created successfully</p>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Basic Information Section */}
          <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#1f2937', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              📋 Basic Information
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
                  Project Title <span style={{ color: '#ca404f' }}>*</span>
                </label>
                <input
                  type="text"
                  name="title"
                  value={projectData.title}
                  onChange={handleInputChange}
                  required
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
                  placeholder="e.g., Build a Weather Dashboard"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
                    Category
                  </label>
                  <input
                    type="text"
                    name="category"
                    value={projectData.category}
                    onChange={handleInputChange}
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
                    placeholder="e.g., Web Development"
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
                    Max Score <span style={{ color: '#ca404f' }}>*</span>
                  </label>
                  <input
                    type="number"
                    name="maxScore"
                    value={projectData.maxScore}
                    onChange={handleInputChange}
                    min="0"
                    required
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
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
                  Deadline <span style={{ color: '#ca404f' }}>*</span>
                </label>
                <input
                  type="datetime-local"
                  name="deadline"
                  value={projectData.deadline}
                  onChange={handleInputChange}
                  required
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
                />
              </div>
            </div>
          </div>

          {/* Description & Instructions Section */}
          <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#1f2937', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              📝 Description & Instructions
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
                  Description <span style={{ color: '#ca404f' }}>*</span>
                </label>
                <textarea
                  name="description"
                  value={projectData.description}
                  onChange={handleInputChange}
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: '2px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                    fontFamily: 'inherit',
                    transition: 'border-color 0.2s',
                    minHeight: '6rem',
                    resize: 'vertical'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#ca404f'}
                  onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  placeholder="Provide a brief overview of the project..."
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
                  Detailed Instructions
                </label>
                <textarea
                  name="instructions"
                  value={projectData.instructions}
                  onChange={handleInputChange}
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
                  placeholder="Enter step-by-step instructions, requirements, and guidelines..."
                />
              </div>
            </div>
          </div>

          {/* Assign Students Section */}
          <div style={{ backgroundColor: '#f9fafb', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                👥 Assign Students
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Selected: <span style={{ fontWeight: '700', color: '#ca404f' }}>{selectedStudents.length}</span> / {students.length}
                </span>
                <button
                  type="button"
                  onClick={handleSelectAll}
                  style={{
                    padding: '0.375rem 0.75rem',
                    fontSize: '0.75rem',
                    backgroundColor: 'white',
                    border: '2px solid #e5e7eb',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#ca404f';
                    e.currentTarget.style.color = '#ca404f';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e5e7eb';
                    e.currentTarget.style.color = '#1f2937';
                  }}
                >
                  {filteredStudents.every(s => selectedStudents.includes(s.id)) ? 'Deselect All' : 'Select All'}
                </button>
              </div>
            </div>

            {/* Search Bar */}
            <div style={{ marginBottom: '1rem', position: 'relative' }}>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="🔍 Search students by name, email, or ID..."
                style={{
                  width: '100%',
                  padding: '0.75rem 0.75rem 0.75rem 2.5rem',
                  border: '2px solid #e5e7eb',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#ca404f'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              />
            </div>

            {fetchingStudents ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>
                <div style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⏳</div>
                <p style={{ color: '#6b7280', marginTop: '0.75rem', fontSize: '0.875rem' }}>Loading students...</p>
              </div>
            ) : filteredStudents.length === 0 ? (
              <div style={{
                padding: '2rem',
                backgroundColor: 'white',
                border: '2px dashed #e5e7eb',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</p>
                <p style={{ color: '#6b7280', fontWeight: '500', fontSize: '0.875rem' }}>
                  {searchTerm ? 'No students match your search' : 'No students found in the system'}
                </p>
                {searchTerm && (
                  <button
                    type="button"
                    onClick={() => setSearchTerm('')}
                    style={{
                      marginTop: '0.75rem',
                      color: '#ca404f',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '600'
                    }}
                  >
                    Clear search
                  </button>
                )}
              </div>
            ) : (
              <div style={{
                backgroundColor: 'white',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                overflow: 'hidden',
                maxHeight: '24rem',
                overflowY: 'auto'
              }}>
                {filteredStudents.map((student, index) => (
                  <div
                    key={student.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '1rem',
                      borderTop: index !== 0 ? '1px solid #e5e7eb' : 'none',
                      backgroundColor: selectedStudents.includes(student.id) ? '#f9fafb' : 'white',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onClick={() => handleStudentToggle(student.id)}
                    onMouseEnter={(e) => {
                      if (!selectedStudents.includes(student.id)) {
                        e.currentTarget.style.backgroundColor = '#f3f4f6';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!selectedStudents.includes(student.id)) {
                        e.currentTarget.style.backgroundColor = 'white';
                      }
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedStudents.includes(student.id)}
                      onChange={() => handleStudentToggle(student.id)}
                      style={{
                        width: '1.25rem',
                        height: '1.25rem',
                        cursor: 'pointer',
                        accentColor: '#ca404f'
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div style={{ marginLeft: '1rem', flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <div style={{
                          width: '2.5rem',
                          height: '2.5rem',
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #ca404f, #e74c3c)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontWeight: '700',
                          fontSize: '1rem'
                        }}>
                          {(student.fullName || student.full_name || student.email)[0].toUpperCase()}
                        </div>
                        <div>
                          <p style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>
                            {student.fullName || student.full_name || 'Unnamed Student'}
                          </p>
                          <p style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                            {student.email}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      backgroundColor: '#f3f4f6',
                      padding: '0.375rem 0.75rem',
                      borderRadius: '9999px',
                      color: '#6b7280',
                      fontFamily: 'monospace'
                    }}>
                      {student.id.substring(0, 8)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              type="button"
              onClick={() => onProjectCreated && onProjectCreated()}
              style={{
                flex: 1,
                padding: '0.75rem 1.5rem',
                border: '2px solid #e5e7eb',
                backgroundColor: 'white',
                borderRadius: '6px',
                color: '#6b7280',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
                e.currentTarget.style.borderColor = '#d1d5db';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'white';
                e.currentTarget.style.borderColor = '#e5e7eb';
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                flex: 1,
                padding: '0.75rem 1.5rem',
                backgroundColor: loading ? '#d1d5db' : '#ca404f',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                boxShadow: loading ? 'none' : '0 4px 6px rgba(202, 64, 79, 0.2)'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.backgroundColor = '#b0303f';
                  e.currentTarget.style.boxShadow = '0 8px 12px rgba(202, 64, 79, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.backgroundColor = '#ca404f';
                  e.currentTarget.style.boxShadow = '0 4px 6px rgba(202, 64, 79, 0.2)';
                }
              }}
            >
              {loading ? '⏳ Creating...' : '✓ Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProjectCreation;