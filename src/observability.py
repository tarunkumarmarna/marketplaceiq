"""
Structured JSON logging with a shared trace ID per request, so I can
follow one query's full journey through retrieval -> generation ->
guardrails -> judge, instead of guessing which log lines go together.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from config import PROJECT_ROOT

# one logger for the whole pipeline, writes to logs/pipeline.log
logger = logging.getLogger("marketplaceiq")
logger.setLevel(logging.INFO)

log_path = PROJECT_ROOT / "logs" / "pipeline.log"
handler = logging.FileHandler(log_path)
logger.addHandler(handler)


def new_trace_id():
    # short id is enough for a student project's log volume - full uuid4
    # would work too but this is easier to eyeball in the log file
    return str(uuid.uuid4())[:8]


def log_event(trace_id, stage, data):
    entry = {
        "trace_id": trace_id,
        "stage": stage,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    logger.info(json.dumps(entry))
    return entry


if __name__ == "__main__":
    from rerank import build_reranking_retriever
    from generate import generate_answer
    from guardrails import verify_citations
    from judge import judge_answer

    trace_id = new_trace_id()
    query = "What is the GST TCS rate under Section 52?"

    log_event(trace_id, "query_received", {"query": query})

    retriever = build_reranking_retriever()
    chunks = retriever.invoke(query)
    log_event(trace_id, "retrieval", {
        "num_chunks": len(chunks),
        "filenames": [c.metadata["filename"] for c in chunks],
    })

    result = generate_answer(query, chunks)
    log_event(trace_id, "generation", {
        "model_used": result["model_used"],
        "confidence": result["confidence"],
    })

    guardrail_result = verify_citations(result, chunks)
    log_event(trace_id, "guardrails", guardrail_result)

    judge_result = judge_answer(chunks, result["answer"])
    log_event(trace_id, "judge", judge_result)

    print(f"Trace ID: {trace_id}")
    print(f"Check logs/pipeline.log for the full trace")