from types import SimpleNamespace


class FakeEmbeddings:
    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    async def create(self, *, input, model, dimensions):
        texts = input if isinstance(input, list) else [input]
        size = dimensions if dimensions is not None else self.dimensions
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.01] * size) for _ in texts]
        )


class FakeChatCompletions:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    async def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.answer))]
        )


class FakeAsyncOpenAI:
    """Drop-in stand-in for AsyncOpenAI used by embedding and LLM services."""

    def __init__(
        self,
        *,
        dimensions: int = 8,
        answer: str = "Grounded test answer.",
    ) -> None:
        self.embeddings = FakeEmbeddings(dimensions)
        self.chat = SimpleNamespace(completions=FakeChatCompletions(answer))
