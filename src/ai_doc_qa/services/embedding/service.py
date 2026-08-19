import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class EmbeddingService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Add it to your .env in the project root."
            )

        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        self.client = OpenAI(api_key=api_key)

    def get_embedding(self, text: str) -> list[float]:
        clean_text = text.replace("\n", " ")

        response = self.client.embeddings.create(
            input=clean_text,
            model=self.model,
            dimensions=self.dimensions,
        )

        return response.data[0].embedding


if __name__ == "__main__":
    embedding_service = EmbeddingService()
    print(len(embedding_service.get_embedding("Hello, world!")))
    print(embedding_service.get_embedding("Hello, world!"))
