from openai import OpenAI, OpenAIError

from ai_doc_qa.exceptions import LLMGenerationError
from ai_doc_qa.services.rag import RAG_SYSTEM_PROMPT
from ai_doc_qa.settings import settings


class LLMService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, context: str):
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                temperature=settings.llm_temperature,
            )
        except OpenAIError as exc:
            raise LLMGenerationError("Failed to generate response.") from exc

        return response.choices[0].message.content
