from ai_doc_qa.services.embedding.service import EmbeddingService
from ai_doc_qa.services.vector_store.qdrant import QdrantService


class RetrievalService:
    def __init__(self):
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()
    
    def retrieve(self, question: str, *, user_id: int, limit: int = 5) -> list[dict]:
        vector = self.embeddings.get_embeddings([question])[0]

        return self.qdrant.search(vector, user_id=user_id, limit=limit)