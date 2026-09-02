import re
import socket
import logging
import ipaddress
from urllib.parse import urlparse
import httpx
import datetime as dTime
import pcStorage
import pcClasses
import timeutil

DEFAULT_TZ = timeutil.DEFAULT_TZ
logger = logging.getLogger(__name__)

def validateExternalUrl(url: str) -> bool:
    """Return True only if url is a public HTTP/HTTPS URL — rejects private/loopback IPs (SSRF guard)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        addr = ipaddress.ip_address(socket.gethostbyname(hostname))
    except Exception:
        return False
    if (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
            or addr.is_multicast or addr.is_unspecified):
        return False
    return True


MAX_REDIRECT_HOPS = 5
MAX_RESPONSE_BYTES = 1_048_576  # 1 MB

def _dropAuth(headers: dict) -> dict:
    """Remove the Authorization header regardless of the casing the caller used."""
    return {k: v for k, v in headers.items() if k.lower() != "authorization"}

def fetchExternal(url: str, timeout: int, headers: dict | None = None):
    """GET url, following redirects manually so every hop is re-checked by validateExternalUrl.

    httpx's own follow_redirects only validates the URL we hand it, so a public URL
    can 302 to an internal address. Credentials in `headers` are dropped the moment a
    redirect crosses to a different host, so a bearer token is never replayed to a
    server the caller did not address. The body is streamed and capped at
    MAX_RESPONSE_BYTES so a hostile endpoint cannot exhaust memory.

    Returns the final response, or None if any hop points somewhere non-public, the
    chain is too long, or the body exceeds the cap.

    Known limitation: validateExternalUrl resolves the hostname and httpx then
    resolves it again independently, so a DNS record that changes between the two
    lookups (DNS rebinding) can still reach a private address. Closing that requires
    pinning the validated IP for the connection itself.
    """
    outgoing = dict(headers or {})
    with httpx.Client(follow_redirects=False, timeout=timeout) as client:
        for _ in range(MAX_REDIRECT_HOPS):
            if not validateExternalUrl(url):
                return None
            current = urlparse(url)
            with client.stream("GET", url, headers=outgoing) as resp:
                if resp.is_redirect:
                    nextUrl = str(resp.next_request.url)
                    nextParsed = urlparse(nextUrl)
                    # Drop credentials when the host changes, and also when the hop
                    # downgrades https -> http, which would otherwise put the bearer
                    # token on the wire in cleartext.
                    if (nextParsed.hostname != current.hostname
                            or (current.scheme == "https" and nextParsed.scheme == "http")):
                        outgoing = _dropAuth(outgoing)
                    url = nextUrl
                    continue

                body = bytearray()
                for chunk in resp.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        return None

                # iter_bytes yields already-decoded bytes, so the transfer-encoding
                # headers no longer describe the payload we are handing back.
                finalHeaders = {
                    k: v for k, v in resp.headers.items()
                    if k.lower() not in ("content-encoding", "content-length")
                }
                return httpx.Response(
                    status_code=resp.status_code,
                    headers=finalHeaders,
                    content=bytes(body),
                    request=resp.request,
                )
    return None



_to_local_date = timeutil.toLocalDate

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

MAX_PENDING_TASKS = 300
MAX_PENDING_FIELD_CHARS = 150

def _pendingDueDate(entry: dict):
    """Parsed MM-DD-YYYY dueDate, or None when absent or unparseable."""
    raw = entry.get("dueDate")
    if not raw:
        return None
    try:
        return dTime.datetime.strptime(raw, "%m-%d-%Y").date()
    except (ValueError, TypeError):
        return None

def _prunePending(uid: str, pending: list, today: dTime.date) -> list:
    """Bound the pendingCanvasTasks array before it is written back.

    Both sync paths append to this list on every run and never remove anything,
    and Canvas-sourced entries bypass the Field(max_length=150) caps that bound
    user-submitted ones. Left alone the array grows until the user document hits
    MongoDB's 16 MB ceiling, after which every write to that document fails —
    settings, timezone, sync status — with no in-app way to recover.

    Entries with no dueDate are kept: they are undated, not overdue.
    """
    kept = []
    for entry in pending:
        due = _pendingDueDate(entry)
        if due is not None and due < today:
            continue
        entry = dict(entry)
        entry["name"] = str(entry.get("name", ""))[:MAX_PENDING_FIELD_CHARS]
        entry["courseName"] = str(entry.get("courseName", ""))[:MAX_PENDING_FIELD_CHARS]
        kept.append(entry)

    if len(kept) > MAX_PENDING_TASKS:
        logger.warning(
            "Pending Canvas tasks for %s reached %d, over the %d cap — keeping the soonest-due.",
            uid, len(kept), MAX_PENDING_TASKS
        )
        # Undated entries sort last: with no due date they are never "soonest-due".
        kept.sort(key=lambda e: (_pendingDueDate(e) is None, _pendingDueDate(e) or dTime.date.max))
        kept = kept[:MAX_PENDING_TASKS]
    return kept

def syncUser(uid: str):
    user = pcStorage.getUser(uid)
    if not user:
        return
    # Decryption lives in pcStorage; canvas.py never touches the stored value.
    token = pcStorage.getCanvasToken(uid)
    base_url = user.get("canvasUrl", "").rstrip("/")
    user_tz = user.get("timezone") or DEFAULT_TZ
    if not token or not base_url:
        return

    if not validateExternalUrl(base_url):
        return

    headers = {"Authorization": f"Bearer {token}"}
    today = timeutil.localToday(uid)
    pcStorage.setSyncStatus(uid, True)
    try:
        try:
            courses_resp = fetchExternal(
                f"{base_url}/api/v1/courses?enrollment_state=active&per_page=50",
                timeout=10, headers=headers
            )
            if courses_resp is None:
                logger.warning("Canvas course fetch for %s blocked or oversized", uid)
                return
            if courses_resp.status_code != 200:
                return
            courses = courses_resp.json()
        except Exception:
            logger.warning("Canvas course fetch for %s failed", uid, exc_info=True)
            return

        existing_names   = {t.getName().lower() for t in pcStorage.getTasks(uid)}
        existing_pending = {p["canvasId"] for p in pcStorage.getPendingCanvasTasks(uid)}
        handled_ids      = set(pcStorage.getHandledCanvasIds(uid))
        new_pending      = list(pcStorage.getPendingCanvasTasks(uid))

        for course in courses:
            course_id = course.get("id")
            if not course_id:
                continue
            try:
                assign_resp = fetchExternal(
                    f"{base_url}/api/v1/courses/{course_id}/assignments?bucket=upcoming&per_page=50",
                    timeout=10, headers=headers
                )
                if assign_resp is None:
                    logger.warning("Canvas assignment fetch for %s course %s blocked or oversized", uid, course_id)
                    continue
                if assign_resp.status_code != 200:
                    continue
                assignments = assign_resp.json()
            except Exception:
                logger.warning("Canvas assignment fetch for %s course %s failed", uid, course_id, exc_info=True)
                continue

            for a in assignments:
                canvas_id = str(a.get("id", ""))
                name      = a.get("name", "").strip()
                due_at    = a.get("due_at")

                if not name or not canvas_id:
                    continue
                if canvas_id in existing_pending:
                    continue
                if canvas_id in handled_ids:
                    continue
                if name.lower() in existing_names:
                    continue

                due_date_str = None
                if due_at:
                    try:
                        due_dt_utc = dTime.datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                        due_dt = _to_local_date(due_dt_utc, user_tz)
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

        pcStorage.storePendingCanvasTasks(uid, _prunePending(uid, new_pending, today))
        pcStorage.updateLastCanvasSync(uid, pcClasses.Task._formatDate(today))
    finally:
        pcStorage.setSyncStatus(uid, False)

def syncUserIcs(uid: str):
    from icalendar import Calendar as iCal
    user = pcStorage.getUser(uid)
    if not user:
        return
    ics_url = user.get("canvasIcsUrl")
    user_tz = user.get("timezone") or DEFAULT_TZ
    if not ics_url:
        return

    if not validateExternalUrl(ics_url):
        return

    today = timeutil.localToday(uid)
    pcStorage.setSyncStatus(uid, True)
    try:
        try:
            resp = fetchExternal(ics_url, timeout=15)
            if resp is None or resp.status_code != 200:
                return
            cal = iCal.from_ical(resp.content)
        except Exception:
            logger.warning("Canvas ICS fetch for %s failed", uid, exc_info=True)
            return

        existing_names   = {t.getName().lower() for t in pcStorage.getTasks(uid)}
        existing_pending = {p["canvasId"] for p in pcStorage.getPendingCanvasTasks(uid)}
        handled_ids      = set(pcStorage.getHandledCanvasIds(uid))
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
            if canvas_id in handled_ids:
                continue
            if name.lower() in existing_names:
                continue

            dtstart = component.get("DTSTART")
            due_date_str = None
            if dtstart:
                dt = dtstart.dt
                if isinstance(dt, dTime.datetime):
                    # Datetime with possible timezone — convert to local date respecting DST
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=dTime.timezone.utc)
                    due_dt = _to_local_date(dt, user_tz)
                else:
                    # Already a plain date — no timezone conversion needed
                    due_dt = dt
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

        pcStorage.storePendingCanvasTasks(uid, _prunePending(uid, new_pending, today))
        pcStorage.updateLastCanvasSync(uid, pcClasses.Task._formatDate(today))
    finally:
        pcStorage.setSyncStatus(uid, False)
