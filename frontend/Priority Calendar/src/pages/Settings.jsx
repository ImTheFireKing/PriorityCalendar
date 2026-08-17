import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
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
  const [lazyDays, setLazyDays] = useState([]);
  const [tLimit,   setTLimit]   = useState(15);
  const [eLimit,   setELimit]   = useState(3);
  const [expiry,   setExpiry]   = useState('2');
  const [loading,  setLoading]  = useState(true);
  const [saved,    setSaved]    = useState(false);

  const [theme, setTheme] = useState(() => localStorage.getItem('pc_theme') || 'peach');

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('pc_theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const [canvasUrl,    setCanvasUrl]    = useState('');
  const [canvasToken,  setCanvasToken]  = useState('');
  const [canvasStatus, setCanvasStatus] = useState(null); // 'ok' | 'error' | 'cooldown' | null
  const [canvasLoading, setCanvasLoading] = useState(false);
  const [canvasCooldownMsg, setCanvasCooldownMsg] = useState('');

  const [icsUrl,     setIcsUrl]     = useState('');
  const [icsStatus,  setIcsStatus]  = useState(null); // 'ok' | 'error' | 'cooldown' | null
  const [icsLoading, setIcsLoading] = useState(false);
  const [icsOpen,    setIcsOpen]    = useState(false);
  const [icsCooldownMsg, setIcsCooldownMsg] = useState('');

  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError,   setDeleteError]   = useState(false);

  useEffect(() => {
    if (!uid) { navigate('/'); return; }

    const fetchAll = async () => {
      try {
        const [lazyRes, tRes, eRes, expRes] = await Promise.all([
          fetch(api(`/api/users/${uid}/settings?settingField=lazy`), {credentials: "include"}),
          fetch(api(`/api/users/${uid}/settings?settingField=Tlimit`), {credentials: "include"}),
          fetch(api(`/api/users/${uid}/settings?settingField=Elimit`), {credentials: "include"}),
          fetch(api(`/api/users/${uid}/settings?settingField=expired`), {credentials: "include"}),
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
      const res = await fetch(api(`/api/users/${uid}/canvas/connect`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ institutionalUrl: canvasUrl, token: canvasToken }),
      });
      if (res.ok) {
        setCanvasStatus('ok');
      } else if (res.status === 429) {
        const data = await res.json();
        setCanvasCooldownMsg(data.detail || 'Token cooldown active. Try again later.');
        setCanvasStatus('cooldown');
      } else {
        setCanvasStatus('error');
      }
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
      const res = await fetch(api(`/api/users/${uid}/canvas/connect/ics`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ icsUrl: icsUrl }),
      });
      if (res.ok) {
        setIcsStatus('ok');
      } else if (res.status === 429) {
        const data = await res.json();
        setIcsCooldownMsg(data.detail || 'Token cooldown active. Try again later.');
        setIcsStatus('cooldown');
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

  const handleDeleteAccount = async () => {
    setDeleteLoading(true);
    setDeleteError(false);
    try {
      const res = await fetch(api(`/api/users/${uid}`), {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.ok) {
        localStorage.removeItem('pc_uid');
        localStorage.removeItem('pc_theme');
        navigate('/');
      } else {
        setDeleteError(true);
      }
    } catch {
      setDeleteError(true);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const res = await fetch(api(`/api/users/${uid}/settings`), {
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
                  {canvasStatus === 'cooldown' && <span className="status-error">{canvasCooldownMsg}</span>}
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
                  {icsStatus === 'cooldown' && <span className="status-error">{icsCooldownMsg}</span>}
                </div>
              </div>
            )}
          </section>
          {/* ── Color Theme ── */}
          <section className="settings-section">
            <h3>Color Theme</h3>
            <p className="settings-desc">Changes the site's color palette instantly.</p>
            <div className="theme-swatches">
              {[
                { id: 'peach',     label: 'Peach',         color: '#f0d4b8' },
                { id: 'maroon',    label: 'Maroon',        color: '#7a1a1a' },
                { id: 'bw',        label: 'Black & White', color: '#111111' },
                { id: 'lightblue', label: 'Light Blue',    color: '#4a90d9' },
                { id: 'dark',      label: 'Dark',          color: '#1a1a1a' },
              ].map(t => (
                <button
                  key={t.id}
                  type="button"
                  className={`theme-swatch${theme === t.id ? ' theme-swatch--active' : ''}`}
                  onClick={() => handleThemeChange(t.id)}
                  title={t.label}
                >
                  <span className="theme-swatch-dot" style={{ background: t.color }} />
                  <span className="theme-swatch-label">{t.label}</span>
                </button>
              ))}
            </div>
          </section>

          {/* ── Danger Zone ── */}
          <section className="settings-section danger-section">
            <h3>Danger Zone</h3>
            <p className="settings-desc">
              Permanently delete your account and all associated data. This cannot be undone.
            </p>
            {!deleteConfirm ? (
              <button className="danger-btn" onClick={() => setDeleteConfirm(true)}>
                Delete Account
              </button>
            ) : (
              <div className="danger-confirm">
                <p className="danger-warning">
                  Are you sure? All your tasks, events, and settings will be deleted forever.
                </p>
                <div className="danger-confirm-actions">
                  <button
                    className="danger-cancel-btn"
                    onClick={() => { setDeleteConfirm(false); setDeleteError(false); }}
                    disabled={deleteLoading}
                  >
                    Cancel
                  </button>
                  <button
                    className="danger-confirm-btn"
                    onClick={handleDeleteAccount}
                    disabled={deleteLoading}
                  >
                    {deleteLoading ? 'Deleting…' : 'Yes, delete my account'}
                  </button>
                </div>
                {deleteError && <span className="status-error">Something went wrong. Please try again.</span>}
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