from ai_doc_qa.exceptions import EmbeddingError, RetrievalError, VectorStoreError
from ai_doc_qa.services.embedding.service import EmbeddingService
from ai_doc_qa.services.vector_store.qdrant import QdrantService


class RetrievalService:
    def __init__(self):
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()

    def retrieve(
        self,
        question: str,
        *,
        user_id: int,
        document_id: int | None = None,
        limit: int = 5,
    ) -> list[dict]:
        try:
            vector = self.embeddings.get_embeddings([question])[0]

            return self.qdrant.search(
                vector, user_id=user_id, document_id=document_id, limit=limit
            )
        except (EmbeddingError, VectorStoreError) as exc:
            raise RetrievalError("Failed to retrieve relevant documents.") from exc


if __name__ == "__main__":
    retrieval = RetrievalService()
    hits = retrieval.retrieve(question="What an FastAPI", user_id=1, document_id=1)
    print(hits)
