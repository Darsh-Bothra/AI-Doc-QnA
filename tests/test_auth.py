import pytest
from httpx import AsyncClient

from tests.helpers import assert_status, register_and_login

pytestmark = pytest.mark.integration


async def test_register_login_then_authenticated_request(client: AsyncClient):
    user = await register_and_login(client, "alice@example.com")

    response = await client.get("/documents/", headers=user["headers"])
    assert_status(response, 200)
    body = response.json()
    assert body["total_count"] == 0
    assert body["documents"] == []


async def test_unauthenticated_request_is_rejected(client: AsyncClient):
    response = await client.get("/documents/")
    assert_status(response, 401)


async def test_invalid_token_is_rejected(client: AsyncClient):
    response = await client.get(
        "/documents/",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert_status(response, 401)


async def test_duplicate_register_returns_conflict(client: AsyncClient):
    payload = {"email": "bob@example.com", "password": "password123"}
    first = await client.post("/auth/register", json=payload)
    assert_status(first, 200)

    second = await client.post("/auth/register", json=payload)
    assert_status(second, 409)


async def test_login_rejects_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert_status(response, 401)


async def test_login_rejects_unknown_email(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert_status(response, 401)
