import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import Shepherd from 'shepherd.js';
import 'shepherd.js/dist/css/shepherd.css';
import Nav from '../components/Nav';
import TaskCard from '../components/TaskCard';
import AddTaskModal from '../components/AddTaskModal';
import SplashScreen from '../components/SplashScreen';
import './Dashboard.css';

function startTour() {
  const tour = new Shepherd.Tour({
    useModalOverlay: true,
    defaultStepOptions: {
      cancelIcon:  { enabled: true },
      scrollTo:    { behavior: 'smooth', block: 'center' },
      modalOverlayOpeningRadius: 8,
      classes: 'pc-shepherd',
    },
  });

  tour.addStep({
    id: 'welcome',
    text: 'Welcome to your dashboard! This is where Priority Calendar figures out <strong>what to work on today</strong> and keeps you from drowning in deadlines.',
    buttons: [{ text: 'Next →', action: tour.next }],
  });

  tour.addStep({
    id: 'recommendations',
    attachTo: { element: '#tour-recs', on: 'top' },
    text: 'These are your <strong>recommended tasks and events for today</strong>. Each one tells you exactly what percentage of it to tackle — no guesswork.',
    buttons: [
      { text: '← Back', action: tour.back,  secondary: true },
      { text: 'Next →', action: tour.next },
    ],
  });

  tour.addStep({
    id: 'calendar',
    attachTo: { element: '#tour-calendar', on: 'right' },
    text: 'Use the <strong>calendar</strong> to see what\'s scheduled on any specific day. Days highlighted in a warm tint are your lazy days.',
    buttons: [
      { text: '← Back', action: tour.back,  secondary: true },
      { text: 'Next →', action: tour.next },
    ],
  });

  tour.addStep({
    id: 'snapshot',
    attachTo: { element: '#tour-snapshot', on: 'right' },
    text: 'The <strong>daily agenda</strong> shows every task due and event happening on the selected date.',
    buttons: [
      { text: '← Back', action: tour.back,  secondary: true },
      { text: 'Next →', action: tour.next },
    ],
  });

  tour.addStep({
    id: 'add-btn',
    attachTo: { element: '#tour-add-btn', on: 'bottom' },
    text: 'Hit <strong>Add Task / Event</strong> to log anything new. If you\'ve connected Canvas, a badge here means there are assignments waiting to be confirmed.',
    buttons: [
      { text: '← Back', action: tour.back,  secondary: true },
      { text: 'Next →', action: tour.next },
    ],
  });

  tour.addStep({
    id: 'settings-link',
    attachTo: { element: '#tour-settings', on: 'bottom' },
    text: 'Head to <strong>Settings</strong> to adjust lazy days, recommendation limits, and connect your Canvas account.',
    buttons: [
      { text: '← Back', action: tour.back,  secondary: true },
      { text: 'Done!',  action: tour.complete },
    ],
  });

  tour.on('complete', () => localStorage.removeItem('pc_tour_pending'));
  tour.on('cancel',   () => localStorage.removeItem('pc_tour_pending'));

  tour.start();
}

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
  const [pendingCanvasCount, setPendingCanvasCount] = useState(0);
  const [isSyncing, setIsSyncing]         = useState(false);

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
        setHadTasksOnLoad(recsData.tasks.length > 0);
      }

      const pendingRes = await fetch(`${apiUrl}/users/${uid}/canvas/pending`, {
        credentials: 'include',
      });
      if (pendingRes.ok) {
        const pendingData = await pendingRes.json();
        setPendingCanvasCount(pendingData.count);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }

    setTimeout(() => {
      setInitialLoad(false);
      setRefreshing(false);
    }, 400);
  }, [selectedDate, uid, initialLoad]);

  // Sync polling effect
  useEffect(() => {
    if (!uid) return;

    const checkSyncStatus = async () => {
      try {
        const res = await fetch(`${apiUrl}/users/${uid}/canvas/status`, {
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          setIsSyncing(prevSyncing => {
            // If it just stopped syncing, trigger a data refresh to grab the new Canvas count
            if (prevSyncing && !data.syncStatus) {
              fetchDashboardData();
            }
            return data.syncStatus;
          });
        }
      } catch (err) {
        console.error("Failed to check sync status", err);
      }
    };

    // Check immediately, then poll every 3 seconds
    checkSyncStatus();
    const intervalId = setInterval(checkSyncStatus, 3000);
    return () => clearInterval(intervalId);
  }, [uid, fetchDashboardData]);


  const handleClearSuggestions = async () => {
    if (!window.confirm("Clear all Canvas suggestions? This won't delete tasks already on your Calendar, but you will have to manually add other tasks back.")) return;

    try {
      // Fixed string interpolation here
      const res = await fetch(`${apiUrl}/users/${uid}/canvas/pending`, {
        method : 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        fetchDashboardData();
      }
    }
    catch (err) {
      console.error("Failed to clear suggestions: ", err);
    }
  };

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

  useEffect(() => {
    if (!initialLoad && localStorage.getItem('pc_tour_pending') === 'true') {
      setTimeout(startTour, 300);
    }
  }, [initialLoad]);

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
              <div id="tour-calendar">
                <Calendar
                  onChange={setSelectedDate}
                  value={selectedDate}
                  className="pc-calendar"
                  tileClassName={({ date }) => {
                    const jsDay = date.getDay();
                    return lazyDays.some(d => DAY_TO_JS[d] === jsDay) ? 'lazy-day' : null;
                  }}
                />
              </div>
              <div className="daily-snapshot" id="tour-snapshot">
                <h3>Agenda for {selectedDate.toLocaleDateString()}</h3>
                <div className="snapshot-section">
                  <h4>Events ({schedule.events.length})</h4>
                  {schedule.events.length === 0
                    ? <p className="snapshot-empty">None</p>
                    : schedule.events.map((e, i) => (
                        <TaskCard
                          key={`sched-event-${i}`}
                          data={e}
                          isRec={false}
                          uid={uid}
                          onRefresh={fetchDashboardData}
                        />
                      ))
                  }
                </div>
                <div className="snapshot-section">
                  <h4>Tasks Due ({schedule.tasks.length})</h4>
                  {schedule.tasks.length === 0
                    ? <p className="snapshot-empty">None</p>
                    : schedule.tasks.map((t, i) => (
                        <TaskCard
                          key={`sched-task-${i}`}
                          data={t}
                          isRec={false}
                          uid={uid}
                          onRefresh={fetchDashboardData}
                        />
                      ))
                  }
                </div>
              </div>
            </aside>

            {/* RIGHT COLUMN */}
            <section className="dashboard-main">
              <header className="dashboard-header">
                <h2>Your Priority Strategy</h2>
                
                {/* Reorganized header controls */}
                <div className="dashboard-controls">
                  {isSyncing && (
                    <div className="sync-indicator">
                      <div className="spinner-tiny"></div>
                      <span>Syncing Canvas...</span>
                    </div>
                  )}

                  <div className="add-btn-container">
                    <button id="tour-add-btn" className="add-btn" onClick={() => setIsModalOpen(true)}>
                      + Add Task / Event
                      {pendingCanvasCount > 0 && (
                        <span className="canvas-badge">{pendingCanvasCount}</span>
                      )}
                    </button>
                    
                    {pendingCanvasCount > 0 && (
                      <button className="clear-suggestions-btn" onClick={handleClearSuggestions}>
                        Clear Suggestions
                      </button>
                    )}
                  </div>
                </div>

              </header>

              <div className="recommendations-hub" id="tour-recs">
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
            pendingCanvasCount={pendingCanvasCount}
          />
        </>
      )}
    </div>
  );
}