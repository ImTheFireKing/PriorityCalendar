import datetime
import pcClasses
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
undercroft = os.getenv("mongoConString")
client = MongoClient(undercroft)
db = client["PriorityCalendarDB"]
tasksCollection = db["Tasks"]
usersCollection = db["Users"]

def getCalendar(uid : str, year : str):
    calendar = []
    current = datetime.date(int(year), 1, 1)
    end = datetime.date(int(year), 12, 31)
    while current <= end:
        newDay = pcClasses.Day(current)
        calendar.append(newDay)
    if uid in usersCollection:
        results = tasksCollection.find({"uid" : uid})
        tasks = list[results]
        for task in results:
            
    return calendar

def storeTask(uid : str, task : pcClasses.Task):
    # If I had a backend, this is where I'd access the cache and throw a task in there to hold for the user

def storeEvent(uid : str, event : pcClasses.Events):
    # If I had a backend, this is where I'd access the cache and throw an event in there to hold for the user

def getSettings(uid : str):
    # If I had a backend, this is where I'd access the settings a user has for those purposes

def storeSettings(uid : str):
    # If I had a backend, this is where I'd save the settings a user has for those purposes