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

  const [canvasUrl,    setCanvasUrl]    = useState('');
  const [canvasToken,  setCanvasToken]  = useState('');
  const [canvasStatus, setCanvasStatus] = useState(null); // 'ok' | 'error' | null
  const [canvasLoading, setCanvasLoading] = useState(false);

  const [icsUrl,     setIcsUrl]     = useState('');
  const [icsStatus,  setIcsStatus]  = useState(null); // 'ok' | 'error' | null
  const [icsLoading, setIcsLoading] = useState(false);
  const [icsOpen,    setIcsOpen]    = useState(false);

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

  const handleCanvasConnect = async () => {
    setCanvasLoading(true);
    setCanvasStatus(null);
    try {
      const res = await fetch(`${apiUrl}/users/${uid}/canvas/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ institutionalUrl: canvasUrl, token: canvasToken }),
      });
      setCanvasStatus(res.ok ? 'ok' : 'error');
    } catch {
      setCanvasStatus('error');
    } finally {
      setCanvasLoading(false);
    }
  };

  const handleIcsConnect = async () => {
    setIcsLoading(true);
    setIcsStatus(null);
    try {
      const res = await fetch(`${apiUrl}/users/${uid}/canvas/connect/ics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ icsUrl: icsUrl }),
      });
      
      if (res.ok) {
        setIcsStatus('ok');
      } else {
        setIcsStatus('error');
      }
    } catch (err) {
      console.error('ICS Connection Error:', err);
      setIcsStatus('error');
    } finally {
      setIcsLoading(false);
    }
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
              How long the recommender will bring up tasks past their due date.
            </p>
            <select value={expiry} onChange={(e) => setExpiry(e.target.value)}>
              {EXPIRY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </section>

          {/* ── Canvas Integration ── */}
          <section className="settings-section">
            <h3>Canvas Integration</h3>
            <p className="settings-desc">
              Automatically pull in upcoming assignments. Create a Canvas Access Token or provide your Canvas Calendar's iCalendar link for a simpler setup.
            </p>
            <div className="integration-toggle-tabs">
              <button 
                className={`tab-btn ${!icsOpen ? 'active' : ''}`} 
                onClick={() => setIcsOpen(false)}
              >
                Canvas API (Recommended)
              </button>
              <button 
                className={`tab-btn ${icsOpen ? 'active' : ''}`} 
                onClick={() => setIcsOpen(true)}
              >
                Calendar Feed (ICS)
              </button>
            </div>

            {!icsOpen ? (
              <div className="canvas-connect-fields">
                <label>
                  Institution URL
                  <input
                    type="url"
                    placeholder="https://canvas.school.edu"
                    value={canvasUrl}
                    onChange={(e) => setCanvasUrl(e.target.value)}
                  />
                </label>
                <label>
                  Personal Access Token
                  <input
                    type="password"
                    placeholder="Canvas access token"
                    value={canvasToken}
                    onChange={(e) => setCanvasToken(e.target.value)}
                  />
                </label>
                <div className="canvas-connect-footer">
                  <button
                    className="canvas-connect-btn"
                    onClick={handleCanvasConnect}
                    disabled={canvasLoading || !canvasUrl || !canvasToken}
                  >
                    {canvasLoading ? 'Connecting…' : 'Connect Canvas API'}
                  </button>
                  {canvasStatus === 'ok' && <span className="status-ok">Connected! Sync started.</span>}
                  {canvasStatus === 'error' && <span className="status-error">Failed — check URL/Token.</span>}
                </div>
              </div>
            ) : (
              <div className="canvas-connect-fields">
                <label>
                  Canvas Calendar URL (ICS)
                  <input
                    type="url"
                    placeholder="https://canvas.school.edu/feeds/calendars/user_..."
                    value={icsUrl}
                    onChange={(e) => setIcsUrl(e.target.value)}
                  />
                </label>
                <p className="settings-hint">Find this in Canvas → Calendar → Calendar Feed</p>
                <div className="canvas-connect-footer">
                  <button
                    className="canvas-connect-btn"
                    onClick={handleIcsConnect}
                    disabled={icsLoading || !icsUrl}
                  >
                    {icsLoading ? 'Connecting…' : 'Connect Calendar Feed'}
                  </button>
                  {icsStatus === 'ok' && <span className="status-ok">Feed Connected! Sync started.</span>}
                  {icsStatus === 'error' && <span className="status-error">Invalid URL or unreachable feed.</span>}
                </div>
              </div>
            )}
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