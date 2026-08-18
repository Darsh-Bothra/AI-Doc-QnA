from sqlalchemy.ext.asyncio import AsyncSession
from ai_doc_qa.services.ingestion.models import ChunkPayload
from ai_doc_qa.db.models.document_chunk import DocumentChunk

class DocumentChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chunks(
        self,
        chunks: list[ChunkPayload]
    ):
        rows = [
            DocumentChunk(
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_id,
                text=chunk.text
            ) for chunk in chunks
        ]
        try:
            self.db.add_all(rows)
            await self.db.commit()

            for row in rows:
                await self.db.refresh(row)

            return rows

        except Exception:
            await self.db.rollback()
            raise