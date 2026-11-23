from collections import Counter
from pathlib import Path

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
pdf_files = sorted(
    path for path in DATA_DIR.rglob("*")
    if path.is_file() and path.suffix.lower() == ".pdf"
)
if not pdf_files:
    raise FileNotFoundError(f"No PDF files found in {DATA_DIR}")

pages = []
for pdf_path in pdf_files:
    source = pdf_path.relative_to(DATA_DIR).as_posix()
    try:
        reader = PdfReader(str(pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(Document(
                    page_content=text,
                    metadata={"source": source, "page": page_number},
                ))
    except Exception as exc:
        print(f"Skipped {source}: {exc}")

if not pages:
    raise ValueError(f"No extractable PDF text found under {DATA_DIR}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
)
chunks = splitter.split_documents(pages)

embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True},
)
sample_chunks = chunks[:3]
vectors = embedder.embed_documents([chunk.page_content for chunk in sample_chunks])

print(f"PDF files found: {len(pdf_files)}")
print(f"Pages with text: {len(pages)}")
print(f"Chunks created: {len(chunks)}")
print("Pages by source:", dict(Counter(doc.metadata["source"] for doc in pages)))
print(f"Sample embeddings created: {len(vectors)}")
print(f"Vector dimensions: {len(vectors[0])}")

for chunk in chunks[:3]:
    print("\n---")
    print("Source:", chunk.metadata.get("source"))
    print("Page:", chunk.metadata.get("page"))
    print(chunk.page_content[:500])
