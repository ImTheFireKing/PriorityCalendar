import { useState } from "react";
import { api } from "../api";
import "./TaskCard.css";

const difficultyDisplayMap = {
  Easy: "Easy",
  Ehhh: "Moderate",
  Dead: "Challenging",
};

// YYYY-MM-DD → MM-DD-YYYY
const toBackendDate = (yyyymmdd) => {
  if (!yyyymmdd) return '';
  const [y, m, d] = yyyymmdd.split('-');
  return `${m}-${d}-${y}`;
};

// ISO string (YYYY-MM-DD...) → YYYY-MM-DD for <input type="date">
const toInputDate = (isoString) => {
  if (!isoString) return '';
  return isoString.slice(0, 10);
};

export default function TaskCard({ data, isRec, uid, onRefresh }) {
  const isEvent = data.priority !== undefined || (data.importance !== undefined && data.needsPrep !== undefined);
  const [showInput, setShowInput]     = useState(false);
  const [customPercent, setCustomPercent] = useState(Math.round(data.howMuch ?? 0));

  // Edit state
  const [editing, setEditing]         = useState(false);
  const [editDate, setEditDate]       = useState(toInputDate(data.dueDate || data.time || data.date || ''));
  const [editSpecial, setEditSpecial] = useState(data.otherDetails ?? '');
  const [editNeedsPrep, setEditNeedsPrep]   = useState(data.needsPrep ?? false);
  const [editImportant, setEditImportant]   = useState(data.importance ?? false);

  const handleMarkProgress = async () => {
    await fetch(api(`/api/users/${uid}/tasks`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ taskName: data.name, percentChange: customPercent }),
      credentials: "include",
    });
    setShowInput(false);
    onRefresh();
  };

  const handleEditSave = async () => {
    const backendDate = toBackendDate(editDate);
    if (isEvent) {
      await fetch(api(`/api/users/${uid}/events`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          ...(backendDate && { date: backendDate }),
          needsPrep: String(editNeedsPrep),
          isImportant: String(editImportant),
        }),
        credentials: "include",
      });
    } else {
      await fetch(api(`/api/users/${uid}/tasks`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          taskName: data.name,
          ...(backendDate && { date: backendDate }),
          ...(editSpecial && { special: editSpecial }),
        }),
        credentials: "include",
      });
    }
    setEditing(false);
    onRefresh();
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete "${data.name}"?`)) return;

    const endpoint = isEvent ? 'events' : 'tasks';
    const body = isEvent ? { name: data.name } : { taskName: data.name };

    try {
      const res = await fetch(api(`/api/users/${uid}/${endpoint}`), {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (res.ok) {
        setEditing(false);
        onRefresh(); // Refresh the list so the card disappears
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to delete");
      }
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  // Format ISO date string (YYYY-MM-DD) into something readable
  const formatDate = (isoString) => {
    if (!isoString) return null;
    const [year, month, day] = isoString.split("-");
    return `${month}/${day}/${year}`;
  };

  const dueDateDisplay = formatDate(data.dueDate || data.time || data.date);

  return (
    <div className={`task-card ${isEvent ? "event-card" : `task-card--${data.type ?? "task"}`} ${data.forced ? "task-card--forced" : ""}`}>

      {/* Header: name + type badge + edit button */}
      <div className="task-card-header">
        <h4 className="task-name">{data.name}</h4>
        <div className="task-badges">
          {data.forced && (
            <span className="task-badge task-badge--forced" title="Needs significant work today — added outside your task limit">
              ⚠ High Priority
            </span>
          )}
          <span className="task-badge">
            {isEvent
              ? data.importance ? "Important Event" : "Event"
              : (data.type ?? "task").toUpperCase()}
          </span>
          <button
            className="edit-btn"
            title="Edit"
            onClick={() => setEditing((v) => !v)}
          >
            ✎
          </button>
        </div>
      </div>

      <div className="task-card-body">

        {/* ── Inline edit form ── */}
        {editing && (
          <div className="task-edit-form">
            <label>
              Due Date
              <input type="date" value={editDate} onChange={(e) => setEditDate(e.target.value)} />
            </label>

            {!isEvent && data.type === 'homework' && (
              <label>
                Difficulty
                <select value={editSpecial} onChange={(e) => setEditSpecial(e.target.value)}>
                  <option value="Easy">Easy</option>
                  <option value="Ehhh">Moderate</option>
                  <option value="Dead">Challenging</option>
                </select>
              </label>
            )}

            {!isEvent && data.type === 'exam' && (
              <label>
                Importance
                <select value={editSpecial} onChange={(e) => setEditSpecial(e.target.value)}>
                  <option value="regular">Regular</option>
                  <option value="Midterm">Midterm</option>
                  <option value="Final">Final</option>
                </select>
              </label>
            )}

            {isEvent && (
              <div className="task-edit-checks">
                <label className="task-edit-check-label">
                  <input type="checkbox" checked={editImportant} onChange={(e) => setEditImportant(e.target.checked)} />
                  Important / Unskippable
                </label>
                <label className="task-edit-check-label">
                  <input type="checkbox" checked={editNeedsPrep} onChange={(e) => setEditNeedsPrep(e.target.checked)} />
                  Needs Preparation
                </label>
              </div>
            )}

            <div className="task-edit-actions">
              <button className="cancel-small-btn" onClick={() => setEditing(false)}>Cancel</button>
              <button className="confirm-btn" onClick={handleEditSave}>Save</button>
              <button className="delete-btn" onClick={handleDelete}>Delete</button>
            </div>
          </div>
        )}

        {/* Due date — always shown */}
        {dueDateDisplay && (
          <div className={`due-date ${data.forced ? "due-date--urgent" : ""}`}>
            Due: {dueDateDisplay}
          </div>
        )}

        {/* Recommendation: show target % + progress interaction */}
        {isRec && !isEvent && data.howMuch && (
          <div className={`rec-action ${data.forced ? "rec-action--forced" : ""}`}>
            <span className="rec-action-label">Target for Today: </span>
            <div className="rec-action-right">
              {!showInput ? (
                <>
                  <span className="rec-percent">Complete {Math.round(data.howMuch)}%</span>
                  <button className="mark-done-btn" onClick={() => { setCustomPercent(Math.round(data.howMuch ?? 0)); setShowInput(true); }}>
                    ✓ Done for today
                  </button>
                </>
              ) : (
                <div className="progress-input">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={customPercent}
                    onChange={(e) => setCustomPercent(Number(e.target.value))}
                  />
                  <span className="rec-percent">%</span>
                  <button className="confirm-btn" onClick={handleMarkProgress}>Confirm</button>
                  <button className="cancel-small-btn" onClick={() => setShowInput(false)}>Cancel</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Special attributes */}
        {!isEvent && data.otherDetails && (
          <div className="task-special">
            Details: {difficultyDisplayMap[data.otherDetails] ?? data.otherDetails}
          </div>
        )}

        {/* Event-specific: prep notice */}
        {isEvent && data.needsPrep && (
          <div className="event-prep">Requires Preparation</div>
        )}

      </div>
    </div>
  );
}
