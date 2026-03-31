import pcClasses
import recommender
from datetime import datetime
import datetime as dTime
import pcStorage

def createTask(uid : str, taskName : str, taskDate : str, taskType : str, existence : list[pcClasses.Day], alreadyDone : float = 0.0):
    newTask : pcClasses.Task = pcClasses.Task.deepConstructor(taskType, taskDate, taskName, alreadyDone)
    index = (newTask.getDate() - dTime.date(newTask.getDate().year, 1 ,1)).days
    existence[index].addTask(newTask)
    pcStorage.storeTask(uid, newTask)
    return newTask

def checkTasks(uid : str, calendar : list[pcClasses.Day]):
    """Checks all tasks to ensure that both due dates aren't passed (give a two week-ish grace period by default...OR WE COULD USE SETTINGS) and that percentages aren't at/above 100; In theory, 100 percent should be the only check, but :shrug:"""
    allTasks = pcStorage.getTasks(uid)
    settings = pcStorage.getSettings(uid)
    expiry = dTime.timedelta(0,0,0,0,0,0,settings['expired'])
    for task in allTasks:
        if task.getPercent() >= 100 or (dTime.datetime.today().date() - task.getDate() > expiry):
            deleteTask(uid, calendar, task)

def taskComplete(uid : str, task : pcClasses.Task, percentDone : float):
    task.updatePercent(percentDone)
    task.setLastWorked(dTime.date.today())
    return pcStorage.updateTasks(uid, task)

def deleteTask(uid : str, calendar : list[pcClasses.Day], task : pcClasses.Task):
    """Manual/automatic mechanism for deleting tasks from both the calendar and backend if a task is marked for deletion by the user or the system"""
    status1 = pcStorage.deleteTask(uid, task)
    index = (task.getDate() - dTime.date(task.getDate().year, 1, 1)).days
    status2 = calendar[index].removeTask(task)
    return status1 and status2

def getTasksForDay(uid : str, day : pcClasses.Day):
    return day.getTasks()
def getEventsForDay(uid : str, day : pcClasses.Day):
    return day.getEvents()
def getThingsForDay(uid : str, day : pcClasses.Day):
    return {"tasks" : getTasksForDay(uid, day), "events" : getEventsForDay(uid, day)}

def getRecommendationsForToday(uid : str):
    settings = pcStorage.getSettings(uid)
    calendar = pcStorage.getCalendar(uid, str(datetime.now().year))
    today = pcClasses.Day(datetime.today().date())
    if settings:
        toDo = recommender.task_recommender(calendar, today, settings, settings["Tlimit"])
        events = recommender.event_recommender(calendar, today, settings["Elimit"])
    else:
        toDo = recommender.task_recommender(calendar, today)
        events = recommender.event_recommender(calendar, today)
    percentages : list[float] = []
    for score, task, forced in toDo:
        percentages.append(recommender.percentCalculate(task, today, calendar, settings or {"lazy": []}))
    return {"tasks" : toDo, "events" : events, "howMuch" : percentages}

def updateTask(task: pcClasses.Task, field: str, newInfo: str, uid: str, calendar: list):
    if field == 'dueDate':
        index = (task.getDate() - dTime.date(task.getDate().year, 1, 1)).days
        calendar[index].removeTask(task)
        task.updateDate(newInfo)
        index = (task.getDate() - dTime.date(task.getDate().year, 1, 1)).days
        calendar[index].addTask(task)
        return pcStorage.updateTasks(uid, task, invalidate_calendar=True)  # date moved
    elif field == 'special':
        taskType = task.getType()
        if taskType == 'homework':
            task.setDifficulty(newInfo)
        elif taskType == 'exam':
            task.setExamDifficulty(newInfo)
        elif taskType == 'project':
            task.setProjectAttributes(newInfo == 'true')
        else: 
            return "Error: Attempted to update special field in a non-special task"
        return pcStorage.updateTasks(uid, task)  # no calendar change


def updateEvent(event: pcClasses.Events, field: str, newInfo: str, uid: str, calendar: list):
    if field == 'date':
        index = (event.getDate() - dTime.date(event.getDate().year, 1, 1)).days
        calendar[index].removeEvent(event)
        event.updateDate(newInfo)
        index = (event.getDate() - dTime.date(event.getDate().year, 1, 1)).days
        calendar[index].addEvent(event)
        return pcStorage.updateEvents(uid, event, invalidate_calendar=True)  #  date moved
    elif field == 'importance':
        event.setImportance(newInfo == 'true')
        return pcStorage.updateEvents(uid, event)  #  no calendar change
    elif field == 'prep':
        event.setPrepNeeded(newInfo == 'true')
        return pcStorage.updateEvents(uid, event)  #  no calendar change

def createEvent(uid : str, eventName : str, eventDate : str, existence : list[pcClasses.Day], needsPrep : bool = False, isImportant : bool = False):
    newEvent : pcClasses.Events = pcClasses.Events(eventName, eventDate, isImportant, needsPrep)
    index = (newEvent.getDate() - dTime.date(newEvent.getDate().year, 1 ,1)).days
    existence[index].addEvent(newEvent)
    pcStorage.storeEvent(uid, newEvent)

def checkEvents(uid : str, calendar : list[pcClasses.Day]):
    events = pcStorage.getEvents(uid)
    for event in events:
        if event.getDate() - datetime.today().date() < dTime.timedelta(0):
            deleteEvent(uid, event, calendar)

def deleteEvent(uid : str, event : pcClasses.Events, calendar : list[pcClasses.Day]):
    """Any event should only be deleted given the following circumstances: the event has already passed or the user has requested to delete the event"""
    index = (event.getDate() - dTime.date(event.getDate().year, 1, 1)).days
    calendar[index].removeEvent(event)
    return pcStorage.deleteEvent(uid, event)