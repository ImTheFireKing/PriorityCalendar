import TaskCard from './components/TaskCard'

function App() {
  return (
    <div>
      <h1>Priority Calendar</h1>
      <TaskCard name="Getting Work Done" taskType="Homework" dueDate="11-15-2026" howMuch={30} />
    </div>
  );
}

export default App;