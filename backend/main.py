import pcClasses
import recommender
import datetime

def getCalendar(uid : str, year : str):
    calendar = []
    current = datetime.date(int(year), 1, 1)
    end = datetime.date(int(year), 12, 31)
    while current <= end:
        newDay = pcClasses.Day(current)
    

def createTask(uid : str, taskName : str, taskDate : str, taskType : str, day : pcClasses.Day, alreadyDone : float = 0.0):
    newTask : pcClasses.Task = pcClasses.Task.deepConstructor(taskType, taskDate, taskName, alreadyDone)
    day.addTask(newTask)
    # Note: Make logic to add day into a kind of cache stored in a database for quick lookups

def getTasksForDay(uid : str, day : pcClasses.Day):
    return day.getTasks()

def getRecommendationsForDay(uid : str, day : pcClasses.Day):
    toDo : list[(int, pcClasses.Task)] = recommender.task_recommender(, today, 3)
    percentages : list[float] = []
    testUser = User()
    User.settings["lazy"] = ["Mo", "Tu", "Wed"]
    for i in range(len(toDo)):
        percentages.append(percentCalculate(toDo[i][1], today, calendar))
    print("These are the tasks to complete today: ")
    for i, entry in enumerate(toDo):
        print(f"{entry[1].name}, {percentages[i]}")


