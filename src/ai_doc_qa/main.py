import os
from pathlib import Path

from fastapi import FastAPI, Depends, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.db.db import get_db
from ai_doc_qa.api.routes.auth import router as auth_router
from ai_doc_qa.api.routes.documents import router as docs_router

app = FastAPI()

_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# text = extract_text("uploaded_documents/test-1.pdf")