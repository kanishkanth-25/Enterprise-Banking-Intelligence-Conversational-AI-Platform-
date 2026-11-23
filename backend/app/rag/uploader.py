import json
import re
from pathlib import Path
from threading import Lock
from uuid import uuid4

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import DATA_DIR, INDEX_DIR
from app.rag.ingest import extract_document
from app.rag.retrieval import _bm25_data, _vectorstore

_index_lock = Lock()
_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _safe_filename(filename: str) -> str:
    basename = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", basename).strip("._")
    return cleaned or "uploaded_document"


def _extract_pages(path: Path) -> list[tuple[int, str]]:
    return list(extract_document(path))


def save_and_index_upload(filename: str, content: bytes) -> dict:
    safe_name = _safe_filename(filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix != ".pdf" and suffix not in _IMAGE_SUFFIXES:
        raise ValueError("Upload a PDF or an image (PNG, JPG, WEBP, BMP, or TIFF).")

    upload_dir = DATA_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid4().hex}_{safe_name}"
    stored_path.write_bytes(content)

    try:
        pages = _extract_pages(stored_path)
        documents = []
        for page_number, text in pages:
            if text.strip():
                documents.extend(
                    _SPLITTER.create_documents(
                        [text],
                        metadatas=[{"source": safe_name, "page": page_number}],
                    )
                )
        if not documents:
            raise ValueError(
                "No text was extracted. The image may be unreadable or OCR may not recognize its text."
            )

        with _index_lock:
            store = _vectorstore()
            store.add_documents(documents)
            store.save_local(str(INDEX_DIR))

            chunks_path = INDEX_DIR / "chunks.json"
            corpus = json.loads(chunks_path.read_text(encoding="utf-8"))
            corpus.extend(
                {
                    "content": document.page_content,
                    "source": document.metadata["source"],
                    "page": document.metadata["page"],
                }
                for document in documents
            )
            temporary_path = chunks_path.with_suffix(".json.tmp")
            temporary_path.write_text(
                json.dumps(corpus, ensure_ascii=False), encoding="utf-8"
            )
            temporary_path.replace(chunks_path)
            _bm25_data.cache_clear()

        return {
            "filename": safe_name,
            "pages_with_text": sum(1 for _, text in pages if text.strip()),
            "chunks_added": len(documents),
        }
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise
