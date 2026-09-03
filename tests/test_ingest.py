import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from ai_doc_qa.db import db as db_module
from ai_doc_qa.db.models import Document, DocumentChunk, DocumentStatus
from ai_doc_qa.exceptions import DocumentExtractionError
from ai_doc_qa.services.ingestion import IngestionService, PDFTextExtractor
from tests.helpers import assert_status, build_pdf_bytes, register_and_login

pytestmark = pytest.mark.integration


async def test_ingest_happy_path_marks_document_completed(client: AsyncClient):
    user = await register_and_login(client, "ingest-ok@example.com")
    pdf_bytes = build_pdf_bytes(
        "Test Document\nThis PDF exists so ingestion has text to chunk."
    )

    upload = await client.post(
        "/documents/",
        headers=user["headers"],
        files={"file": ("manual.pdf", pdf_bytes, "application/pdf")},
    )
    assert_status(upload, 200)
    document_id = upload.json()["id"]

    fetched = await client.get(
        f"/documents/{document_id}",
        headers=user["headers"],
    )
    assert_status(fetched, 200)
    body = fetched.json()
    assert body["status"] == "completed"
    assert body["error_message"] is None

    assert db_module.AsyncSessionLocal is not None
    async with db_module.AsyncSessionLocal() as session:
        chunk_count = await session.scalar(
            select(func.count())
            .select_from(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
        )
    assert chunk_count is not None
    assert chunk_count >= 1

    search = await client.post(
        "/documents/search",
        headers=user["headers"],
        json={"question": "What is this document?", "document_id": document_id},
    )
    assert_status(search, 200)
    assert search.json()["results"]


async def test_ingest_failure_marks_document_failed(
    client: AsyncClient, tmp_path, monkeypatch
):
    user = await register_and_login(client, "ingest-fail@example.com")
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 not actually a valid document")

    def fail_extract(self):
        raise DocumentExtractionError(f"Failed to extract text from {self.file_path}.")

    monkeypatch.setattr(PDFTextExtractor, "extract_text", fail_extract)

    assert db_module.AsyncSessionLocal is not None
    async with db_module.AsyncSessionLocal() as session:
        document = Document(
            user_id=user["id"],
            name="broken.pdf",
            path=str(broken),
            status=DocumentStatus.PROCESSING,
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        document_id = document.id

        service = IngestionService(session)
        with pytest.raises(DocumentExtractionError):
            await service.process_document(
                file_path=str(broken),
                document_id=document_id,
                user_id=user["id"],
            )

    fetched = await client.get(
        f"/documents/{document_id}",
        headers=user["headers"],
    )
    assert_status(fetched, 200)
    body = fetched.json()
    assert body["status"] == "failed"
    assert body["error_message"]
    assert "Failed to extract text" in body["error_message"]
