from __future__ import annotations

import io

import pymupdf
from httpx import AsyncClient, Response


def build_pdf_bytes(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    buffer = io.BytesIO()
    document.save(buffer)
    document.close()
    return buffer.getvalue()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> dict:
    register = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert register.status_code == 200, register.text

    login = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text

    token = login.json()["access_token"]
    return {
        "id": register.json()["id"],
        "email": email,
        "token": token,
        "headers": auth_header(token),
    }


def assert_status(response: Response, expected: int) -> None:
    assert response.status_code == expected, (
        f"expected {expected}, got {response.status_code}: {response.text}"
    )
