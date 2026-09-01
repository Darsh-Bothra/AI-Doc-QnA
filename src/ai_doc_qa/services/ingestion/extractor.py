import pymupdf4llm

from ai_doc_qa.exceptions import DocumentExtractionError


class PDFTextExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_text(self) -> str:
        try:
            markdown = pymupdf4llm.to_markdown(self.file_path)
        except (OSError, FileNotFoundError) as exc:
            raise DocumentExtractionError(
                f"Failed to extract text from {self.file_path}."
            ) from exc
        return markdown
