import React, { useState, useEffect } from 'react';
import "./Modal.css";

// Maps your professional UI terms to your specific backend strings
const difficultyMapper = {
    "Moderate": "Ehhh",
    "Challenging": "Dead"
};

export default function AddTaskModal({ isOpen, onClose, uid, onTaskAdded }) {
    const [taskType, setTaskType] = useState('homework');
    const [name, setName] = useState('');
    const [date, setDate] = useState('');
    
    // Dynamic fields based on pcClasses
    const [difficulty, setDifficulty] = useState('Moderate'); // For Homework/Exams
    const [isCollaborative, setIsCollaborative] = useState(false); // For Project 'attributes'
    const [isImportant, setIsImportant] = useState(false); // For Events
    const [needsPrep, setNeedsPrep] = useState(false); // For Events

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Convert YYYY-MM-DD to MM-DD-YYYY for your string slicing in pcClasses
        const [year, month, day] = date.split('-');
        const formattedDate = `${month}-${day}-${year}`;

        let payload = {
            name: name,
            date: formattedDate,
            type: taskType,
            percentDone: 0.0
        };

        // MATCHING pcClasses logic
        if (taskType === 'homework') {
            payload.difficulty = difficultyMapper[difficulty] || "Easy";
        } else if (taskType === 'exam') {
            payload.difficulty = difficulty; // e.g., "Standard", "High"
        } else if (taskType === 'project') {
            payload.attributes = isCollaborative; // Major.setProjectAttributes(bool)
        } else if (taskType === 'event') {
            // Events is a separate class, not a Task subclass in your code
            payload = {
                name: name,
                date: formattedDate,
                importance: isImportant,
                needsPrep: needsPrep
            };
        }

        try {
            // Check if your api.py has a different endpoint for events vs tasks!
            const endpoint = taskType === 'event' ? `/users/${uid}/events` : `/users/${uid}/tasks`;
            
            const response = await fetch(`http://localhost:8000${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                onTaskAdded();
                onClose();
            }
        } catch (error) {
            console.error("Submission error:", error);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2>Add {taskType.charAt(0).toUpperCase() + taskType.slice(1)}</h2>
                <form onSubmit={handleSubmit}>
                    <label>Type:
                        <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
                            <option value="homework">Homework</option>
                            <option value="exam">Exam</option>
                            <option value="project">Project</option>
                            <option value="quiz">Quiz</option>
                            <option value="prep">Prep</option>
                            <option value="event">Event</option>
                        </select>
                    </label>

                    <label>Name:
                        <input type="text" required value={name} onChange={(e) => setName(e.target.value)} />
                    </label>

                    <label>Date:
                        <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
                    </label>

                    {/* DYNAMIC FIELDS BASED ON pcClasses REQUIREMENTS */}
                    {taskType === 'homework' && (
                        <label>Difficulty:
                            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                                <option value="Easy">Easy</option>
                                <option value="Moderate">Moderate</option>
                                <option value="Challenging">Challenging</option>
                            </select>
                        </label>
                    )}

                    {taskType === 'exam' && (
                        <label>Importance:
                            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                                <option value="regular">Regular</option>
                                <option value="midterm">Midterm</option>
                                <option value="final">Final</option>
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

                    <div className="modal-actions">
                        <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
                        <button type="submit" className="submit-btn">Create</button>
                    </div>
                </form>
            </div>
        </div>
    );
}