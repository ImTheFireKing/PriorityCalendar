from datetime import datetime
import datetime as dTime

class Task:
    '''Overall class used to get types from smaller types + how we control most logic'''
    def deepConstructor(taskType : str, taskDate : str, taskName : str, alreadyDone : float = 0.0):
        '''Essentialy a constructor for the smaller types that inherit behaviors from the overall Task class'''
        if taskType == "exam":
            return Major(taskDate, taskName, alreadyDone, True)
        elif taskType == "project":
            return Major(taskDate, taskName, alreadyDone, False)
        elif taskType == "quiz":
            return Quiz(taskDate, taskName, alreadyDone)
        elif taskType in ("hw", "homework"):
            return Homework(taskDate, taskName, alreadyDone)
        elif taskType == "prep":
            return Prep(taskDate, taskName, alreadyDone)

    @staticmethod
    def fromDict(taskPackage : dict):
        taskType = taskPackage["type"]
        taskDate = taskPackage["date"]
        taskName = taskPackage["name"]
        taskPercentDone = taskPackage["percentDone"]
        # lastWorked may not exist on older documents — default to None
        rawLastWorked = taskPackage.get("lastWorked", None)
        if rawLastWorked:
            try:
                lastWorked = dTime.datetime.strptime(rawLastWorked, '%m-%d-%Y').date()
            except ValueError:
                lastWorked = None  # fallback for any legacy YYYY-MM-DD values
        else:
            lastWorked = None
            
        if taskType == "exam":
            constructedTask = Major(taskDate, taskName, taskPercentDone, True)
            constructedTask.setExamDifficulty(taskPackage["difficulty"])
        elif taskType == "project":
            constructedTask = Major(taskDate, taskName, taskPercentDone, False)
            constructedTask.setProjectAttributes(taskPackage["attributes"])
        elif taskType == "homework":
            constructedTask = Homework(taskDate, taskName, taskPercentDone, taskPackage["difficulty"])
        else:
            constructedTask = Task.deepConstructor(taskType, taskDate, taskName, taskPercentDone)

        constructedTask.lastWorked = lastWorked
        return constructedTask

    def getName(self):
        return self.name
    def getDate(self):
        return self.date
    def getLastWorked(self):
        return self.lastWorked
    def setLastWorked(self, workDate : dTime.date):
        self.lastWorked = workDate

    @staticmethod
    def _formatDate(d : dTime.date) -> str:
        return str(d.month).zfill(2) + "-" + str(d.day).zfill(2) + "-" + str(d.year)

class Homework(Task):
    '''First inherited class, comes with the unique behavior of homework difficulty'''
    # MM-DD-YYYY
    def __init__(self, taskDate, taskName : str, alreadyDone : float = 0.0, taskDifficulty : str = "Not Selected"):
        self.name = taskName
        self.date = dTime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5])) if type(taskDate) == str else taskDate
        self.difficulty = taskDifficulty
        self.percentDone = alreadyDone
        self.lastWorked = None
    def getType(self):
        return "homework"
    def setDifficulty(self, taskDifficulty : str):
        self.difficulty = taskDifficulty
    def getDifficulty(self):
        return self.difficulty
    def getPercent(self):
        return self.percentDone
    def updateDate(self, newDate : str):
        self.date = dTime.date(int(newDate[6:]), int(newDate[0:2]), int(newDate[3:5]))
    def updatePercent(self, updateBy : float):
        self.percentDone = self.percentDone + updateBy
    def getSpecial(self):
        return self.getDifficulty()
    def toDict(self):
        return {
            "name": self.name,
            "date": Task._formatDate(self.date),
            "difficulty": self.difficulty,
            "percentDone": self.percentDone,
            "type": self.getType(),
            "lastWorked": Task._formatDate(self.lastWorked) if self.lastWorked else None
        }

class Major(Task):
    '''Two classes in one; contains exams for exam logic and projects for project logic'''
    def __init__(self, taskDate, taskName : str, alreadyDone : float = 0.0, projectOrExam : bool = True):
        self.name = taskName
        self.date = dTime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5])) if type(taskDate) == str else taskDate
        if projectOrExam:
            self.examType = "regular"
        else:
            self.projectType = "individual"
        self.percentDone = alreadyDone
        self.lastWorked = None
    def getType(self):
        try:
            if self.examType:
                return "exam"
        except:
            return "project"
    def setExamDifficulty(self, examDifficulty : str):
        try:
            if self.getType() == "exam":
                self.examType = examDifficulty
                return True
            else:
                raise TypeError
        except TypeError:
            return "Error: Tried to set an exam difficulty for a project"
    def getExamDifficulty(self):
        try:
            if self.getType() == "exam":
                return self.examType
            else:
                raise TypeError
        except TypeError:
            return "Error: Tried to grab exam difficulty for a project"
    def setProjectAttributes(self, projectCollaboration : bool):
        try:
            if self.getType() == "project":
                self.projectType = projectCollaboration
            else:
                raise TypeError
        except TypeError:
            return "Error: Tried to set project attributes for an exam"
    def getProjectAttributes(self):
        try:
            if self.getType() == "project":
                return self.projectType
            else:
                raise TypeError
        except TypeError:
            return "Error: Tried to grab project attributes for an exam"
    def getPercent(self):
        return self.percentDone
    def updatePercent(self, updateBy : float):
        self.percentDone = self.percentDone + updateBy
    def updateDate(self, newDate : str):
        self.date = dTime.date(int(newDate[6:]), int(newDate[0:2]), int(newDate[3:5]))
    def getSpecial(self):
        return self.getExamDifficulty() if self.getType() == "exam" else self.getProjectAttributes()
    def toDict(self):
        typing = self.getType()
        base = {
            "name": self.name,
            "date": Task._formatDate(self.date),
            "percentDone": self.percentDone,
            "type": typing,
            "lastWorked": Task._formatDate(self.lastWorked) if self.lastWorked else None
        }
        if typing == "exam":
            base["difficulty"] = self.getExamDifficulty()
        else:
            base["attributes"] = self.getProjectAttributes()
        return base

class Quiz(Task):
    def __init__(self, taskDate, taskName : str, alreadyDone : float = 0.0):
        self.name = taskName
        self.date = dTime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5])) if type(taskDate) == str else taskDate
        self.percentDone = alreadyDone
        self.lastWorked = None
    def getType(self):
        return "quiz"
    def updateDate(self, newDate : str):
        self.date = dTime.date(int(newDate[6:]), int(newDate[0:2]), int(newDate[3:5]))
    def getPercent(self):
        return self.percentDone
    def updatePercent(self, updateBy : float):
        self.percentDone = self.percentDone + updateBy
    def getSpecial(self):
        return None
    def toDict(self):
        return {
            "name": self.name,
            "date": Task._formatDate(self.date),
            "percentDone": self.percentDone,
            "type": self.getType(),
            "lastWorked": Task._formatDate(self.lastWorked) if self.lastWorked else None
        }

class Prep(Task):
    def __init__(self, taskDate, taskName : str, alreadyDone : float = 0.0):
        self.name = taskName
        self.date = dTime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5])) if type(taskDate) == str else taskDate
        self.percentDone = alreadyDone
        self.lastWorked = None
    def getType(self):
        return "prep"
    def updateDate(self, newDate : str):
        self.date = dTime.date(int(newDate[6:]), int(newDate[0:2]), int(newDate[3:5]))
    def getPercent(self):
        return self.percentDone
    def updatePercent(self, updateBy : float):
        self.percentDone = self.percentDone + updateBy
    def getSpecial(self):
        return None
    def toDict(self):
        return {
            "name": self.name,
            "date": Task._formatDate(self.date),
            "percentDone": self.percentDone,
            "type": self.getType(),
            "lastWorked": Task._formatDate(self.lastWorked) if self.lastWorked else None
        }

class Events:
    '''Event logic: Contains when and what an event is and whether it's skippable or not'''
    def __init__(self, eventName : str, eventDate, eventImportant : bool = False, eventNeedsPrep : bool = False):
        self.name = eventName
        self.date = dTime.date(int(eventDate[6:]), int(eventDate[0:2]), int(eventDate[3:5])) if type(eventDate) == str else eventDate
        self.importance = eventImportant
        self.prepNeeded = eventNeedsPrep
    def getName(self):
        return self.name
    def getDate(self):
        return self.date
    def updateDate(self, newDate : str):
        self.date = dTime.date(int(newDate[6:]), int(newDate[0:2]), int(newDate[3:5]))
    def toDict(self):
        return {
            "name": self.name,
            "date": Task._formatDate(self.date),
            "importance": self.importance,
            "needsPrep": self.prepNeeded
        }
    @staticmethod
    def fromDict(eventPackage : dict):
        return Events(eventPackage["name"], eventPackage["date"], eventPackage["importance"], eventPackage["needsPrep"])
    def getImportance(self):
        return self.importance
    def setImportance(self, importance : bool):
        self.importance = importance
    def getPrepNeeded(self):
        return self.prepNeeded
    def setPrepNeeded(self, prep : bool):
        self.prepNeeded = prep

class Day:
    '''Kinda realized today that I sorta need a day class to hold information such as what tasks it contains and what day of the week it is...'''
    valid_days : dict[str] = {1 : "Mo", 2 : "Tu", 3 : "Wed", 4 : "Th", 5 : "F", 6 : "Sa", 7 : "Su"}
    def __init__(self, date):
        self.tasks : list[Task] = []
        self.dayEvents : list[Events] = []
        self.date = dTime.date(int(date[6:]), int(date[0:2]), int(date[3:5])) if type(date) == str else date
        self.dow : str = Day.valid_days[self.date.isoweekday()]

    def addTask(self, task : Task):
        if task in self.tasks:
            return False
        self.tasks.append(task)
        return True
    def removeTask(self, task : Task):
        index = -1
        for i in range(len(self.tasks)):
            if task.getName() == self.tasks[i].getName() and task.getDate() == self.tasks[i].getDate():
                index = i
                break
        if index == -1:
            return False
        del self.tasks[index]
        return True
    def getTasks(self):
        return self.tasks
    def addEvent(self, event : Events):
        if event in self.dayEvents:
            return False
        self.dayEvents.append(event)
        return True
    def removeEvent(self, event : Events):
        index = -1
        for i in range(len(self.dayEvents)):
            if event.getName() == self.dayEvents[i].getName() and event.getDate() == self.dayEvents[i].getDate():
                index = i
                break
        if index == -1:
            return False
        del self.dayEvents[index]
        return True
    def getEvents(self):
        return self.dayEvents

class User:
    def __init__(self, uid : str):
        self.settings : dict[str] = {}
        self.settings["lazy"] = []
        self.settings["Tlimit"] = 15
        self.settings["Elimit"] = 3
        self.settings["expired"] = 2
        self.uid = uid