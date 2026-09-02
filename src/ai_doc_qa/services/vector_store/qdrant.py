from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import (
    ResponseHandlingException,
    UnexpectedResponse,
)
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from ai_doc_qa.exceptions import VectorStoreError
from ai_doc_qa.settings import settings


class QdrantService:
    def __init__(self):
        self.url = settings.qdrant_url
        self.collection = settings.qdrant_collection
        self.dimensions = settings.embedding_dimensions
        self.score_threshold = settings.qdrant_score_threshold
        self.client = AsyncQdrantClient(url=self.url)

    async def ensure_collection(self) -> None:
        try:
            if await self.client.collection_exists(self.collection):
                return

            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.dimensions,
                    distance=Distance.COSINE,
                ),
            )
        except (UnexpectedResponse, ResponseHandlingException) as exc:
            raise VectorStoreError("Failed to ensure vector collection.") from exc

    async def upsert_chunks(
        self,
        *,
        chunk_ids: list[int],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        await self.ensure_collection()

        points = [
            PointStruct(id=chunk_id, vector=vector, payload=payload)
            for chunk_id, vector, payload in zip(chunk_ids, vectors, payloads)
        ]
        try:
            await self.client.upsert(collection_name=self.collection, points=points)
        except (UnexpectedResponse, ResponseHandlingException) as exc:
            raise VectorStoreError("Failed to upsert vectors.") from exc

    async def search(
        self,
        query_vector: list[float],
        *,
        user_id: int,
        limit: int = 5,
        document_id: int | None = None,
        score_threshold: float | None = None,
    ) -> list[dict]:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        if score_threshold is None:
            score_threshold = self.score_threshold

        must = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
        ]
        if document_id is not None:
            must.append(
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            )
        try:
            res = await self.client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=limit,
                query_filter=Filter(must=must),
                with_payload=True,
            )
        except (UnexpectedResponse, ResponseHandlingException) as exc:
            raise VectorStoreError("Failed to search vectors.") from exc

        return [
            {
                "score": hit.score,
                "text": hit.payload.get("text") if hit.payload else None,
                "document_id": hit.payload.get("document_id") if hit.payload else None,
                "chunk_id": hit.id,
            }
            for hit in res.points
            if hit.score >= score_threshold
        ]

    async def delete_document(self, *, user_id: int, document_id: int) -> None:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        try:
            if not await self.client.collection_exists(self.collection):
                return

            await self.client.delete(
                collection_name=self.collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        ),
                    ]
                ),
            )
        except (UnexpectedResponse, ResponseHandlingException) as exc:
            raise VectorStoreError("Failed to delete document vectors.") from exc
