from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.api.routes import auth_router, docs_router
from ai_doc_qa.client import close_clients, init_clients
from ai_doc_qa.db.db import close_db, get_db, init_db
from ai_doc_qa.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_clients()
    yield
    await close_db()
    await close_clients()


app = FastAPI(lifespan=lifespan)

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


@app.get("/health/db")
async def test_connection(db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT 1"))
    value = res.scalar()
    return {"result": value, "message": "DB created successfully"}
