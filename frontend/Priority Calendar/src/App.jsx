import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import Landing from './pages/Landing';
import About from './pages/About';
import Changelog from './pages/Changelog';
import './index.css';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Onboarding from './pages/Onboarding';

const PUBLIC_PATHS = new Set(['/', '/about', '/changelog']);

function ThemeManager() {
  const { pathname } = useLocation();
  useEffect(() => {
    if (PUBLIC_PATHS.has(pathname)) {
      document.documentElement.removeAttribute('data-theme');
    } else {
      const saved = localStorage.getItem('pc_theme') || 'peach';
      document.documentElement.setAttribute('data-theme', saved);
    }
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeManager />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/changelog" element={<Changelog />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/onboarding" element={<Onboarding />} />
      </Routes>
    </BrowserRouter>
  );
}
