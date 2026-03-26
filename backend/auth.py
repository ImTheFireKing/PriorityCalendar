from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from jose import jwt, JWTError
from datetime import datetime, timedelta
import datetime as dTime
import os
import pcStorage
import httpx

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
SESSION_HOURS = 5

class GoogleTokenBody(BaseModel):
    token : str

def createSessionToken(uid : str) -> str:
    expire = datetime.utcnow() + timedelta(hours=SESSION_HOURS) 
    return jwt.encode({"sub": uid, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verifySessionToken(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Session Expired/Invalid, Log In")

@router.post("/auth/google")
def googleAuth(body : GoogleTokenBody, response : Response):
    userInfo = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {body.token}"}
    )
    if userInfo.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    info       = userInfo.json()
    googleUID = str(info["sub"])
    email      = info["email"]
    name       = info.get("name", "")
    # Creates uses in Mongo if not there, grabs from Mongo otherwise
    existing = pcStorage.getUser(googleUID)
    if not existing:
        pcStorage.addUser(googleUID, [], [], {"lazy" : [], "Tlimit" : 15, "Elimit" : 3, "expired" : 2})

    sessionToken = createSessionToken(googleUID)
    response.set_cookie(
        key="session",
        value=sessionToken,
        httponly=True,
        secure=False, # Note: Change this to true once we push to AWS
        samesite="lax",
        max_age = SESSION_HOURS * 3600,
        path="/"
    )

    return {"uid" : googleUID, "name" : name, "email" : email}

@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"status": "logged out"}

# Dependency — use this to protect any endpoint
def get_current_uid(request: Request) -> str:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verifySessionToken(token)

@router.get("/auth/session")
def check_session(current_uid: str = Depends(get_current_uid)):
    return {"uid": current_uid}