import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.api import get_current_user
from ai_doc_qa.db import get_db
from ai_doc_qa.db.models import Document, DocumentStatus, User
from ai_doc_qa.exceptions import (
    DatabaseError,
    LLMGenerationError,
    RetrievalError,
    VectorStoreError,
)
from ai_doc_qa.schemas import (
    AskRequest,
    AskResponse,
    DocumentListResponse,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
)
from ai_doc_qa.services.rag import RAGService
from ai_doc_qa.services.retrieval import RetrievalService
from ai_doc_qa.services.vector_store import QdrantService
from ai_doc_qa.settings import settings
from ai_doc_qa.utils import run_ingestion_service

settings.upload_dir.mkdir(exist_ok=True)

router = APIRouter(prefix="/documents", tags=["Document processing route"])


@router.get("/", response_model=DocumentListResponse)
async def get_docs(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    query = select(Document).where(user.id == Document.user_id)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        total_count=len(documents),
        documents=documents,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_doc(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(
        Document.id == document_id, Document.user_id == user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.post("/", response_model=DocumentResponse)
async def upload_docs(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    filename = f"{uuid4()}.pdf"
    file_path = settings.upload_dir / filename
    document_persisted = False

    try:
        file_size = 0

        with file_path.open("wb") as buffer:
            while chunk := await file.read(settings.read_buffer_size):
                file_size += len(chunk)
                if file_size > settings.max_file_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large.",
                    )
                buffer.write(chunk)

        new_doc = Document(
            user_id=user.id,
            name=file.filename,
            path=str(file_path),
            status=DocumentStatus.PROCESSING,
        )

        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        document_persisted = True
        document_id = new_doc.id

        run_ingestion_service(
            background_tasks=background_tasks,
            document_id=document_id,
            file_path=str(file_path),
            user_id=user.id,
        )

        await db.refresh(new_doc)
        return new_doc

    except HTTPException:
        if not document_persisted:
            await db.rollback()
            if file_path.exists():
                file_path.unlink()
        raise

    except (OSError, SQLAlchemyError, DatabaseError) as exc:
        if not document_persisted:
            await db.rollback()
            if file_path.exists():
                file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document.",
        ) from exc

    finally:
        await file.close()


@router.delete("/{document_id}")
async def delete_doc(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(
        Document.id == document_id, Document.user_id == user.id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )

    try:
        QdrantService().delete_document(user_id=user.id, document_id=document_id)
    except VectorStoreError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to delete document vectors.",
        )

    await db.delete(doc)
    # Delete the file path also
    file_path = Path(doc.path)
    await db.commit()
    if file_path.exists():
        file_path.unlink()
    return {"message": "Document deleted successfully"}


@router.post("/search", response_model=SearchResponse)
async def search_docs(
    req: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.document_id is not None:
        query = select(Document).where(
            Document.id == req.document_id,
            Document.user_id == user.id,
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        if document.status != DocumentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document is not ready for search (status={document.status.value}).",
            )

    retrieval = RetrievalService()  # better: FastAPI Depends + singleton
    try:
        hits = await asyncio.to_thread(
            retrieval.retrieve,
            req.question,
            user_id=user.id,
            document_id=req.document_id,
            limit=req.limit,
        )
    except RetrievalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search temporarily unavailable.",
        )
    return SearchResponse(question=req.question, results=hits)


@router.post("/{document_id}/ask", response_model=AskResponse)
async def ask_doc(
    req: AskRequest,
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document).where(
        Document.id == document_id, Document.user_id == user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    if document.status != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is not ready for questions (status={document.status.value}).",
        )
    rag = RAGService()
    try:
        response, hits = rag.run(
            question=req.query, user_id=user.id, document_id=document_id
        )
    except (RetrievalError, LLMGenerationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question answering temporarily unavailable.",
        )
    return AskResponse(answer=response, sources=hits)
