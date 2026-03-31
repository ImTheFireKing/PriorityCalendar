import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import './Onboarding.css';

const DAY_LABELS = [
  { key: 'Mo',  label: 'Mon' },
  { key: 'Tu',  label: 'Tue' },
  { key: 'Wed', label: 'Wed' },
  { key: 'Th',  label: 'Thu' },
  { key: 'F',   label: 'Fri' },
  { key: 'Sa',  label: 'Sat' },
  { key: 'Su',  label: 'Sun' },
];

const EXPIRY_OPTIONS = [
  { value: '1', label: '1 Week'  },
  { value: '2', label: '2 Weeks' },
  { value: '4', label: '4 Weeks' },
];

const TOTAL_STEPS = 4;

export default function Onboarding() {
  const navigate = useNavigate();
  const uid = localStorage.getItem('pc_uid');

  const [step, setStep]         = useState(1);
  const [lazyDays, setLazyDays] = useState([]);
  const [tLimit, setTLimit]     = useState(15);
  const [eLimit, setELimit]     = useState(3);
  const [expiry, setExpiry]     = useState('2');
  const [saving, setSaving]     = useState(false);

  const toggleLazyDay = (day) => {
    setLazyDays(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    );
  };

  const handleFinish = async () => {
    if (!uid) return;
    setSaving(true);
    try {
      // Save settings first
      await fetch(api(`/api/users/${uid}/settings`), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          newDays:       lazyDays,
          newTLimit:     tLimit,
          newELimit:     eLimit,
          newExpiration: expiry,
        }),
      });
      // Mark onboarded (refreshes session cookie)
      await fetch(api(`/api/users/${uid}/onboarding`), {
        method: 'POST',
        credentials: 'include',
      });
      // Signal dashboard to run the tour
      localStorage.setItem('pc_tour_pending', 'true');
      navigate('/dashboard');
    } finally {
      setSaving(false);
    }
  };

  const progress = ((step - 1) / (TOTAL_STEPS - 1)) * 100;

  return (
    <div className="onboarding-page">
      <div className="onboarding-card">

        {/* Progress bar */}
        <div className="onboarding-progress-track">
          <div className="onboarding-progress-fill" style={{ width: `${progress}%` }} />
        </div>

        {/* ── Step 1: Welcome ── */}
        {step === 1 && (
          <div className="onboarding-step">
            <div className="onboarding-icon">📅</div>
            <h1>Welcome to Priority Calendar</h1>
            <p>
              Priority Calendar figures out <em>what</em> to work on and <em>how much</em> of it to
              tackle each day — so you never wake up overwhelmed by a pile of deadlines.
            </p>
            <p>
              It'll take about 30 seconds to get you set up. We just need to know a
              couple of things about how you like to work.
            </p>
            <div className="onboarding-actions">
              <button className="onboarding-next-btn" onClick={() => setStep(2)}>
                Let's go →
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Lazy Days ── */}
        {step === 2 && (
          <div className="onboarding-step">
            <div className="onboarding-step-label">Step 1 of 2</div>
            <h2>Pick your lazy days</h2>
            <p>
              On these days the recommender will dial back on tasks — useful for
              weekends, game days, or any day you know you won't be at full capacity.
            </p>
            <div className="day-toggles">
              {DAY_LABELS.map(({ key, label }) => (
                <button
                  key={key}
                  type="button"
                  className={`day-toggle${lazyDays.includes(key) ? ' day-toggle--active' : ''}`}
                  onClick={() => toggleLazyDay(key)}
                >
                  {label}
                </button>
              ))}
            </div>
            <p className="onboarding-hint">
              {lazyDays.length === 0
                ? 'No lazy days selected — you\'re a machine.'
                : `Lazy: ${lazyDays.map(k => DAY_LABELS.find(d => d.key === k)?.label).join(', ')}`}
            </p>
            <div className="onboarding-actions">
              <button className="onboarding-back-btn" onClick={() => setStep(1)}>← Back</button>
              <button className="onboarding-next-btn" onClick={() => setStep(3)}>Next →</button>
            </div>
          </div>
        )}

        {/* ── Step 3: Limits ── */}
        {step === 3 && (
          <div className="onboarding-step">
            <div className="onboarding-step-label">Step 2 of 2</div>
            <h2>Set your daily limits</h2>
            <p>
              How many tasks and events should the recommender surface per day?
              You can always change these in Settings.
            </p>

            <div className="onboarding-limits">
              <label>
                Max Tasks per day
                <div className="onboarding-number-row">
                  <button type="button" className="num-btn" onClick={() => setTLimit(v => Math.max(1, v - 1))}>−</button>
                  <span className="num-display">{tLimit}</span>
                  <button type="button" className="num-btn" onClick={() => setTLimit(v => Math.min(50, v + 1))}>+</button>
                </div>
              </label>

              <label>
                Max Events per day
                <div className="onboarding-number-row">
                  <button type="button" className="num-btn" onClick={() => setELimit(v => Math.max(1, v - 1))}>−</button>
                  <span className="num-display">{eLimit}</span>
                  <button type="button" className="num-btn" onClick={() => setELimit(v => Math.min(20, v + 1))}>+</button>
                </div>
              </label>

              <label>
                How long to keep incomplete Tasks
                <select value={expiry} onChange={(e) => setExpiry(e.target.value)}>
                  {EXPIRY_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </label>
            </div>

            <div className="onboarding-actions">
              <button className="onboarding-back-btn" onClick={() => setStep(2)}>← Back</button>
              <button className="onboarding-next-btn" onClick={() => setStep(4)}>Next →</button>
            </div>
          </div>
        )}

        {/* ── Step 4: Done ── */}
        {step === 4 && (
          <div className="onboarding-step onboarding-step--final">
            <div className="onboarding-icon">🎉</div>
            <h2>You're all set</h2>
            <p>
              Your preferences are saved. We'll give you a quick tour of the dashboard
              so you know where everything lives.
            </p>
            <div className="onboarding-actions">
              <button className="onboarding-back-btn" onClick={() => setStep(3)}>← Back</button>
              <button
                className="onboarding-next-btn"
                onClick={handleFinish}
                disabled={saving}
              >
                {saving ? 'Saving…' : 'Take me to the dashboard →'}
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
