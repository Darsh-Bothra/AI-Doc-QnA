from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from ai_doc_qa.client import get_openai_client, get_vector_db_client
from ai_doc_qa.db import get_db
from ai_doc_qa.db.models import User
from ai_doc_qa.services.embedding import EmbeddingService
from ai_doc_qa.services.llm import LLMService
from ai_doc_qa.services.rag import RAGService
from ai_doc_qa.services.retrieval import RetrievalService
from ai_doc_qa.services.vector_store import QdrantService
from ai_doc_qa.utils import decode_access_token

protected = APIRouter(prefix="/protected", tags=["Protected"])


async def get_current_user(
    payload=Depends(decode_access_token), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    query = select(User).where(User.id == int(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    return user


def get_embedding_service(
    client: AsyncOpenAI = Depends(get_openai_client),
) -> EmbeddingService:
    return EmbeddingService(client)


def get_llm_service(
    client: AsyncOpenAI = Depends(get_openai_client),
) -> LLMService:
    return LLMService(client)


def get_qdrant_service(
    client: AsyncQdrantClient = Depends(get_vector_db_client),
) -> QdrantService:
    return QdrantService(client)


def get_retrieval_service(
    embeddings: EmbeddingService = Depends(get_embedding_service),
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> RetrievalService:
    return RetrievalService(embeddings, qdrant)


def get_rag_service(
    retrieval: RetrievalService = Depends(get_retrieval_service),
    llm: LLMService = Depends(get_llm_service),
) -> RAGService:
    return RAGService(retrieval, llm)


@protected.get("/")
async def get_users(current_user: User = Depends(get_current_user)):
    return current_user
