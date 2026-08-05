import os
from pathlib import Path

# root of the whole project, so paths work no matter where I run scripts from
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# where the raw docs and processed chunk metadata live
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# models - keeping these in one place so I'm not hunting through files to change one
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL = "gemini-3.6-flash"
GROQ_MODEL = "llama-3.1-8b-instant"

# chunking - starting point, will probably tune this after seeing real chunk counts
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# retrieval - how many chunks come back from the hybrid retriever before reranking
RETRIEVAL_TOP_K = 15
# how many survive after reranking, this is what actually goes to the LLM
RERANK_TOP_K = 5

# qdrant
QDRANT_COLLECTION_NAME = "marketplaceiq_docs"