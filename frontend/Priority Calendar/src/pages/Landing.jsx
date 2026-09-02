import Nav from '../components/Nav';
import { GoogleLogin } from '@react-oauth/google';
import { useAuthTrigger } from '../hooks/useAuthTrigger';
import AuthOverlay from '../components/AuthOverlay';
import './Landing.css';
import recommendedImg from '../assets/recommended.png';
import canvasDemoImg from '../assets/CanvasDemo.png';
import calendarAgendaImg from '../assets/calendarAgendaWide.png'
import calendarAgendaTallImg from '../assets/calendarAgenda.png'

const features = [
  {
    title: 'Get recommendations for what to do.',
    image: recommendedImg,
  },
  {
    title: 'Add tasks and events — including those Canvas assignments.',
    image: canvasDemoImg,
  },
  {
    title: 'See your month at a glance.',
    image: calendarAgendaImg,
    mobileImage: calendarAgendaTallImg,
    wide: true,
  },
];

export default function Landing() {
  const { googleLoginProps, authLoading, slowTip, authError, dismissError } = useAuthTrigger();

  if (authLoading || authError) return (
    <AuthOverlay
      authLoading={authLoading}
      slowTip={slowTip}
      authError={authError}
      retryButton={<GoogleLogin {...googleLoginProps} />}
      onDismiss={dismissError}
    />
  );

  return (
    <div className="landing">
      <Nav />

      <section className="hero">
        <h1 className="hero-headline">
          Every day has a<br /> strategy. This is yours.
        </h1>
        <p className="hero-sub">
          Stop drowning in hundreds of deadlines — float above them instead.
        </p>
        <div className="hero-cta-google">
          <GoogleLogin {...googleLoginProps} />
        </div>
      </section>

      <section className="features">
        {features.map((f, i) => (
          <div className={`feature-card${f.wide ? ' feature-card--wide' : ''}`} key={i}>
            <p className="feature-title">{f.title}</p>
            {f.image
              ? (
                <picture className="feature-picture">
                  {f.mobileImage && <source media="(max-width: 600px)" srcSet={f.mobileImage} />}
                  <img src={f.image} className="feature-img" alt={f.title} />
                </picture>
              )
              : <div className={`feature-img${f.dots ? ' feature-img--dots' : ''}`} style={{ background: f.gradient }} />
            }
          </div>
        ))}
      </section>

    </div>
  );
}