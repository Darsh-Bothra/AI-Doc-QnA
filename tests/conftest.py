"""Shared fixtures for Phase 0 API tests.

Postgres and Qdrant are started once per session with testcontainers.
The OpenAI client is replaced with an in-process fake so tests never
hit the network. Import of `ai_doc_qa.main` is deferred until env vars
point at those containers.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]


def _apply_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def postgres_container() -> Iterator:
    from testcontainers.community.postgres import PostgresContainer

    with PostgresContainer("postgres:17-alpine", driver="psycopg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def qdrant_container() -> Iterator:
    from testcontainers.community.qdrant import QdrantContainer

    with QdrantContainer() as qdrant:
        yield qdrant


@pytest.fixture(scope="session")
def app(postgres_container, qdrant_container, tmp_path_factory) -> Iterator:
    upload_dir = tmp_path_factory.mktemp("uploads")

    os.environ.update(
        {
            "POSTGRES_URL": postgres_container.get_connection_url(driver="psycopg"),
            "JWT_SECRET": "test-secret-key-32-bytes-long!!!!",
            "JWT_ALGO": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "OPENAI_API_KEY": "sk-test-not-used",
            "OPENAI_MODEL": "gpt-4o-mini",
            "EMBEDDING_MODEL": "text-embedding-3-small",
            "EMBEDDING_DIMENSIONS": "8",
            "EMBEDDING_BATCH_SIZE": "100",
            "QDRANT_URL": f"http://{qdrant_container.rest_host_address}",
            "QDRANT_COLLECTION": "test_document_chunks",
            "DB_ECHO": "false",
            "UPLOAD_DIR": str(upload_dir),
        }
    )

    from ai_doc_qa.settings import get_settings

    get_settings.cache_clear()
    get_settings()
    _apply_migrations()

    from ai_doc_qa.main import app as fastapi_app

    yield fastapi_app


@pytest.fixture(scope="session")
async def app_runtime(app) -> AsyncIterator:
    from ai_doc_qa import client as clients
    from ai_doc_qa.db.db import close_db, init_db
    from ai_doc_qa.settings import get_settings
    from tests.fakes import FakeAsyncOpenAI

    init_db()
    await clients.init_clients()
    clients._openai_client = FakeAsyncOpenAI(
        dimensions=get_settings().embedding_dimensions
    )
    try:
        yield app
    finally:
        await clients.close_clients()
        await close_db()


async def _reset_db() -> None:
    from ai_doc_qa.db.db import AsyncSessionLocal

    assert AsyncSessionLocal is not None
    async with AsyncSessionLocal() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        await session.commit()


async def _reset_qdrant() -> None:
    from ai_doc_qa.client import get_vector_db_client
    from ai_doc_qa.settings import get_settings

    vector_db = get_vector_db_client()
    collection = get_settings().qdrant_collection
    if await vector_db.collection_exists(collection):
        await vector_db.delete_collection(collection)


@pytest.fixture
async def client(app_runtime) -> AsyncIterator[AsyncClient]:
    await _reset_db()
    await _reset_qdrant()
    transport = ASGITransport(app=app_runtime)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
