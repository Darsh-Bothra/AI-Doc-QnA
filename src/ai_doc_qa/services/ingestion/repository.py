from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.db.models import DocumentChunk
from ai_doc_qa.exceptions import DatabaseError

from .models import ChunkPayload


class DocumentChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chunks(self, chunks: list[ChunkPayload]):
        rows = [
            DocumentChunk(
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_id,
                text=chunk.text,
            )
            for chunk in chunks
        ]
        try:
            self.db.add_all(rows)
            await self.db.commit()

            for row in rows:
                await self.db.refresh(row)

            return rows

        except SQLAlchemyError as exc:
            await self.db.rollback()
            raise DatabaseError("Failed to persist document chunks.") from exc
