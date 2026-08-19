
import os
from openai import OpenAI
from dotenv import load_dotenv

from ai_doc_qa.services.rag.prompt import RAG_SYSTEM_PROMPT

load_dotenv()

class LLMService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def generate(self, context: str):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            temperature=0.2
        )

        return response.choices[0].message.content