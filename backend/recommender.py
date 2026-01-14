from pcClasses import Task, Homework, Major, Quiz, Events, Prep, Day, User
import datetime
import pcStorage

def compute_task_score(task : Task, today : Day):
    ''' Thought line: Exams and projects should have the greatest weight out of any kind of task; they also need more time to work on compared to other assignments; Most HWs can be completed in 2 weeks or less, 
    most (good) projects need more time than that. Additionally, sometimes it's worth prepping for a class even if there's no exam or quiz coming up. We'll calculate the time differential into days, then move forward.'''
    # Intensity: Should scale from 1-5, with 5 being used for projects and exams, 4 being used for quizzes, 3 being used for hw assignments, 2 being used for events, and 1 being used for prepwork
    # Urgency: Scale from 1 - 10, with a different score used where necessary; 10 is basically GET IT DONE NOW OR WE'RE COOKED, while 1 is you can forget this exists, lmao
    if task.getType() == "exam" or task.getType() == "project":
        if (task.date - today.date >= datetime.timedelta(days=28)):
            return 5 * 2
            # For the mathematicians raging internally about why I'm not multiplying them together, it's to make the combo make sense; Intensity of Task * Urgency of It = Priority Score
        elif (task.date - today.date >= datetime.timedelta(days=21)):
            return 5 * 3
        elif (task.date - today.date >= datetime.timedelta(days=14)):
            return 5 * 4
        elif (task.date - today.date >= datetime.timedelta(days=7)):
            return 5 * 6
        else:
            return 5 * 9
    elif task.getType() == "quiz":
        if (task.date - today.date >= datetime.timedelta(days=14)):
            return 4 * 2
        elif (task.date - today.date >= datetime.timedelta(days=7)):
            return 4 * 3
        elif (task.date - today.date >= datetime.timedelta(days=2)):
            return 4 * 6
        elif (task.date - today.date <= datetime.timedelta(days=1)):
            return 4 * 9
    elif task.getType() == "homework":
        if task.getDifficulty() == "Easy":
            difMultiplier : int = 1
        elif task.getDifficulty() == "Ehhh":
            difMultiplier : int = 2
        elif task.getDifficulty() == "Dead":
            difMultiplier : int = 3
        if (task.date - today.date >= datetime.timedelta(days=21)):
            return 2 * 2 * difMultiplier
        elif (task.date - today.date >= datetime.timedelta(days=14)):
            return 2 * 3 * difMultiplier
        elif (task.date - today.date >= datetime.timedelta(days=7)):
            return 2 * 5 * difMultiplier
        elif (task.date - today.date >= datetime.timedelta(days=3)):
            return 2 * 6 * difMultiplier
        else:
            return 2 * 8 * difMultiplier
    elif task.getType() == "prep":
        # Prep is a weird case tbh....
        # Either people actively like preparing for their classes the next day and will genuinely do that, or people don't
        # Best pratice: Allow users to set the importance of preparing for classes and then force preparations to be added (probably shouldn't make it count toward limit though if they care about prep, just force add any prep to the list)
        if (task.date - today.date <= datetime.timedelta(days=1)):
            return 4
        else:
            return 1

def compute_event_score(event : Events, today : Day):
    # Maybe I'm thinking about this wrong...
    # If an event is important, then we should want to do things to free up our calendar for the event; Else, we'll attend if we have time
    # By that logic, an event being important should scale high....
    # Thought: Separate the recommender logic for events and tasks; keep the highest x events shown but don't factor events into the tasks themselves
    if event.getImportance():
        importanceMult = 9
    else:
        importanceMult = 5
    
    if event.prepNeeded():
        prepMult = 2
    else:
        prepMult = 1
    
    if (event.date - today.date >= datetime.timedelta(days=28)):
        return importanceMult * prepMult 
    elif (event.date - today.date >= datetime.timedelta(days=14)):
        return importanceMult * prepMult * 2
    elif (event.date - today.date >= datetime.timedelta(days=7)):
        return importanceMult * prepMult * 3
    else:
        return importanceMult * prepMult * 4

def task_recommender(existence : list[list[Day]], today : Day, taskLimit : int = 15):
    # Assume that there's a normal person limit of 15 tasks per day
    if taskLimit == 0:
    # If the user asks for infinite tasks, calculate task score for all tasks
        dumList = []
        for month in existence:
            for day in month:
                for task in day.tasks:
                    dumList.append((compute_task_score(task, today), task))
    else:
    # Otherwise, calculate all tasks the user asks for
        dumList = []
        addedTasks : int = 0
        for month in existence:
            if (addedTasks < taskLimit):
                for day in month:
                    if (addedTasks < taskLimit):
                        for task in day.tasks:  
                            if (addedTasks < taskLimit):
                                dumList.append((compute_task_score(task, today), task))
                                addedTasks+= 1
                            else:
                                break
                    else:
                        break
            else:
                    break
            
    # Sort in descending order, then return the list
    dumList.sort(reverse=True, key=lambda entry: entry[0])
    print(dumList)
    return dumList

def event_recommender(altExistence : list[list[Day]], today : Day, eventLimit : int = 3):
    if eventLimit == 0:
        dumList = [] 
        for month in altExistence:
            for day in month:
                for event in day:
                    dumList.append((compute_event_score(event, today), event))
    else:
        dumList = []
        addedEvents = 0
        for month in altExistence:
            if (addedEvents < eventLimit):
                for day in month:
                    if (addedEvents < eventLimit):
                        for event in day:
                            if (addedEvents < eventLimit):
                                dumList.append((compute_event_score(event, today), event))
                            else:
                                break
                    else:
                        break
            else:
                break

    dumList.sort(reverse=True, key=lambda entry: entry[0])
    return dumList

def percentCalculate(thatTask : Task, today : Day, existence : list[list[Day]], settings = User.settings):
    '''Calculates the percentage of a task that should be done that day based on the amount of days that are able to be worked on'''
    lazyDays = settings["lazy"]
    startingMonth : int
    startingDay : int
    for i, month in enumerate(existence):
        for j, day in enumerate(month):
            if today.date == day.date:
                startingMonth = i
                startingDay = j
    daysAvailable : int = 0
    for i, month in enumerate(existence):
        if startingMonth > i:
            continue
        else:
            correctMonth = True
        for j, day in enumerate(month):
            if startingDay > j and i == startingMonth:
                continue
            if day.dow in lazyDays:
                continue
            if thatTask.date < day.date:
                break
            else:
                daysAvailable += 1
    if (daysAvailable == 0):
        return "You're cooked"
    # Note to self: Fix this later
    return max(round(100-thatTask.getPercent()/daysAvailable, 2), 1)


