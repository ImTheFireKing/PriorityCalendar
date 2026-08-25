"""Single source of truth for "what day is it for this user?".

Realized way too late that the backend server's deployed location became what was considered time for 
all, so a bare date.today() rolls over at 19:00 for a Chicago user — which is what the 
recommender's percentages used to recalculate on. Everything day-boundary-sensitive 
resolves the user's own zone through here instead, so DST is handled by the zone 
database rather than a fixed offset.
"""
import datetime as dTime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import pcStorage

DEFAULT_TZ = "America/New_York"

# Percentages recalculate at this hour of the user's local day rather than at
# midnight: work done just after midnight should still count toward the day it
# felt like, so the new day's split doesn't land mid-study-session.
RECALC_HOUR = 1


def isValidTz(tzName) -> bool:
    """True if tzName names a zone in the tz database."""
    if not isinstance(tzName, str) or not tzName:
        return False
    try:
        ZoneInfo(tzName)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def resolveTz(tzName):
    """Turn a stored zone name into a tzinfo, falling back to DEFAULT_TZ.

    Last resort is UTC: on a host with no tz database (Windows without the
    tzdata package) even DEFAULT_TZ fails to load, and a day-boundary lookup
    must not take a request down with it.
    """
    if isValidTz(tzName):
        return ZoneInfo(tzName)
    if isValidTz(DEFAULT_TZ):
        return ZoneInfo(DEFAULT_TZ)
    return dTime.timezone.utc


def getUserTz(uid: str) -> ZoneInfo:
    """The user's own zone, or DEFAULT_TZ if they have never reported one."""
    return resolveTz(pcStorage.getUserTimezone(uid))


def toLocalDate(dtAware: dTime.datetime, tz) -> dTime.date:
    """Convert a timezone-aware datetime to a calendar date in tz, respecting DST."""
    if dtAware.tzinfo is None:
        dtAware = dtAware.replace(tzinfo=dTime.timezone.utc)
    if isinstance(tz, str) or tz is None:
        tz = resolveTz(tz)
    return dtAware.astimezone(tz).date()


def localNow(uid: str) -> dTime.datetime:
    """Current time where the user is."""
    return dTime.datetime.now(getUserTz(uid))


def localToday(uid: str) -> dTime.date:
    """The calendar date where the user is — what a date picker would show them."""
    return localNow(uid).date()


def logicalToday(uid: str) -> dTime.date:
    """The day the recommender treats as today: local date, rolling at RECALC_HOUR.

    Between midnight and RECALC_HOUR this is still yesterday's date, which is
    what keeps percentages from re-splitting on someone at 12:01am.
    """
    return (localNow(uid) - dTime.timedelta(hours=RECALC_HOUR)).date()
