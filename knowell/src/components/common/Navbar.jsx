import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';

const Navbar = ({ user }) => {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase();
  };

  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <Link to="/" className="logo">Knowell</Link>
        
        {user && (
          <div className="nav-menu">
            <div className="flex items-center gap-2">
              <div className="avatar">
                {getInitials(user.fullName)}
              </div>
              <div>
                <div style={{ fontWeight: 500 }}>{user.fullName}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--secondary)' }}>
                  {user.role === 'student' ? 'Student' : 'Teacher'}
                </div>
              </div>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;