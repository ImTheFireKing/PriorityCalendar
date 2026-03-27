import React, { useState } from "react";
import "./TaskCard.css";

const difficultyDisplayMap = {
  Easy: "Easy",
  Ehhh: "Moderate",
  Dead: "Challenging",
};

export default function TaskCard({ data, isRec, uid, onRefresh }) {
  const isEvent = data.priority !== undefined || (data.importance !== undefined && data.needsPrep !== undefined);
  const [showInput, setShowInput] = useState(false);
  const [customPercent, setCustomPercent] = useState(Math.round(data.howMuch ?? 0));

  const handleMarkProgress = async () => {
    await fetch(`/api/users/${uid}/tasks`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        taskName: data.name,
        percentChange: customPercent,
      }),
      credentials: "include",
    });
    setShowInput(false);
    onRefresh();
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

      {/* Header: name + type badge + forced badge */}
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
        </div>
      </div>

      <div className="task-card-body">

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
                  <button className="mark-done-btn" onClick={() => {setCustomPercent(Math.round(data.howMuch ?? 0)); 
                  setShowInput(true);}}>
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

        {/* Special attributes: difficulty for HW, type for exams, collab for projects */}
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