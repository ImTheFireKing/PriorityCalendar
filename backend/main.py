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
    for task in allTasks:
        if task.getPercent() >= 100 or (dTime.today().date - task.getDate() > settings["expired"]):
            deleteTask(uid, calendar, task)

def taskComplete(uid : str, task : pcClasses.Task, percentDone : float):
    task.updatePercent(percentDone)
    return pcStorage.updateTasks(uid, task)

def deleteTask(uid : str, calendar : list[pcClasses.Day], task : pcClasses.Task):
    """Manual/automatic mechanism for deleting tasks from both the calendar and backend if a task is marked for deletion by the user or the system"""
    status1 = pcStorage.deleteTask(uid, task)
    index = (task.getDate() - dTime.date(task.getDate().year, 1, 1)).days
    status2 = calendar[index].removeTask(task)
    return status1 and status2
    # I feel like I'm forgetting something but I don't know why...
def getTasksForDay(uid : str, day : pcClasses.Day):
    return day.getTasks()
def getEventsForDay(uid : str, day : pcClasses.Day):
    return day.getEvents()
def getThingsForDay(uid : str, day : pcClasses.Day):
    things : dict = {"tasks" : getTasksForDay(uid, day), "events" : getEventsForDay(uid, day)}
    return things
def getRecommendationsForToday(uid : str):
    settings = pcStorage.getSettings(uid)
    calendar = pcStorage.getCalendar(uid, str(datetime.now().year))
    if settings:
        toDo : list[(int, pcClasses.Task)] = recommender.task_recommender(calendar, datetime.now().year, settings["Tlimit"])
        events : list[(int, pcClasses.Events)] = recommender.event_recommender(calendar, datetime.now().year, settings["Elimit"])
    else:
        toDo : list[(int, pcClasses.Task)] = recommender.task_recommender(calendar, datetime.now().year)
        events : list[(int, pcClasses.Events)] = recommender.event_recommender(calendar, datetime.now().year)
    percentages : list[float] = []
    today = pcClasses.Day(datetime.today())
    for i in range(len(toDo)):
        percentages.append(recommender.percentCalculate(toDo[i][1], today, calendar))
    forToday : dict = {"tasks" : toDo, "events" : events, "howMuch" : percentages}
    return forToday
# TODO: Work on creating systems to update a task/event's attributes (Done)
# Allow the ability to update a task/event's due date and special attribute (Done) ; Updates the Calendar to reflect the changed date (also updates storage) (Done)
def updateTask(task : pcClasses.Task, field : str, newInfo : str, uid : str, calendar : list[pcClasses.Day]):
    if field == "dueDate":
        index = (task.getDate() - dTime.date(task.getDate().year, 1 ,1)).days
        calendar[index].removeTask(task)
        task.updateDate(newInfo)
        index = (task.getDate() - dTime.date(task.getDate().year, 1, 1)).days
        calendar[index].addTask(task)
        return pcStorage.updateTasks(uid, task)
    elif field == "special":
        taskType = task.getType()
        if taskType == "homework":
            task.setDifficulty(newInfo)
        elif taskType == "exam":
            task.setExamDifficulty(newInfo)
        elif taskType == "project":
            task.setProjectAttributes(newInfo=="true")
        else:
            return "Error: Attempted to update special field in a non-special task"
        return pcStorage.updateTasks(uid, task)
        

def updateEvent(event : pcClasses.Events, field : str, newInfo : str, uid : str, calendar : list[pcClasses.Day]):
    if field == "date":
        index = (event.getDate() - dTime.date(event.getDate().year, 1, 1)).days
        calendar[index].removeEvent(event)
        event.updateDate(newInfo)
        index = (event.getDate()-dTime.date(event.getDate().year, 1, 1)).days
        calendar[index].addEvent(event)
        return pcStorage.updateEvents(uid, event)
    elif field == "importance":
        event.setImportance(newInfo == "true")
    elif field == "prep":
        event.setPrepNeeded(newInfo == "true")
    return pcStorage.updateEvents(uid, event)
        

def createEvent(uid : str, eventName : str, eventDate : str, existence : list[pcClasses.Day], needsPrep : bool = False, isImportant : bool = False):
    newEvent : pcClasses.Events = pcClasses.Events(eventName, eventDate, isImportant, needsPrep)
    index = (newEvent.getDate() - datetime.date(newEvent.getDate().year, 1 ,1)).days
    existence[index].addTask(newEvent)
    pcStorage.storeTask(uid, newEvent)
def checkEvents(uid : str, calendar : list[pcClasses.Day]):
    events = pcStorage.getEvents(uid)
    for event in events:
        if event.getDate() - datetime.today().date < 0:
            deleteEvent(uid, event, calendar)
def deleteEvent(uid : str, event : pcClasses.Events, calendar : list[pcClasses.Day]):
    """Any event should only be deleted given the following circumstances: the event has already passed or the user has requested to delete the event"""
    index = (event.getDate() - dTime.date(event.getDate().year, 1, 1)).days
    calendar[index].removeEvent(event)
    return pcStorage.deleteEvent(uid, event)