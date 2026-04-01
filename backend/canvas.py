import re
import socket
import ipaddress
from urllib.parse import urlparse
import httpx
import datetime as dTime
import pcStorage
import pcClasses

_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

def validateExternalUrl(url: str) -> bool:
    if not url.startswith("https://"):
        return False
    try:
        hostname = urlparse(url).hostname
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return not any(ip in net for net in _PRIVATE_RANGES)
    except Exception:
        return False

KEYWORD_MAP = {
    "exam":    ["exam", "midterm", "final"],
    "project": ["project"],
    "quiz":    ["quiz"],
}

def _inferType(name: str, submission_types: list) -> str:
    if "online_quiz" in submission_types:
        return "quiz"
    lower = name.lower()
    for taskType, keywords in KEYWORD_MAP.items():
        if any(k in lower for k in keywords):
            return taskType
    return "homework"

def _stripHtml(raw: str) -> str:
    return re.sub(r"<[^>]+>", " ", raw).strip()

def _formatDueDate(due_dt: dTime.date) -> str:
    return (
        f"{str(due_dt.month).zfill(2)}-"
        f"{str(due_dt.day).zfill(2)}-"
        f"{due_dt.year}"
    )

def syncUser(uid: str):
    user = pcStorage.getUser(uid)
    if not user:
        return
    token = user.get("canvasToken")
    base_url = user.get("canvasUrl", "").rstrip("/")
    if not token or not base_url:
        return

    headers = {"Authorization": f"Bearer {token}"}
    today = dTime.date.today()
    pcStorage.setSyncStatus(uid, True)
    try:
        courses_resp = httpx.get(
            f"{base_url}/api/v1/courses?enrollment_state=active&per_page=50",
            headers=headers, timeout=10
        )
        if courses_resp.status_code != 200:
            return
        courses = courses_resp.json()
    except Exception:
        return
    finally:
        pcStorage.setSyncStatus(uid, False)

    existing_names   = {t.getName().lower() for t in pcStorage.getTasks(uid)}
    existing_pending = {p["canvasId"] for p in pcStorage.getPendingCanvasTasks(uid)}
    new_pending      = list(pcStorage.getPendingCanvasTasks(uid))

    for course in courses:
        course_id = course.get("id")
        if not course_id:
            continue
        try:
            assign_resp = httpx.get(
                f"{base_url}/api/v1/courses/{course_id}/assignments?bucket=upcoming&per_page=50",
                headers=headers, timeout=10
            )
            if assign_resp.status_code != 200:
                continue
            assignments = assign_resp.json()
        except Exception:
            continue

        for a in assignments:
            canvas_id = str(a.get("id", ""))
            name      = a.get("name", "").strip()
            due_at    = a.get("due_at")

            if not name or not canvas_id:
                continue
            if canvas_id in existing_pending:
                continue
            if name.lower() in existing_names:
                continue

            due_date_str = None
            if due_at:
                try:
                    due_dt = dTime.datetime.fromisoformat(due_at.replace("Z", "+00:00")).date()
                    if due_dt <= today:
                        continue
                    due_date_str = _formatDueDate(due_dt)
                except ValueError:
                    pass

            task_type   = _inferType(name, a.get("submission_types", []))
            description = _stripHtml(a.get("description") or "")
            if len(description) > 400:
                description = description[:400] + " (See More on Canvas)"

            new_pending.append({
                "canvasId":    canvas_id,
                "name":        name,
                "dueDate":     due_date_str,
                "taskType":    task_type,
                "description": description,
                "courseName":  course.get("name", ""),
            })
            existing_pending.add(canvas_id)

    pcStorage.storePendingCanvasTasks(uid, new_pending)
    pcStorage.updateLastCanvasSync(uid, pcClasses.Task._formatDate(today))

def syncUserIcs(uid: str):
    from icalendar import Calendar as iCal
    user = pcStorage.getUser(uid)
    if not user:
        return
    ics_url = user.get("canvasIcsUrl")
    if not ics_url:
        return

    if not validateExternalUrl(ics_url):
        return

    today = dTime.date.today()
    pcStorage.setSyncStatus(uid, True)
    try:
        resp = httpx.get(ics_url, timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return
        cal = iCal.from_ical(resp.content)
    except Exception:
        return
    finally:
        pcStorage.setSyncStatus(uid, False)

    existing_names   = {t.getName().lower() for t in pcStorage.getTasks(uid)}
    existing_pending = {p["canvasId"] for p in pcStorage.getPendingCanvasTasks(uid)}
    new_pending      = list(pcStorage.getPendingCanvasTasks(uid))

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        canvas_id = str(component.get("UID", "")).strip()
        raw_name  = str(component.get("SUMMARY", "")).strip()

        # ICS SUMMARY format: "Assignment Name [Course Name]"
        course_name = ""
        name = raw_name
        bracket = raw_name.rfind("[")
        if bracket != -1 and raw_name.endswith("]"):
            course_name = raw_name[bracket + 1:-1].strip()
            name = raw_name[:bracket].strip()

        if not name or not canvas_id:
            continue
        if canvas_id in existing_pending:
            continue
        if name.lower() in existing_names:
            continue

        dtstart = component.get("DTSTART")
        due_date_str = None
        if dtstart:
            dt = dtstart.dt
            due_dt = dt.date() if hasattr(dt, "date") else dt
            if due_dt <= today:
                continue
            due_date_str = _formatDueDate(due_dt)

        description = _stripHtml(str(component.get("DESCRIPTION") or ""))
        if len(description) > 400:
            description = description[:400] + " (See More on Canvas)"
        task_type   = _inferType(name, [])

        new_pending.append({
            "canvasId":    canvas_id,
            "name":        name,
            "dueDate":     due_date_str,
            "taskType":    task_type,
            "description": description,
            "courseName":  course_name,
        })
        existing_pending.add(canvas_id)

    pcStorage.storePendingCanvasTasks(uid, new_pending)
    pcStorage.updateLastCanvasSync(uid, pcClasses.Task._formatDate(today))
