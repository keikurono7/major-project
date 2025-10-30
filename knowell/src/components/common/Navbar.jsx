import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import { createClass, getClassesForUser } from '../../services/class';
import { getAllSubjects } from '../../services/sub';

const Navbar = (props) => {
  const navigate = useNavigate();
  const ctx = useContext(AuthContext) || {};
  const ctxUser = ctx.currentUser || ctx.user || null;
  const user = props.user || ctxUser;

  const [classes, setClasses] = useState([]);
  const [currentClassId, setCurrentClassId] = useState(localStorage.getItem('currentClassId') || '');
  const [loadingClasses, setLoadingClasses] = useState(false);

  // subject state for students
  const [subjects, setSubjects] = useState([]);
  const [currentSubjectId, setCurrentSubjectId] = useState(localStorage.getItem('currentSubjectId') || '');
  const [loadingSubjects, setLoadingSubjects] = useState(false);

  // create-class UI state
  const [showCreate, setShowCreate] = useState(false);
  const [newClassName, setNewClassName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  useEffect(() => {
    const load = async () => {
      if (!user) {
        setClasses([]);
        setCurrentClassId('');
        return;
      }
      setLoadingClasses(true);
      try {
        const list = await getClassesForUser(user.id || user.uid || user._id, user.role);
        setClasses(list || []);
        const savedClassId = localStorage.getItem('currentClassId');
        const initialClassId = savedClassId || (list && list.length ? (list[0].id || list[0]._id) : '');
        setCurrentClassId(initialClassId);
        if (initialClassId) {
          localStorage.setItem('currentClassId', initialClassId);
        }
      } catch (err) {
        console.error('Failed to load classes in Navbar', err);
        setClasses([]);
        setCurrentClassId('');
      } finally {
        setLoadingClasses(false);
      }
    };
    load();
  }, [user]);

  // Load subjects when component mounts (for students only)
  useEffect(() => {
    const loadSubjects = async () => {
      if (!user || user.role === 'teacher') {
        setSubjects([]);
        return;
      }
      setLoadingSubjects(true);
      try {
        // Use the same method as AssignmentInterface - get all subjects
        const subjectList = await getAllSubjects();
        setSubjects(subjectList || []);
        
        const savedSubjectId = localStorage.getItem('currentSubjectId');
        const initialSubjectId = savedSubjectId || (subjectList.length ? subjectList[0].id : '');
        setCurrentSubjectId(initialSubjectId);
        if (initialSubjectId) {
          localStorage.setItem('currentSubjectId', initialSubjectId);
        }
      } catch (err) {
        console.error('Failed to load subjects in Navbar', err);
        setSubjects([]);
      } finally {
        setLoadingSubjects(false);
      }
    };
    loadSubjects();
  }, [user]);

  const onChangeClass = (e) => {
    const val = e.target.value;
    if (val === '__create__') {
      setShowCreate(true);
      return;
    }
    setCurrentClassId(val);
    localStorage.setItem('currentClassId', val);
  };

  const onChangeSubject = (e) => {
    const val = e.target.value;
    setCurrentSubjectId(val);
    localStorage.setItem('currentSubjectId', val);
    // Trigger a custom event so other components can react
    window.dispatchEvent(new Event('subjectChanged'));
  };

  const handleCreate = async () => {
    if (!newClassName.trim()) return;
    if (!user) {
      setCreateError('Sign in to create a class');
      return;
    }
    setCreateError('');
    setCreating(true);
    try {
      const teacherId = user.id || user.uid || user._id || null;
      const cls = await createClass(newClassName.trim(), teacherId);
      try {
        const list = await getClassesForUser(teacherId, 'teacher');
        setClasses(list || []);
        setCurrentClassId(cls.id || cls._id);
        localStorage.setItem('currentClassId', cls.id || cls._id);
      } catch (refreshErr) {
        setClasses((prev) => [{ id: cls.id, name: cls.name }, ...prev]);
        setCurrentClassId(cls.id);
        localStorage.setItem('currentClassId', cls.id);
      }
      setNewClassName('');
      setShowCreate(false);
    } catch (err) {
      console.error('Create class failed', err);
      setCreateError(err.message || 'Failed to create class');
    } finally {
      setCreating(false);
    }
  };

  const currentClass = classes.find((c) => (c.id || c._id) === currentClassId);
  const currentSubject = subjects.find((s) => s.id === currentSubjectId);

  return (
    <nav className="navbar" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12 }}>
      <div style={{ fontWeight: 700 }}>Knowell</div>

      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
        {user && (
          <>
            {user.role === 'teacher' ? (
              <>
                <select value={currentClassId || ''} onChange={onChangeClass} style={{ padding: 8, borderRadius: 8 }}>
                  {loadingClasses && <option>Loading classes...</option>}
                  {!loadingClasses && classes.length === 0 && <option value="">No classes</option>}
                  {classes.map((c) => (
                    <option key={c.id || c._id} value={c.id || c._id}>{c.name}</option>
                  ))}
                  <option value="__create__">Create a class...</option>
                </select>

                {showCreate && (
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <input
                      value={newClassName}
                      onChange={(e) => setNewClassName(e.target.value)}
                      placeholder="New class name"
                      style={{ padding: 8, borderRadius: 8, border: '1px solid #d1d5db' }}
                    />
                    <button onClick={handleCreate} disabled={creating || !newClassName.trim()} style={{ padding: '8px 12px', borderRadius: 8, background: '#ca404f', color: '#fff', border: 'none', cursor: 'pointer' }}>
                      {creating ? 'Creating...' : 'Create'}
                    </button>
                    <button onClick={() => { setShowCreate(false); setNewClassName(''); }} style={{ padding: 8, borderRadius: 8, background: 'transparent', border: '1px solid #e5e7eb', cursor: 'pointer' }}>
                      Cancel
                    </button>
                  </div>
                )}
                {createError && <div style={{ color: '#b91c1c', marginLeft: 8 }}>{createError}</div>}
              </>
            ) : (
              <>
                <div style={{ padding: 8 }}>{currentClass ? currentClass.name : 'No class'}</div>
                <select value={currentSubjectId} onChange={onChangeSubject} style={{ padding: 8, borderRadius: 8 }}>
                  {loadingSubjects && <option>Loading subjects...</option>}
                  {!loadingSubjects && subjects.length === 0 && <option value="">No subjects available</option>}
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>{s.name || s.title || 'Unnamed Subject'}</option>
                  ))}
                </select>
              </>
            )}
          </>
        )}

        {user ? (
          <>
            <button onClick={() => navigate('/profile')} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
              {user.fullName || user.name || user.email}
            </button>
            <button onClick={() => { if (ctx.logout) ctx.logout(); navigate('/login'); }} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#ca404f' }}>
              Sign out
            </button>
          </>
        ) : (
          <button onClick={() => navigate('/login')} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            Sign in
          </button>
        )}
      </div>
    </nav>
  );
};

export default Navbar;