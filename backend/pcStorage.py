from datetime import datetime, timedelta
import datetime as dTime
import pcClasses
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os


load_dotenv()
undercroft = os.getenv('mongoConString')
client = MongoClient(undercroft, tlsAllowInvalidCertificates=True)
client.admin.command('ping')
db = client['PriorityCalendarDB']

users_collection  = db['Users']
tasks_collection  = db['Tasks']
events_collection = db['Events']

# Compound indexes — idempotent, fast lookups by (uid, name)
tasks_collection.create_index([("uid", ASCENDING), ("name", ASCENDING)], unique=True)
events_collection.create_index([("uid", ASCENDING), ("name", ASCENDING)], unique=True)
users_collection.create_index("uid", unique=True)

# ── Caches ────────────────────────────────────────────────────────────────────
_calendarCache:  dict = {}
_tasksCache:     dict = {}
_eventsCache:    dict = {}
_settingsCache:  dict = {}
_cacheTimestamp: dict = {}
CACHE_TTL = timedelta(minutes=30)

# ── Calendar ──────────────────────────────────────────────────────────────────
def _invalidateCalendar(uid: str):
    for key in [k for k in list(_calendarCache.keys()) if k[0] == uid]:
        del _calendarCache[key]
    for key in [k for k in list(_cacheTimestamp.keys()) if k[0] == uid]:
        del _cacheTimestamp[key]

def getCalendar(uid: str, year: str) -> list:
    yearKey = (uid, year)
    now     = datetime.now()
    stale   = (yearKey not in _cacheTimestamp or
               now - _cacheTimestamp[yearKey] > CACHE_TTL)

    if not stale and yearKey in _calendarCache:
        return _calendarCache[yearKey]

    startOfYear = dTime.date(int(year), 1, 1)
    current, end = startOfYear, dTime.date(int(year), 12, 31)
    calendar = []
    while current <= end:
        calendar.append(pcClasses.Day(current))
        current += timedelta(days=1)

    for task in getTasks(uid):
        if str(task.getDate().year) == year:
            calendar[(task.getDate() - startOfYear).days].addTask(task)

    for event in getEvents(uid):
        if str(event.getDate().year) == year:
            calendar[(event.getDate() - startOfYear).days].addEvent(event)

    _calendarCache[yearKey] = calendar
    _cacheTimestamp[yearKey] = now
    return calendar

# ── Tasks ─────────────────────────────────────────────────────────────────────
def getTasks(uid: str) -> list:
    if uid in _tasksCache:
        return _tasksCache[uid]
    docs  = list(tasks_collection.find({"uid": uid}, {"_id": 0, "uid": 0}))
    tasks = [pcClasses.Task.fromDict(d) for d in docs]
    _tasksCache[uid] = tasks
    return tasks

def storeTask(uid: str, task: pcClasses.Task) -> bool:
    result = tasks_collection.insert_one({"uid": uid, **task.toDict()})
    if result.inserted_id:
        _tasksCache.pop(uid, None)
        _invalidateCalendar(uid)
        return True
    return False

def updateTasks(uid: str, updatedTask: pcClasses.Task,
                invalidate_calendar: bool = True) -> bool:
    result = tasks_collection.update_one(
        {"uid": uid, "name": updatedTask.getName()},
        {"$set": updatedTask.toDict()}
    )
    if result.modified_count != 0:
        _tasksCache.pop(uid, None)
        if invalidate_calendar:
            _invalidateCalendar(uid)
        return True
    return False

def deleteTask(uid: str, task: pcClasses.Task) -> bool:
    result = tasks_collection.delete_one({"uid": uid, "name": task.getName()})
    if result.deleted_count != 0:
        _tasksCache.pop(uid, None)
        _invalidateCalendar(uid)
        return True
    return False

# ── Events ────────────────────────────────────────────────────────────────────
def getEvents(uid: str) -> list:
    if uid in _eventsCache:
        return _eventsCache[uid]
    docs   = list(events_collection.find({"uid": uid}, {"_id": 0, "uid": 0}))
    events = [pcClasses.Events.fromDict(d) for d in docs]
    _eventsCache[uid] = events
    return events

def storeEvent(uid: str, event: pcClasses.Events) -> bool:
    result = events_collection.insert_one({"uid": uid, **event.toDict()})
    if result.inserted_id:
        _eventsCache.pop(uid, None)
        _invalidateCalendar(uid)
        return True
    return False

def updateEvents(uid: str, updatedEvent: pcClasses.Events,
                 invalidate_calendar: bool = True) -> bool:
    result = events_collection.update_one(
        {"uid": uid, "name": updatedEvent.getName()},
        {"$set": updatedEvent.toDict()}
    )
    if result.modified_count != 0:
        _eventsCache.pop(uid, None)
        if invalidate_calendar:
            _invalidateCalendar(uid)
        return True
    return False

def deleteEvent(uid: str, event: pcClasses.Events) -> bool:
    result = events_collection.delete_one({"uid": uid, "name": event.getName()})
    if result.deleted_count != 0:
        _eventsCache.pop(uid, None)
        _invalidateCalendar(uid)
        return True
    return False

# ── Users & Settings ──────────────────────────────────────────────────────────
def addUser(uid: str, userSettings: dict) -> bool:
    if not users_collection.find_one({"uid": uid}):
        users_collection.insert_one({"uid": uid, "settings": userSettings, "onboarded" : False})
        return True
    return False
def onboardUser(uid: str):
    return users_collection.update_one({"uid": uid}, {"$set" : {"onboarded" : True}}).modified_count == 1
def getUser(uid: str):
    user = users_collection.find_one({"uid": uid})
    return user if user else False
def getLastCanvasSync(uid : str):
    possibleUser = users_collection.find_one({"uid" : uid})
    if possibleUser:
        return possibleUser["lastCanvasSync"]
def setSyncStatus(uid : str, status : bool):
    return users_collection.update_one({"uid" : uid}, {"$set" : {"syncStatus" : status}}).modified_count == 1
def getSyncStatus(uid : str):
    status = users_collection.find_one({"uid" : uid})
    return status.get("syncStatus", False) if status else False
def getSettings(uid: str) -> dict | None:
    if uid in _settingsCache:
        return _settingsCache[uid]
    user = users_collection.find_one({"uid": uid})
    if user:
        _settingsCache[uid] = user.get("settings", {})
        return _settingsCache[uid]
    return None

def storeSettings(uid: str, settings: dict) -> bool:
    result = users_collection.update_one(
        {"uid": uid}, {"$set": {"settings": settings}}
    )
    if result.modified_count != 0:
        _settingsCache.pop(uid, None)
        return True
    return False

def delUser(uid: str):
    users_collection.delete_one({"uid": uid})
    tasks_collection.delete_many({"uid": uid})
    events_collection.delete_many({"uid": uid})
    _tasksCache.pop(uid, None)
    _eventsCache.pop(uid, None)
    _settingsCache.pop(uid, None)
    _invalidateCalendar(uid)

# ── Canvas ────────────────────────────────────────────────────────────────────
def storeCanvasCredentials(uid: str, token: str, institutionUrl: str) -> bool:
    result = users_collection.update_one(
        {"uid": uid},
        {"$set": {"canvasToken": token, "canvasUrl": institutionUrl}}
    )
    return result.modified_count == 1

def getPendingCanvasTasks(uid: str) -> list:
    user = users_collection.find_one({"uid": uid}, {"pendingCanvasTasks": 1})
    return user.get("pendingCanvasTasks", []) if user else []

def storePendingCanvasTasks(uid: str, tasks: list) -> bool:
    result = users_collection.update_one(
        {"uid": uid},
        {"$set": {"pendingCanvasTasks": tasks}}
    )
    return result.modified_count == 1

def removePendingCanvasTask(uid: str, canvasId: str) -> bool:
    result = users_collection.update_one(
        {"uid": uid},
        {"$pull": {"pendingCanvasTasks": {"canvasId": canvasId}}}
    )
    return result.modified_count == 1

def updateLastCanvasSync(uid: str, dateStr: str) -> bool:
    result = users_collection.update_one(
        {"uid": uid},
        {"$set": {"lastCanvasSync": dateStr}}
    )
    return result.modified_count == 1

def storeCanvasIcsUrl(uid: str, icsUrl: str) -> bool:
    result = users_collection.update_one(
        {"uid": uid},
        {"$set": {"canvasIcsUrl": icsUrl}}
    )
    return result.modified_count == 1

def storeCanvasConnectTime(uid: str) -> bool:
    result = users_collection.update_one(
        {"uid": uid},
        {"$set": {"lastCanvasConnect": datetime.now(dTime.timezone.utc).isoformat()}}
    )
    return result.modified_count == 1

def getCanvasConnectTime(uid: str):
    user = users_collection.find_one({"uid": uid}, {"lastCanvasConnect": 1})
    return user.get("lastCanvasConnect") if user else None