"""
Independent faithfulness check: asks Groq (always Groq, regardless of
which model generated the answer) whether the answer's claims are
actually supported by the context - a second opinion, not a rubber stamp.
"""

import json
import os
from dotenv import load_dotenv
from groq import Groq

from config import GROQ_MODEL

load_dotenv()

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You will be given a context (source documents) and an answer that was generated from that context. Your job is to check whether the answer's claims are actually supported by the context - not whether the answer is well-written, just whether it's faithful to the source material.

Respond with a JSON object with exactly these keys:
- "faithful": true or false - true only if every claim in the answer is supported by the context
- "unsupported_claims": a list of specific claims in the answer that are NOT backed by the context (empty list if faithful is true)
- "reasoning": one sentence explaining your verdict

Be strict. If the answer states something the context doesn't actually say - even if it sounds plausible or true in general - that counts as unsupported."""


def judge_answer(context_chunks, answer):
    context = "\n\n".join(chunk.page_content for chunk in context_chunks)

    user_message = f"""Context:
{context}

Answer to check:
{answer}"""

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


if __name__ == "__main__":
    from rerank import build_reranking_retriever
    from generate import generate_answer

    retriever = build_reranking_retriever()

    # known-good case - real query, real generated answer, should pass
    query = "What is the GST TCS rate under Section 52?"
    chunks = retriever.invoke(query)
    result = generate_answer(query, chunks)

    print("Known-good case:")
    print(f"Answer: {result['answer']}")
    verdict = judge_answer(chunks, result["answer"])
    print(verdict)

    # known-bad case - deliberately fabricated answer the context does NOT support
    print("\nKnown-bad case (deliberately fabricated claim):")
    fake_answer = "The GST TCS rate is 5% for all e-commerce transactions regardless of state, and this has been unchanged since 2015."
    verdict = judge_answer(chunks, fake_answer)
    print(verdict)