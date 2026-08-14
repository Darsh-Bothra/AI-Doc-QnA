"""
    DB_URL -> SQLAlchemy engine -> Session Factory -> Db session
"""
import os
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
# DB url
DB_URL = os.getenv("POSTGRES_URL")

# SQL engine
engine = create_async_engine(DB_URL, echo=True, pool_size=20, max_overflow=0)

# Async session
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

