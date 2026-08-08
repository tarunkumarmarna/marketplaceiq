# MarketplaceIQ

A RAG system that answers natural-language questions about Indian e-commerce marketplace policies - returns, seller onboarding, listing rules, GST/invoicing, shipping SLA, and dispute resolution - sourced from real Flipkart, Amazon India, and Meesho documents. Every answer is retrieved from real source documents, reranked for relevance, generated with citations, and independently fact-checked before being shown to the user.

**Live demo:** _add your deployed Streamlit link here_

## Architecture

```
User question
    -> Hybrid retrieval (dense embeddings + BM25 keyword search)
    -> Cross-encoder reranking (top 15 -> top 5)
    -> Generation (routed to Gemini or Groq based on query complexity)
    -> Citation guardrail (are the cited sources real?)
    -> LLM-as-judge (is the answer actually faithful to the context?)
    -> Answer + sources + confidence, shown to the user
```

Every request gets a trace ID that follows it through every stage, logged as structured JSON in `logs/pipeline.log`.

## Tech stack

| Layer | Tool | Why |
|---|---|---|
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Free, fully local, no API cost per chunk |
| Reranker | CrossEncoder (ms-marco-MiniLM-L-6-v2) | Scores query+chunk together for much better precision than embedding similarity alone |
| Vector DB | Qdrant Cloud (free tier) | Simple API, generous free tier |
| Hybrid retrieval | LangChain `EnsembleRetriever` | Combines dense + BM25 - used here specifically because merging two ranked lists correctly (reciprocal rank fusion) is fiddly to hand-roll |
| Reranking wrapper | LangChain `ContextualCompressionRetriever` | Same reasoning - wraps the cross-encoder cleanly |
| Chunking | Hand-written sliding window (not a LangChain splitter) | Full control, one fewer dependency to break, and I can explain every line |
| Generation | Direct Gemini/Groq SDK calls (not a LangChain chain) | Prompt building and generation logic stays visible and debuggable, not hidden behind a chain abstraction |
| Primary LLM | Gemini (`gemini-3.6-flash`) | Free tier, used for complex/comparison queries |
| Fast + judge LLM | Groq (`llama-3.1-8b-instant`) | Free tier, used for simple queries and always for the independent faithfulness judge |
| Evaluation | RAGAS `evaluate()` (metrics only, not `TestsetGenerator`) | See Design Decisions below |
| Backend | FastAPI | `/ask` and `/health` endpoints |
| Frontend | Streamlit | Simple UI calling the backend |
| Deployment | Render/HF Spaces (backend) + Streamlit Community Cloud (frontend) | Free tiers |

## Design decisions

**Source tiering, not padding to an arbitrary document count.** The 12-document corpus is deliberately tiered: `official` (real downloaded policy pages), `seller_help_center`, and `synthesized_from_public_sources` (built from multiple real public sources, cited, reviewed). This is disclosed rather than hidden, because uneven data quality is the normal state of a real-world corpus, not a flaw to paper over.

**Manual chunking and generation instead of full LangChain chains.** LangChain is used only where it earns its place - hybrid retrieval merging and cross-encoder reranking, both genuinely fiddly to get right by hand. Chunking and generation are plain Python, calling the Gemini/Groq SDKs directly. This was a deliberate tradeoff: fewer dependency layers means fewer places for an upstream breaking change to hit (see below), and every line of the core logic is something I can explain, not something a library did for me.

**Dependency churn was a real, recurring problem during this build**, worth naming honestly rather than hiding: the Gemini SDK was fully replaced mid-build (`google-generativeai` -> `google-genai`), LangChain's `EnsembleRetriever` moved to a new `langchain-classic` package, `HuggingFaceEmbeddings` moved to `langchain-huggingface`, and RAGAS's `TestsetGenerator` turned out to have a known, still-unresolved bug on documents without markdown headline structure (confirmed via multiple open GitHub issues spanning 2024-2025). Every one of these was in a wrapper/abstraction layer, not in hand-written code - which is itself part of why this project leans toward direct SDK calls where LangChain isn't adding real value.

**RAGAS is used for evaluation metrics only, not question generation.** `TestsetGenerator` requires markdown-style headline structure to work reliably, which these policy PDFs don't have. Test questions are hand-reviewed against source documents instead (see `eval/`), and RAGAS's `evaluate()` scores the pipeline's faithfulness, context precision/recall, and answer relevancy against them - using RAGAS for the half of it that's actually stable.

## Evaluation results

_Run `eval/evaluate.py` and paste the output table here._

## Future work (explicitly deferred)

- Agentic tool-routing for multi-step questions
- Multimodal retrieval (product images)
- Table-aware chunking beyond the current row-filtering approach
- Web-search fallback for out-of-corpus questions

## Setup

1. Copy `.env.example` to `.env` and fill in your Gemini, Groq, and Qdrant credentials
2. `pip install -r requirements.txt`
3. `python verify_setup.py` - confirms all three services are reachable
4. Place your 12 source documents + `source_manifest.csv` in `data/raw/`
5. `python src/ingest.py` - chunks, embeds, and stores everything in Qdrant
6. `python eval/generate_candidates.py` then review the drafts into `eval/test_questions.json`
7. `python eval/evaluate.py` - runs the full pipeline against your test set and scores it
8. `uvicorn api.main:app --reload` (backend) and `streamlit run frontend/app.py` (frontend), in separate terminals
