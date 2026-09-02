from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import pcStorage
import pcClasses
import timeutil
from ratelimit import limiter

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    # verify_oauth2_token skips the audience check entirely when the audience is
    # None, which would silently reopen the token-substitution hole. Refuse to start.
    # RuntimeError, not HTTPException: this runs at import, outside any request,
    # so nothing would turn an HTTPException into a response anyway.
    raise RuntimeError("GOOGLE_CLIENT_ID is not configured")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
SESSION_HOURS = 5

class GoogleTokenBody(BaseModel):
    token : str
    # IANA zone from the browser (Intl.DateTimeFormat). Optional so older
    # clients keep working — they just fall back to timeutil.DEFAULT_TZ.
    timezone : str | None = None

def createSessionToken(uid : str, onboarded : bool) -> str:
    expire = datetime.utcnow() + timedelta(hours=SESSION_HOURS) 
    return jwt.encode({"sub": uid, "exp": expire, "onboarded" : onboarded}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verifySessionToken(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"uid" : payload["sub"], "onboarded" : payload.get("onboarded", False)}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session Expired/Invalid, Log In")

@router.post("/auth/google")
@limiter.limit("20/minute")
def googleAuth(request : Request, body : GoogleTokenBody, response : Response):
    # An ID token is bound to our OAuth client via its `aud` claim, so a token
    # minted for some other Google app can no longer be replayed here. The old
    # userinfo probe accepted any valid Google access token whatsoever.
    try:
        info = id_token.verify_oauth2_token(body.token, grequests.Request(), GOOGLE_CLIENT_ID)
    except ValueError:
        # Bad signature, wrong audience, or expired. The exception text can echo
        # token internals, so it is deliberately kept out of the response.
        raise HTTPException(status_code=401, detail="Invalid Google token")

    googleUID = str(info["sub"])
    email      = info.get("email", "")
    name       = info.get("name", "")
    # Creates user in Mongo if not there, grabs from Mongo otherwise
    existing = pcStorage.getUser(googleUID)
    if not existing:
        pcStorage.addUser(googleUID, {"lazy": [], "Tlimit": 15, "Elimit": 3, "expired": 2, "hidePct": 0})
    onboardedStatus = existing.get("onboarded", False) if existing else False
    # Refresh the stored zone every sign-in: people travel, and a stale zone
    # silently shifts when their percentages recalculate.
    if body.timezone and timeutil.isValidTz(body.timezone):
        if body.timezone != (existing.get("timezone") if existing else None):
            pcStorage.setUserTimezone(googleUID, body.timezone)
    today = pcClasses.Task._formatDate(timeutil.localToday(googleUID))
    if existing and existing.get("lastCanvasSync") != today:
        import threading, canvas
        if existing.get("canvasToken"):
            threading.Thread(target=canvas.syncUser, args=(googleUID,), daemon=True).start()
        elif existing.get("canvasIcsUrl"):
            threading.Thread(target=canvas.syncUserIcs, args=(googleUID,), daemon=True).start()
    sessionToken = createSessionToken(googleUID, onboardedStatus)
    response.set_cookie(
        key="session",
        value=sessionToken,
        httponly=True,
        secure=True, # Note: Change this to true once we push to AWS
        samesite="none",
        max_age = SESSION_HOURS * 3600,
        path="/"
    )

    return {"uid" : googleUID, "name" : name, "email" : email, "onboarded" : onboardedStatus}

@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"status": "logged out"}

# Dependency — use this to protect any endpoint
def get_current_uid(request: Request) -> str:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verifySessionToken(token)["uid"]

@router.get("/auth/session")
def check_session(request : Request):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Session Expired")
    return verifySessionToken(token)