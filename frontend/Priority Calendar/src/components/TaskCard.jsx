import React from 'react';
import './TaskCard.css';

export default function TaskCard({ data, isRec }) {
  // We can determine if it's an event because Events have "importance" and "needsPrep"
  const isEvent = data.importance !== undefined || data.needsPrep !== undefined;

  return (
    <div className={`task-card ${isEvent ? 'event-card' : `task-card--${data.type}`}`}>
      <div className="task-card-header">
        <h4 className="task-name">{data.name}</h4>
        
        {/* Render a badge based on the type of task or event */}
        <span className="task-badge">
          {isEvent ? (data.importance ? '⭐ Important Event' : '📅 Event') : data.type.toUpperCase()}
        </span>
      </div>

      <div className="task-card-body">
        {/* If it's a Recommendation, tell the user how much to do! */}
        {isRec && !isEvent && data.howMuch && (
          <div className="rec-action">
            <strong>Target for today:</strong> Complete {Math.round(data.howMuch)}%
          </div>
        )}
        
        {/* If it's a Calendar item, show the due date/time */}
        {!isRec && (data.dueDate || data.time) && (
          <div className="due-date">
            Due: {data.dueDate || data.time}
          </div>
        )}

        {/* Display Special Attributes (Exam Difficulty or Project Collaboration) */}
        {!isEvent && data.otherDetails && (
          <div className="task-special">
            Details: {data.otherDetails}
          </div>
        )}

        {/* Display Event Prep Needs */}
        {isEvent && data.needsPrep && (
          <div className="event-prep">⚠️ Requires Preparation</div>
        )}
      </div>
    </div>
  );
}