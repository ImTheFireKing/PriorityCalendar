import pcClasses
import recommender
from datetime import datetime
import datetime as dTime
import pcStorage

def createTask(uid : str, taskName : str, taskDate : str, taskType : str, existence : list[pcClasses.Day], alreadyDone : float = 0.0):
    newTask : pcClasses.Task = pcClasses.Task.deepConstructor(taskType, taskDate, taskName, alreadyDone)
    index = (newTask.getDate() - datetime.date(newTask.getDate().year, 1 ,1)).days
    existence[index].addTask(newTask)
    pcStorage.storeTask(uid, newTask)

def checkTasks(uid : str, calendar : list[pcClasses.Day]):
    """Checks all tasks to ensure that both due dates aren't passed (give a two week-ish grace period by default...OR WE COULD USE SETTINGS) and that percentages aren't at/above 100; In theory, 100 percent should be the only check, but :shrug:"""
    allTasks = pcStorage.getTasks(uid)
    settings = pcStorage.getSettings(uid)
    for task in allTasks:
        if task.getPercent() >= 100 or (datetime.today().date - task.getDate() > settings["expired"]):
            deleteTask(uid, calendar, task)
def deleteTask(uid : str, calendar : list[pcClasses.Day], task : pcClasses.Task):
    """Manual/automatic mechanism for deleting tasks from both the calendar and backend if a task is marked for deletion by the user or the system"""
    pcStorage.deleteTask(uid, task)
    index = (task.getDate() - dTime.date(task.getDate().year, 1, 1)).days
    calendar[index].removeTask(task)
    # I feel like I'm forgetting something but I don't know why...
def getTasksForDay(uid : str, day : pcClasses.Day):
    return day.getTasks()

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
    return toDo, events, percentages

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
# TODO - Make a Delete Event and Delete Task (Done), Make a Check Tasks for Deletion (Done)
def deleteEvent(uid : str, event : pcClasses.Events, calendar : list[pcClasses.Day]):
    """Any event should only be deleted given the following circumstances: the event has already passed or the user has requested to delete the event"""
    pcStorage.deleteEvent(uid, event)
    index = (event.getDate() - dTime.date(event.getDate().year, 1, 1)).days
    calendar[index].removeEvent(event)
def main():
    uid = "0002"
    testUser = pcClasses.User(uid)
    pcStorage.addUser(uid, [], [], testUser.settings)
    today = datetime.today().date

    # 1. Make sure the calendar is loaded for this year
    year_str = str(datetime.today().year)
    calendar = pcStorage.getCalendar(uid, year_str)

    # 2. Get today’s recommendations
    recs = getRecommendationsForToday(uid)

    # 3. For now, just print them (CLI mode)
    print("Tasks for today:")
    for i in range(len(recs[0])):
        print(f"- {recs[0][i].getName()} (Due Date: {recs[0][i].getDate()}, do {recs[2][i]}%)")

    print("\nEvents to watch for:")
    for e in recs[1]:
        print(f"- {e.getName()} (important={e.getImportance()}, prep={e.getPrepNeeded()})")


if __name__ == "__main__":
    main() 