"""
Hybrid retrieval: combines dense (embedding) search from Qdrant with
BM25 keyword search, merged via LangChain's EnsembleRetriever.
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL, QDRANT_COLLECTION_NAME, RETRIEVAL_TOP_K

load_dotenv()


def load_all_chunks_from_qdrant(client):
    # BM25 needs every chunk in memory up front to build its keyword index -
    # it can't query Qdrant live like the dense side does
    all_points, _ = client.scroll(
        collection_name=QDRANT_COLLECTION_NAME,
        limit=1000,  # we only have 74 chunks, 1000 is way more than enough headroom
        with_payload=True,
        with_vectors=False,
    )
    docs = []
    for point in all_points:
        docs.append(
            Document(
                page_content=point.payload["page_content"],
                metadata=point.payload["metadata"],
            )
        )
    return docs


def build_hybrid_retriever():
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # dense side - queries Qdrant directly
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings,
    )
    dense_retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_TOP_K})

    # sparse side - needs chunks loaded into memory first
    all_docs = load_all_chunks_from_qdrant(client)
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = RETRIEVAL_TOP_K

    # merge both - equal weight for now, this split is one of the things
    # the Day 4 ablation study will actually test
    hybrid_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[0.5, 0.5],
    )
    return hybrid_retriever


if __name__ == "__main__":
    retriever = build_hybrid_retriever()

    test_queries = [
        "What is the GST TCS rate under Section 52?",
        "Can I return electronics on Flipkart if the box is opened?",
        "How long does Meesho take to resolve a dispute?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = retriever.invoke(query)
        for i, doc in enumerate(results[:5]):
            print(f"  [{i+1}] {doc.metadata['filename']} ({doc.metadata['company']}, {doc.metadata['source_tier']})")
            print(f"      {doc.page_content[:100]}...")