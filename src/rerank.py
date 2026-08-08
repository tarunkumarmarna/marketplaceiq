"""
Wraps hybrid retrieval with a cross-encoder reranker. Retrieval casts a
wide, cheap net (top 15); the cross-encoder is slower but scores query
and chunk together for much better precision, so it narrows that down
to the best few before generation ever sees them.
"""

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from config import RERANK_TOP_K, RERANKER_MODEL
from retrieval import build_hybrid_retriever


def build_reranking_retriever():
    hybrid_retriever = build_hybrid_retriever()
    cross_encoder = HuggingFaceCrossEncoder(model_name=RERANKER_MODEL)
    reranker = CrossEncoderReranker(model=cross_encoder, top_n=RERANK_TOP_K)

    return ContextualCompressionRetriever(
        base_compressor=reranker, base_retriever=hybrid_retriever
    )
