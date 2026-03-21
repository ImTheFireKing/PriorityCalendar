from datetime import datetime, timedelta
import datetime as dTime
import pcClasses
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys
# Remember: Implement CRUD in Database
load_dotenv()
undercroft = os.getenv("mongoConString")
client = MongoClient(undercroft, tlsAllowInvalidCertificates=True)
client.admin.command("ping")
db = client["PriorityCalendarDB"]
usersCollection = db["Users"]
currentSettingsCache : dict[tuple[str,str], dict] = {}
currentCalendarCache : dict[tuple[str, str], list[pcClasses.Day]] = {}
currentTasksCache : dict[tuple[str, str], list[pcClasses.Task]] = {}
currentEventsCache : dict[tuple[str, str], list[pcClasses.Events]] = {} 
cacheTooStale = timedelta(0,0,0,0,30)
cacheTimeStamp : dict[tuple[str, str], datetime.time] = {}
def getCalendar(uid : str, year : str):
    # Retrieval of Tasks and Events
    calendar = []
    startOfYear = dTime.date(int(year), 1, 1)
    current = startOfYear
    end = dTime.date(int(year), 12, 31) 
    yearKey = (uid, year)
    if (uid, year) not in cacheTimeStamp:
        cacheTimeStamp[(uid, year)] = datetime.now()
    if yearKey not in currentCalendarCache or (datetime.now() - cacheTimeStamp[uid, year]) > cacheTooStale:
        while current <= end:
            newDay = pcClasses.Day(current)
            calendar.append(newDay)
            current += timedelta(days=1)
        user = usersCollection.find_one({"uid" : uid})
        currentEventsCache[("uid", uid)] = []
        currentTasksCache[("uid", uid)] = []
        if user:
            realTasks : list[pcClasses.Task] = []
            tasks = user.get("tasks", [])
            realEvents : list[pcClasses.Events] = [] 
            events = user.get("events", [])
            for task in tasks:
                trueTask = pcClasses.Task.fromDict(task)
                realTasks.append(trueTask)
            for event in events:
                trueEvent = pcClasses.Events.fromDict(event)
                realEvents.append(trueEvent)
            for task in realTasks:
                index = (task.getDate() - startOfYear).days
                calendar[index].addTask(task)
                currentTasksCache[("uid", uid)].append(task)
            for event in realEvents:
                index = (event.getDate() - startOfYear).days
                calendar[index].addEvent(event)
                currentEventsCache[("uid", uid)].append(event)
        currentCalendarCache[yearKey] = calendar
        cacheTimeStamp[(uid, year)] = datetime.now()
        return calendar
    else:
        return currentCalendarCache[yearKey]

def storeTask(uid : str, task : pcClasses.Task):
    # Creation of Tasks
    user = usersCollection.find_one({"uid" : uid})
    if user:
        tasks = user.get("tasks", [])
        tasks.append(task.toDict())
        usersCollection.update_one(filter={"uid": uid}, update={"$set": {"tasks": tasks}})
        cacheRemovalList = []
        for u, year in currentCalendarCache.keys():
            if u == uid:
                cacheRemovalList.append(year)
        for year in cacheRemovalList:
            if (uid, year) in currentCalendarCache:
                del currentCalendarCache[(uid, year)]
        if ("uid", uid) in currentTasksCache:
            del currentTasksCache[("uid", uid)]
        return True
    else:
        return False
    
def getTasks(uid : str):
    # Retrieval of Tasks
    if ("uid", uid) in currentTasksCache:
        return currentTasksCache[("uid", uid)]
    user = usersCollection.find_one({"uid" : uid})
    if user:
        currentTasksCache[("uid", uid)] = user.get("tasks", [])
        for i in range(len(currentTasksCache[("uid", uid)])):
            currentTasksCache[("uid", uid)][i] = pcClasses.Task.fromDict(currentTasksCache[("uid", uid)][i])
        return currentTasksCache[("uid", uid)]
    else:
        return []
def updateTasks(uid : str, updatedTask : pcClasses.Task):
    # Updating of Tasks
    if ("uid", uid) in currentTasksCache:
        del currentTasksCache[("uid", uid)]
    user = usersCollection.find_one({"uid" : uid})
    formattedTask = updatedTask.toDict()
    if user:
        tasks = user.get("tasks", [])
        for i in range(len(tasks)):
            if tasks[i]["name"] == formattedTask["name"]:
                tasks[i] = formattedTask
                break
        usersCollection.update_one(filter={"uid" : uid}, update={"$set": {"tasks" : tasks}})
        return True
    else:
        return False

def getEvents(uid : str):
    # Retrieval of Events
    if ("uid", uid) in currentEventsCache:
        return currentEventsCache[("uid", uid)]
    user = usersCollection.find_one({"uid" : uid})
    if user:
        currentEventsCache[("uid", uid)] = user.get("events", [])
        for i in range(len(currentEventsCache[("uid", uid)])):
            currentEventsCache[("uid", uid)][i] = pcClasses.Events.fromDict(currentEventsCache[("uid", uid)][i])
        return currentEventsCache[("uid", uid)]
    else:
        return []
    
def updateEvents(uid : str, updatedEvent : pcClasses.Events):
    # Updating of Events
    if ("uid", uid) in currentEventsCache:
        del currentEventsCache[("uid", uid)]
    user = usersCollection.find_one({"uid" : uid})
    formattedEvent = updatedEvent.toDict()
    if user:
        events = user.get("events", [])
        for i in range(len(events)):
            if events[i]["name"] == formattedEvent["name"]:
                events[i] = formattedEvent
                break
        usersCollection.update_one(filter={"uid" : uid}, update={"$set": {"events" : events}})
        return True
    else:
        return False
    

def storeEvent(uid : str, event : pcClasses.Events):
    # Creation of Events
    user = usersCollection.find_one({"uid" : uid})
    if user:
        events = user.get("events", [])
        events.append(event.toDict())
        usersCollection.update_one(filter={"uid": uid}, update={"$set": {"events": events}})
        cacheRemovalList = []
        for u, year in currentCalendarCache.keys():
            if u == uid:
                cacheRemovalList.append(year)
        for year in cacheRemovalList:
            if (uid, year) in currentCalendarCache:
                del currentCalendarCache[(uid, year)]
        if ("uid", uid) in currentEventsCache:
            del currentEventsCache[("uid", uid)]
        return True
    else:
        return False
    
def getSettings(uid : str):
    # Retrieval of Settings
    if ("uid", uid) not in currentSettingsCache:
        user = usersCollection.find_one({"uid" : uid})
        if user:
            currentSettingsCache [("uid", uid)]= user.get("settings", {})
            return currentSettingsCache[("uid", uid)]
        else:
            return {}
    else:
        return currentSettingsCache[("uid", uid)]
    
def storeSettings(uid : str, settings : dict):
    # Creation/Update of Settings
    user = usersCollection.find_one({"uid" : uid})
    if user:
        usersCollection.update_one(filter={"uid": uid}, update={"$set": {"settings": settings}})
        if ("uid", uid) in currentSettingsCache:
            del currentSettingsCache[("uid", uid)]
        return True
    else:
        return False

def deleteTask(uid : str, task : pcClasses.Task):
    # Deletion of Tasks
    user = usersCollection.find_one({"uid" : uid})
    formattedTask = task.toDict()
    if user:
        tasks = user.get("tasks", [])
        index = 0
        for i in range(len(tasks)):
            if tasks[i] == formattedTask:
                index = i
                break
        else:
            return False
        del tasks[index]
        usersCollection.update_one(filter={"uid": uid}, update={"$set": {"tasks": tasks}})
        cacheRemovalList = []
        for u, year in currentCalendarCache.keys():
            if u == uid:
                cacheRemovalList.append(year)
        for year in cacheRemovalList:
            if (uid, year) in currentCalendarCache:
                del currentCalendarCache[(uid, year)]
        if ("uid", uid) in currentTasksCache:
            del currentTasksCache[("uid", uid)]
        return True
    else:
        return False

def deleteEvent(uid : str, event : pcClasses.Events):
    # Deletion of Events
    user = usersCollection.find_one({"uid" : uid})
    formattedEvent = event.toDict()
    if user:
        events = user.get("events", [])
        index = 0
        for i in range(len(events)):
            if events[i] == formattedEvent:
                index = i
                break
        else:
            return False
        del events[index]
        usersCollection.update_one(filter={"uid": uid}, update={"$set": {"events": events}})
        cacheRemovalList = []
        for u, year in currentCalendarCache.keys():
            if u == uid:
                cacheRemovalList.append(year)
        for year in cacheRemovalList:
            if (uid, year) in currentCalendarCache:
                del currentCalendarCache[(uid, year)]
        if ("uid", uid) in currentEventsCache:
            del currentEventsCache[("uid", uid)]
        return True
    else:
        return False
    
def addUser(uid : str, userTasks : list[pcClasses.Task], userEvents : list[pcClasses.Events], userSettings : dict):
    # Creation of a User
    if not usersCollection.find({"uid" : uid}):
        usersCollection.insert_one({"uid" : uid, "tasks" : userTasks, "events" : userEvents, "settings" : userSettings})
        return True
    else:
        return False
def getUser(uid : str):
    # Retrieval of a User
    user = usersCollection.find_one({"uid" : uid})
    if user:
        return user
    else:
        return False
def delUser(uid : str):
    # Deletion of User, Settings
    usersCollection.delete_many(filter={"uid" : uid})
    cacheRemovalList = []
    for u, year in currentCalendarCache.keys():
        if u == uid:
            cacheRemovalList.append(year)
    for year in cacheRemovalList:
        if (uid, year) in currentCalendarCache:
            del currentCalendarCache[(uid, year)]
        
        if (uid, year) in cacheTimeStamp:
            del cacheTimeStamp[(uid, year)]
    if ("uid", uid) in currentSettingsCache:
        del currentSettingsCache[("uid", uid)]
    if ("uid", uid) in currentTasksCache:
        del currentTasksCache[("uid", uid)]
    if ("uid", uid) in currentEventsCache:
        del currentEventsCache[("uid", uid)]