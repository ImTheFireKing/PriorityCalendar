import datetime
import pcClasses
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
undercroft = os.getenv("mongoConString")
client = MongoClient(undercroft)
db = client["PriorityCalendarDB"]
usersCollection = db["Users"]

def getCalendar(uid : str, year : str, cacheStatus : bool):
    calendar = []
    current = datetime.date(int(year), 1, 1)
    end = datetime.date(int(year), 12, 31)
    while current <= end:
        newDay = pcClasses.Day(current)
        calendar.append(newDay)
    if not cacheStatus:
        user = usersCollection.find_one({"uid" : uid})
        if type(user) != None:
            tasks : list[pcClasses.Task] = list[user["tasks"]]
            events : list[pcClasses.Events] = list[user["events"]]
            for task in tasks:
                index = (task.getDate() - datetime.date(int(year), 1, 1)) / datetime.timedelta(days=1) - 1
                calendar[index].addTask(task)
            for event in events:
                index = (event.getDate() - datetime.date(int(year), 1, 1)) / datetime.timedelta(days=1) - 1
                calendar[index].addEvent(event)
        cacheStatus = 
    return calendar

def storeTask(uid : str, task : pcClasses.Task):
    user = usersCollection.find_one({"uid" : uid})
    if type(user) != None:
        tasks = user["tasks"]
        tasks.insert(task)
        return True
    else:
        return False

def storeEvent(uid : str, event : pcClasses.Events):
    user = usersCollection.find_one({"uid" : uid})
    if type(user) != None:
        events = user["events"]
        events.insert(event)
        return True
    else:
        return False
def getSettings(uid : str):
    user = usersCollection.find_one({"uid" : uid})
    if type(user) != None:
        settings = user["settings"]
        return settings
    else:
        return False
def storeSettings(uid : str, settings : dict):
    user = usersCollection.find_one({"uid" : uid})
    if type(user) != None:
        


def deleteTask(uid : str, task : pcClasses.Task):

def deleteEvent(uid : str, event : pcClasses.Events):