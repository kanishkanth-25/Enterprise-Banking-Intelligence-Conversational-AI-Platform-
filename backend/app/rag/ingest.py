from pathlib import Path
from typing import Iterator
from pypdf import PdfReader


def extract_document(path: Path) -> Iterator[tuple[int, str]]:
    if path.suffix.lower() == ".txt":
        yield 1, path.read_text(encoding="utf-8", errors="replace")
        return

    image_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    if path.suffix.lower() in image_suffixes:
        from PIL import Image

        from app.ocr import image_to_text

        with Image.open(path) as image:
            text = image_to_text(image.convert("RGB"))
        if text.strip():
            yield 1, text
        return

    pdf = PdfReader(str(path))
    needs_ocr = [i for i, page in enumerate(pdf.pages) if not (page.extract_text() or "").strip()]
    ocr_pages = {}
    if needs_ocr:
        import fitz
        from PIL import Image
        from app.ocr import image_to_text

        rendered = fitz.open(str(path))
        for i in needs_ocr:
            pixmap = rendered[i].get_pixmap(
                matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False
            )
            image = Image.frombytes(
                "RGB", (pixmap.width, pixmap.height), pixmap.samples
            )
            ocr_pages[i] = image_to_text(image)

    for i, page in enumerate(pdf.pages):
        text = ocr_pages.get(i) or page.extract_text() or ""
        if text.strip():
            yield i + 1, text
