from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.services.ingestion.pipeline import IngestionPipeline
from ai_doc_qa.services.ingestion.repository import DocumentChunkRepository

from ai_doc_qa.services.embedding.service import EmbeddingService
from ai_doc_qa.services.vector_store.qdrant import QdrantService

class IngestionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_document(
        self,
        file_path: str,
        document_id: int,
        user_id: int
    ):

        # 1. Extract + chunk
        pipeline = IngestionPipeline(
            file_path=file_path,
            document_id=document_id,
            user_id=user_id,
        )

        chunks = pipeline.run()

        # 2. Store chunks in PostgreSQL
        repository = DocumentChunkRepository(self.db)

        saved_chunks = await repository.create_chunks(chunks)

        # 3. Generate embeddings
        embedding_service = EmbeddingService()

        texts = [chunk.text for chunk in saved_chunks]
        vectors = embedding_service.get_embeddings(texts)

        # 4. Store vectors in Qdrant
        qdrant = QdrantService()

        qdrant.upsert_chunks(
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
            ]
        )