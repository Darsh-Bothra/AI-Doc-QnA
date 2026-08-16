import pymupdf4llm


def extract_text(file_path: str) -> str:
    markdown = pymupdf4llm.to_markdown(file_path)
    return markdown