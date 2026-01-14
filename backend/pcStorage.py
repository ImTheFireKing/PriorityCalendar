import datetime
import pcClasses

def getCalendar(uid : str, year : str):
    calendar = []
    current = datetime.date(int(year), 1, 1)
    end = datetime.date(int(year), 12, 31)
    while current <= end:
        newDay = pcClasses.Day(current)
        calendar.append(newDay)
    # if uid in users: grab the cached dates, jump to each date in my cache, and update those games
    # else, just return the calendar
    return calendar

def storeTask(uid : str, task : pcClasses.Task):
    # If I had a backend, this is where I'd access the cache and throw a task in there to hold for the user

def storeEvent(uid : str, event : pcClasses.Events):
    # If I had a backend, this is where I'd access the cache and throw an event in there to hold for the user

def getSettings(uid : str):
    # If I had a backend, this is where I'd access the settings a user has for those purposes

def storeSettings(uid : str):
    # If I had a backend, this is where I'd save the settings a user has for those purposes