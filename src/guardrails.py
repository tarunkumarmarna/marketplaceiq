"""
Checks that every citation the LLM claims actually matches a chunk that
was genuinely retrieved for this query - catches hallucinated or
mismatched citations before the answer reaches the user.
"""


def verify_citations(result, retrieved_chunks):
    retrieved_filenames = {chunk.metadata["filename"] for chunk in retrieved_chunks}
    claimed_citations = set(result.get("citations", []))

    # citations the LLM claimed but that weren't actually in the chunks
    # it was given - this is the hallucination case we care about most
    hallucinated = claimed_citations - retrieved_filenames

    verification = {
        "passed": len(hallucinated) == 0,
        "hallucinated_citations": list(hallucinated),
        "retrieved_filenames": list(retrieved_filenames),
        "claimed_citations": list(claimed_citations),
    }
    return verification


if __name__ == "__main__":
    from rerank import build_reranking_retriever
    from generate import generate_answer

    retriever = build_reranking_retriever()

    # one normal query, and one deliberately broken test - forcing a fake
    # citation into the result to confirm the guardrail actually catches it
    query = "What is the GST TCS rate under Section 52?"
    chunks = retriever.invoke(query)
    result = generate_answer(query, chunks)

    print("Normal case:")
    print(verify_citations(result, chunks))

    print("\nDeliberately broken case (forced fake citation):")
    fake_result = dict(result)
    fake_result["citations"] = result["citations"] + ["this_file_does_not_exist.pdf"]
    print(verify_citations(fake_result, chunks))