from fastapi import FastAPI
from pydantic import BaseModel
import main
import pcStorage

app = FastAPI()
# Section 1: Tasks
class CreateTask(BaseModel):
    name : str
    date : str
    taskType : str
    special : str | None = None
    alreadyDone : float = 0.0
@app.post("/users/{uid}/tasks")
def createTask(uid : str, dataGiven : CreateTask):
    # MM-DD-YYYY
    calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
    newTask = main.createTask(uid, dataGiven.name, dataGiven.date, dataGiven.taskType, calendar, dataGiven.alreadyDone)
    if dataGiven.special:
        main.updateTask(newTask, "special", dataGiven.special, uid, calendar)
    return {"status" : "ok"}
class UpdateTask(BaseModel):
    taskName : str
    date : str | None = None
    special : str | None = None
    percentChange : float | None = None
@app.patch("users/{uid}/tasks")
def updateTask(uid : str, dataGiven : UpdateTask):
    #MM-DD-YYYY
    tasks = pcStorage.getTasks(uid)
    taskFound = None
    for task in tasks:
        if task.getName() == dataGiven.taskName:
            taskFound = task
            break
    if taskFound:
        statusList : dict[str, dict[str]] = {}
        calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
        if dataGiven.date:
            outcome = main.updateTask(taskFound, "date", dataGiven.date, uid, calendar)
            statusList["status"] = {"date" : outcome if type(outcome) == str else "ok"} 
        if dataGiven.special:
            outcome = main.updateTask(taskFound, "special", dataGiven.special, calendar)
            statusList["status"] = {"special" : outcome if type(outcome) == str else "ok"}
        if dataGiven.percentChange:
            outcome = main.taskComplete(uid, taskFound, dataGiven.percentChange)
            statusList["status"] = {"percentChange" : "ok" if outcome else "Error: Failed to update percent of task completed"}
        return statusList
    else:
        return {"status" : "Error: Task not found"}
    
class DeleteTask(BaseModel):
    taskName : str
@app.delete("users/{uid}/tasks")
def deleteTask(uid : str, dataGiven : DeleteTask):
    tasks = pcStorage.getTasks(uid)
    taskFound = None
    for task in tasks:
        if task.getName() == dataGiven.taskName:
            taskFound = task
            break
    if taskFound:
        calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
        outcome = main.deleteTask(uid, calendar, taskFound)
        return {"status" : "ok" if outcome else "Error: Task could not be found in database and/or day"}

# I lowkey cannot remember what else I need tbh...

    
        






# Section 3: Recommendations
@app.get("/users/{uid}/recommendations")
def sendRecommendations(uid : str):
    recommendations = main.getRecommendationsForToday(uid)
    tasks = recommendations["tasks"]
    events = recommendations["events"]
    percentages = recommendations["howMuch"]
    return {
        "tasks" : [
            {
                "name" : task.getName(),
                "type" : task.getType(),
                "dueDate" : task.getDate().isoformat(),
                "howMuch" : percent,
                "otherDetails" : task.getSpecial()
            }
            for (score, task), percent in zip(tasks, percentages)
        ],
        "events" : [
            {
                "name" : event.getName(),
                "priority" : event.getImportance(),
                "date" : event.getDate().isoformat(),
                "needsPrep" : event.getPrepNeed(),
            }
            for event in events
        ]
    }

