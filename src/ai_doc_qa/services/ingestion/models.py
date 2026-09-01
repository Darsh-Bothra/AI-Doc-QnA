from dataclasses import dataclass


@dataclass
class ChunkPayload:
    document_id: int
    chunk_id: int
    text: str
    user_id: int
