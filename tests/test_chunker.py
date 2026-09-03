import pytest

from ai_doc_qa.services.ingestion.chunker import BasicChunker, StructureAwareChunker


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

    def test_oversized_document_is_split_to_chunk_size(self):
        document = "a" * 250
        chunk_size = 100
        overlap = 10
        chunks = BasicChunker(
            document=document,
            chunk_size=chunk_size,
            overlap=overlap,
        ).basic_chunker()

        assert len(chunks) > 1
        assert all(len(chunk) <= chunk_size for chunk in chunks)
        rebuilt = chunks[0] + "".join(chunk[overlap:] for chunk in chunks[1:])
        assert rebuilt == document


class TestStructureAwareChunker:
    def test_splits_on_markdown_headings(self):
        document = "# Intro\nhello\n\n## Details\nworld"
        sections = StructureAwareChunker(document).split_section()

        assert sections == ["# Intro\nhello", "## Details\nworld"]

    def test_document_without_headings_is_one_section(self):
        sections = StructureAwareChunker("just a paragraph").split_section()

        assert sections == ["just a paragraph"]

    def test_empty_document_yields_no_sections(self):
        assert StructureAwareChunker("").split_section() == []
        assert StructureAwareChunker("   \n\n").split_section() == []

    def test_splits_heading_levels_one_through_six(self):
        document = (
            "# H1\na\n\n## H2\nb\n\n### H3\nc\n\n"
            "#### H4\nd\n\n##### H5\ne\n\n###### H6\nf"
        )
        sections = StructureAwareChunker(document).split_section()

        assert len(sections) == 6
        assert sections[0].startswith("# H1")
        assert sections[-1].startswith("###### H6")

    def test_preamble_before_first_heading_is_its_own_section(self):
        document = "preamble text\n\n# Heading\nbody"
        sections = StructureAwareChunker(document).split_section()

        assert sections[0] == "preamble text"
        assert sections[1].startswith("# Heading")

    def test_oversized_section_is_not_split(self):
        """Heading-only splitting ignores chunk_size / overlap.

        A long single-heading section stays one chunk, which can exceed the
        embedding token limit. Phase 1 replaces this with token-aware splits.
        """
        chunk_size = 50
        body = "word " * 40
        document = f"# Only heading\n{body}"
        sections = StructureAwareChunker(
            document,
            chunk_size=chunk_size,
            overlap=10,
        ).split_section()

        assert len(sections) == 1
        assert len(sections[0]) > chunk_size
        assert sections[0].startswith("# Only heading")
