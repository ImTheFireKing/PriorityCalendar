from fastapi import FastAPI
from pydantic import BaseModel
import main
import pcStorage
import datetime as dTime

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

class GetTask(BaseModel):
    name : str
    date : str
@app.get("/users/{uid}/tasks")
def getTask(uid : str, taskDetails : GetTask):
    tasks = pcStorage.getTasks(uid)
    for task in tasks:
        if task.getName() == taskDetails.name:
            return {"task" :[
                {
                "name" : task.getName(),
                "type" : task.getType(),
                "dueDate" : task.getDate().isoformat(),
                "otherDetails" : task.getSpecial()
            }]}
class UpdateTask(BaseModel):
    taskName : str
    date : str | None = None
    special : str | None = None
    percentChange : float | None = None
@app.patch("/users/{uid}/tasks")
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
@app.delete("/users/{uid}/tasks")
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

# Note: For raw resources, implement CRUD transactions into these areas

# Section 2: Events

class CreateEvent(BaseModel):
    name : str
    date : str
    needsPrep : bool  = False
    isImportant : bool  = False
        
@app.post("/users/{uid}/events")
def createEvent(uid : str, dataGiven : CreateEvent):
    calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
    main.createEvent(uid, dataGiven.name, dataGiven.date, calendar, dataGiven.needsPrep, dataGiven.isImportant)

class GetEvent(BaseModel):
    name : str
@app.get("/users/{uid}/events")
def getEvent(uid : str, dataGiven : GetEvent):
    events = pcStorage.getEvents(uid)
    for event in events:
        if event.getName() == dataGiven.name:
            return {"event" : [{
                "name" : event.getName(),
                "date" : event.getDate(),
                "needsPrep" : event.getPrepNeeded(),
                "importance" : event.getImportance()
            }]}

class UpdateEvent:
    name : str
    date : str | None = None
    needsPrep : str | None = None
    isImportant : str | None = None
@app.patch("/users/{uid}/events")    
def updateEvent(uid : str, dataGiven : UpdateEvent):
    #MM-DD-YYYY
    events = pcStorage.getEvents(uid)
    eventFound = None
    for event in events:
        if event.getName() == dataGiven.name:
            eventFound = event
            break
    if eventFound:
        statusList : dict[str, dict[str]] = {}
        calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
        if dataGiven.date:
            outcome = main.updateEvent(eventFound, "date", dataGiven.date, uid, calendar)
            statusList["date"] = {"date" : outcome if type(outcome) == str else "ok"} 
        if dataGiven.needsPrep:
            outcome = main.updateEvent(eventFound, "prep", dataGiven.needsPrep, calendar)
            statusList["prep"] = {"prep" : outcome if type(outcome) == str else "ok"}
        if dataGiven.isImportant:
            outcome = main.updateEvent(eventFound, "importance", dataGiven.isImportant, )
            statusList["importance"] = {"importance" : "ok" if outcome else "Error: Failed to update percent of task completed"}
        return statusList
    else:
        return {"status" : "Error: Task not found"}
    
class DeleteEvent:
    name : str
@app.delete("/users/{uid}/events")
def deleteEvent(uid : str, dataGiven : DeleteEvent):
    events = pcStorage.getEvents(uid)
    eventFound = None
    for event in events:
        if event.getName() == dataGiven.name:
            eventFound = event
            break
    if eventFound:
        calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
        outcome = main.deleteEvent(uid, eventFound, calendar)
        return {"status" : "ok" if outcome else "Error: Task could not be found in database and/or day"}


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

# Think I just got settings left and that's the framework for APIs done...and backend done as a result
class GetSetting:
    field : str
@app.get("/users/{uid}/settings")
def getSetting(uid : str, dataGiven : GetSetting):
    settings = pcStorage.getSettings(uid)
    if dataGiven.field not in settings:
        return {"status" : "Error: Field requested non-existent"}
    else:
        return settings[dataGiven.field]
    
class updateSetting:
    newDays : list[str] | None = None
    newELimit : int | None = None
    newTLimit : int | None = None
    # By default, keep expiration date at two weeks; Else, allow changes to preset values (2 weeks, 1 week, 4 weeks)
    newExpiration : str | None = None
@app.patch("/users/{uid}/settings")
def updateSettings(uid : str, dataGiven : updateSetting):
    settings = pcStorage.getSettings(uid)
    if dataGiven.newDays:
        settings["lazy"] = dataGiven.newDays
    if dataGiven.newELimit:
        settings["Elimit"] = dataGiven.newELimit
    if dataGiven.newTLimit:
        settings["Tlimit"] = dataGiven.newTLimit
    if dataGiven.newExpiration:
        if dataGiven.newExpiration == "2":
            settings["expired"] = dTime.timedelta(0,0,0,0,0,0,2)
        elif dataGiven.newExpiration == "1":
            settings["expired"] = dTime.timedelta(0,0,0,0,0,0,1)
        elif dataGiven.newExpiration == "4":
            settings["expired"] = dTime.timedelta(0,0,0,0,0,0,4)
    return {"status" : "ok"}


