"""
Takes the hybrid retriever's ~15 candidates and reranks them with a
cross-encoder for a more precise final top-5.
"""

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from config import RERANKER_MODEL, RERANK_TOP_K
from retrieval import build_hybrid_retriever


def build_reranking_retriever():
    hybrid_retriever = build_hybrid_retriever()

    cross_encoder = HuggingFaceCrossEncoder(model_name=RERANKER_MODEL)
    reranker = CrossEncoderReranker(model=cross_encoder, top_n=RERANK_TOP_K)

    # wraps the hybrid retriever - pulls its candidates, then reranks them
    # down to the final top_n before returning
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=hybrid_retriever,
    )
    return compression_retriever


if __name__ == "__main__":
    retriever = build_reranking_retriever()

    test_queries = [
        "What is the GST TCS rate under Section 52?",
        "Can I return electronics on Flipkart if the box is opened?",
        "How long does Meesho take to resolve a dispute?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = retriever.invoke(query)
        for i, doc in enumerate(results):
            print(f"  [{i+1}] {doc.metadata['filename']} ({doc.metadata['company']}, {doc.metadata['source_tier']})")
            print(f"      {doc.page_content[:120]}...")