from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from ai_doc_qa.db.db import get_db
from ai_doc_qa.services.ingestion.pipeline import IngestionPipeline
from ai_doc_qa.services.ingestion.repository import DocumentChunkRepository
from ai_doc_qa.services.ingestion.models import ChunkPayload


class IngestionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_document(
        self,
        file_path: str,
        document_id: int
    ) -> list[ChunkPayload]:
        # 1. Extract + chunk
        pipeline = IngestionPipeline(
            file_path=file_path,
            document_id=document_id
        )

        chunks = pipeline.run()

        # 2. Store chunks
        repository = DocumentChunkRepository(self.db)

        await repository.create_chunks(chunks)

        return chunks
