from recommender import *
from pcClasses import *

calendar = []

start_dates = [
    ["01-01-2025", "01-02-2025", "01-03-2025", "01-04-2025", "01-05-2025", "01-06-2025", "01-07-2025"],
    ["01-08-2025", "01-09-2025", "01-10-2025", "01-11-2025", "01-12-2025", "01-13-2025", "01-14-2025"],
    ["01-15-2025", "01-16-2025", "01-17-2025", "01-18-2025", "01-19-2025", "01-20-2025", "01-21-2025"],
    ["01-22-2025", "01-23-2025", "01-24-2025", "01-25-2025", "01-26-2025", "01-27-2025", "01-28-2025"],
]

for week in start_dates:
    week_row = []
    for date in week:
        d = Day(date)
        week_row.append(d)
    calendar.append(week_row)


tasks = [
    Homework("01-03-2025", "Math HW 1", "Easy"),
    Homework("01-10-2025", "Physics HW 1", "Ehhh"),
    Quiz("01-05-2025", "Calc Quiz"),
    Major("01-15-2025", "Calculus Exam"),
    Major("01-22-2025", "CS Project", projectOrExam=False),
    Prep("01-14-2025", "Study for Calc Exam"),
]


def assign_tasks(calendar, tasks):
    date_to_day = {}

    # Build lookup table
    for week in calendar:
        for day in week:
            date_to_day[day.date] = day

    # Assign tasks
    for task in tasks:
        task_date = task.date
        if task_date in date_to_day:
            date_to_day[task_date].addTask(task)

assign_tasks(calendar, tasks)
today : Day = Day("01-01-2025")

toDo : list[(int, Task)] = task_recommender(calendar, today, 3)
percentages : list[float] = []
testUser = User()
User.settings["lazy"] = ["Mo", "Tu", "Wed"]
for i in range(len(toDo)):
    percentages.append(percentCalculate(toDo[i][1], today, calendar))
print("These are the tasks to complete today: ")
for i, entry in enumerate(toDo):
    print(f"{entry[1].name}, {percentages[i]}")


