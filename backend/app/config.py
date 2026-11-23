import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / "backend" / ".env")

DATA_DIR = ROOT_DIR / "data"
INDEX_DIR = ROOT_DIR / "vector_indexes" / "banking_support_bge_m3"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/banking_assistant",
)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_ENCODE_KWARGS = {"normalize_embeddings": True}
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANKER_CANDIDATE_COUNT = int(os.getenv("RERANKER_CANDIDATE_COUNT", "20"))
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
