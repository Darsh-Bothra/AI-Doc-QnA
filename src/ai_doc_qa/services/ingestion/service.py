import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.db.models import Document, DocumentStatus
from ai_doc_qa.exceptions import AppError
from ai_doc_qa.services.embedding import EmbeddingService
from ai_doc_qa.services.ingestion import DocumentChunkRepository, IngestionPipeline
from ai_doc_qa.services.vector_store import QdrantService


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _set_status(
        self,
        document_id: int,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> None:
        doc = await self.db.get(Document, document_id)

        if doc is None:
            return

        doc.status = status

        if status == DocumentStatus.COMPLETED:
            doc.error_message = None
        elif error_message is not None:
            doc.error_message = error_message

        await self.db.commit()

    async def process_document(self, file_path: str, document_id: int, user_id: int):
        try:
            # 1. Extract + chunk
            pipeline = IngestionPipeline(
                file_path=file_path,
                document_id=document_id,
                user_id=user_id,
            )

            chunks = await asyncio.to_thread(pipeline.run)

            # 2. Store chunks in PostgreSQL
            repository = DocumentChunkRepository(self.db)

            saved_chunks = await repository.create_chunks(chunks)

            # 3. Generate embeddings
            embedding_service = EmbeddingService()

            texts = [chunk.text for chunk in saved_chunks]
            vectors = await asyncio.to_thread(embedding_service.get_embeddings, texts)

            # 4. Store vectors in Qdrant
            qdrant = QdrantService()

            await asyncio.to_thread(
                qdrant.upsert_chunks,
                chunk_ids=[chunk.id for chunk in saved_chunks],
                vectors=vectors,
                payloads=[
                    {
                        "document_id": document_id,
                        "chunk_index": chunk.chunk_index,
                        "user_id": user_id,
                        "text": chunk.text,
                    }
                    for chunk in saved_chunks
                ],
            )

        except AppError as e:
            await self._set_status(
                document_id,
                DocumentStatus.FAILED,
                error_message=str(e),
            )
            raise

        await self._set_status(
            document_id,
            DocumentStatus.COMPLETED,
        )
