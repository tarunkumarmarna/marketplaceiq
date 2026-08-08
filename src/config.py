from pathlib import Path

# root of the project, so paths work no matter where a script is run from
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# models - one place to change if I ever swap any of these
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL = "gemini-3.6-flash"
GROQ_MODEL = "llama-3.1-8b-instant"

# chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# retrieval / reranking
RETRIEVAL_TOP_K = 15
RERANK_TOP_K = 5

# qdrant
QDRANT_COLLECTION_NAME = "marketplaceiq_docs"
