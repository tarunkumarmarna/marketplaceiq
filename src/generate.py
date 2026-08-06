"""
Builds the prompt from reranked chunks, decides whether the question
is simple enough for Groq or needs Gemini, and gets back a structured
answer (not just a paragraph) so guardrails.py can actually check it.
"""

import json
import os
from dotenv import load_dotenv
from google import genai
from groq import Groq

from config import GEMINI_MODEL, GROQ_MODEL

load_dotenv()

COMPANY_NAMES = ["flipkart", "amazon", "meesho"]
COMPARISON_WORDS = ["compare", "vs", "versus", "difference between", "which is better", "better than"]

SYSTEM_PROMPT = """You are a marketplace policy assistant. You answer questions about e-commerce operations (returns, seller onboarding, listing rules, GST/invoicing, shipping SLA, disputes) using ONLY the context provided in each user message.

Rules:
- Never use outside knowledge, even if you're confident about it. If it's not in the context, it doesn't exist for this answer.
- If the context doesn't have enough information to answer, say so directly in "answer" and set "confidence" to "low". Do not guess or fill gaps.
- Always respond with a JSON object with exactly these keys: "answer", "citations" (list of source filenames actually used), "confidence" ("high", "medium", or "low").

Example response shape:
{"answer": "Flipkart allows returns within 7 days for electronics.", "citations": ["flipkart_returns_electronics.pdf"], "confidence": "high"}"""


def is_complex_query(query):
    query_lower = query.lower()

    companies_mentioned = sum(1 for c in COMPANY_NAMES if c in query_lower)
    has_comparison_language = any(word in query_lower for word in COMPARISON_WORDS)
    is_long = len(query.split()) > 25

    # any one of these is enough to call it complex - comparing companies
    # or explicitly asking to compare needs more reasoning than a single
    # fact lookup, so it goes to the stronger model
    return companies_mentioned >= 2 or has_comparison_language or is_long


def build_user_message(query, chunks):
    context_blocks = []
    for chunk in chunks:
        meta = chunk.metadata
        context_blocks.append(
            f"[Source: {meta['filename']} | {meta['company']} | {meta['source_tier']}]\n{chunk.page_content}"
        )
    context = "\n\n".join(context_blocks)

    return f"""Context:
{context}

Question: {query}"""


def generate_with_gemini(user_message):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_message,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "temperature": 0.1,  # low temp - want consistent, non-creative answers for policy facts
        },
    )
    return json.loads(response.text)


def generate_with_groq(user_message):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return json.loads(response.choices[0].message.content)


def generate_answer(query, chunks):
    user_message = build_user_message(query, chunks)

    if is_complex_query(query):
        model_used = "gemini"
        result = generate_with_gemini(user_message)
    else:
        model_used = "groq"
        result = generate_with_groq(user_message)

    result["model_used"] = model_used
    return result


if __name__ == "__main__":
    from rerank import build_reranking_retriever

    retriever = build_reranking_retriever()

    test_queries = [
        "What is the GST TCS rate under Section 52?",
        "Compare Flipkart and Amazon's return policies for electronics",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        chunks = retriever.invoke(query)
        result = generate_answer(query, chunks)
        print(json.dumps(result, indent=2))