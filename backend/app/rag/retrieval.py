import json
import re
from functools import lru_cache
from pathlib import Path
from rank_bm25 import BM25Okapi
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith import traceable
from sentence_transformers import CrossEncoder
from app.config import (
    EMBEDDING_ENCODE_KWARGS,
    EMBEDDING_MODEL,
    INDEX_DIR,
    RERANKER_CANDIDATE_COUNT,
    RERANKER_MODEL,
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())


@lru_cache(maxsize=1)
def _embedder():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs=EMBEDDING_ENCODE_KWARGS,
    )


@lru_cache(maxsize=1)
def _reranker():
    return CrossEncoder(RERANKER_MODEL, max_length=512)


@lru_cache(maxsize=1)
def _vectorstore():
    if not (INDEX_DIR / "index.faiss").exists():
        raise FileNotFoundError("Search index is missing. Run: python -m app.rag.indexer")
    return FAISS.load_local(
        str(INDEX_DIR), _embedder(), allow_dangerous_deserialization=True
    )


@lru_cache(maxsize=1)
def _bm25_data():
    path = INDEX_DIR / "chunks.json"
    if not path.exists():
        raise FileNotFoundError("BM25 corpus is missing. Run: python -m app.rag.indexer")
    corpus = json.loads(path.read_text(encoding="utf-8"))
    tokens = [_tokens(item["content"]) for item in corpus]
    return corpus, BM25Okapi(tokens)


@traceable(name="hybrid_search", run_type="retriever")
def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    candidate_count = max(top_k, RERANKER_CANDIDATE_COUNT)
    semantic_docs = _vectorstore().similarity_search(query, k=candidate_count)
    corpus, bm25 = _bm25_data()
    scores = bm25.get_scores(_tokens(query))
    keyword_ids = [
        i for i in sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
        if scores[i] > 0
    ][:candidate_count]

    # Fuse by chunk, not only by page. Several distinct chunks can share one page.
    fused: dict[tuple[str, int, str], dict] = {}
    for rank, doc in enumerate(semantic_docs, 1):
        key = (
            doc.metadata.get("source", "unknown"),
            doc.metadata.get("page", 1),
            doc.page_content,
        )
        item = fused.setdefault(
            key,
            {"source": key[0], "page": key[1], "content": key[2], "score": 0.0},
        )
        item["score"] += 1 / (60 + rank)
    for rank, i in enumerate(keyword_ids, 1):
        source = corpus[i]
        key = (source["source"], source["page"], source["content"])
        item = fused.setdefault(key, {**source, "score": 0.0})
        item["score"] += 1 / (60 + rank)
    candidates = sorted(fused.values(), key=lambda item: item["score"], reverse=True)
    if not candidates:
        return []

    rerank_scores = _reranker().predict(
        [(query, item["content"]) for item in candidates],
        batch_size=16,
        show_progress_bar=False,
    )
    reranked = [
        {**item, "rerank_score": float(score)}
        for item, score in zip(candidates, rerank_scores)
    ]
    return sorted(
        reranked, key=lambda item: item["rerank_score"], reverse=True
    )[:top_k]
