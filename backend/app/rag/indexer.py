import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import DATA_DIR, EMBEDDING_ENCODE_KWARGS, EMBEDDING_MODEL, INDEX_DIR
from app.rag.ingest import extract_document


def initialize_vector_database() -> int:
    supported_suffixes = {
        ".pdf", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"
    }
    sources = sorted(
        path for path in DATA_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )
    if not sources:
        raise FileNotFoundError(f"No PDF or TXT documents found in {DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    docs = []
    for position, path in enumerate(sources, 1):
        print(f"[{position}/{len(sources)}] Reading {path.relative_to(DATA_DIR)}", flush=True)
        for page_number, text in extract_document(path):
            if text.strip():
                docs.extend(splitter.create_documents(
                    [text],
                    metadatas=[{"source": path.name, "page": page_number}],
                ))
    if not docs:
        raise ValueError("No text could be extracted from the source documents")

    print(f"Embedding {len(docs)} chunks with {EMBEDDING_MODEL}...", flush=True)
    embedder = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={**EMBEDDING_ENCODE_KWARGS, "batch_size": 16},
        show_progress=True,
    )
    store = FAISS.from_documents(docs, embedder)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(INDEX_DIR))

    corpus = [
        {"content": doc.page_content, "source": doc.metadata["source"], "page": doc.metadata["page"]}
        for doc in docs
    ]
    (INDEX_DIR / "chunks.json").write_text(
        json.dumps(corpus, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Indexed {len(docs)} chunks from {len(sources)} source files at {INDEX_DIR}")
    return len(docs)


if __name__ == "__main__":
    initialize_vector_database()
