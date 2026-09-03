from openai import AsyncOpenAI, OpenAIError

from ai_doc_qa.exceptions import EmbeddingError
from ai_doc_qa.settings import get_settings


class EmbeddingService:
    def __init__(self, client: AsyncOpenAI):
        settings = get_settings()
        self.client = client
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.batch_size = settings.embedding_batch_size

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        try:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                response = await self.client.embeddings.create(
                    input=batch,
                    model=self.model,
                    dimensions=self.dimensions,
                )
                embeddings.extend([embedding.embedding for embedding in response.data])
        except OpenAIError as exc:
            raise EmbeddingError("Failed to generate embeddings.") from exc

        return embeddings
