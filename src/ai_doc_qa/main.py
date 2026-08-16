from fastapi import FastAPI, Depends, UploadFile

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.db.db import get_db

from ai_doc_qa.services.document_processing import extract_text

from ai_doc_qa.api.routes.auth import router as auth_router
from ai_doc_qa.api.routes.documents import router as docs_router

from pathlib import Path

app = FastAPI()

app.include_router(auth_router)
app.include_router(docs_router)

UPLOAD_DIR = Path("uploaded_documents")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def test_route():
    return {
        "message": "Testing route"
    }

@app.post("/test-upload")
async def test_upload(
    file: UploadFile
): 
    content = await file.read()
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    return {
        "file_name": file.filename,
        "path": str(file_path),
        "content_type": file.content_type,
        "size": len(content)
    }



@app.get("/health/db")
async def test_connection(db: AsyncSession=Depends(get_db)):
    res = await db.execute(text("SELECT 1"))
    value = res.scalar()
    return {
        "result": value,
        "message": "DB created successfully"
    }


text = extract_text("uploaded_documents/test-1.pdf")
print(text)