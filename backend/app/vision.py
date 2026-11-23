import io
import fitz
from PIL import Image
from pypdf import PdfReader
from app.ocr import image_to_text


def extract_upload_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        pdf = PdfReader(io.BytesIO(content))
        rendered = fitz.open(stream=content, filetype="pdf")
        pages = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if not text.strip():
                pixmap = rendered[i].get_pixmap(
                    matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False
                )
                image = Image.frombytes(
                    "RGB", (pixmap.width, pixmap.height), pixmap.samples
                )
                text = image_to_text(image)
            if text.strip():
                pages.append(text)
        return "\n\n".join(pages)

    image = Image.open(io.BytesIO(content)).convert("RGB")
    return image_to_text(image)
