from fastapi import FastAPI, Depends

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_doc_qa.db.db import get_db

from ai_doc_qa.api.routes.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router)

@app.get("/")
def test_route():
    return {
        "message": "Testing route"
    }

@app.get("/health/db")
async def test_connection(db: AsyncSession=Depends(get_db)):
    res = await db.execute(text("SELECT 1"))
    value = res.scalar()
    return {
        "result": value,
        "message": "DB created successfully"
    }
