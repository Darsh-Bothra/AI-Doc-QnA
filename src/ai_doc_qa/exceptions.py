class AppError(Exception):
    """Base for application/domain errors."""


class DocumentExtractionError(AppError):
    """Raised when PDF text extraction fails."""


class EmbeddingError(AppError):
    """Raised when embedding generation fails."""


class VectorStoreError(AppError):
    """Raised when vector store operations fail."""


class RetrievalError(AppError):
    """Raised when document retrieval fails."""


class LLMGenerationError(AppError):
    """Raised when LLM text generation fails."""


class DatabaseError(AppError):
    """Raised when database operations fail."""
