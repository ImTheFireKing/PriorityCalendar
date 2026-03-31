import { Link, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api';
import './Nav.css';
import logo from '../assets/PriorityCalendarSmallLogoTransparent.png';

const DASHBOARD_PATHS = ['/dashboard', '/settings'];

export default function Nav({ onAuthTrigger }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isDashboard = DASHBOARD_PATHS.some(p => location.pathname.startsWith(p));

  const handleLogOut = () => {
    fetch(api('/api/auth/logout'), {
      method: 'POST',
      credentials: 'include',
    });
    localStorage.removeItem('pc_uid');
    navigate('/');
  };

  if (isDashboard) {
    return (
      <nav className="nav">
        <Link to="/dashboard" className="nav-logo">
          <img src={logo} alt="Priority Calendar Logo, Small" />
          Priority Calendar
        </Link>
        <div className="nav-links">
          <a href="/changelog" className="nav-link" target="_blank" rel="noreferrer">
            Changelog
          </a>
          <Link to="/settings" className="nav-link" id="tour-settings">Settings</Link>
          <button className="nav-logout" onClick={handleLogOut}>Log Out</button>
        </div>
      </nav>
    );
  }

  return (
    <nav className="nav">
      <Link to="/" className="nav-logo">
        <img src={logo} alt="Priority Calendar Logo, Small" />
        Priority Calendar
      </Link>
      <div className="nav-links">
        <Link to="/about" className="nav-link">About</Link>
        <a href="/changelog" className="nav-link" target="_blank" rel="noreferrer">
          Changelog
        </a>
        {onAuthTrigger ? (
          <button className="nav-logout" onClick={onAuthTrigger}>Log In</button>
        ) : (
          <Link to="/" className="nav-link">Log In</Link>
        )}
      </div>
    </nav>
  );
}