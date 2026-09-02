from fastapi import Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.api.routes import auth_router, docs_router
from ai_doc_qa.db import get_db
from ai_doc_qa.settings import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(docs_router)

settings.upload_dir.mkdir(exist_ok=True)


@app.get("/")
def test_route():
    return {"message": "Testing route"}


@app.post("/test-upload")
async def test_upload(file: UploadFile):
    content = await file.read()
    file_path = settings.upload_dir / file.filename

    with file_path.open("wb") as buffer:
        while chunk := await file.read(settings.read_buffer_size):
            buffer.write(chunk)

    return {
        "file_name": file.filename,
        "path": str(file_path),
        "content_type": file.content_type,
        "size": len(content),
    }


@app.get("/health/db")
async def test_connection(db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT 1"))
    value = res.scalar()
    return {"result": value, "message": "DB created successfully"}
