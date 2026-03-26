import React, { useState } from "react";
import "./TaskCard.css";

const difficultyDisplayMap = {
  Easy: "Easy",
  Ehhh: "Moderate",
  Dead: "Challenging",
};

export default function TaskCard({ data, isRec, uid, onRefresh }) {
  const isEvent = data.importance !== undefined && data.needsPrep !== undefined;
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

  return (
    <div className={`task-card ${isEvent ? "event-card" : `task-card--${data.type}`}`}>

      {/* Header: name + type badge */}
      <div className="task-card-header">
        <h4 className="task-name">{data.name}</h4>
        <span className="task-badge">
          {isEvent
            ? data.importance ? "Important Event" : "Event"
            : data.type.toUpperCase()}
        </span>
      </div>

      <div className="task-card-body">

        {/* Recommendation: show target % + progress interaction */}
        {isRec && !isEvent && data.howMuch && (
        <div className="rec-action">
          <span className="rec-action-label">Target for Today: </span>
          <div className="rec-action-right">
            {!showInput ? (
              <>
                <span className="rec-percent">Complete {Math.round(data.howMuch)}%</span>
                <button className="mark-done-btn" onClick={() => setShowInput(true)}>
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

        {/* Schedule view: show due date or event time */}
        {!isRec && (data.dueDate || data.time) && (
          <div className="due-date">
            Due: {data.dueDate || data.time}
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