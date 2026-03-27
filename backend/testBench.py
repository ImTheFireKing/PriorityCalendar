import sys
import random
from datetime import date, timedelta
import pcStorage
import pcClasses
import main
import recommender
import os
from dotenv import load_dotenv

load_dotenv()
UID    = os.getenv('TESTING_UID')
YEAR   = '2026'

backup_tasks    = []
backup_events   = []
backup_settings = {}

TASK_TYPES  = ['homework', 'exam', 'project', 'quiz', 'prep']
TASK_NAMES  = ['Math HW', 'Physics Study', 'Algo Assignment', 'Database Prep', 'AI Reading', 'Networking Review']
EVENT_NAMES = ['Club Meeting', 'Office Hours', 'Hackathon', 'Study Group', 'Career Fair', 'Seminar']

_name_counter = 0
def unique_name(base: str) -> str:
    global _name_counter
    _name_counter += 1
    return f"{base}_{_name_counter}"

def datestr(d: date) -> str:
    return d.strftime('%m-%d-%Y')

def random_date(year: int = 2026) -> date:
    return date(year, 1, 1) + timedelta(days=random.randint(0, 364))

def assert_(condition: bool, msg: str):
    if not condition:
        raise AssertionError(f"FAIL {msg}")
    print(f" PASS {msg}")

# ── Backup / Restore / Cache ──────────────────────────────────────────────────
def backup_user():
    global backup_tasks, backup_events, backup_settings
    backup_tasks   = list(pcStorage.tasks_collection.find({"uid": UID}, {"_id": 0}))
    backup_events  = list(pcStorage.events_collection.find({"uid": UID}, {"_id": 0}))
    user           = pcStorage.users_collection.find_one({"uid": UID})
    backup_settings = user.get('settings', {}) if user else {}
    print(f"Backup stored: {len(backup_tasks)} tasks, {len(backup_events)} events.")

def restore_user():
    if not backup_tasks and not backup_events:
        print("No backup exists — run backup first.")
        return
    pcStorage.tasks_collection.delete_many({"uid": UID})
    pcStorage.events_collection.delete_many({"uid": UID})
    if backup_tasks:   pcStorage.tasks_collection.insert_many(backup_tasks)
    if backup_events:  pcStorage.events_collection.insert_many(backup_events)
    pcStorage.users_collection.update_one({"uid": UID}, {"$set": {"settings": backup_settings}})
    flush_cache()
    print("User restored.")

def flush_cache():
    pcStorage._calendarCache.clear()
    pcStorage._tasksCache.clear()
    pcStorage._eventsCache.clear()
    pcStorage._settingsCache.clear()

# ── Tests ─────────────────────────────────────────────────────────────────────
def test_last_worked_roundtrip():
    print('test_last_worked_roundtrip')
    calendar = pcStorage.getCalendar(UID, YEAR)
    name = unique_name('lwtest')
    task = main.createTask(UID, name, '06-15-2026', 'homework', calendar)
    main.taskComplete(UID, task, 25.0)
    flush_cache()
    tasks = pcStorage.getTasks(UID)
    found = next((t for t in tasks if t.getName() == name), None)
    assert_(found is not None,            'task exists after reload')
    assert_(found.getLastWorked() is not None, 'lastWorked is not None')
    assert_(found.getLastWorked() == date.today(), 'lastWorked == today')
    doc = pcStorage.tasks_collection.find_one({"uid": UID, "name": name})
    raw = doc.get('lastWorked', '')
    assert_(len(raw) == 10 and raw[2] == '-' and raw[5] == '-',
            f"stored format is MM-DD-YYYY, got {raw}")
    flush_cache()
    calendar = pcStorage.getCalendar(UID, YEAR)
    tasks = pcStorage.getTasks(UID)
    found = next((t for t in tasks if t.getName() == name), None)
    if found:
        main.deleteTask(UID, calendar, found)
    flush_cache()
    print('done')

def test_forced_task_logic():
    print('test_forced_task_logic')
    calendar  = pcStorage.getCalendar(UID, YEAR)
    today_obj = pcClasses.Day(date.today())
    n_urgent  = unique_name('forced_urgent')
    n_normal  = unique_name('forced_normal')
    urgent = main.createTask(UID, n_urgent, datestr(date.today() + timedelta(days=1)),  'exam',     calendar)
    normal = main.createTask(UID, n_normal, datestr(date.today() + timedelta(days=60)), 'homework', calendar)
    flush_cache()
    calendar = pcStorage.getCalendar(UID, YEAR)
    settings = pcStorage.getSettings(UID) or {'lazy': []}
    results  = recommender.taskRecommender(calendar, today_obj, settings, taskLimit=1)
    names    = [t.getName() for _, t, _ in results]
    forced   = {t.getName(): f for _, t, f in results}
    assert_(n_urgent in names,               'urgent task appears in results')
    assert_(forced.get(n_urgent) == True,    'urgent task is flagged forced=True')
    flush_cache()
    calendar = pcStorage.getCalendar(UID, YEAR)
    tasks    = pcStorage.getTasks(UID)
    for name in [n_urgent, n_normal]:
        t = next((x for x in tasks if x.getName() == name), None)
        if t: main.deleteTask(UID, calendar, t)
    flush_cache()
    print('done')

def test_events_sort():
    print('test_events_sort')
    calendar = pcStorage.getCalendar(UID, YEAR)
    today_obj = pcClasses.Day(date.today())
    dates_in_order = [date.today() + timedelta(days=d) for d in [5, 15, 30]]
    shuffled = dates_in_order[:]
    random.shuffle(shuffled)
    event_names = []
    for i, d in enumerate(shuffled):
        n = unique_name(f'sortevent{i}')
        main.createEvent(UID, n, datestr(d), calendar, needsPrep=False, isImportant=False)
        event_names.append(n)
    flush_cache()
    calendar = pcStorage.getCalendar(UID, YEAR)
    results  = recommender.eventRecommender(calendar, today_obj, eventLimit=0)
    test_results = [(s, e) for s, e in results if e.getName() in event_names]
    for i in range(len(test_results) - 1):
        da = test_results[i][1].getDate()
        db = test_results[i+1][1].getDate()
        assert_(da <= db, f"event at index {i} ({da}) <= index {i+1} ({db})")
    events = pcStorage.getEvents(UID)
    for name in event_names:
        e = next((x for x in events if x.getName() == name), None)
        if e: main.deleteEvent(UID, e, calendar)
    flush_cache()
    print('done')

def test_check_tasks_expiry():
    print('test_check_tasks_expiry')
    old_year = str(date.today().year - 1)
    old_date = f'01-01-{old_year}'
    calendar = pcStorage.getCalendar(UID, old_year)
    n = unique_name('expirytest')
    main.createTask(UID, n, old_date, 'quiz', calendar)
    flush_cache()
    calendar = pcStorage.getCalendar(UID, old_year)
    main.checkTasks(UID, calendar)
    flush_cache()
    tasks = pcStorage.getTasks(UID)
    assert_(not any(t.getName() == n for t in tasks), 'expired task removed by checkTasks')
    print('done')

def test_recommendation_limit():
    print('test_recommendation_limit')
    LIMIT  = 5
    NTASKS = LIMIT + 5
    calendar  = pcStorage.getCalendar(UID, YEAR)
    today_obj = pcClasses.Day(date.today())
    far       = datestr(date.today() + timedelta(days=60))
    task_names = []
    for i in range(NTASKS):
        n = unique_name(f'limittask{i}')
        main.createTask(UID, n, far, 'prep', calendar)
        task_names.append(n)
    flush_cache()
    calendar = pcStorage.getCalendar(UID, YEAR)
    settings = {'lazy': []}
    results  = recommender.taskRecommender(calendar, today_obj, settings, taskLimit=LIMIT)
    non_forced = [r for r in results if not r[2]]
    assert_(len(non_forced) <= LIMIT, f"non-forced count {len(non_forced)} <= limit {LIMIT}")
    flush_cache()
    calendar = pcStorage.getCalendar(UID, YEAR)
    tasks    = pcStorage.getTasks(UID)
    for name in task_names:
        t = next((x for x in tasks if x.getName() == name), None)
        if t: main.deleteTask(UID, calendar, t)
    flush_cache()
    print('done')

def simulate_year():
    print('simulate_year')
    calendar = pcStorage.getCalendar(UID, YEAR)
    current  = date(2026, 1, 1)
    while current.year == 2026:
        ds = datestr(current)
        if random.random() < 0.35:
            main.createTask(UID, unique_name(random.choice(TASK_NAMES)), ds,
                            random.choice(TASK_TYPES), calendar,
                            alreadyDone=random.uniform(0, 40))
        if random.random() < 0.1:
            main.createEvent(UID, unique_name(random.choice(EVENT_NAMES)), ds, calendar,
                             needsPrep=random.choice([True, False]),
                             isImportant=random.choice([True, False]))
        tasks = pcStorage.getTasks(UID)
        for _ in range(random.randint(0, 2)):
            if tasks:
                main.taskComplete(UID, random.choice(tasks), random.uniform(5, 20))
        main.checkTasks(UID, calendar)
        main.checkEvents(UID, calendar)
        if random.random() < 0.2:
            main.getRecommendationsForToday(UID)
        current += timedelta(days=1)
    print('Year simulation complete.')

def fuzz_test(operations: int = 10000):
    print(f'fuzz_test {operations}')
    calendar = pcStorage.getCalendar(UID, YEAR)
    ops = ['createTask', 'createEvent', 'completeTask', 'updateTask', 'deleteTask', 'recommend']
    for i in range(operations):
        op    = random.choice(ops)
        tasks  = pcStorage.getTasks(UID)
        events = pcStorage.getEvents(UID)
        try:
            if op == 'createTask':
                main.createTask(UID, unique_name(random.choice(TASK_NAMES)),
                                datestr(random_date()), random.choice(TASK_TYPES), calendar,
                                alreadyDone=random.uniform(0, 50))
            elif op == 'createEvent':
                main.createEvent(UID, unique_name(random.choice(EVENT_NAMES)),
                                 datestr(random_date()), calendar,
                                 random.choice([True, False]), random.choice([True, False]))
            elif op == 'completeTask' and tasks:
                main.taskComplete(UID, random.choice(tasks), random.uniform(1, 30))
            elif op == 'updateTask' and tasks:
                main.updateTask(random.choice(tasks), 'dueDate', datestr(random_date()), UID, calendar)
            elif op == 'deleteTask' and tasks:
                main.deleteTask(UID, calendar, random.choice(tasks))
            elif op == 'recommend':
                main.getRecommendationsForToday(UID)
        except Exception as e:
            print(f"FUZZ FAILURE at {op} {i}")
            print(f"  Operation: {op}")
            print(f"  Error: {e}")
            import traceback; traceback.print_exc()
            return
        if i % 500 == 0 and i > 0:
            print(f"  {i} ops completed")
    print(f"Fuzz test finished {operations} operations, no failures.")

COMMANDS = {
    'backup':    backup_user,
    'restore':   restore_user,
    'simulate':  simulate_year,
    'fuzz':      fuzz_test,
    'testlw':    test_last_worked_roundtrip,
    'testforced': test_forced_task_logic,
    'testsort':  test_events_sort,
    'testexpiry': test_check_tasks_expiry,
    'testlimit': test_recommendation_limit,
    'testall':   lambda: [f() for f in [
        test_last_worked_roundtrip, test_forced_task_logic,
        test_events_sort, test_check_tasks_expiry, test_recommendation_limit
    ]],
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print('Commands:', ', '.join(COMMANDS))
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'fuzz' and len(sys.argv) >= 3:
        fuzz_test(int(sys.argv[2]))
    else:
        COMMANDS[cmd]()