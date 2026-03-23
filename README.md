# Priority Calendar (WIP)

## Background

Most people - especially in college - have terrible time management, not because they're lazy, but because they lack a system for knowing *what* to work on and *how much* to do in a given day. Priority Calendar solves this by treating your academic workload like a strategy game: it analyzes your upcoming tasks and events, scores them by urgency and importance, and tells you exactly what to focus on each day so nothing sneaks up on you.

Rather than giving vague advice like "start early," the app uses a priority scoring algorithm to rank tasks and calculate the percentage of each one you should realistically complete today — accounting for your personal schedule, lazy days, and how much work is left.

---

## Tech Stack

### Backend

**Language:** Python  
**Framework:** FastAPI  
**Database:** MongoDB Atlas (via PyMongo)  
**Other:** Pydantic (request validation), python-dotenv (env management), Uvicorn (ASGI server)

### Frontend *(in progress)*

**Framework:** React + Vite  
**Design Reference:** Figma mockup (landing page, about page, changelog, main dashboard)

---

## Architecture Overview

### Classes (`pcClasses.py`)

The data model is built around a hierarchy of Python classes:

- **`Task`** — Base class with shared behavior (name, date, percent complete). Uses a `deepConstructor` factory method to instantiate subtypes, and a `fromDict` static method to deserialize from MongoDB.
  - **`Homework`** — Adds difficulty rating (`Easy`, `Moderate`, `Challenging`, or `Not Selected`)
  - **`Major`** — Handles both exams and projects via a `projectOrExam` flag. Supports exam difficulty and project collaboration type.
  - **`Quiz`** — Lightweight task with no special attributes
  - **`Prep`** — Low-priority prep work for upcoming classes/events
- **`Events`** — Standalone events with importance and prep-needed flags. Includes `toDict`/`fromDict` for serialization.
- **`Day`** — Container for tasks and events on a given date; computes day-of-week automatically. Accepts both `MM-DD-YYYY` strings and `datetime.date` objects.
- **`User`** — Holds user settings: lazy days, task/event limits, and expiration window

All dates are stored as `MM-DD-YYYY` strings in MongoDB and parsed into `datetime.date` objects internally. All task and event classes implement `toDict()`/`fromDict()` for MongoDB serialization.

### Storage (`pcStorage.py`)

Handles all MongoDB reads and writes with an in-memory cache layer:

- **Caches:** `currentCalendarCache`, `currentTasksCache`, `currentEventsCache`, `currentSettingsCache` — keyed by `(uid, year)` or `("uid", uid)`
- **Cache invalidation:** Triggered on any write; calendar cache also expires after 30 minutes
- **Serialization:** All tasks and events are stored as dicts via `toDict()` and reconstructed via `fromDict()` on retrieval
- **CRUD support for:** Tasks, Events, Settings, Users, Calendar (reconstructed on retrieval)

### Business Logic (`main.py`)

Orchestrates interactions between storage, classes, and the recommender:

- `createTask` / `createEvent` — Instantiates and stores new tasks/events; places them on the calendar
- `updateTask` / `updateEvent` — Handles date changes (moves item on calendar) and special field updates
- `deleteTask` / `deleteEvent` — Removes from both calendar and database
- `checkTasks` / `checkEvents` — Automated expiration: removes tasks past their due date (+ grace period from settings) or already 100% complete
- `getRecommendationsForToday` — Builds a `today` Day instance, pulls ranked task/event lists, and calculates per-task percentage targets using the user's settings

### Recommender (`recommender.py`)

The core algorithmic layer. Scores tasks and events on a **priority = intensity × urgency** model:

| Task Type | Intensity | Urgency Factors |
|-----------|-----------|-----------------|
| Exam / Project | 5 | Days until due (2–9x) |
| Quiz | 4 | Days until due (2–9x) |
| Homework | 2–6 | Days until due × difficulty multiplier (1–3) |
| Prep | 1–4 | Due tomorrow or not |
| Events | — | Importance × prep needed × time proximity |

- **`task_recommender`** — Collects up to `taskLimit * 3` candidates, scores them, sorts descending, returns top `taskLimit`
- **`event_recommender`** — Returns top `eventLimit` events sorted by score descending
- **`percentCalculate`** — Computes the % of a task to complete today based on available (non-lazy) working days remaining before the deadline, using the user's `lazy` days setting

### API (`api.py`)

RESTful API built with FastAPI. All routes are namespaced under `/users/{uid}/`. Errors are returned as proper HTTP exceptions rather than inline error strings.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/{uid}/tasks` | Create a task |
| `GET` | `/users/{uid}/tasks` | Get a task by name (query param) |
| `PATCH` | `/users/{uid}/tasks` | Update date, special field, or percent complete |
| `DELETE` | `/users/{uid}/tasks` | Delete a task |
| `POST` | `/users/{uid}/events` | Create an event |
| `GET` | `/users/{uid}/events` | Get an event by name (query param) |
| `PATCH` | `/users/{uid}/events` | Update event fields |
| `DELETE` | `/users/{uid}/events` | Delete an event |
| `GET` | `/users/{uid}/recommendations` | Get today's ranked tasks + events + percentage targets |
| `GET` | `/users/{uid}/settings` | Get a specific settings field (query param) |
| `PATCH` | `/users/{uid}/settings` | Update lazy days, task/event limits, or expiration window |

Interactive docs available at `http://127.0.0.1:8000/docs` when running locally.

---

## Running Locally

```bash
# Install dependencies
pip install fastapi uvicorn pymongo python-dotenv pydantic

# Set up your .env file
echo "mongoConString=<your_atlas_connection_string>" > .env

# Start the server
uvicorn api:app --reload
```

---

## Outstanding Work

- [ ] Recommendations endpoint — CRUD endpoints verified via Swagger; recommendations not yet end-to-end tested
- [ ] Canvas LMS API integration (planned)
- [ ] Full frontend build-out following Figma mockup

---

## Planned Features

- Canvas LMS API integration for auto-importing academic tasks
- User authentication
- Frontend dashboard: calendar view (left), recommendation hub (right), task/event creation and Canvas import (bottom)