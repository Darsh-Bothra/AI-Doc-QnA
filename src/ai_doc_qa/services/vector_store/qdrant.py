import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

load_dotenv()

class QdrantService:    
    def __init__(self):
        self.url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        self.collection = os.getenv("QDRANT_COLLECTION", "document_chunks")
        self.dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        self.client = QdrantClient(
            url=self.url
        )
    
    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection):
            return
        
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=self.dimensions,   # must match EmbeddingService
                distance=Distance.COSINE,
            ),
        )
    
    def upsert_chunks(self, 
        *, chunk_ids: list[int], 
        vectors: list[list[float]],
        payloads: list[dict]
    ) -> None:
        self.ensure_collection()

        points = [
            PointStruct(id=chunk_id, vector=vector, payload=payload)
            for chunk_id, vector, payload in zip(chunk_ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    

    def search(
        self,
        query_vector: list[float],
        *,
        user_id: int,
        limit: int = 5,
    ) -> list[dict]:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        res = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=limit,
            query_filter=Filter(
                must=[
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                ]
            ),
            with_payload=True,
        )

        return [
            {
                "score": hit.score,
                "text": hit.payload.get("text") if hit.payload else None,
                "document_id": hit.payload.get("document_id") if hit.payload else None,
                "chunk_id": hit.id
            }
            for hit in res.points
        ]




if __name__ == "__main__":
    from ai_doc_qa.services.embedding.service import EmbeddingService

    texts = [
        "Python is a programming language",
        "FastAPI is a Python web framework",
        "Pizza is an Italian food",
    ]

    q = QdrantService()
    q.ensure_collection()
    emb = EmbeddingService()

    vectors = [emb.get_embedding(text) for text in texts]
    payloads = [
        {
            "document_id": 1,
            "chunk_index": i,
            "user_id": 1,
            "text": text,
        }
        for i, text in enumerate(texts)
    ]

    q.upsert_chunks(
        chunk_ids=[101, 102, 103],  # any unique ints
        vectors=vectors,
        payloads=payloads,
    )
    print("upserted 3 points")

    query = "Python web development"
    query_vector = emb.get_embedding(query)
    hits = q.search(query_vector, user_id=1, limit=3)

    print(f"\nQuery: {query!r}\n")
    for rank, hit in enumerate(hits, start=1):
        print(f"{rank}. score={hit['score']:.4f}  text={hit['text']!r}")