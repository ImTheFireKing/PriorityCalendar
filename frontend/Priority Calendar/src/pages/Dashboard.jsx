import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css'; 
import Nav from '../components/Nav';
import TaskCard from '../components/TaskCard'; 
import AddTaskModal from '../components/AddTaskModal'; // Import the new modal
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const uid = localStorage.getItem("pc_uid"); 

  const [selectedDate, setSelectedDate] = useState(new Date());
  const [schedule, setSchedule] = useState({ tasks: [], events: [] });
  const [recs, setRecs] = useState({ tasks: [], events: [] });
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const apiUrl = "http://localhost:8000";

  // We wrap this in useCallback so we can trigger it from the modal
  const fetchDashboardData = useCallback(async () => {
    if (!uid) return;

    const formatForBackend = (dateObj) => {
      const m = String(dateObj.getMonth() + 1).padStart(2, '0');
      const d = String(dateObj.getDate()).padStart(2, '0');
      const y = dateObj.getFullYear();
      return `${m}-${d}-${y}`;
    };

    try {
      const dateStr = formatForBackend(selectedDate);

      const schedRes = await fetch(`${apiUrl}/users/${uid}/schedule/${dateStr}`);
      if (schedRes.ok) {
        const schedData = await schedRes.json();
        setSchedule(schedData);
      }

      const recsRes = await fetch(`${apiUrl}/users/${uid}/recommendations`);
      if (recsRes.ok) {
        const recsData = await recsRes.json();
        setRecs(recsData);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  }, [selectedDate, uid]);

  useEffect(() => {
    if (!uid) {
      navigate('/login');
      return;
    }
    fetchDashboardData();
  }, [uid, navigate, fetchDashboardData]);

  if (!uid) return null;

  return (
    <div className="dashboard-page">
      <Nav />
      
      <main className="dashboard-layout">
        {/* LEFT COLUMN */}
        <aside className="dashboard-sidebar">
          <Calendar 
            onChange={setSelectedDate} 
            value={selectedDate} 
            className="pc-calendar"
          />
          
          <div className="daily-snapshot">
            <h3>Agenda for {selectedDate.toLocaleDateString()}</h3>
            <div className="snapshot-section">
              <h4>Events ({schedule.events.length})</h4>
              <ul>
                {schedule.events.map((e, i) => <li key={i}>{e.name}</li>)}
              </ul>
            </div>
            <div className="snapshot-section">
              <h4>Tasks Due ({schedule.tasks.length})</h4>
              <ul>
                {schedule.tasks.map((t, i) => <li key={i}>{t.name}</li>)}
              </ul>
            </div>
          </div>
        </aside>

        {/* RIGHT COLUMN */}
        <section className="dashboard-main">
          <header className="dashboard-header">
            <h2>Your Priority Strategy</h2>
            {/* Updated Button to open modal */}
            <button className="add-btn" onClick={() => setIsModalOpen(true)}>
              + Add Task / Event
            </button>
          </header>

          <div className="recommendations-hub">
            <h3>Recommended Focus for Today</h3>
            {recs.tasks.map((task, index) => (
              <TaskCard key={`rec-task-${index}`} data={task} isRec={true} />
            ))}
            {recs.events.map((event, index) => (
              <TaskCard key={`rec-event-${index}`} data={event} isRec={true} />
            ))}
            {recs.tasks.length === 0 && recs.events.length === 0 && (
              <p>You're all caught up! Go take a nap.</p>
            )}
          </div>
        </section>
      </main>

      {/* The Modal Component */}
      <AddTaskModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        uid={uid}
        onTaskAdded={fetchDashboardData} // Automatically refresh UI
      />
    </div>
  );
}