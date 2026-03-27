import React, { useState } from 'react';
import './Modal.css';

// Maps your professional UI terms to your specific backend strings
const difficultyMapper = {
  Moderate: 'Ehhh',
  Challenging: 'Dead',
};

export default function AddTaskModal({ isOpen, onClose, uid, onTaskAdded }) {
  const [taskType, setTaskType] = useState('homework');
  const [name, setName] = useState('');
  const [date, setDate] = useState('');
  const [closing, setClosing] = useState(false);

  // Dynamic fields based on pcClasses
  const [difficulty, setDifficulty] = useState('Moderate'); // For Homework/Exams
  const [isCollaborative, setIsCollaborative] = useState(false); // For Project attributes
  const [isImportant, setIsImportant] = useState(false);   // For Events
  const [needsPrep, setNeedsPrep] = useState(false);       // For Events

  if (!isOpen) return null;

  const handleClose = () => {
    setClosing(true);
    setTimeout(() => {
      setClosing(false);
      onClose();
    }, 200); // matches modalSlideDown duration
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const [year, month, day] = date.split('-');
    const formattedDate = `${month}-${day}-${year}`;

    // ── Duplicate check ───────────────────────────────────────────────────────
    const endpoint = taskType === 'event'
      ? `/api/users/${uid}/events?name=${encodeURIComponent(name)}`
      : `/api/users/${uid}/tasks?taskName=${encodeURIComponent(name)}`;

    try {
      const checkRes = await fetch(endpoint, { credentials: 'include' });
      if (checkRes.ok) {
        alert(`A ${taskType === 'event' ? 'event' : 'task'} named "${name}" already exists.`);
        return;
      }
      // 404 = doesn't exist = safe to proceed
    } catch {
      // network error — let it fall through to the creation attempt
    }
    // ── Creation ──────────────────────────────────────────────────────────────

    if (taskType === 'event') {
      const payload = { name, date: formattedDate, isImportant, needsPrep };
      try {
        const response = await fetch(`/api/users/${uid}/events`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          credentials: 'include',
        });
        if (!response.ok) {
          const err = await response.json();
          console.error('Event creation failed', err);
          return;
        }
        onTaskAdded();
        handleClose();
      } catch (error) {
        console.error('Submission error', error);
      }
      return;
    }

    // All task types
    let special = null;
    if (taskType === 'homework')    special = difficultyMapper[difficulty] ?? 'Easy';
    else if (taskType === 'exam')   special = difficulty;
    else if (taskType === 'project') special = String(isCollaborative);

    const payload = {
      name,
      date: formattedDate,
      taskType,
      alreadyDone: 0.0,
      ...(special !== null && { special }),
    };

    try {
      const response = await fetch(`/api/users/${uid}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      });
      if (!response.ok) {
        const err = await response.json();
        console.error('Task creation failed', err);
        return;
      }
      onTaskAdded();
      handleClose();
    } catch (error) {
      console.error('Submission error', error);
    }
  };

  return (
    <div className="modal-overlay">
      <div className={`modal-content${closing ? ' modal-content--closing' : ''}`}>
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
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>

          <label>
            Date
            <input
              type="date"
              required
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>

          {/* ── DYNAMIC FIELDS BASED ON pcClasses REQUIREMENTS ── */}

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
              <input
                type="checkbox"
                checked={isCollaborative}
                onChange={(e) => setIsCollaborative(e.target.checked)}
              />
              Group Project?
            </label>
          )}

          {taskType === 'event' && (
            <div className="event-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={isImportant}
                  onChange={(e) => setIsImportant(e.target.checked)}
                />
                Important / Unskippable?
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={needsPrep}
                  onChange={(e) => setNeedsPrep(e.target.checked)}
                />
                Needs Preparation?
              </label>
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={handleClose}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}