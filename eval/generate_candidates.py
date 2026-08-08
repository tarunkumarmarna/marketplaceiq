"""
Drafts candidate eval questions from real doc chunks using Groq, spread
across areas so coverage isn't skewed toward one topic. These are DRAFTS -
every one gets reviewed against its source document before being treated
as real ground truth in test_questions.json.
"""

import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq
from qdrant_client import QdrantClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from config import QDRANT_COLLECTION_NAME

load_dotenv()

QUESTIONS_PER_AREA = 3

SYSTEM_PROMPT = """You write factual test questions for a RAG system, based only on the document excerpt given. Write ONE question a real user might ask, and the exact answer found in the text - not a paraphrase, not outside knowledge.

Respond with a JSON object with exactly these keys:
- "question": a natural question the excerpt actually answers
- "expected_answer": the precise answer, taken directly from the excerpt"""


def get_chunks_by_area(client):
    points, _ = client.scroll(collection_name=QDRANT_COLLECTION_NAME, limit=1000, with_payload=True)
    by_area = {}
    for p in points:
        area = p.payload["metadata"]["area"]
        by_area.setdefault(area, []).append(p.payload)
    return by_area


def draft_question(groq_client, chunk_payload):
    user_message = f"Document: {chunk_payload['metadata']['filename']}\n\nExcerpt:\n{chunk_payload['page_content']}"
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)


def pick_chunks_for_area(chunks, quota):
    # take evenly spaced chunks across the whole list instead of just the
    # first N - spreads picks across different files and different parts
    # of long documents, without needing to track filenames by hand
    if len(chunks) <= quota:
        return chunks
    step = len(chunks) // quota
    return chunks[::step][:quota]


def main():
    qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

    chunks_by_area = get_chunks_by_area(qdrant)
    candidates, qid = [], 1

    for area, chunks in chunks_by_area.items():
        picked = pick_chunks_for_area(chunks, QUESTIONS_PER_AREA)

        for chunk in picked:
            try:
                draft = draft_question(groq, chunk)
                candidates.append({
                    "id": qid,
                    "question": draft["question"],
                    "expected_answer": draft["expected_answer"],
                    "expected_sources": [chunk["metadata"]["filename"]],
                    "area": area,
                })
                qid += 1
                print(f"[{area}] {draft['question']}")
            except Exception as e:
                print(f"Skipped a chunk in {area}: {e}")

    out_path = os.path.join(os.path.dirname(__file__), "candidate_questions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)

    print(f"\n{len(candidates)} candidates written to eval/candidate_questions.json")
    print("These are DRAFTS - review each against its source before treating as ground truth")


if __name__ == "__main__":
    main()