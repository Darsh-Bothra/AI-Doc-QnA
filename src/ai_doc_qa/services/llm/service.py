from openai import OpenAI

from ai_doc_qa.services.rag.prompt import RAG_SYSTEM_PROMPT
from ai_doc_qa.settings import settings


class LLMService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, context: str):
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            temperature=settings.llm_temperature,
        )

        return response.choices[0].message.content
