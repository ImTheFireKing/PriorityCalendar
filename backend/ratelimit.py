"""Shared rate-limiter instance.

This lives in its own module rather than in api.py because auth.py also needs the
limiter (to decorate /auth/google) and api.py already imports auth.py. Defining
the limiter in api.py makes that pair circular, which works only when api.py
happens to be imported first and breaks outright otherwise.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rateLimitKey(request: Request) -> str:
    """Bucket by authenticated user when we have one, else by IP.

    Keying purely on IP would put an entire campus behind one NAT into a single
    bucket, so one student syncing would rate-limit everyone else on the network.
    """
    token = request.cookies.get("session")
    if token:
        try:
            # Imported lazily: auth.py imports this module, so a top-level import
            # here would be circular. verifySessionToken returns a dict and raises
            # HTTPException on a bad token, so an invalid cookie falls through to IP.
            from auth import verifySessionToken
            return f"user:{verifySessionToken(token)['uid']}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_rateLimitKey, default_limits=["100/minute"])
