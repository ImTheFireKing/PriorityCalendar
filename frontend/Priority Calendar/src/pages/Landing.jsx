import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { api } from '../api';
import Nav from '../components/Nav';
import './Landing.css';

const features = [
  {
    title: 'Get recommendations for what to do.',
    gradient: 'linear-gradient(135deg, #E8A84C 0%, #C97B20 60%, #F0C060 100%)',
    noise: true,
  },
  {
    title: 'See your month at a glance.',
    gradient: 'radial-gradient(circle at 30% 50%, #5BC8DC 0%, #2EAABF 40%, #1A8A9E 100%)',
    dots: true,
  },
  {
    title: 'Add tasks and events — including those Canvas assignments.',
    gradient: 'linear-gradient(145deg, #F0D4A0 0%, #6DC4B0 50%, #2A9E8A 100%)',
  },
];

export default function Landing() {
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse) => {
    const res = await fetch(api('/api/auth/google'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ token: credentialResponse.access_token}),
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('pc_uid', data.uid);
      navigate(data.onboarded ? '/dashboard' : '/onboarding');
    }
  };

  // Programmatic Google popup — no visible Google button needed
  const triggerGoogleLogin = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => console.error('Google login failed'),
    flow: 'implicit',
  });

  return (
    <div className="landing">
      <Nav onAuthTrigger={triggerGoogleLogin} />

      <section className="hero">
        <h1 className="hero-headline">
          Every day has a<br /> strategy. This is yours.
        </h1>
        <p className="hero-sub">
          Stop drowning in hundreds of deadlines — float above them instead.
        </p>
        <button className="hero-cta" onClick={triggerGoogleLogin}>
          Get Started
        </button>
      </section>

      <section className="features">
        {features.map((f, i) => (
          <div className="feature-card" key={i}>
            <p className="feature-title">{f.title}</p>
            <div
              className={`feature-img${f.noise ? ' feature-img--noise' : ''}${f.dots ? ' feature-img--dots' : ''}`}
              style={{ background: f.gradient }}
            />
          </div>
        ))}
      </section>

      <footer className="footer">
        <div className="footer-social">
          <a href="#" aria-label="Instagram">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="2" width="20" height="20" rx="5"/>
              <circle cx="12" cy="12" r="4"/>
              <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/>
            </svg>
          </a>
          <a href="#" aria-label="LinkedIn">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="2" width="20" height="20" rx="3"/>
              <path d="M7 10v7M7 7v.01M11 17v-4a2 2 0 014 0v4M11 10v7"/>
            </svg>
          </a>
          <a href="#" aria-label="X / Twitter">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
          </a>
        </div>
      </footer>
    </div>
  );
}