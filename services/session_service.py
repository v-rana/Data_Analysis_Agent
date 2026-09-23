import uuid

from fastapi import HTTPException

from config import settings

ROOT_USER_ID = "root"
GUEST_USER_ID = "guest"
SESSION_STORE: dict[str, dict[str, str]] = {}


def create_session(mode: str, secret_key: str | None = None) -> dict[str, str]:
    if mode == "admin":
        if secret_key != settings.UPLOAD_SECRET_KEY:
            raise HTTPException(status_code=403, detail="Invalid secret key")
        user_id = ROOT_USER_ID
    elif mode == "personal":
        user_id = GUEST_USER_ID
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    session_id = str(uuid.uuid4())
    SESSION_STORE[session_id] = {
        "user_id": user_id,
        "mode": mode,
    }
    return {
        "session_id": session_id,
        "user_id": user_id,
        "mode": mode,
    }


def list_sessions(secret_key: str | None = None) -> list[dict[str, str]]:
    if secret_key != settings.UPLOAD_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    return [
        {
            "session_id": session_id,
            "user_id": session["user_id"],
            "mode": session["mode"],
        }
        for session_id, session in SESSION_STORE.items()
    ]


def delete_session(session_id: str, secret_key: str | None = None) -> dict[str, str]:
    if secret_key != settings.UPLOAD_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    if session_id not in SESSION_STORE:
        raise HTTPException(status_code=404, detail="Session not found")

    del SESSION_STORE[session_id]
    return {
        "status": "deleted",
        "session_id": session_id,
    }


def get_session_context(session_id: str) -> dict[str, str]:
    session = SESSION_STORE.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return session
