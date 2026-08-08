"""
Structured JSON logging with a shared trace ID per request, so one
query's full journey through retrieval -> generation -> guardrails ->
judge can be followed in the log file instead of guessing which lines
belong together.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from config import PROJECT_ROOT

logger = logging.getLogger("marketplaceiq")
logger.setLevel(logging.INFO)

log_path = PROJECT_ROOT / "logs" / "pipeline.log"
if not logger.handlers:
    logger.addHandler(logging.FileHandler(log_path))


def new_trace_id():
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
