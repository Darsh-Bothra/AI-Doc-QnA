from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, BackgroundTasks

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.api.dependencies import get_current_user
from ai_doc_qa.db.db import get_db
from ai_doc_qa.db.models.document import Document, DocumentStatus
from ai_doc_qa.db.models.user import User
from ai_doc_qa.schemas.document import AskRequest, AskResponse, DocumentListResponse, DocumentResponse, SearchRequest, SearchResponse

from ai_doc_qa.services.ingestion.service import IngestionService
from ai_doc_qa.services.rag.service import RAGService
from ai_doc_qa.services.retrieval.service import RetrievalService

import asyncio

from ai_doc_qa.services.vector_store.qdrant import QdrantService

UPLOAD_DIR = Path("uploaded_documents")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_CONTENT_TYPES = {  
    "application/pdf",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

router = APIRouter(
    prefix="/documents",
    tags=["Document processing route"]
)

@router.get("/", response_model=DocumentListResponse)
async def get_docs(
    user: User=Depends(get_current_user),
    db: AsyncSession=Depends(get_db)
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
    db: AsyncSession=Depends(get_db)
):
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@router.post("/", response_model=DocumentResponse)
async def upload_docs(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    filename = f"{uuid4()}.pdf"
    file_path = UPLOAD_DIR / filename
    document_persisted = False

    try:
        file_size = 0

        with file_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large."
                    )
                buffer.write(chunk)

        new_doc = Document(
            user_id=user.id,
            name=file.filename,
            path=str(file_path),
            status=DocumentStatus.PROCESSING
        )

        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        document_persisted = True
        document_id = new_doc.id

        # Initialize the ingestion service
        ingestion_service = IngestionService(db)
        await ingestion_service.process_document(
            file_path=str(file_path),
            document_id=document_id,
            user_id=user.id,
        )
        # background_tasks.add_task(
        #     ingestion_service.process_document,
        #     file_path=str(file_path),
        #     document_id=document_id,
        #     user_id=user.id,
        #     background_tasks=background_tasks,
        # )

        await db.refresh(new_doc)
        return new_doc

    except HTTPException:
        if not document_persisted:
            await db.rollback()
            if file_path.exists():
                file_path.unlink()

        raise

    except Exception:
        if not document_persisted:
            await db.rollback()
            if file_path.exists():
                file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document."
        )

    finally:
        await file.close()
    

@router.delete("/{document_id}")
async def delete_doc(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession=Depends(get_db)
):
    query = select(Document).where(Document.id == document_id, Document.user_id == user.id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )   
    
    QdrantService().delete_document(user_id=user.id, document_id=document_id)

    await db.delete(doc)
    # Delete the file path also
    file_path = Path(doc.path)
    await db.commit()
    if file_path.exists():
        file_path.unlink()
    return {
        "message": "Document deleted successfully"
    }


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
    except Exception:
        raise HTTPException(status_code=503, detail="Search temporarily unavailable.")
    return SearchResponse(question=req.question, results=hits)


@router.post("/{document_id}/ask", response_model=AskResponse)
async def ask_doc(
    req: AskRequest,
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Document).where(Document.id == document_id, Document.user_id == user.id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
    if document.status != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is not ready for questions (status={document.status.value}).",
        )
    rag = RAGService()
    response, hits = rag.run(question=req.query, user_id=user.id, document_id=document_id)
    return AskResponse(answer=response, sources=hits)