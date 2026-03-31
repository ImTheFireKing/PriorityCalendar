from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
import main
import pcStorage
import datetime as dTime
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from auth import router as authRouter
from auth import get_current_uid
from fastapi import Depends
from fastapi import Response

app = FastAPI()
app.include_router(authRouter)

origins = [
    "http://localhost:5173"
    "https://prioritycalendar.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Section 1: Tasks
class CreateTask(BaseModel):
    name : str
    date : str
    taskType : str
    special : str | None = None
    alreadyDone : float = 0.0
@app.post("/users/{uid}/tasks")
def createTask(uid : str, dataGiven : CreateTask, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, details="Forbidden Resources")
    # MM-DD-YYYY
    calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
    newTask = main.createTask(uid, dataGiven.name, dataGiven.date, dataGiven.taskType, calendar, dataGiven.alreadyDone)
    if dataGiven.special:
        main.updateTask(newTask, "special", dataGiven.special, uid, calendar)
    return {"status" : "ok"}

@app.get("/users/{uid}/tasks")
def getTask(uid : str, taskName : str, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
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
def updateTask(uid : str, dataGiven : UpdateTask, currentUid : str = Depends(get_current_uid)):
    #MM-DD-YYYY
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
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
            outcome = main.updateTask(taskFound, "dueDate", dataGiven.date, uid, calendar)
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
                main.checkTasks(uid, calendar)
        return statusList
    else:
        raise HTTPException(status_code=404, detail="Error: Task not found")
    
class DeleteTask(BaseModel):
    taskName : str
@app.delete("/users/{uid}/tasks")
def deleteTask(uid : str, dataGiven : DeleteTask, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
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
def createEvent(uid : str, dataGiven : CreateEvent, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    calendar = pcStorage.getCalendar(uid, dataGiven.date[6:])
    main.createEvent(uid, dataGiven.name, dataGiven.date, calendar, dataGiven.needsPrep, dataGiven.isImportant)
    return {"status" : "ok"}

@app.get("/users/{uid}/events")
def getEvent(uid : str, name : str, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
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
def updateEvent(uid : str, dataGiven : UpdateEvent, currentUid : str = Depends(get_current_uid)):
    #MM-DD-YYYY
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
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
        main.checkEvents(uid, calendar)
        return statusList
    else:
        raise HTTPException(status_code=404, detail="Error: Event not found")
    
class DeleteEvent(BaseModel):
    name : str
@app.delete("/users/{uid}/events")
def deleteEvent(uid : str, dataGiven : DeleteEvent, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
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
def sendRecommendations(uid : str, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    calendar = pcStorage.getCalendar(uid, str(datetime.now().year))
    main.checkTasks(uid, calendar)
    main.checkEvents(uid, calendar)
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
                "otherDetails" : task.getSpecial(),     
                "forced" : forced                # True = bypassed task limit due to high workload today
            }
            for (score, task, forced), percent in zip(tasks, percentages)
        ],
        "events" : [
            {
                "name" : event.getName(),
                "priority" : event.getImportance(),
                "date" : event.getDate().isoformat(),
                "needsPrep" : event.getPrepNeeded(),
            }
            for (score, event) in events
        ]
    }

@app.get("/users/{uid}/schedule/{dateString}")
def getDailySchedule(uid : str, dateString: str, currentUid : str = Depends(get_current_uid)):
    # Expects dateString in MM-DD-YYYY format
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    year = dateString[6:]
    calendar = pcStorage.getCalendar(uid, year)
    
    target_date = dTime.datetime.strptime(dateString, "%m-%d-%Y").date()
    start_of_year = dTime.date(int(year), 1, 1)
    index = (target_date - start_of_year).days
    
    target_day = calendar[index]
    
    return {
            "tasks": [
                {
                    "name": task.getName(),
                    "type": task.getType(),
                    "dueDate": task.getDate().isoformat(),
                    "otherDetails": task.getSpecial(),
                } for task in target_day.getTasks()
            ],
            "events": [
                {
                    "name": event.getName(),
                    "time": event.getDate().isoformat(),
                    "importance": event.getImportance(),
                    "needsPrep": event.getPrepNeeded(),
                } for event in target_day.getEvents()
            ]
        }


@app.get("/users/{uid}/settings")
def getSetting(uid : str, settingField : str, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    settings = pcStorage.getSettings(uid)
    if settingField not in settings:
        raise HTTPException(status_code=404, detail="Error: Field requested non-existent")
    else:
        return settings[settingField]
    
class updateSetting(BaseModel):
    newDays : list[str] | None = None
    newELimit : int | None = None
    newTLimit : int | None = None
    newExpiration : str | None = None
@app.patch("/users/{uid}/settings")
def updateSettings(uid : str, dataGiven : updateSetting, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    settings = pcStorage.getSettings(uid)
    if dataGiven.newDays:
        settings["lazy"] = dataGiven.newDays
    if dataGiven.newELimit:
        settings["Elimit"] = dataGiven.newELimit
    if dataGiven.newTLimit:
        settings["Tlimit"] = dataGiven.newTLimit
    if dataGiven.newExpiration in ("1", "2", "4"):
        settings["expired"] = int(dataGiven.newExpiration)
    pcStorage.storeSettings(uid, settings)
    return {"status" : "ok"}


@app.post("/users/{uid}/onboarding")
def markOnboarded(uid: str, response : Response, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    if pcStorage.onboardUser(uid):
        from auth import createSessionToken, SESSION_HOURS
        newToken = createSessionToken(uid, True)
        response.set_cookie(key="session", value=newToken, httponly=True, secure=False, samesite="lax", max_age=SESSION_HOURS * 3600, path="/")
        return {"status" : "ok"}
    else:
        raise HTTPException(status_code=404, detail="Error: User could not be found somehow?")

class CanvasConnect(BaseModel):
    institutionalUrl : str
    token : str

@app.post("/users/{uid}/canvas/connect")
def connectCanvas(uid: str, body: CanvasConnect, currentUid: str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    import httpx as _httpx
    test = _httpx.get(
        f"{body.institutionalUrl.rstrip('/')}/api/v1/users/self",
        headers={"Authorization": f"Bearer {body.token}"}, timeout=8
    )
    if test.status_code != 200:
        raise HTTPException(status_code=400, detail="Canvas token invalid or URL incorrect")
    pcStorage.storeCanvasCredentials(uid, body.token, body.institutionalUrl)
    import threading, canvas
    threading.Thread(target=canvas.syncUser, args=(uid,), daemon=True).start()
    return {"status": "ok"}

class CanvasIcsConnect(BaseModel):
    icsUrl: str

@app.post("/users/{uid}/canvas/connect/ics")
def connectCanvasIcs(uid: str, body: CanvasIcsConnect, currentUid: str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    import httpx as _httpx
    try:
        test = _httpx.get(body.icsUrl, timeout=8, follow_redirects=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not reach that URL")
    if test.status_code != 200 or "BEGIN:VCALENDAR" not in test.text[:200]:
        raise HTTPException(status_code=400, detail="URL does not appear to be a valid Canvas ICS feed")
    pcStorage.storeCanvasIcsUrl(uid, body.icsUrl)
    import threading, canvas
    threading.Thread(target=canvas.syncUserIcs, args=(uid,), daemon=True).start()
    return {"status": "ok"}

@app.post("/users/{uid}/canvas/import")
def importCanvas(uid: str, currentUid: str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    import threading, canvas
    threading.Thread(target=canvas.syncUser, args=(uid,), daemon=True).start()
    return {"status": "ok"}

@app.get("/users/{uid}/canvas/pending")
def getPendingCanvasTasks(uid: str, currentUid: str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    tasks = pcStorage.getPendingCanvasTasks(uid)
    return {"pending": tasks, "count": len(tasks)}

class ConfirmCanvasTask(BaseModel):
    canvasId : str
    name     : str
    date     : str          # MM-DD-YYYY
    taskType : str
    special  : str | None = None

@app.post("/users/{uid}/canvas/confirm")
def confirmCanvasTask(uid: str, body: ConfirmCanvasTask, currentUid: str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    calendar = pcStorage.getCalendar(uid, body.date[6:])
    newTask = main.createTask(uid, body.name, body.date, body.taskType, calendar, 0.0)
    if body.special:
        main.updateTask(newTask, "special", body.special, uid, calendar)
    pcStorage.removePendingCanvasTask(uid, body.canvasId)
    return {"status": "ok"}

@app.delete("/users/{uid}/canvas/pending/{canvasId}")
def dismissCanvasTask(uid: str, canvasId: str, currentUid: str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    pcStorage.removePendingCanvasTask(uid, canvasId)
    return {"status": "ok"}

@app.delete("/users/{uid}/canvas/pending")
def clearCanvasChamber(uid : str, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbiden Resources")
    newChamber = pcStorage.storePendingCanvasTasks(uid, [])
    if not newChamber:
        raise HTTPException(status_code=500, detail="Failed to clear all suggestions.")
    return {"status" : "ok", "message" : "Pending Tasks Cleared"}
@app.get("/users/{uid}/canvas/status")
def getCanvasSyncStatus(uid : str, currentUid : str = Depends(get_current_uid)):
    if uid != currentUid:
        raise HTTPException(status_code=403, detail="Forbidden Resources")
    syncStatus = pcStorage.getSyncStatus(uid)
    return {"syncStatus" : syncStatus}