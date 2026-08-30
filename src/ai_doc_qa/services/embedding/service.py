from openai import OpenAI

from ai_doc_qa.settings import settings


class EmbeddingService:
    def __init__(self):
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.batch_size = settings.embedding_batch_size
        self.client = OpenAI(api_key=settings.openai_api_key)

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self.model,
                dimensions=self.dimensions,
            )
            embeddings.extend(
                [embedding.embedding for embedding in response.data]
            )

        return embeddings


if __name__ == "__main__":
    embedding_service = EmbeddingService()
    print(len(embedding_service.get_embeddings("Hello, world!")))
    print(embedding_service.get_embeddings("Hello, world!"))
