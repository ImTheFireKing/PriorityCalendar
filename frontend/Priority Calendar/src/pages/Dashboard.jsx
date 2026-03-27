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
  const uid = localStorage.getItem('pc_uid');

  const [selectedDate, setSelectedDate]   = useState(new Date());
  const [schedule, setSchedule]           = useState({ tasks: [], events: [] });
  const [recs, setRecs]                   = useState({ tasks: [], events: [] });
  const [lazyDays, setLazyDays]           = useState([]);
  const [initialLoad, setInitialLoad]     = useState(true);
  const [refreshing, setRefreshing]       = useState(false);
  const [isModalOpen, setIsModalOpen]     = useState(false);
  const [noMoreRecs, setNoMoreRecs]       = useState(false);
  const [hadTasksOnLoad, setHadTasksOnLoad] = useState(false);

  const apiUrl    = '/api';
  const DAY_TO_JS = { Su: 0, Mo: 1, Tu: 2, Wed: 3, Th: 4, F: 5, Sa: 6 };

  const fetchDashboardData = useCallback(async () => {
    if (!uid) return;

    if (initialLoad) setRefreshing(false);
    else             setRefreshing(true);

    setNoMoreRecs(false);

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

      const recsRes = await fetch(`${apiUrl}/users/${uid}/recommendations`, {
      credentials: 'include',
    });
    if (recsRes.ok) {
      const recsData = await recsRes.json();
      setRecs(recsData);
      setHadTasksOnLoad(recsData.tasks.length > 0);  // Set once per refresh
    }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }

    setTimeout(() => {
      setInitialLoad(false);
      setRefreshing(false);
    }, 400);
  }, [selectedDate, uid, initialLoad]);

  const fetchMoreRecs = async () => {
    try {
      const res = await fetch(`${apiUrl}/users/${uid}/recommendations`, {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();

        const existingNames  = new Set(recs.tasks.map(t => t.name));
        const existingEvents = new Set(recs.events.map(e => e.name));
        const newTasks       = data.tasks.filter(t => !existingNames.has(t.name));
        const newEvents      = data.events.filter(e => !existingEvents.has(e.name));

        if (newTasks.length === 0 && newEvents.length === 0) {
          setNoMoreRecs(true);
        } else {
          setRecs(prev => ({
            tasks:  [...prev.tasks,  ...newTasks],
            events: [...prev.events, ...newEvents],
          }));
        }
      }
    } catch (err) {
      console.error('Failed to fetch more recs:', err);
    }
  };

  useEffect(() => {
    if (!uid) { navigate('/login'); return; }
    fetchDashboardData();
  }, [uid, navigate, fetchDashboardData]);

  if (!uid) return null;

  return (
    <div className="dashboard-page">
      {initialLoad ? (
        <SplashScreen />
      ) : (
        <>
          <Nav />
          {refreshing && <div className="refresh-indicator" />}

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
                    <TaskCard
                      key={`rec-task-${index}`}
                      data={task}
                      isRec={true}
                      uid={uid}
                      onRefresh={fetchDashboardData}
                    />
                  ))
                }

                {recs.events.map((event, index) => (
                  <TaskCard
                    key={`rec-event-${index}`}
                    data={event}
                    isRec={true}
                    uid={uid}
                    onRefresh={fetchDashboardData}
                  />
                ))}

                {/* Batch cleared — offer more */}
                {recs.tasks.length === 0 && hadTasksOnLoad && !noMoreRecs && (
                  <button className="get-more-btn" onClick={fetchMoreRecs}>
                    + Get More
                  </button>
                )}

                {/* Nothing left at all */}
                {recs.tasks.length === 0 && (!hadTasksOnLoad || noMoreRecs) && (
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