from ai_doc_qa.services.rag.prompt import RAG_SYSTEM_PROMPT, user_prompt

__all__ = ["RAG_SYSTEM_PROMPT", "RAGService", "user_prompt"]


def __getattr__(name: str):
    if name == "RAGService":
        from ai_doc_qa.services.rag.service import RAGService

        return RAGService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
