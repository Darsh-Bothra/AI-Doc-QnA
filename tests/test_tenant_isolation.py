import pytest
from httpx import AsyncClient

from ai_doc_qa.db import db as db_module
from ai_doc_qa.db.models import Document, DocumentStatus
from tests.helpers import assert_status, register_and_login

pytestmark = pytest.mark.integration


async def _seed_document(*, user_id: int, name: str = "tenant-b.pdf") -> int:
    assert db_module.AsyncSessionLocal is not None
    async with db_module.AsyncSessionLocal() as session:
        document = Document(
            user_id=user_id,
            name=name,
            path="/tmp/tenant-b.pdf",
            status=DocumentStatus.COMPLETED,
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document.id


async def test_cross_tenant_isolation_returns_404(client: AsyncClient):
    alice = await register_and_login(client, "alice@example.com")
    bob = await register_and_login(client, "bob@example.com")
    bob_doc_id = await _seed_document(user_id=bob["id"])

    get_response = await client.get(
        f"/documents/{bob_doc_id}",
        headers=alice["headers"],
    )
    assert_status(get_response, 404)

    delete_response = await client.delete(
        f"/documents/{bob_doc_id}",
        headers=alice["headers"],
    )
    assert_status(delete_response, 404)

    search_response = await client.post(
        "/documents/search",
        headers=alice["headers"],
        json={"question": "what is this about?", "document_id": bob_doc_id},
    )
    assert_status(search_response, 404)

    ask_response = await client.post(
        f"/documents/{bob_doc_id}/ask",
        headers=alice["headers"],
        json={"query": "what is this about?"},
    )
    assert_status(ask_response, 404)

    list_response = await client.get("/documents/", headers=alice["headers"])
    assert_status(list_response, 200)
    assert list_response.json()["total_count"] == 0

    owner_get = await client.get(
        f"/documents/{bob_doc_id}",
        headers=bob["headers"],
    )
    assert_status(owner_get, 200)
    assert owner_get.json()["id"] == bob_doc_id
