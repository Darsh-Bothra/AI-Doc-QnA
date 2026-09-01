from ai_doc_qa.services.ingestion.chunker import StructureAwareChunker
from ai_doc_qa.services.ingestion.extractor import PDFTextExtractor
from ai_doc_qa.services.ingestion.models import ChunkPayload


class IngestionPipeline:
    def __init__(self, file_path: str, document_id: int, user_id: int):
        self.file_path = file_path
        self.document_id = document_id
        self.user_id = user_id

    def run(self) -> list[ChunkPayload]:
        text = PDFTextExtractor(self.file_path).extract_text()
        chunks = StructureAwareChunker(text).split_section()
        return [
            ChunkPayload(
                document_id=self.document_id,
                chunk_id=index,
                text=chunk,
                user_id=self.user_id,
            )
            for index, chunk in enumerate(chunks)
        ]
