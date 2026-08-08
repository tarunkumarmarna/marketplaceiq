"""
FastAPI wrapper around the pipeline - exposes /ask for real queries and
/health so the deployment platform (and the frontend) can confirm the
backend is actually up before sending traffic to it.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI
from pydantic import BaseModel

from pipeline import answer_question

app = FastAPI(title="MarketplaceIQ API")


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(request: AskRequest):
    result = answer_question(request.question)
    # drop the raw LangChain Document objects before returning - the
    # frontend just needs plain JSON, not internal pipeline objects
    result.pop("retrieved_chunks", None)
    return result
