import re


class BasicChunker:
    def __init__(self, document: str, chunk_size: int = 100, overlap: int = 10):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.document = document
        self.chunk_size = chunk_size
        self.overlap = overlap

    def basic_chunker(self):
        chunks = []
        idx = 0
        step = self.chunk_size - self.overlap

        while idx < len(self.document):
            chunks.append(self.document[idx : idx + self.chunk_size])
            idx += step
        return chunks


class StructureAwareChunker:
    def __init__(self, document: str, chunk_size: int = 100, overlap: int = 10):
        self.document = document
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_section(self):
        section = re.split(
            r"(?=^#{1,6}\s+)",
            self.document,
            flags=re.MULTILINE,
        )

        return [section.strip() for section in section if section.strip()]
