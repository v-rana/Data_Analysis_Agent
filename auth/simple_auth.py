import hmac
from typing import Iterable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SimpleAuthService:
    def __init__(self, expected_token: str):
        self.expected_token = expected_token

    def is_valid(self, token: str | None) -> bool:
        if not token:
            return False
        return hmac.compare_digest(token, self.expected_token)


def bearer_token_from_request(headers) -> str | None:
    auth_header = headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token or None


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service: SimpleAuthService, public_paths: Iterable[str] | None = None):
        super().__init__(app)
        self.auth_service = auth_service
        self.public_paths = set(public_paths or [])

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.public_paths or any(
            path.startswith(f"{public_path}/")
            for public_path in self.public_paths
            if public_path != "/"
        ):
            return await call_next(request)

        token = bearer_token_from_request(request.headers)
        if not self.auth_service.is_valid(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
            )

        return await call_next(request)
