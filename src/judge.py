"""
Independent faithfulness check: always Groq, regardless of which model
generated the answer, so the same model isn't grading its own homework.
Checks whether the answer's claims are actually backed by the context.
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq

from config import GROQ_MODEL

load_dotenv()

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You will be given a context (source documents) and an answer generated from that context. Check whether the answer's claims are actually supported by the context - not whether it's well-written, just whether it's faithful to the source.

Respond with a JSON object with exactly these keys:
- "faithful": true or false - true only if every claim is supported by the context
- "unsupported_claims": list of claims NOT backed by the context (empty if faithful)
- "reasoning": one sentence explaining the verdict

Be strict. A claim that sounds plausible but isn't actually stated in the context counts as unsupported."""


def judge_answer(context_chunks, answer):
    context = "\n\n".join(c.page_content for c in context_chunks)
    user_message = f"Context:\n{context}\n\nAnswer to check:\n{answer}"

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)
