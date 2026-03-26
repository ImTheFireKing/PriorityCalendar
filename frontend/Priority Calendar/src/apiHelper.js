const API_BASE = "http://localhost:8000"; // adjust if needed
const UID = "test-user-1";                // temp hard‑coded

export async function fetchRecommendations() {
  const res = await fetch(`${API_BASE}/users/${UID}/recommendations`);
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return await res.json();
}

export async function createTask(task) {
  const res = await fetch(`${API_BASE}/users/${UID}/tasks`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(task),
  });
  if (!res.ok) throw new Error("Failed to create task");
  return await res.json();
}

export async function deleteTask(taskName) {
  const res = await fetch(`${API_BASE}/users/${UID}/tasks`, {
    method: "DELETE",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ taskName }),
  });
  if (!res.ok) throw new Error("Failed to delete task");
  return await res.json();
}