import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { api } from '../api';
import Nav from '../components/Nav';
import './Landing.css';
import recommendedImg from '../assets/recommended.png';
import canvasDemoImg from '../assets/CanvasDemo.png';

const features = [
  {
    title: 'Get recommendations for what to do.',
    image: recommendedImg,
  },
  {
    title: 'See your month at a glance.',
    gradient: 'radial-gradient(circle at 30% 50%, #5BC8DC 0%, #2EAABF 40%, #1A8A9E 100%)',
    dots: true,
  },
  {
    title: 'Add tasks and events — including those Canvas assignments.',
    image: canvasDemoImg,
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
            {f.image
              ? <img src={f.image} className="feature-img" alt={f.title} />
              : <div className={`feature-img${f.dots ? ' feature-img--dots' : ''}`} style={{ background: f.gradient }} />
            }
          </div>
        ))}
      </section>

    </div>
  );
}