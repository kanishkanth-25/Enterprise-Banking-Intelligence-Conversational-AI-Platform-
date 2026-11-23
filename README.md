# Enterprise Banking Intelligence Conversational AI Platform

A full-stack retrieval-augmented generation (RAG) application for answering questions about banking policies, deposit rules, account rules, and related banking documents.

The platform combines semantic search, keyword search, cross-encoder reranking, OCR, Groq-hosted LLM generation, PostgreSQL conversation storage, and a Next.js chat interface. The repository currently contains a prebuilt FAISS/BM25 index covering **1,579 chunks from 16 source documents**.

## Key features

- Hybrid document retrieval using FAISS vector search and BM25 keyword search
- Cross-encoder reranking with BGE reranker
- Grounded answer generation with Groq
- Source citations returned by the API
- PDF, TXT, PNG, JPG, JPEG, WEBP, BMP, and TIFF ingestion
- Tesseract OCR fallback for scanned PDFs and images
- Live document upload and index extension
- PostgreSQL persistence for conversations and chat messages
- LangSmith tracing for the RAG and LLM pipelines
- Responsive Next.js chat and document-upload interfaces

## Technology stack

| Area | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| API | FastAPI, Pydantic 2, Uvicorn |
| Retrieval | LangChain, FAISS, BM25, Sentence Transformers |
| Embeddings | `BAAI/bge-m3` |
| Reranking | `BAAI/bge-reranker-v2-m3` |
| Answer model | Configurable Groq model; default `openai/gpt-oss-120b` |
| OCR | PyTesseract, Tesseract OCR, PyMuPDF |
| PDF/text processing | PyPDF, LangChain text splitters |
| Database | PostgreSQL with SQLAlchemy 2 |
| Observability | LangSmith |

## Repository structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application and API routes
│   │   ├── config.py               # Environment and application configuration
│   │   ├── database.py             # SQLAlchemy engine and sessions
│   │   ├── models.py               # Conversation and chat message models
│   │   ├── ocr.py                  # Shared Tesseract OCR helper
│   │   ├── vision.py               # OCR for chat-attached PDFs and images
│   │   ├── storage.py              # Optional Google Cloud Storage support
│   │   └── rag/
│   │       ├── indexer.py          # Full index build
│   │       ├── ingest.py           # PDF and image text extraction
│   │       ├── retrieval.py        # Hybrid retrieval and reranking
│   │       ├── uploader.py         # Upload-time extraction and index updates
│   │       └── preview_chunks.py   # Chunking preview utility
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/page.tsx                # Chat interface
│   ├── app/upload/page.tsx         # Document upload interface
│   └── package.json
├── data/                           # Source documents and uploaded files
├── vector_indexes/                 # Generated FAISS and BM25 artifacts
└── LICENSE
```

## How it works

1. Source PDFs, images, and text files are discovered under `data/`.
2. Selectable PDF text is extracted; scanned pages and image documents fall back to Tesseract OCR.
3. Text is split into overlapping chunks of approximately 900 characters.
4. Each chunk is embedded with BGE-M3 and stored in a FAISS index.
5. Chunk content is also stored in `chunks.json` for BM25 keyword retrieval.
6. A question retrieves candidates from both FAISS and BM25.
7. Reciprocal-rank-fusion-style scoring combines both result lists.
8. BGE reranker scores the fused candidates and returns the top five chunks.
9. Groq generates an answer strictly from the retrieved context.
10. Conversation messages and source citations are saved in PostgreSQL.

## Prerequisites

- Windows 10/11 or another supported environment
- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL 14+
- A Groq API key
- Tesseract OCR installed for scanned documents
- Optional: A LangSmith account and API key

### Install Tesseract on Windows

Install Tesseract from the official Tesseract installer or package manager. The default executable path is commonly:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Set `TESSERACT_CMD` in `backend/.env` if Tesseract is installed elsewhere.

## Installation

Open PowerShell in the repository root.

### 1. Configure PostgreSQL

Create a PostgreSQL database for the application, for example `ai_chatbot`, and use an application database URL:

```text
postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_chatbot
```

### 2. Configure the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and set at least:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_chatbot
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
ALLOWED_ORIGINS=http://localhost:3000
MAX_UPLOAD_MB=20
```

LangSmith settings are optional:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=ai-banking-assistant
```

### 3. Build or rebuild the vector index

Place source documents in `data/`, then run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.rag.indexer
```

This scans `data/`, extracts text, creates 900-character chunks with 120-character overlap, and writes the FAISS and BM25 artifacts to `vector_indexes/banking_support_bge_m3/`.

To preview chunks and embedding behavior:

```powershell
python -m app.rag.preview_chunks
```

### 4. Start the backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API documentation is available at:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health: http://127.0.0.1:8000/api/health

### 5. Configure and start the frontend

In a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

If `.env.local.example` is not present in this repository, create `frontend/.env.local` with:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Open http://localhost:3000.

## Environment reference

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | PostgreSQL localhost example | SQLAlchemy PostgreSQL connection URL |
| `GROQ_API_KEY` | Empty | Required to generate answers |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq chat completion model |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Chunk embedding model |
| `RERANKER_MODEL` | `BAAI/bge-reranker-v2-m3` | Cross-encoder reranker |
| `RERANKER_CANDIDATE_COUNT` | `20` | Maximum candidate count before reranking |
| `TESSERACT_CMD` | Empty | Optional explicit path to `tesseract.exe` |
| `MAX_UPLOAD_MB` | `20` | Maximum PDF/document/image upload size |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `GCS_BUCKET_NAME` | Empty | Optional Google Cloud Storage bucket |
| `LANGSMITH_TRACING` | Optional | Enables LangSmith tracing |
| `LANGSMITH_API_KEY` | Optional | Authenticates LangSmith tracing |
| `LANGSMITH_PROJECT` | Optional | LangSmith project name |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Backend URL used by the Next.js application |

## API overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Basic service health check |
| `POST` | `/api/chat` | Ask a text question for a session |
| `GET` | `/api/chat/{session_id}` | Retrieve persisted conversation history |
| `POST` | `/api/chat/image` | Ask a question with OCR-extracted PDF or image text |
| `POST` | `/api/documents/upload` | Upload and incrementally index a PDF or image |

Example chat request:

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"demo-session\",\"message\":\"What is a fixed deposit?\"}"
```

Example document upload:

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/upload" ^
  -F "file=@data/Comprehensive_Deposit_Policy.pdf"
```

## Frontend

The chat page provides:

- Suggested banking questions
- Text conversation
- Screenshot or document-image attachment
- Loading and connection error states
- A direct link to the upload page

The upload page accepts PDF, PNG, JPG, JPEG, WEBP, BMP, and TIFF files up to 20 MB. On success, it reports the source filename, number of pages with extracted text, and chunks added to the index.

The included demo UI currently uses the fixed session ID `web-demo-session`. API consumers can provide their own session IDs.

## Data and index management

- Source documents are stored under `data/`.
- User uploads are saved under `data/uploads/` before extraction.
- Uploaded files are removed if indexing fails.
- The prebuilt index is stored under `vector_indexes/banking_support_bge_m3/`.
- Rebuilding replaces the complete FAISS and BM25 index.
- Uploading incrementally appends documents to the current FAISS and BM25 indexes.
- Restart the backend after a full index rebuild so cached vectorstore and BM25 objects are reloaded.

## Build and validation

Frontend production build:

```powershell
cd frontend
npm run build
npm run lint
```

Backend syntax check:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m compileall app
```

## Project assessment

The existing project summary reports **92% Recall@5** and **0.84 MRR@5** across 1,579 indexed chunks. These metrics describe the indexed banking-document retrieval setup; they are not replacement guarantees for every new document or domain.

## Security and production considerations

- Never commit real API keys or database passwords.
- Keep `backend/.env` and `frontend/.env.local` out of version control.
- Restrict `ALLOWED_ORIGINS` to trusted frontend origins in production.
- Add authentication and authorization before exposing chat or document upload publicly.
- Add rate limiting and request auditing for abuse prevention.
- Scan uploaded documents and isolate OCR/storage processing in production.
- Use managed PostgreSQL credentials and TLS.
- The current chat endpoint uses a fixed demo session in the UI but supports arbitrary API session IDs.
- Answers should be reviewed where policy, financial, legal, or compliance decisions are involved.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
