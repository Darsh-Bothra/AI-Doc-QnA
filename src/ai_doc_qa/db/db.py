"""
DB_URL -> SQLAlchemy engine -> Session Factory -> Db session
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ai_doc_qa.settings import settings

# Declare placeholders for your singletons
engine = None
AsyncSessionLocal = None

def init_db():
    """Initializes the singleton engine and session factory."""
    global engine, AsyncSessionLocal
    
    engine = create_async_engine(
        settings.postgres_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def close_db():
    """Disposes of the connection pool gracefully on shutdown."""
    if engine:
        await engine.dispose()

async def get_db():
    """FastAPI Dependency that yields a unique session from the singleton pool."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
        
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
