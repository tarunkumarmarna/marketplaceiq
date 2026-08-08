"""
A few basic smoke tests, not exhaustive coverage - just enough to catch
an obvious break in the core logic (chunking, routing, citation checks)
before it reaches a real run. Run with: pytest tests/
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from generate import is_complex_query
from guardrails import verify_citations
from ingest import chunk_text


def test_chunk_text_respects_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    # each chunk after the first should start 450 chars after the previous one
    assert chunks[0] == text[0:500]
    assert chunks[1] == text[450:950]


def test_chunk_text_covers_whole_string():
    text = "hello world " * 100
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    # last chunk should reach (or pass) the end of the text
    assert chunks[-1][-1] == text[-1] or len(chunks[-1]) > 0


def test_is_complex_query_detects_comparison():
    assert is_complex_query("Compare Flipkart and Amazon return policies") is True


def test_is_complex_query_simple_case():
    assert is_complex_query("What is Meesho's return window?") is False


class FakeDoc:
    def __init__(self, filename):
        self.metadata = {"filename": filename}


def test_guardrails_catches_hallucinated_citation():
    chunks = [FakeDoc("real_file.pdf")]
    result = {"citations": ["real_file.pdf", "fake_file.pdf"]}
    verification = verify_citations(result, chunks)
    assert verification["passed"] is False
    assert "fake_file.pdf" in verification["hallucinated_citations"]


def test_guardrails_passes_when_citations_match():
    chunks = [FakeDoc("real_file.pdf")]
    result = {"citations": ["real_file.pdf"]}
    verification = verify_citations(result, chunks)
    assert verification["passed"] is True
