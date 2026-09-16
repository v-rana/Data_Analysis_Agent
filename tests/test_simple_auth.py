from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.simple_auth import SimpleAuthService, bearer_token_from_request, AuthMiddleware


def test_bearer_token_extraction():
    headers = {"Authorization": "Bearer my-secret-token"}
    assert bearer_token_from_request(headers) == "my-secret-token"


def test_auth_service_validates_secret():
    service = SimpleAuthService("my-secret-token")
    assert service.is_valid("my-secret-token") is True
    assert service.is_valid("wrong-token") is False


def test_auth_middleware_rejects_missing_token():
    app = FastAPI()

    @app.get("/protected")
    async def protected():
        return {"ok": True}

    app.add_middleware(AuthMiddleware, auth_service=SimpleAuthService("my-secret-token"), public_paths=["/health"])

    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code == 401

    response = client.get("/protected", headers={"Authorization": "Bearer my-secret-token"})
    assert response.status_code == 200
