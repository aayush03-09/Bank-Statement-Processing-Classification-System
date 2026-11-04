import os
from datetime import datetime
from typing import List, Dict, Any

import fitz  # PyMuPDF
import pdfplumber
import numpy as np
import cv2
import pytesseract

from flask import current_app

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _extract_text(page: fitz.Page) -> Dict[str, Any]:
    """Extract raw text and words from a PDF page.

    Returns a dictionary with keys:
        - text: full extracted string
        - words: list of word dicts from ``page.get_text("words")``
        - images: list of images extracted via ``page.get_images()``
    """
    text = page.get_text("text")
    words = page.get_text("words")  # list of tuples (x0, y0, x1, y1, "word", block_no, line_no, word_no)
    images = page.get_images(full=True)
    return {"text": text, "words": words, "images": images}

def _text_density(page: fitz.Page, extracted: Dict[str, Any]) -> float:
    """Calculate a simple text‑density metric.

    Density = number of characters / page area.
    ``page.rect.area`` gives the area in PDF points.
    """
    char_count = len(extracted["text"]))
    area = page.rect.width * page.rect.height
    if area == 0:
        return 0.0
    return char_count / area

def _detect_page_type(page: fitz.Page, extracted: Dict[str, Any]) -> str:
    """Classify a single page.

    Returns one of: 'TEXT_BASED', 'IMAGE_BASED', 'MIXED', 'UNREADABLE'.
    The policy uses configurable thresholds from ``current_app.config``.
    """
    # Configurable thresholds (fallback defaults)
    density_thresh = current_app.config.get('TEXT_DENSITY_THRESHOLD', 0.001)
    min_words = current_app.config.get('MIN_WORD_COUNT', 5)

    has_text = bool(extracted["text"].strip())
    word_count = len(extracted["words"])
    has_images = len(extracted["images"]) > 0
    density = _text_density(page, extracted)

    if not has_text and not has_images:
        return 'UNREADABLE'
    if has_text and not has_images:
        if word_count >= min_words and density >= density_thresh:
            return 'TEXT_BASED'
        else:
            # Very sparse text – treat as unreadable
            return 'UNREADABLE'
    if has_images and not has_text:
        return 'IMAGE_BASED'
    # Both text and images present
    return 'MIXED'

def _render_page_image(page: fitz.Page, dpi: int = 300) -> np.ndarray:
    """Render a PDF page to a NumPy RGB image.
    """
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:  # RGBA -> RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    return img

def _preprocess_image(img: np.ndarray) -> np.ndarray:
    """Apply OpenCV preprocessing steps.
    Returns a binary image ready for OCR.
    Steps: grayscale, denoise (median blur), adaptive threshold, deskew.
    """
    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Noise reduction
    denoised = cv2.medianBlur(gray, 3)
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    # Deskew – compute image moments
    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        return thresh
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = thresh.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed

def _run_ocr(image: np.ndarray) -> Dict[str, Any]:
    """Perform OCR using pytesseract.
    Returns a dict with ``text`` and ``mean_confidence`` (0‑100)."""
    # Tesseract config – allow overrides via Flask config
    tess_config = current_app.config.get('OCR_TESSERACT_CONFIG', '--oem 3 --psm 3')
    # Run OCR and also ask for confidence data
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=tess_config)
    # Concatenate text
    text = " ".join([t for t in data['text'] if t.strip()])
    confidences = [int(conf) for conf in data['conf'] if conf != '-1']
    mean_conf = sum(confidences) / len(confidences) if confidences else 0
    return {"text": text, "confidence": mean_conf}

# ---------------------------------------------------------------------------
# Public service API
# ---------------------------------------------------------------------------

def process_pdf_document(pdf_path: str) -> Dict[str, Any]:
    """Process an entire PDF document page‑by‑page.

    Returns a dictionary containing:
        - ``page_count`` (int)
        - ``pages`` (list of dicts per page) where each dict includes:
            * ``page_number`` (1‑based)
            * ``type`` (TEXT_BASED, IMAGE_BASED, MIXED, UNREADABLE)
            * ``method`` ("text" or "ocr")
            * ``text`` (extracted string, may be empty)
            * ``ocr_confidence`` (float, present for OCR pages)
            * ``warnings`` (list of strings)
            * ``errors`` (list of strings)
    """
    result: Dict[str, Any] = {
        "page_count": 0,
        "pages": [],
        "warnings": [],
        "errors": [],
    }
    try:
        doc = fitz.open(pdf_path)
        result["page_count"] = doc.page_count
    except Exception as e:
        result["errors"].append(f"Unable to open PDF: {e}")
        return result

    for page_number in range(1, doc.page_count + 1):
        page = doc.load_page(page_number - 1)
        page_info: Dict[str, Any] = {
            "page_number": page_number,
            "type": "UNREADABLE",
            "method": None,
            "text": "",
            "ocr_confidence": None,
            "warnings": [],
            "errors": [],
        }
        extracted = _extract_text(page)
        page_type = _detect_page_type(page, extracted)
        page_info["type"] = page_type

        if page_type in ("TEXT_BASED", "MIXED"):
            # Use PyMuPDF text extraction as primary method
            page_info["method"] = "text"
            page_info["text"] = extracted["text"].strip()
            # Optional: pdfplumber table extraction (placeholder – store as warning if needed)
            try:
                with pdfplumber.open(pdf_path) as pdfpl:
                    pdf_page = pdfpl.pages[page_number - 1]
                    tables = pdf_page.extract_tables()
                    if tables:
                        page_info["warnings"].append(f"{len(tables)} table(s) detected – not parsed yet.")
            except Exception as e:
                page_info["warnings"].append(f"pdfplumber table extraction failed: {e}")

        if page_type in ("IMAGE_BASED", "MIXED"):
            # Perform OCR on the rendered image
            img = _render_page_image(page)
            preproc = _preprocess_image(img)
            ocr_res = _run_ocr(preproc)
            # If we already have text from the text‑based path, we concatenate
            if page_info["method"] == "text" and ocr_res["text"]:
                page_info["text"] += "\n" + ocr_res["text"]
                page_info["warnings"].append("Mixed page – OCR text appended.")
            else:
                page_info["method"] = "ocr"
                page_info["text"] = ocr_res["text"]
                page_info["ocr_confidence"] = ocr_res["confidence"]
            # Low confidence handling – add a warning
            conf_thresh = current_app.config.get('OCR_CONFIDENCE_THRESHOLD', 70)
            if page_info.get("ocr_confidence") is not None and page_info["ocr_confidence"] < conf_thresh:
                page_info["warnings"].append(
                    f"OCR confidence low ({page_info['ocr_confidence']:.1f}%). Review required."
                )

        if page_type == "UNREADABLE":
            page_info["warnings"].append("No extractable content found on this page.")

        result["pages"].append(page_info)

    return result
