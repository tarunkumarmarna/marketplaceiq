"""
Ties every stage together into one function: retrieve -> rerank ->
generate -> verify citations -> judge -> log. Both the API and the eval
script call this same function, so the actual pipeline logic only
exists in one place.
"""

from generate import generate_answer
from guardrails import verify_citations
from judge import judge_answer
from observability import log_event, new_trace_id
from rerank import build_reranking_retriever

# built once at import time - loading the embedding/reranker models is slow,
# don't want to redo it on every single query
_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = build_reranking_retriever()
    return _retriever


def answer_question(query):
    trace_id = new_trace_id()
    log_event(trace_id, "query_received", {"query": query})

    chunks = get_retriever().invoke(query)
    log_event(
        trace_id,
        "retrieval",
        {"num_chunks": len(chunks), "filenames": [c.metadata["filename"] for c in chunks]},
    )

    result = generate_answer(query, chunks)
    log_event(trace_id, "generation", {"model_used": result["model_used"], "confidence": result["confidence"]})

    guardrail_result = verify_citations(result, chunks)
    log_event(trace_id, "guardrails", guardrail_result)

    judge_result = judge_answer(chunks, result["answer"])
    log_event(trace_id, "judge", judge_result)

    return {
        "trace_id": trace_id,
        "answer": result["answer"],
        "citations": result["citations"],
        "confidence": result["confidence"],
        "model_used": result["model_used"],
        "guardrail_passed": guardrail_result["passed"],
        "judge_faithful": judge_result["faithful"],
        "retrieved_chunks": chunks,  # kept for eval.py to build RAGAS contexts; API strips this before responding
    }
