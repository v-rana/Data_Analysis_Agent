import json
import uuid

from fastapi import HTTPException
from redis.asyncio import Redis

from config import settings

ROOT_USER_ID = "root"
GUEST_USER_ID = "guest"

SESSION_KEY_PREFIX = "sql_agent:session:"


def _session_key(session_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{session_id}"


async def create_session(
    redis_client: Redis,
    mode: str,
    secret_key: str | None = None,
) -> dict[str, str]:
    if mode == "admin":
        if secret_key != settings.UPLOAD_SECRET_KEY:
            raise HTTPException(
                status_code=403,
                detail="Invalid secret key",
            )
        user_id = ROOT_USER_ID

    elif mode == "personal":
        user_id = GUEST_USER_ID

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode",
        )

    session_id = str(uuid.uuid4())

    session = {
        "user_id": user_id,
        "mode": mode,
    }

    await redis_client.set(
        _session_key(session_id),
        json.dumps(session),
        ex=settings.REDIS_SESSION_TTL_SECONDS,
    )

    return {
        "session_id": session_id,
        "user_id": user_id,
        "mode": mode,
    }


async def list_sessions(
    redis_client: Redis,
    secret_key: str | None = None,
) -> list[dict[str, str]]:
    if secret_key != settings.UPLOAD_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid secret key",
        )

    sessions: list[dict[str, str]] = []

    async for key in redis_client.scan_iter(
        match=f"{SESSION_KEY_PREFIX}*"
    ):
        session_data = await redis_client.get(key)

        # The session may expire between SCAN and GET.
        if session_data is None:
            continue

        session = json.loads(session_data)
        session_id = key.removeprefix(SESSION_KEY_PREFIX)

        sessions.append(
            {
                "session_id": session_id,
                "user_id": session["user_id"],
                "mode": session["mode"],
            }
        )

    return sessions


async def delete_session(
    redis_client: Redis,
    session_id: str,
    secret_key: str | None = None,
) -> dict[str, str]:
    if secret_key != settings.UPLOAD_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid secret key",
        )

    deleted = await redis_client.delete(_session_key(session_id))

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    return {
        "status": "deleted",
        "session_id": session_id,
    }


async def get_session_context(
    redis_client: Redis,
    session_id: str,
) -> dict[str, str]:
    session_data = await redis_client.get(_session_key(session_id))

    if session_data is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
        )

    return json.loads(session_data)
