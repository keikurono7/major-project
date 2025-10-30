import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { User, Lock, BookOpen } from 'lucide-react';
import { getClasses, createClass } from '../services/class';

const Register = () => {
  const [credentials, setCredentials] = useState({ email: '', full_name: '', password: '' });
  const [isStudent, setIsStudent] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { signup } = useContext(AuthContext);

  // class-related state
  const [availableClasses, setAvailableClasses] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [newClassName, setNewClassName] = useState('');
  const [createdClassId, setCreatedClassId] = useState(null);
  const [creatingClass, setCreatingClass] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const list = await getClasses();
        setAvailableClasses(list || []);
        if (list && list.length) setSelectedClassId(list[0].id || list[0]._id);
      } catch (err) {
        console.error('Failed to load classes', err);
      }
    };
    load();
  }, []);

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  const handleCreateClass = async () => {
    if (!newClassName.trim()) return;
    try {
      setCreatingClass(true);
      const cls = await createClass(newClassName.trim(), null);
      setCreatedClassId(cls.id);
      setAvailableClasses((prev) => [{ id: cls.id, name: cls.name }, ...prev]);
      setSelectedClassId(cls.id);
      setNewClassName('');
    } catch (err) {
      console.error('Failed to create class', err);
    } finally {
      setCreatingClass(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const classIdForSignup = isStudent ? selectedClassId : (createdClassId || null);

      const payload = {
        username: credentials.email,
        email: credentials.email,
        fullName: credentials.full_name,
        password: credentials.password,
        role: isStudent ? 'student' : 'teacher',
        classId: classIdForSignup
      };

      await signup(payload);
      navigate(isStudent ? '/student' : '/teacher');
    } catch (err) {
      setError(err.message || 'Registration failed. Try a different email/username.');
    }
  };

  return (
    <div className="login-layout" style={{ minHeight: '100vh' }}>
      <div className="login-left" style={{ background: 'linear-gradient(180deg, #ca404f 0%, #a7373f 100%)', color: 'white', padding: 48 }}>
        <div className="brand" style={{ textAlign: 'center', maxWidth: 360 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 96, height: 96, backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: '50%', margin: '0 auto' }}>
            <BookOpen size={44} />
          </div>
          <h1>Knowell</h1>
          <p style={{ marginTop: 8 }}>Create an account to get started</p>
        </div>
      </div>

      <div className="login-right" style={{ padding: 32, background: '#f3f4f6' }}>
        <div className="login-card" style={{ maxWidth: 520, margin: '0 auto', background: 'white', borderRadius: 16, padding: 24 }}>
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ margin: 0 }}>Create account</h2>
            <p style={{ margin: 0, color: '#6b7280' }}>Sign up as a student or teacher</p>
          </div>

          {error && (
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#fee2e2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: 8 }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', backgroundColor: '#f8fafc', borderRadius: 8, padding: 4, border: '1px solid #e2e8f0' }}>
              <button
                type="button"
                onClick={() => setIsStudent(true)}
                style={{
                  flex: 1, padding: 12, borderRadius: 6, border: 'none', cursor: 'pointer',
                  backgroundColor: isStudent ? 'white' : 'transparent', color: isStudent ? '#ca404f' : '#6b7280'
                }}
              >
                Student
              </button>
              <button
                type="button"
                onClick={() => setIsStudent(false)}
                style={{
                  flex: 1, padding: 12, borderRadius: 6, border: 'none', cursor: 'pointer',
                  backgroundColor: !isStudent ? 'white' : 'transparent', color: !isStudent ? '#7c1d21' : '#6b7280'
                }}
              >
                Teacher
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Email</label>
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', right: 12, top: 10, pointerEvents: 'none' }}><User size={18} color="#9ca3af" /></div>
                <input
                  name="email"
                  type="email"
                  required
                  value={credentials.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  style={{ width: '100%', padding: '12px 12px', paddingRight: 40, borderRadius: 8, border: '1px solid #d1d5db' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Full name</label>
              <input
                name="full_name"
                type="text"
                required
                value={credentials.full_name}
                onChange={handleChange}
                placeholder="Your full name"
                style={{ width: '100%', padding: 12, borderRadius: 8, border: '1px solid #d1d5db' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Password</label>
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', right: 12, top: 10, pointerEvents: 'none' }}><Lock size={18} color="#9ca3af" /></div>
                <input
                  name="password"
                  type="password"
                  required
                  value={credentials.password}
                  onChange={handleChange}
                  placeholder="Create a password"
                  style={{ width: '100%', padding: '12px 12px', paddingRight: 40, borderRadius: 8, border: '1px solid #d1d5db' }}
                />
              </div>
            </div>

            {/* class controls */}
            {isStudent && (
              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Select class</label>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                  required
                  style={{ width: '100%', padding: 12, borderRadius: 8, border: '1px solid #d1d5db' }}
                >
                  {availableClasses.length === 0 && <option value="">No classes available</option>}
                  {availableClasses.map((c) => (
                    <option key={c.id || c._id} value={c.id || c._id}>{c.name}</option>
                  ))}
                </select>
              </div>
            )}

            {!isStudent && (
              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Create a class (optional)</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    placeholder="New class name"
                    value={newClassName}
                    onChange={(e) => setNewClassName(e.target.value)}
                    style={{ flex: 1, padding: 12, borderRadius: 8, border: '1px solid #d1d5db' }}
                  />
                  <button type="button" onClick={handleCreateClass} disabled={creatingClass || !newClassName.trim()} style={{ padding: '12px 16px', borderRadius: 8, background: '#ca404f', color: 'white', border: 'none', cursor: 'pointer' }}>
                    {creatingClass ? 'Creating...' : 'Create'}
                  </button>
                </div>
                {createdClassId && <small>Created class selected</small>}
              </div>
            )}

            <button
              type="submit"
              style={{ width: '100%', background: '#ca404f', color: 'white', padding: '12px', borderRadius: 8, border: 'none', fontWeight: 600, cursor: 'pointer' }}
            >
              Create account
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <p style={{ color: '#6b7280' }}>
              Already have an account?{' '}
              <button onClick={() => navigate('/login')} style={{ color: '#ca404f', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
                Sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;