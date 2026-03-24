import { Link, useLocation } from 'react-router-dom';
import './Nav.css';
import logo from '../assets/PriorityCalendarSmallLogoTransparent.png'

const navConfigs = {
  '/': [
    { label: 'About', to: '/about' },
    { label: 'Changelog', to: '/changelog' },
    { label: 'Log In', to: '/login', plain: false },
  ],
  '/about': [
    { label: 'Get Started', to: '/' },
    { label: 'Changelog', to: '/changelog' },
    { label: 'Log In', to: '/login', plain: false },
  ],
  '/changelog': [
    { label: 'About', to: '/about' },
    { label: 'Get Started', to: '/' },
    { label: 'Log In', to: '/login', plain: false },
  ],
};

export default function Nav() {
  const location = useLocation();
  const links = navConfigs[location.pathname] ?? navConfigs['/'];

  return (
    <nav className="nav">
      <Link to="/" className="nav-logo"> <img src={logo} alt="Priority Calendar Logo, Small"/> Priority Calendar</Link>
      <div className="nav-links">
        {links.map(({ label, to, plain }) => (
          <Link key={label} to={to} className={plain ? 'nav-link nav-link--plain' : 'nav-link'}>
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}