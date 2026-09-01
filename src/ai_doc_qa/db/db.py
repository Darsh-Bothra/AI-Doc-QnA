"""
DB_URL -> SQLAlchemy engine -> Session Factory -> Db session
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ai_doc_qa.settings import settings

engine = create_async_engine(
    settings.postgres_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
