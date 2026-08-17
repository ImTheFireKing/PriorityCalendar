import { Link, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuthTrigger } from '../hooks/useAuthTrigger';
import './Nav.css';
import logo from '../assets/PriorityCalendarSmallLogoTransparent.png';

const DASHBOARD_PATHS = ['/dashboard', '/settings'];

export default function Nav() {
  const location = useLocation();
  const navigate = useNavigate();
  const isDashboard = DASHBOARD_PATHS.some(p => location.pathname.startsWith(p));
  const { trigger: triggerLogin, authLoading } = useAuthTrigger();

  const handleLogOut = () => {
    fetch(api('/api/auth/logout'), {
      method: 'POST',
      credentials: 'include',
    });
    localStorage.removeItem('pc_uid');
    navigate('/');
  };

  return (
    <>
      {authLoading && (
        <div className="auth-overlay">
          <div className="auth-overlay-spinner" />
          <p className="auth-overlay-text">Signing you in…</p>
        </div>
      )}

      {isDashboard ? (
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
      ) : (
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
            <button className="nav-logout" onClick={triggerLogin}>Log In</button>
          </div>
        </nav>
      )}
    </>
  );
}
