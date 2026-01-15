import pcClasses
import recommender
from datetime import datetime
import pcStorage

def createTask(uid : str, taskName : str, taskDate : str, taskType : str, existence : list[pcClasses.Day], alreadyDone : float = 0.0):
    newTask : pcClasses.Task = pcClasses.Task.deepConstructor(taskType, taskDate, taskName, alreadyDone)
    index = (newTask.getDate() - datetime.date(newTask.getDate().year, 1 ,1)).days
    existence[index].addTask(newTask)
    pcStorage.storeTask(uid, newTask)
    # Note: Make logic to add day into a kind of cache stored in a database for quick lookups

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

# TODO - Make a Delete Event and Delete Task, Make a 

def main():
    uid = "0001"
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