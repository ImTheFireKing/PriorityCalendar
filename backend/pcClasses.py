import datetime

class Task:
    '''Overall class used to get types from smaller types + how we control most logic'''
    def deepConstructor(taskType : str, taskDate : str, taskName : str, alreadyDone : float = 0.0):
        '''Essentialy a constructor for the smaller types that inherit behaviors from the overall Task class'''
        if taskType == "exam" or taskType == "project":
            return Major(taskDate, taskName, alreadyDone)
        elif taskType == "quiz":
            return Quiz(taskDate, taskName, alreadyDone)
        elif taskType == "hw":
            return Homework(taskDate, taskName, alreadyDone)
        elif taskType == "prep":
            return Prep(taskDate, taskName, alreadyDone)
    # def getDate(self):
    #     '''Returns the date the task occurs as an integer ranging from 1 (Jan 1) to 365 (Dec 31) + 1 for a leap year'''
    #     # Note for later: We need a way to standardize dates; Preferably into a MM-DD format (and maybe MM-DD-YY, but let's focus on MM-DD rn)
    #     # We need to add up all the days in previous months, then add the days passed in that month
    #     dateCounter : int = 0
    #     monthPortion : int = int(self.date[0:2])
    #     dayPortion : int = int(self.date[3:5])
    #     # Adding every single day that's passed previously
    #     if monthPortion > 1:
    #         dateCounter += 31
    #     if monthPortion > 2:
    #         # Leap year check
    #         if (int(self.date[6:8]) % 4 == 0):
    #             dateCounter += 29
    #         else:
    #             dateCounter += 28
    #     if monthPortion > 3:
    #         dateCounter += 31
    #     if monthPortion > 4:
    #         dateCounter += 30
    #     if monthPortion > 5:
    #         dateCounter += 31
    #     if monthPortion > 6:
    #         dateCounter += 30
    #     if monthPortion > 7:
    #         dateCounter += 31
    #     if monthPortion > 8:
    #         dateCounter += 31
    #     if monthPortion > 9:
    #         dateCounter += 30
    #     if monthPortion > 10:
    #         dateCounter += 31
    #     if monthPortion > 11:
    #         dateCounter += 30
    #     dateCounter += dayPortion
    #     return dateCounter
    def getName(self):
        return self.name
    
class Homework(Task):
    '''First inherited class, comes with the unique behavior of homework difficulty'''
    # MM-DD-YYYY
    def __init__(self, taskDate : str, taskName : str, alreadyDone : float = 0.0, taskDifficulty : str = "Not Selected"):
        self.name = taskName
        self.date = datetime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5]))
        self.difficulty = taskDifficulty
        self.percentDone = alreadyDone
    def getType(self):
        return "homework"
    def setDifficulty(self, taskDifficulty : str):
        self.difficulty = taskDifficulty
    def getDifficulty(self):
        return self.difficulty
    def getPercent(self):
        return self.percent
    def updatePercent(self, updateBy : float):
        self.percent = self.percent + updateBy
class Major(Task):
    '''Two classes in one; contains exams for exam logic and projects for project logic'''
    def __init__(self, taskDate : str, taskName : str, alreadyDone : float = 0.0, projectOrExam : bool = True):
        self.name = taskName
        self.date = datetime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5]))
        if (projectOrExam):
            self.examType = "regular"
        else:
            self.projectType = "individual"
        self.percentDone = alreadyDone
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
            else:
                raise TypeError
        except TypeError:
            # I'm...probably gonna have to deal with this later but I'll cross that bridge when I get to it
            print("wah")
    def getExamDifficulty(self):
        try:
            if self.getType() == "exam":
                return self.examType
            else:
                raise TypeError
        except TypeError:
            print("wah")

    def setProjectAttributes(self, projectCollaboration : bool):
        try:
            if self.getType() == "project":
                self.projectType = projectCollaboration
            else:
                raise TypeError
        except TypeError:
            print("wah")

    def getProjectAttributes(self):
        try:
            if self.getType() == "project":
                return self.projectType
            else:
                raise TypeError
        except TypeError:
            print("wah")
    def getPercent(self):
        return self.percent
    def updatePercent(self, updateBy : float):
        self.percent = self.percent + updateBy

class Quiz(Task):
    def __init__(self, taskDate : str, taskName : str, alreadyDone : float = 0.0):
        self.name = taskName
        self.date = datetime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5]))
        self.percentDone = alreadyDone
    def getType(self):
        return "quiz"
    def getPercent(self):
        return self.percent
    def updatePercent(self, updateBy : float):
        self.percent = self.percent + updateBy

class Prep(Task):
    def __init__(self, taskDate : str, taskName : str, alreadyDone : float = 0.0):
        self.name = taskName
        self.date = datetime.date(int(taskDate[6:]), int(taskDate[0:2]), int(taskDate[3:5]))
        self.percentDone = alreadyDone
    def getType(self):
        return "prep"
    def getPercent(self):
        return self.percent
    def updatePercent(self, updateBy : float):
        self.percent = self.percent + updateBy

class Events:
    '''Event logic: Contains when and what an event is and whether it's skippable or not'''
    def __init__(self, eventName : str, eventDate : str, eventImportant : bool = False, eventNeedsPrep : bool = False):
        self.name = eventName
        self.date = datetime.date(int(eventDate[6:]), int(eventDate[0:2]), int(eventDate[3:5]))
        self.importance = eventImportant
        self.prepNeeded = eventNeedsPrep
    def getName(self):
        return self.name
    # def getDate(self):
    #     '''Returns the date the task occurs as an integer ranging from 1 (Jan 1) to 365 (Dec 31) + 1 for a leap year'''
    #     # Note for later: We need a way to standardize dates; Preferably into a MM-DD format (and maybe MM-DD-YYYY, but let's focus on MM-DD rn)
    #     # We need to add up all the days in previous months, then add the days passed in that month
    #     dateCounter : int = 0
    #     monthPortion : int = int(self.date[0:2])
    #     dayPortion : int = int(self.date[3:5])
    #     # Adding every single day that's passed previously
    #     if monthPortion > 1:
    #         dateCounter += 31
    #     if monthPortion > 2:
    #         # Leap year check
    #         if (int(self.date[6:8]) % 4 == 0):
    #             dateCounter += 29
    #         else:
    #             dateCounter += 28
    #     if monthPortion > 3:
    #         dateCounter += 31
    #     if monthPortion > 4:
    #         dateCounter += 30
    #     if monthPortion > 5:
    #         dateCounter += 31
    #     if monthPortion > 6:
    #         dateCounter += 30
    #     if monthPortion > 7:
    #         dateCounter += 31
    #     if monthPortion > 8:
    #         dateCounter += 31
    #     if monthPortion > 9:
    #         dateCounter += 30
    #     if monthPortion > 10:
    #         dateCounter += 31
    #     if monthPortion > 11:
    #         dateCounter += 30
    #     dateCounter += dayPortion
    #     return dateCounter
    
    def getImportance(self):
        return self.importance
    def getPrepNeeded(self):
        return self.prepNeeded
    
class Day:
    '''Kinda realized today that I sorta need a day class to hold information such as what tasks it contains and what day of the week it is...'''
    valid_days : dict[str] = {1 : "Mo", 2 : "Tu", 3 : "Wed", 4 : "Th",  5 : "F", 6 : "Sa", 7 :"Su"}
    def __init__(self, date):
        try:
            self.tasks : list[Task] = []
            self.dayEvents : list[Events]= []
            self.date = datetime.date(int(date[6:]), int(date[0:2]), int(date[3:5]))
            self.dow : str = Day.valid_days[self.date.isoweekday()]
        except:
            if type(date) != datetime.date:
                print("wah")
            else:
                self.tasks : list[Task] = []
                self.dayEvents : list[Events] = []
                self.date = date
                self.dow = Day.valid_days[self.date.isoweekday()]

    def addTask(self, task : Task):
        if task in self.tasks:
            return False
        else:
            self.tasks.append(task)
            return True
    def removeTask(self, taskl : Task):
        if taskl not in self.tasks:
            return False
        self.tasks.remove(taskl)
        return True
    def getTasks(self):
        return self.tasks
    
    # def getDate(self):
    #     dateCounter : int = 0
    #     monthPortion : int = int(self.date[0:2])
    #     dayPortion : int = int(self.date[3:5])
    #     # Adding every single day that's passed previously
    #     if monthPortion > 1:
    #         dateCounter += 31
    #     if monthPortion > 2:
    #         # Leap year check
    #         if (int(self.date[6:8]) % 4 == 0):
    #             dateCounter += 29
    #         else:
    #             dateCounter += 28
    #     if monthPortion > 3:
    #         dateCounter += 31
    #     if monthPortion > 4:
    #         dateCounter += 30
    #     if monthPortion > 5:
    #         dateCounter += 31
    #     if monthPortion > 6:
    #         dateCounter += 30
    #     if monthPortion > 7:
    #         dateCounter += 31
    #     if monthPortion > 8:
    #         dateCounter += 31
    #     if monthPortion > 9:
    #         dateCounter += 30
    #     if monthPortion > 10:
    #         dateCounter += 31
    #     if monthPortion > 11:
    #         dateCounter += 30
    #     dateCounter += dayPortion
    #     return dateCounter

    
class User:
     def __init__(self, uid : str):
        self.settings : dict[str] = {}
        self.settings["lazy"] = []
        self.uid = uid 
     


    