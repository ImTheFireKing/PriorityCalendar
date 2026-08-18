import Nav from '../components/Nav';
import { useAuthTrigger } from '../hooks/useAuthTrigger';
import './Landing.css';
import recommendedImg from '../assets/recommended.png';
import canvasDemoImg from '../assets/CanvasDemo.png';
import calendarAgendaImg from '../assets/calendarAgenda.png'

const features = [
  {
    title: 'Get recommendations for what to do.',
    image: recommendedImg,
  },
  {
    title: 'See your month at a glance.',
    image: calendarAgendaImg,
  },
  {
    title: 'Add tasks and events — including those Canvas assignments.',
    image: canvasDemoImg,
  },
];

export default function Landing() {
  const { trigger: triggerGoogleLogin } = useAuthTrigger();

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