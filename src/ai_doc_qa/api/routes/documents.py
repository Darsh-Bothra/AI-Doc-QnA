from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.api.dependencies import get_current_user
from ai_doc_qa.db.db import get_db
from ai_doc_qa.db.models.document import Document, DocumentStatus
from ai_doc_qa.db.models.user import User
from ai_doc_qa.schemas.document import DocumentListResponse, DocumentResponse

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

@router.get("/")
async def get_docs(
    user: User=Depends(get_current_user),
    db: AsyncSession=Depends(get_db)
):
    query = select(Document).where(user.id == Document.user_id)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        total_count=len(documents),
        documents=documents
    )
    
@router.get("/{document_id}")
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
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    filename = f"{uuid4()}.pdf"
    file_path = UPLOAD_DIR / filename

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

        return new_doc

    except HTTPException:
        await db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise

    except Exception:
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
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )   
    
    if doc.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document."
        )
    
    await db.delete(doc)
    # Delete the file path also
    file_path = Path(doc.path)
    if file_path.exists():
        file_path.unlink()
    await db.commit()

    return {
        "message": "Document deleted successfully"
    }
