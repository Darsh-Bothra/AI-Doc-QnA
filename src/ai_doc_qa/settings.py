from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        extra = "ignore",
    )

    # DB
    postgres_url: str
    db_echo: bool = True
    db_pool_size: int = 10
    db_max_overflow: int = 0

    # SECURITY/JWT
    jwt_secret: str
    jwt_algo: str
    access_token_expire_minutes: int

    # LLM
    openai_api_key: str 
    openai_model: str 
    llm_temperature: float = 0.2
    embedding_model: str 
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 100

    # Vector DB
    qdrant_url: str 
    qdrant_collection: str 
    qdrant_score_threshold: float = 0.2

    # API/CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # UPLOADS
    upload_dir: Path = Path("uploaded_documents")
    max_file_size: int = 10 * 1024 * 1024
    allowed_content_types: set[str] = {"application/pdf"}
    read_buffer_size: int = 1024 * 1024

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

settings = Settings()