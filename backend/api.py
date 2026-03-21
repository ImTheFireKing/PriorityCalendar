from fastapi import FastAPI
from fastapi import HTTPException
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

@app.get("/users/{uid}/tasks")
def getTask(uid : str, taskName : str):
    tasks = pcStorage.getTasks(uid)
    for task in tasks:
        if task.getName() == taskName:
            return {"task" :[
                {
                "name" : task.getName(),
                "type" : task.getType(),
                "dueDate" : task.getDate().isoformat(),
                "otherDetails" : task.getSpecial()
            }]}
    else:
        raise HTTPException(status_code=404, detail="Error: Task could not be found")
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
        calendar = pcStorage.getCalendar(uid, str(taskFound.getDate().year))
        if dataGiven.date:
            outcome = main.updateTask(taskFound, "date", dataGiven.date, uid, calendar)
            if type(outcome) == str:
                raise HTTPException(status_code=400, detail=outcome)
            else:
                statusList["status"] = {"date" : "ok"} 
        if dataGiven.special:
            outcome = main.updateTask(taskFound, "special", dataGiven.special, uid, calendar)
            if type(outcome) == str:
                raise HTTPException(status_code=400, detail=outcome)
            else:
                statusList["status"] = {"special" : "ok"}
        if dataGiven.percentChange:
            outcome = main.taskComplete(uid, taskFound, dataGiven.percentChange)
            if not outcome:
                raise HTTPException(status_code=404, detail="Error: Failed to update percent of task completed")
            else:
                statusList["status"] = {"percentChange" : "ok"}
        return statusList
    else:
        raise HTTPException(status_code=404, detail="Error: Task not found")
    
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
        calendar = pcStorage.getCalendar(uid, str(taskFound.getDate().year))
        outcome = main.deleteTask(uid, calendar, taskFound)
        if outcome:
            return {"status" : "ok"}
        else: 
            raise HTTPException(status_code=404, detail="Error: Task not found in calendar")

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
    return {"status" : "ok"}

@app.get("/users/{uid}/events")
def getEvent(uid : str, name : str):
    events = pcStorage.getEvents(uid)
    for event in events:
        if event.getName() == name:
            return {"event" : [{
                "name" : event.getName(),
                "date" : event.getDate(),
                "needsPrep" : event.getPrepNeeded(),
                "importance" : event.getImportance()
            }]}
    else:
        raise HTTPException(status_code=404, detail="Error: Task could not be found")

class UpdateEvent(BaseModel):
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
        calendar = pcStorage.getCalendar(uid, str(eventFound.getDate().year))
        if dataGiven.date:
            outcome = main.updateEvent(eventFound, "date", dataGiven.date, uid, calendar)
            if type(outcome) == str:
                raise HTTPException(status_code=400, detail=outcome)
            else:
                statusList["date"] = {"date" : "ok"} 
        if dataGiven.needsPrep:
            outcome = main.updateEvent(eventFound, "prep", dataGiven.needsPrep, uid, calendar)
            if type(outcome) == str:
                raise HTTPException(status_code=400, detail=outcome)
            else:
                statusList["prep"] = {"prep" : "ok"}
        if dataGiven.isImportant:
            outcome = main.updateEvent(eventFound, "importance", dataGiven.isImportant, uid, calendar)
            if not outcome:
                raise HTTPException(status_code=400, detail="Error: Failed to update importance of event")
            else: 
                statusList["importance"] = {"importance" : "ok"}
        return statusList
    else:
        raise HTTPException(status_code=404, detail="Error: Event not found")
    
class DeleteEvent(BaseModel):
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
        calendar = pcStorage.getCalendar(uid, str(eventFound.getDate().year))
        outcome = main.deleteEvent(uid, eventFound, calendar)
        if not outcome:
            raise HTTPException(status_code=404, detail="Error: Event could not be found in calendar")
        else:
            return {"status" : "ok"}


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

@app.get("/users/{uid}/settings")
def getSetting(uid : str, settingField : str):
    settings = pcStorage.getSettings(uid)
    if settingField not in settings:
        raise HTTPException(status_code=404, detail="Error: Field requested non-existent")
    else:
        return settings[settingField]
    
class updateSetting(BaseModel):
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


