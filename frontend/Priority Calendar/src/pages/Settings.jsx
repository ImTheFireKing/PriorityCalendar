import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Nav from '../components/Nav';
import './Settings.css';

// Matches pcClasses.py Day.validdays keys exactly
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

// Reverse-map timedelta seconds → "1"/"2"/"4" in case backend returns raw timedelta
function parseExpiry(raw) {
  if (!raw) return '2';
  if (typeof raw === 'string' && ['1','2','4'].includes(raw)) return raw;
  const weeks = Math.round(Number(raw) / 604800);
  if (weeks === 1) return '1';
  if (weeks === 4) return '4';
  return '2';
}

export default function Settings() {
  const navigate = useNavigate();
  const uid = localStorage.getItem('pc_uid');
  const apiUrl = '/api';

  const [lazyDays, setLazyDays] = useState([]);
  const [tLimit,   setTLimit]   = useState(15);
  const [eLimit,   setELimit]   = useState(3);
  const [expiry,   setExpiry]   = useState('2');
  const [loading,  setLoading]  = useState(true);
  const [saved,    setSaved]    = useState(false);

  useEffect(() => {
    if (!uid) { navigate('/login'); return; }

    const fetchAll = async () => {
      try {
        const [lazyRes, tRes, eRes, expRes] = await Promise.all([
          fetch(`${apiUrl}/users/${uid}/settings?settingField=lazy`, {credentials: "include"}),
          fetch(`${apiUrl}/users/${uid}/settings?settingField=Tlimit`, {credentials: "include"}),
          fetch(`${apiUrl}/users/${uid}/settings?settingField=Elimit`, {credentials: "include"}),
          fetch(`${apiUrl}/users/${uid}/settings?settingField=expired`, {credentials: "include"}),
        ]);
        if (lazyRes.ok) setLazyDays(await lazyRes.json());
        if (tRes.ok)    setTLimit(await tRes.json());
        if (eRes.ok)    setELimit(await eRes.json());
        if (expRes.ok)  setExpiry(parseExpiry(await expRes.json()));
      } catch (err) {
        console.error('Failed to load settings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [uid]);

  const toggleLazyDay = (day) => {
    setLazyDays(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    );
  };

  const handleSave = async () => {
    try {
      const res = await fetch(`${apiUrl}/users/${uid}/settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          newDays:       lazyDays,
          newTLimit:     tLimit,
          newELimit:     eLimit,
          newExpiration: expiry,
        }),
        credentials: "include",
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
      }
    } catch (err) {
      console.error('Failed to save settings:', err);
    }
  };

  if (loading) return (
    <div className="settings-page">
      <Nav />
      <p className="settings-loading">Loading settings...</p>
    </div>
  );

  return (
    <div className="settings-page">
      <Nav />
      <main className="settings-main">
        <div className="settings-card">
          <h2>Settings</h2>

          {/* ── Lazy Days ── */}
          <section className="settings-section">
            <h3>Lazy Days</h3>
            <p className="settings-desc">
              Days where the recommender will ease up on heavy tasks.
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
          </section>

          {/* ── Rec Limits ── */}
          <section className="settings-section">
            <h3>Recommendation Limits</h3>
            <p className="settings-desc">
              Max number of tasks and events surfaced by the recommender per day.
            </p>
            <div className="settings-row">
              <label>
                Task Limit
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={tLimit}
                  onChange={(e) => setTLimit(Number(e.target.value))}
                />
              </label>
              <label>
                Event Limit
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={eLimit}
                  onChange={(e) => setELimit(Number(e.target.value))}
                />
              </label>
            </div>
          </section>

          {/* ── Expiration Window ── */}
          <section className="settings-section">
            <h3>Task Expiration Window</h3>
            <p className="settings-desc">
              How far ahead the recommender looks for upcoming tasks.
            </p>
            <select value={expiry} onChange={(e) => setExpiry(e.target.value)}>
              {EXPIRY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </section>

          <div className="settings-actions">
            <button className="save-btn" onClick={handleSave}>
              {saved ? '✓ Saved!' : 'Save Changes'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}