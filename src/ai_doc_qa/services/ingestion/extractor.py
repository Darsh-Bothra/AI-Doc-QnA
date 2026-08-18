import pymupdf4llm

class PDFTextExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_text(self) -> str:
        markdown = pymupdf4llm.to_markdown(self.file_path)
        return markdown
