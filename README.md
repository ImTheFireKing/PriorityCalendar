# Priority Calendar

## Overview

Most people — especially in college — have terrible time management, not because they're lazy, but because they lack a system for knowing *what* to work on and *how much* to do in a given day. Priority Calendar solves this by treating your academic workload like a strategy game: it analyzes your upcoming tasks and events, scores them by urgency and importance, and tells you exactly what to focus on each day so nothing sneaks up on you.

Rather than giving vague advice like "start early," the app uses a priority scoring algorithm to rank tasks and calculate the percentage of each one you should realistically complete today — accounting for your personal schedule, lazy days, and how much work is left.

---

## Tech Stack

### Backend

| | |
|---|---|
| **Language** | Python |
| **Framework** | FastAPI |
| **Database** | MongoDB Atlas (via PyMongo) |
| **Auth** | Google OAuth 2.0 + JWT session cookies |
| **Other** | Pydantic, python-dotenv, Uvicorn |

### Frontend

| | |
|---|---|
| **Framework** | React + Vite |
| **Routing** | React Router v7 |
| **Auth** | @react-oauth/google |
| **UI** | react-calendar, Shepherd.js (guided tour) |

### Deployment

| | |
|---|---|
| **Frontend** | Vercel |
| **Backend** | Render |
| **Database** | MongoDB Atlas |

---

## Architecture Overview

### Classes (`pcClasses.py`)

The data model is built around a hierarchy of Python classes:

- **`Task`** — Base class with shared behavior (name, date, percent complete). Uses a `deepConstructor` factory method to instantiate subtypes, and a `fromDict` static method to deserialize from MongoDB.
  - **`Homework`** — Adds difficulty rating (`Easy`, `Ehhh`, `Dead`)
  - **`Major`** — Handles both exams and projects via a `projectOrExam` flag. Supports exam difficulty (`regular`, `Midterm`, `Final`) and project collaboration type.
  - **`Quiz`** — Lightweight task with no special attributes
  - **`Prep`** — Low-priority prep work for upcoming classes/events
- **`Events`** — Standalone events with `importance` and `needsPrep` flags.
- **`Day`** — Container for tasks and events on a given date; computes day-of-week automatically.
- **`User`** — Holds user settings: lazy days, task/event limits, and expiration window.

All dates are stored as `MM-DD-YYYY` strings in MongoDB and parsed into `datetime.date` objects internally.

### Storage (`pcStorage.py`)

Handles all MongoDB reads and writes with an in-memory cache layer:

- **Collections:** `Users`, `Tasks`, `Events`
- **Caches:** calendar (TTL 30 min), tasks, events, settings — all keyed by uid, invalidated on write
- **Calendar rebuild:** `getCalendar(uid, year)` reconstructs a list of 365 `Day` objects from stored tasks/events

### Business Logic (`main.py`)

Orchestrates interactions between storage, classes, and the recommender:

- `createTask` / `createEvent` — Instantiates and stores new tasks/events; places them on the calendar
- `updateTask` / `updateEvent` — Handles date changes (moves item on calendar) and special field updates
- `deleteTask` / `deleteEvent` — Removes from both calendar and database
- `checkTasks` / `checkEvents` — Automated expiration: removes tasks past their due date (+ grace period) or 100% complete
- `getRecommendationsForToday` — Builds today's `Day`, pulls ranked task/event lists, calculates per-task percentage targets

### Recommender (`recommender.py`)

The core algorithmic layer. Scores tasks and events on a **priority = intensity × urgency** model:

| Task Type | Intensity | Urgency Factors |
|-----------|-----------|-----------------|
| Exam / Project | 5 | Days until due (2–9x) |
| Quiz | 4 | Days until due (2–9x) |
| Homework | 2–6 | Days until due × difficulty multiplier (1–3x) |
| Prep | 1–4 | Due tomorrow or not |
| Events | — | Importance × prep needed × time proximity |

- **`task_recommender`** — Scores and returns top N tasks; high-urgency tasks (needing 50%+ today) are marked `forced: true` and bypass the task limit
- **`event_recommender`** — Returns top N events sorted by score descending, ties broken by date
- **`percentCalculate`** — Computes % of a task to complete today based on available (non-lazy) working days remaining

### Authentication (`auth.py`)

Google OAuth 2.0 + JWT flow:

1. Frontend sends Google access token to `POST /auth/google`
2. Backend validates with Google's API, creates user in MongoDB on first login
3. Returns a signed JWT session cookie (HS256, 5-hour TTL) + uid + onboarded status
4. All subsequent requests are authenticated via the session cookie; uid in the URL must match the token

### Canvas Integration (`canvas.py`)

Syncs academic assignments from Canvas LMS into the app:

- **API method** — Uses a Canvas API token to fetch active courses and upcoming assignments
- **ICS method** — Parses the Canvas calendar ICS feed directly (no token required)
- Both methods infer task type from assignment name keywords (exam, midterm, final, project, quiz)
- Imported assignments are stored as "pending" and require user confirmation before being added to the calendar

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/google` | Exchange Google access token for a session cookie |
| `GET` | `/auth/session` | Check if current session is valid |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/{uid}/tasks` | Create a task |
| `GET` | `/users/{uid}/tasks?taskName=X` | Get a task by name |
| `PATCH` | `/users/{uid}/tasks` | Update date, special field, or percent complete |
| `DELETE` | `/users/{uid}/tasks` | Delete a task |

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/{uid}/events` | Create an event |
| `GET` | `/users/{uid}/events?name=X` | Get an event by name |
| `PATCH` | `/users/{uid}/events` | Update event fields |
| `DELETE` | `/users/{uid}/events` | Delete an event |

### Recommendations & Schedule

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/{uid}/recommendations` | Get today's ranked tasks + events + percentage targets |
| `GET` | `/users/{uid}/schedule/{dateString}` | Get all tasks/events for a specific date (MM-DD-YYYY) |

### Settings & Onboarding

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/{uid}/settings?settingField=X` | Get a specific setting |
| `PATCH` | `/users/{uid}/settings` | Update lazy days, task/event limits, or expiration window |
| `POST` | `/users/{uid}/onboarding` | Mark user as onboarded |

### Canvas

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/{uid}/canvas/connect` | Connect Canvas via API token |
| `POST` | `/users/{uid}/canvas/connect/ics` | Connect Canvas via ICS calendar URL |
| `POST` | `/users/{uid}/canvas/import` | Trigger a manual Canvas sync |
| `GET` | `/users/{uid}/canvas/pending` | Get pending (unconfirmed) Canvas tasks |
| `POST` | `/users/{uid}/canvas/confirm` | Confirm a pending Canvas task |
| `DELETE` | `/users/{uid}/canvas/pending/{canvasId}` | Dismiss a specific pending Canvas task |
| `DELETE` | `/users/{uid}/canvas/pending` | Clear all pending Canvas tasks |
| `GET` | `/users/{uid}/canvas/status` | Get current Canvas sync status |

Interactive docs available at `http://127.0.0.1:8000/docs` when running locally.

---

## Running Locally

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up .env
cp .env.example .env
# Fill in: mongoConString, GOOGLE_CLIENT_ID, JWT_SECRET

# Start the server
uvicorn api:app --reload
```

### Frontend

```bash
cd "frontend/Priority Calendar"

# Install dependencies
npm install

# Set up environment
echo "VITE_GOOGLE_CLIENT_ID=your_client_id_here" > .env.local

# Start dev server
npm run dev
```

The frontend dev server proxies `/api` requests to the backend. To point at a local backend instead, update the proxy target in `vite.config.js`.

---

## V2 Roadmap

- Notifications / reminders for high-priority tasks
- Mobile-responsive UI
- Recurring tasks support
- Multi-semester task archiving
- Smarter Canvas type inference (submission type heuristics)
