"""Shared Tesseract OCR configuration and image-to-text helper."""

import pytesseract
from PIL import Image
from app.config import TESSERACT_CMD

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def image_to_text(image: Image.Image) -> str:
    return pytesseract.image_to_string(image, lang="eng", config="--psm 6").strip()
