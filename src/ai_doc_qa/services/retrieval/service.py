from ai_doc_qa.exceptions import EmbeddingError, RetrievalError, VectorStoreError
from ai_doc_qa.services.embedding import EmbeddingService
from ai_doc_qa.services.vector_store import QdrantService


class RetrievalService:
    def __init__(self):
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

    async def retrieve(
        self,
        question: str,
        *,
        user_id: int,
        document_id: int | None = None,
        limit: int = 5,
    ) -> list[dict]:
        try:
            vectors = await self.embeddings.get_embeddings([question])
            vector = vectors[0]

            return await self.qdrant.search(
                vector, user_id=user_id, document_id=document_id, limit=limit
            )
        except (EmbeddingError, VectorStoreError) as exc:
            raise RetrievalError("Failed to retrieve relevant documents.") from exc

