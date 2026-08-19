from ai_doc_qa.services.llm.service import LLMService
from ai_doc_qa.services.rag.prompt import user_prompt
from ai_doc_qa.services.retrieval.service import RetrievalService


class RAGService:
    def __init__(self):
        self.retrieval = RetrievalService()
        self.llm = LLMService()
    
    def run(self, question: str, user_id: int, document_id: int, *, limit: int = 5) -> str:
        hits = self.retrieval.retrieve(question=question, user_id=user_id, document_id=document_id, limit=limit)
        texts = [h["text"] for h in hits if h.get("text")]
        if not texts:
            return "I'm sorry, but I do not have enough information to answer that question."

        context = "\n\n".join(texts)
        response = self.llm.generate(context=user_prompt(context, question=question))
        return response


if __name__ == "__main__":
    rag = RAGService()
    response = rag.run(question="What an FastAPI", user_id=1, document_id=2)
    print(response)