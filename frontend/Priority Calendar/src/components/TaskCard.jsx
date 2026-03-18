function TaskCard({name, taskType, dueDate, howMuch}) {
    return (
        <div>
            <h3>{name}</h3>
            <p>{taskType}</p>
            <p>{dueDate}</p>
            <p>{howMuch}% today</p>
        </div>
    );
}

export default TaskCard