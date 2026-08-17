import { useState } from 'react';
import { api } from '../api';
import './Modal.css';

// Maps your professional UI terms to your specific backend strings
const difficultyMapper = {
  Moderate: 'Ehhh',
  Challenging: 'Dead',
};

export default function AddTaskModal({ isOpen, onClose, uid, onTaskAdded, pendingCanvasCount }) {
  const [panel, setPanel] = useState('form'); // 'form' | 'canvas'

  // ── Date range constants ──────────────────────────────────────────────────
  const _today = new Date();
  const DATE_MIN = _today.toISOString().split('T')[0]; // YYYY-MM-DD (today)
  const _maxDate = new Date(_today.getFullYear() + 2, _today.getMonth(), _today.getDate());
  const DATE_MAX = _maxDate.toISOString().split('T')[0];

  // ── Form panel state ──────────────────────────────────────────────────────
  const [taskType, setTaskType] = useState('homework');
  const [name, setName] = useState('');
  const [date, setDate] = useState('');
  const [closing, setClosing] = useState(false);
  const [difficulty, setDifficulty] = useState('Moderate');
  const [isCollaborative, setIsCollaborative] = useState(false);
  const [isImportant, setIsImportant] = useState(false);
  const [needsPrep, setNeedsPrep] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // ── Repeat state ─────────────────────────────────────────────────────────
  const [isRepeating, setIsRepeating]     = useState(false);
  const [repeatDays, setRepeatDays]       = useState([]);
  const [repeatStart, setRepeatStart]     = useState('');
  const [repeatEnd, setRepeatEnd]         = useState('');

  const REPEAT_DAY_LABELS = [
    { key: 'Mo', label: 'Mon' },
    { key: 'Tu', label: 'Tue' },
    { key: 'Wed', label: 'Wed' },
    { key: 'Th', label: 'Thu' },
    { key: 'F', label: 'Fri' },
    { key: 'Sa', label: 'Sat' },
    { key: 'Su', label: 'Sun' },
  ];

  const toggleRepeatDay = (key) => {
    setRepeatDays(prev => prev.includes(key) ? prev.filter(d => d !== key) : [...prev, key]);
  };

  // ── Canvas panel state ────────────────────────────────────────────────────
  const [pendingTasks, setPendingTasks]     = useState([]);
  const [selectedPending, setSelectedPending] = useState(null);
  const [canvasLoading, setCanvasLoading]   = useState(false);
  // Editable fields for the selected pending item
  const [cName, setCName]         = useState('');
  const [cDate, setCDate]         = useState('');
  const [cType, setCType]         = useState('homework');
  const [cSpecial, setCSpecial]   = useState('');

  if (!isOpen) return null;

  // ── Helpers ───────────────────────────────────────────────────────────────
  const handleClose = () => {
    setClosing(true);
    setTimeout(() => {
      setClosing(false);
      setPanel('form');
      onClose();
    }, 200);
  };

  // Convert MM-DD-YYYY → YYYY-MM-DD for <input type="date">
  const toInputDate = (mmddyyyy) => {
    if (!mmddyyyy) return '';
    const [m, d, y] = mmddyyyy.split('-');
    return `${y}-${m}-${d}`;
  };

  // Convert YYYY-MM-DD → MM-DD-YYYY for backend
  const toBackendDate = (yyyymmdd) => {
    if (!yyyymmdd) return '';
    const [y, m, d] = yyyymmdd.split('-');
    return `${m}-${d}-${y}`;
  };

  const loadPending = async () => {
    setCanvasLoading(true);
    try {
      const res = await fetch(api(`/api/users/${uid}/canvas/pending`), { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setPendingTasks(data.pending);
        if (data.pending.length > 0) selectPending(data.pending[0]);
        else setSelectedPending(null);
      }
    } finally {
      setCanvasLoading(false);
    }
  };

  const selectPending = (item) => {
    setSelectedPending(item);
    setCName(item.courseName ? `[${item.courseName}] ${item.name}` : item.name);
    setCDate(toInputDate(item.dueDate));
    setCType(item.taskType);
    setCSpecial('');
  };

  const openCanvasPanel = async () => {
    setPanel('canvas');
    await loadPending();
  };

  const handleConfirm = async () => {
    if (!selectedPending) return;
    const backendDate = toBackendDate(cDate);
    if (!backendDate) return;

    let special = cSpecial || null;
    await fetch(api(`/api/users/${uid}/canvas/confirm`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        canvasId: selectedPending.canvasId,
        name: cName,
        date: backendDate,
        taskType: cType,
        special,
      }),
    });
    onTaskAdded();
    afterAction();
  };

  const handleDismiss = async () => {
    if (!selectedPending) return;
    await fetch(api(`/api/users/${uid}/canvas/pending/${selectedPending.canvasId}`), {
      method: 'DELETE',
      credentials: 'include',
    });
    afterAction();
  };

  const afterAction = async () => {
    const res = await fetch(api(`/api/users/${uid}/canvas/pending`), { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      setPendingTasks(data.pending);
      if (data.pending.length > 0) selectPending(data.pending[0]);
      else {
        setSelectedPending(null);
        setPanel('form'); // auto-return when chamber is empty
      }
    }
  };

  // ── Form submit ───────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError('');

    // ── Repeating task path ───────────────────────────────────────────────
    if (isRepeating && taskType !== 'event') {
      if (repeatDays.length === 0) { setSubmitError('Select at least one repeat day.'); return; }
      if (!repeatStart || !repeatEnd)  { setSubmitError('Both start and end dates are required.'); return; }
      if (repeatEnd < repeatStart)     { setSubmitError('End date must be on or after start date.'); return; }

      let special = null;
      if (taskType === 'homework')       special = difficultyMapper[difficulty] ?? 'Easy';
      else if (taskType === 'exam')      special = difficulty;
      else if (taskType === 'project')   special = String(isCollaborative);

      const [sy, sm, sd] = repeatStart.split('-');
      const [ey, em, ed] = repeatEnd.split('-');

      try {
        const res = await fetch(api(`/api/users/${uid}/tasks/repeat`), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            name,
            taskType,
            special,
            startDate: `${sm}-${sd}-${sy}`,
            endDate:   `${em}-${ed}-${ey}`,
            repeatDays,
          }),
        });
        if (res.status === 429) { const d = await res.json(); setSubmitError(d.detail); return; }
        if (!res.ok)            { setSubmitError('Failed to create repeating tasks.'); return; }
        const data = await res.json();
        if (data.created === 0) { setSubmitError('No matching dates found in that range.'); return; }
        onTaskAdded();
        handleClose();
      } catch { setSubmitError('Network error. Please try again.'); }
      return;
    }

    const [year, month, day] = date.split('-');
    const formattedDate = `${month}-${day}-${year}`;

    const endpoint = taskType === 'event'
      ? api(`/api/users/${uid}/events?name=${encodeURIComponent(name)}`)
      : api(`/api/users/${uid}/tasks?taskName=${encodeURIComponent(name)}`);

    try {
      const checkRes = await fetch(endpoint, { credentials: 'include' });
      if (checkRes.ok) {
        alert(`A ${taskType === 'event' ? 'event' : 'task'} named "${name}" already exists.`);
        return;
      }
    } catch {
      // network error — fall through
    }

    if (taskType === 'event') {
      const payload = { name, date: formattedDate, isImportant, needsPrep };
      try {
        const response = await fetch(api(`/api/users/${uid}/events`), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          credentials: 'include',
        });
        if (response.status === 429) {
          const data = await response.json();
          setSubmitError(data.detail || 'Event limit reached.');
          return;
        }
        if (!response.ok) { console.error('Event creation failed', await response.json()); return; }
        onTaskAdded();
        handleClose();
      } catch (error) { console.error('Submission error', error); }
      return;
    }

    let special = null;
    if (taskType === 'homework')   special = difficultyMapper[difficulty] ?? 'Easy';
    else if (taskType === 'exam')  special = difficulty;
    else if (taskType === 'project') special = String(isCollaborative);

    const payload = {
      name, date: formattedDate, taskType, alreadyDone: 0.0,
      ...(special !== null && { special }),
    };

    try {
      const response = await fetch(api(`/api/users/${uid}/tasks`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      });
      if (response.status === 429) {
        const data = await response.json();
        setSubmitError(data.detail || 'Task limit reached.');
        return;
      }
      if (!response.ok) { console.error('Task creation failed', await response.json()); return; }
      onTaskAdded();
      handleClose();
    } catch (error) { console.error('Submission error', error); }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="modal-overlay">
      <div className={`modal-content${closing ? ' modal-content--closing' : ''}${panel === 'canvas' ? ' modal-content--canvas' : ''}`}>

        {/* ══ FORM PANEL ══ */}
        {panel === 'form' && (
          <>
            <h2>Add {taskType.charAt(0).toUpperCase() + taskType.slice(1)}</h2>

            <form onSubmit={handleSubmit}>
              <label>
                Type
                <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
                  <option value="homework">Homework</option>
                  <option value="exam">Exam</option>
                  <option value="project">Project</option>
                  <option value="quiz">Quiz</option>
                  <option value="prep">Prep</option>
                  <option value="event">Event</option>
                </select>
              </label>

              <label>
                Name
                <input type="text" required value={name} maxLength={100} onChange={(e) => setName(e.target.value)} />
                <span className="char-counter">{name.length}/100</span>
              </label>

              {/* Repeat toggle — only for non-event types */}
              {taskType !== 'event' && (
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isRepeating}
                    onChange={(e) => setIsRepeating(e.target.checked)}
                  />
                  Repeating Task?
                </label>
              )}

              {/* ── Repeat fields ── */}
              {isRepeating && taskType !== 'event' ? (
                <div className="repeat-fields">
                  <label className="repeat-days-label">Repeat on</label>
                  <div className="repeat-days">
                    {REPEAT_DAY_LABELS.map(({ key, label }) => (
                      <button
                        key={key}
                        type="button"
                        className={`repeat-day-btn${repeatDays.includes(key) ? ' repeat-day-btn--active' : ''}`}
                        onClick={() => toggleRepeatDay(key)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <label>
                    Start Date
                    <input
                      type="date"
                      required
                      value={repeatStart}
                      min={DATE_MIN}
                      max={DATE_MAX}
                      onChange={(e) => setRepeatStart(e.target.value)}
                    />
                  </label>
                  <label>
                    End Date
                    <input
                      type="date"
                      required
                      value={repeatEnd}
                      min={repeatStart || DATE_MIN}
                      max={DATE_MAX}
                      onChange={(e) => setRepeatEnd(e.target.value)}
                    />
                  </label>
                </div>
              ) : (
                <label>
                  Date
                  <input type="date" required value={date} min={DATE_MIN} max={DATE_MAX} onChange={(e) => setDate(e.target.value)} />
                </label>
              )}

              {taskType === 'homework' && (
                <label>
                  Difficulty
                  <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    <option value="Easy">Easy</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Challenging">Challenging</option>
                  </select>
                </label>
              )}

              {taskType === 'exam' && (
                <label>
                  Importance
                  <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    <option value="Regular">Regular</option>
                    <option value="Midterm">Midterm</option>
                    <option value="Final">Final</option>
                  </select>
                </label>
              )}

              {taskType === 'project' && (
                <label className="checkbox-label">
                  <input type="checkbox" checked={isCollaborative} onChange={(e) => setIsCollaborative(e.target.checked)} />
                  Group Project?
                </label>
              )}

              {taskType === 'event' && (
                <div className="event-options">
                  <label className="checkbox-label">
                    <input type="checkbox" checked={isImportant} onChange={(e) => setIsImportant(e.target.checked)} />
                    Important / Unskippable?
                  </label>
                  <label className="checkbox-label">
                    <input type="checkbox" checked={needsPrep} onChange={(e) => setNeedsPrep(e.target.checked)} />
                    Needs Preparation?
                  </label>
                </div>
              )}

              {submitError && <div className="modal-error">{submitError}</div>}
              <div className="modal-actions">
                <button type="button" className="cancel-btn" onClick={handleClose}>Cancel</button>
                <button type="submit" className="submit-btn">Create</button>
              </div>
            </form>

            {pendingCanvasCount > 0 && (
              <button className="canvas-manage-btn" type="button" onClick={openCanvasPanel}>
                Manage Canvas Tasks ({pendingCanvasCount})
              </button>
            )}
          </>
        )}

        {/* ══ CANVAS PANEL ══ */}
        {panel === 'canvas' && (
          <>
            <div className="canvas-panel-header">
              <button className="canvas-back-btn" type="button" onClick={() => setPanel('form')}>← Back</button>
              <h2>Canvas Tasks</h2>
            </div>

            {canvasLoading ? (
              <p className="canvas-loading">Loading…</p>
            ) : (
              <div className="canvas-panel-body">

                {/* Left — assignment list */}
                <ul className="canvas-list">
                  {pendingTasks.map((item) => (
                    <li
                      key={item.canvasId}
                      className={`canvas-list-item${selectedPending?.canvasId === item.canvasId ? ' canvas-list-item--active' : ''}`}
                      onClick={() => selectPending(item)}
                    >
                      <span className="canvas-list-name">{item.name}</span>
                      <span className="canvas-list-meta">{item.courseName} · {item.taskType}</span>
                    </li>
                  ))}
                </ul>

                {/* Right — detail + edit form */}
                {selectedPending && (
                  <div className="canvas-detail">
                    <label>
                      Name
                      <input type="text" value={cName} maxLength={100} onChange={(e) => setCName(e.target.value)} />
                      <span className="char-counter">{cName.length}/100</span>
                    </label>
                    <label>
                      Due Date
                      <input type="date" value={cDate} min={DATE_MIN} max={DATE_MAX} onChange={(e) => setCDate(e.target.value)} />
                    </label>
                    <label>
                      Type
                      <select value={cType} onChange={(e) => setCType(e.target.value)}>
                        <option value="homework">Homework</option>
                        <option value="exam">Exam</option>
                        <option value="project">Project</option>
                        <option value="quiz">Quiz</option>
                        <option value="prep">Prep</option>
                      </select>
                    </label>
                    {(cType === 'homework' || cType === 'exam') && (
                      <label>
                        {cType === 'homework' ? 'Difficulty' : 'Importance'}
                        <select value={cSpecial} onChange={(e) => setCSpecial(e.target.value)}>
                          {cType === 'homework' && <>
                            <option value="">Easy</option>
                            <option value="Ehhh">Moderate</option>
                            <option value="Dead">Challenging</option>
                          </>}
                          {cType === 'exam' && <>
                            <option value="regular">Regular</option>
                            <option value="Midterm">Midterm</option>
                            <option value="Final">Final</option>
                          </>}
                        </select>
                      </label>
                    )}
                    {selectedPending.description && (
                      <div className="canvas-description">
                        <span className="canvas-description-label">From Canvas</span>
                        <p>{selectedPending.description}</p>
                      </div>
                    )}
                    <div className="canvas-detail-actions">
                      <button className="cancel-btn" type="button" onClick={handleDismiss}>Skip</button>
                      <button className="submit-btn" type="button" onClick={handleConfirm} disabled={!cDate}>
                        Confirm
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

      </div>
    </div>
  );
}
