import pytest

from ai_doc_qa.services.ingestion import BasicChunker, StructureAwareChunker


class TestBasicChunker:
    def test_splits_with_overlap(self):
        chunks = BasicChunker(
            document="abcdefghij",
            chunk_size=4,
            overlap=2,
        ).basic_chunker()

        assert chunks == ["abcd", "cdef", "efgh", "ghij", "ij"]

    def test_rejects_invalid_sizes(self):
        with pytest.raises(ValueError, match="chunk_size"):
            BasicChunker(document="x", chunk_size=0)
        with pytest.raises(ValueError, match="overlap cannot be negative"):
            BasicChunker(document="x", chunk_size=4, overlap=-1)
        with pytest.raises(ValueError, match="overlap must be smaller"):
            BasicChunker(document="x", chunk_size=4, overlap=4)


class TestStructureAwareChunker:
    def test_splits_on_markdown_headings(self):
        document = "# Intro\nhello\n\n## Details\nworld"
        sections = StructureAwareChunker(document).split_section()

        assert sections == ["# Intro\nhello", "## Details\nworld"]

    def test_document_without_headings_is_one_section(self):
        sections = StructureAwareChunker("just a paragraph").split_section()

        assert sections == ["just a paragraph"]
