import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import Nav from '../components/Nav';
import TaskCard from '../components/TaskCard';
import AddTaskModal from '../components/AddTaskModal';
import SplashScreen from '../components/SplashScreen';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const checkSession = async () => {
  const res = await fetch('/api/auth/session', {
    credentials: 'include',
  });
  return res.ok;
  };
  const uid = localStorage.getItem('pc_uid');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [schedule, setSchedule]         = useState({ tasks: [], events: [] });
  const [recs, setRecs]                 = useState({ tasks: [], events: [] });
  const [lazyDays, setLazyDays]         = useState([]);
  const [loading, setLoading]           = useState(true);
  const [isModalOpen, setIsModalOpen]   = useState(false);

  const apiUrl   = '/api'; // Change in Production to where API code will be hosted
  const DAY_TO_JS = { Su: 0, Mo: 1, Tu: 2, Wed: 3, Th: 4, F: 5, Sa: 6 };

  const fetchDashboardData = useCallback(async () => {
    if (!uid) return;
    setLoading(true);

    const formatForBackend = (dateObj) => {
      const m = String(dateObj.getMonth() + 1).padStart(2, '0');
      const d = String(dateObj.getDate()).padStart(2, '0');
      const y = dateObj.getFullYear();
      return `${m}-${d}-${y}`;
    };

    const settingsRes = await fetch(`${apiUrl}/users/${uid}/settings?settingField=lazy`, {
      credentials: 'include',
    });
    if (settingsRes.ok) {
      const days = await settingsRes.json();
      setLazyDays(Array.isArray(days) ? days : []);
    }

    try {
      const dateStr  = formatForBackend(selectedDate);

      const schedRes = await fetch(`${apiUrl}/users/${uid}/schedule/${dateStr}`, {
        credentials: 'include',
      });
      if (schedRes.ok) {
        const schedData = await schedRes.json();
        setSchedule(schedData);
      }

      const recsRes  = await fetch(`${apiUrl}/users/${uid}/recommendations`, {
        credentials: 'include',
      });
      if (recsRes.ok) {
        const recsData = await recsRes.json();
        setRecs(recsData);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }

    // Fade splash out, then unmount
    setTimeout(() => setLoading(false), 400);
  }, [selectedDate, uid]);

  useEffect(() => {
    if (!uid) { navigate('/login'); return; }
    fetchDashboardData();
  }, [uid, navigate, fetchDashboardData]);

  if (!uid) return null;

  return (
    <div className="dashboard-page">

      {loading ? (
        <SplashScreen />
      ) : (
        <>
          <Nav />
          <main className="dashboard-layout">

            {/* LEFT COLUMN */}
            <aside className="dashboard-sidebar">
              <Calendar
                onChange={setSelectedDate}
                value={selectedDate}
                className="pc-calendar"
                tileClassName={({ date }) => {
                  const jsDay = date.getDay();
                  return lazyDays.some(d => DAY_TO_JS[d] === jsDay) ? 'lazy-day' : null;
                }}
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
                <button className="add-btn" onClick={() => setIsModalOpen(true)}>
                  + Add Task / Event
                </button>
              </header>

              <div className="recommendations-hub">
                <h3>Recommended Focus for Today</h3>

                {[...recs.tasks]
                  .sort((a, b) => (b.howMuch ?? 0) - (a.howMuch ?? 0))
                  .map((task, index) => (
                    <TaskCard key={`rec-task-${index}`} data={task} isRec={true} />
                  ))
                }

                {recs.events.map((event, index) => (
                  <TaskCard key={`rec-event-${index}`} data={event} isRec={true} />
                ))}

                {recs.tasks.length === 0 && recs.events.length === 0 && (
                  <p>You're all caught up! Go take a nap.</p>
                )}
              </div>
            </section>

          </main>

          <AddTaskModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            uid={uid}
            onTaskAdded={fetchDashboardData}
          />
        </>
      )}

    </div>
  );
}