"""
Checks that every citation the LLM claims actually matches a chunk that
was genuinely retrieved for this query - catches hallucinated citations
before an answer reaches a user.
"""


def verify_citations(result, retrieved_chunks):
    retrieved_filenames = {c.metadata["filename"] for c in retrieved_chunks}
    claimed_citations = set(result.get("citations", []))
    hallucinated = claimed_citations - retrieved_filenames

    return {
        "passed": len(hallucinated) == 0,
        "hallucinated_citations": list(hallucinated),
        "retrieved_filenames": list(retrieved_filenames),
        "claimed_citations": list(claimed_citations),
    }
