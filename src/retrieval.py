"""
Hybrid retrieval: dense (embedding) search from Qdrant, merged with BM25
keyword search, via LangChain's EnsembleRetriever. Dense catches semantic
matches, BM25 catches exact terms (like a GST section number) that an
embedding model might not weight heavily.
"""

import os

from dotenv import load_dotenv
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from config import EMBEDDING_MODEL, QDRANT_COLLECTION_NAME, RETRIEVAL_TOP_K

load_dotenv()


def load_all_chunks_from_qdrant(client):
    # BM25 needs every chunk in memory up front to build its keyword index -
    # it can't query Qdrant live like the dense side does
    all_points, _ = client.scroll(
        collection_name=QDRANT_COLLECTION_NAME,
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )
    return [
        Document(
            page_content=p.payload["page_content"], metadata=p.payload["metadata"]
        )
        for p in all_points
    ]


def build_hybrid_retriever():
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    vector_store = QdrantVectorStore(
        client=client, collection_name=QDRANT_COLLECTION_NAME, embedding=embeddings
    )
    dense_retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_TOP_K})

    all_docs = load_all_chunks_from_qdrant(client)
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = RETRIEVAL_TOP_K

    return EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever], weights=[0.5, 0.5]
    )
