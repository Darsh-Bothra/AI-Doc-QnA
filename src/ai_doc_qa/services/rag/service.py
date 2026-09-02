from ai_doc_qa.services.llm.service import LLMService
from ai_doc_qa.services.rag.prompt import user_prompt
from ai_doc_qa.services.retrieval.service import RetrievalService


class RAGService:
    def __init__(self, retrieval: RetrievalService, llm: LLMService):
        self.retrieval = retrieval
        self.llm = llm

    async def run(
        self, question: str, user_id: int, document_id: int, *, limit: int = 5
    ) -> tuple[str, list[dict]]:
        hits = await self.retrieval.retrieve(
            question=question, user_id=user_id, document_id=document_id, limit=limit
        )
        context_parts = [
            f"[Source {i + 1}]\n{hit['text']}"
            for i, hit in enumerate(hits)
            if hit.get("text")
        ]

        if not context_parts:
            return (
                "I'm sorry, but I do not have enough information to answer that question.",
                hits,
            )

        context = "\n\n".join(context_parts)
        response = await self.llm.generate(context=user_prompt(context, question=question))
        return response, hits
