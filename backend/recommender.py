from pcClasses import Task, Homework, Major, Quiz, Events, Prep, Day, User
from datetime import datetime, timedelta
import datetime as dTime
import pcStorage

def compute_task_score(task : Task, today : Day):
    ''' Thought line: Exams and projects should have the greatest weight out of any kind of task; they also need more time to work on compared to other assignments; Most HWs can be completed in 2 weeks or less, 
    most (good) projects need more time than that. Additionally, sometimes it's worth prepping for a class even if there's no exam or quiz coming up. We'll calculate the time differential into days, then move forward.'''
    # Intensity: Should scale from 1-5, with 5 being used for projects and exams, 4 being used for quizzes, 3 being used for hw assignments, 2 being used for events, and 1 being used for prepwork
    # Urgency: Scale from 1 - 10, with a different score used where necessary; 10 is basically GET IT DONE NOW OR WE'RE COOKED, while 1 is you can forget this exists, lmao
    if task.getType() == "exam" or task.getType() == "project":
        if (task.date - today.date >= timedelta(days=28)):
            return 5 * 2
        elif (task.date - today.date >= timedelta(days=21)):
            return 5 * 3
        elif (task.date - today.date >= timedelta(days=14)):
            return 5 * 4
        elif (task.date - today.date >= timedelta(days=7)):
            return 5 * 6
        else:
            return 5 * 9
    elif task.getType() == "quiz":
        if (task.date - today.date >= timedelta(days=14)):
            return 4 * 2
        elif (task.date - today.date >= timedelta(days=7)):
            return 4 * 3
        elif (task.date - today.date >= timedelta(days=2)):
            return 4 * 6
        elif (task.date - today.date <= timedelta(days=1)):
            return 4 * 9
    elif task.getType() == "homework":
        if task.getDifficulty() == "Easy":
            difMultiplier : int = 1
        elif task.getDifficulty() == "Ehhh":
            difMultiplier : int = 2
        elif task.getDifficulty() == "Dead":
            difMultiplier : int = 3
        else:
            difMultiplier : int = 1
        if (task.date - today.date >= timedelta(days=21)):
            return 2 * 2 * difMultiplier
        elif (task.date - today.date >= timedelta(days=14)):
            return 2 * 3 * difMultiplier
        elif (task.date - today.date >= timedelta(days=7)):
            return 2 * 5 * difMultiplier
        elif (task.date - today.date >= timedelta(days=3)):
            return 2 * 6 * difMultiplier
        else:
            return 2 * 8 * difMultiplier
    elif task.getType() == "prep":
        if (task.date - today.date <= timedelta(days=1)):
            return 4
        else:
            return 1

def compute_event_score(event : Events, today : Day):
    if event.getImportance():
        importanceMult = 9
    else:
        importanceMult = 5
    
    if event.getPrepNeeded():
        prepMult = 2
    else:
        prepMult = 1
    
    if (event.date - today.date >= timedelta(days=28)):
        return importanceMult * prepMult 
    elif (event.date - today.date >= timedelta(days=14)):
        return importanceMult * prepMult * 2
    elif (event.date - today.date >= timedelta(days=7)):
        return importanceMult * prepMult * 3
    else:
        return importanceMult * prepMult * 4

def task_recommender(existence : list[Day], today : Day, settings = {"lazy" : []}, taskLimit : int = 15):
    """Returns a list of (score, task, forced) tuples sorted descending by score.
    """
    today_date = today.date

    dumList : list[tuple[int, Task, bool]] = []

    if taskLimit == 0:
        for day in existence:
            for task in day.tasks:
                if task.getLastWorked() == today_date:
                    continue
                dumList.append((compute_task_score(task, today), task, False))
    else:
        addedTasks : int = 0
        for day in existence:
            if addedTasks >= taskLimit:
                break
            for task in day.tasks:
                if task.getLastWorked() == today_date:
                    continue
                pct = percentCalculate(task, today, existence, settings)
                # Tasks requiring >=70% completion today are added unconditionally and
                # flagged so the UI can surface them distinctly. They do not consume a
                # slot in the limit — this is intentional product behaviour, not a bug.
                needs_heavy_work = isinstance(pct, (int, float)) and pct >= 50
                if needs_heavy_work:
                    dumList.append((compute_task_score(task, today), task, True))
                else:
                    if addedTasks < taskLimit:
                        dumList.append((compute_task_score(task, today), task, False))
                        addedTasks += 1
                    else:
                        break

    dumList.sort(reverse=True, key=lambda entry: entry[0])
    return dumList

def event_recommender(altExistence : list[Day], today : Day, eventLimit : int = 3):
    if eventLimit == 0:
        dumList = [] 
        for day in altExistence:
            for event in day.dayEvents:
                dumList.append((compute_event_score(event, today), event))
    else: 
        dumList = []
        addedEvents = 0
        for day in altExistence:
            if addedEvents >= eventLimit:
                break
            for event in day.dayEvents:
                if addedEvents < eventLimit:
                    dumList.append((compute_event_score(event, today), event))
                    addedEvents += 1
                else:
                    break

    # Sort by score descending; break ties by date ascending (soonest event first)
    dumList.sort(key=lambda entry: (-entry[0], entry[1].getDate()))
    return dumList

def percentCalculate(thatTask : Task, today : Day, existence : list[Day], settings):
    '''Calculates the percentage of a task that should be done that day based on the amount of days that are able to be worked on'''
    lazyDays = settings["lazy"]
    startOfYear = dTime.date(today.date.year, 1, 1)
    startingDay = int((today.date - startOfYear).days)
    daysAvailable : int = 0
    for i, day in enumerate(existence):
        if startingDay > i:
            continue
        if day.dow in lazyDays:
            continue
        if thatTask.date < day.date:
            break
        else:
            daysAvailable += 1
    if daysAvailable == 0:
        return 100
    return max(round((100 - thatTask.getPercent()) / daysAvailable, 2), 1)