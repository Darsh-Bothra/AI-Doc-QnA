from httpx import AsyncClient
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from ai_doc_qa.settings import get_settings

_openai_client: AsyncOpenAI | None = None
_vector_db_client: AsyncQdrantClient | None = None
_http_client: AsyncClient | None = None


async def init_clients() -> None:
    """Instantiate shared API clients once at application startup."""
    global _openai_client, _vector_db_client, _http_client
    settings = get_settings()
    _http_client = AsyncClient(timeout=30.0)

    _openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        http_client=_http_client,
    )

    qdrant_kwargs: dict = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        qdrant_kwargs["api_key"] = settings.qdrant_api_key

    _vector_db_client = AsyncQdrantClient(**qdrant_kwargs)


async def close_clients() -> None:
    """Gracefully close connection pools on server shutdown."""
    global _vector_db_client, _http_client

    if _vector_db_client is not None:
        await _vector_db_client.close()
        _vector_db_client = None

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def get_openai_client() -> AsyncOpenAI:
    if _openai_client is None:
        raise RuntimeError("OpenAI client is not initialized.")
    return _openai_client


def get_vector_db_client() -> AsyncQdrantClient:
    if _vector_db_client is None:
        raise RuntimeError("Vector DB client is not initialized.")
    return _vector_db_client
