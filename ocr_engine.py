"""
OCR engine — combines Pix2Tex (math) and Tesseract (text) for full OCR.
"""

import os
from typing import Optional, Tuple, List

from config import TESSERACT_LANG, TESSERACT_CONFIG, LATEX_OCR_MODEL


# ── Lazy-load OCR models ──────────────────────────────────────────────────

_tesseract_instance = None
_latex_ocr_instance = None


def _get_tesseract():
    """Lazy-load Tesseract via pytesseract."""
    global _tesseract_instance
    if _tesseract_instance is None:
        import pytesseract
        _tesseract_instance = pytesseract
    return _tesseract_instance


def _get_latex_ocr():
    """Lazy-load Pix2Tex model."""
    global _latex_ocr_instance
    if _latex_ocr_instance is None:
        try:
            from pix2tex.cli import LatexOCR
            _latex_ocr_instance = LatexOCR()
        except ImportError:
            print("[OCR] WARNING: pix2tex package not installed. Math OCR will use Tesseract only.")
            print("[OCR] Install with: pip install pix2tex")
            return None
        except Exception as e:
            print(f"[OCR] WARNING: Could not load pix2tex model: {e}")
            return None
    return _latex_ocr_instance


# ── Image preparation for OCR ─────────────────────────────────────────────

def prepare_for_ocr(img) -> "np.ndarray":
    """
    Prepare an image region for optimal OCR:
      - Convert to grayscale if needed
      - Upscale small images
      - Ensure good contrast
    """
    import cv2
    import numpy as np
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    h, w = gray.shape

    # Upscale if too small (OCR models work better on larger images)
    min_dim = min(h, w)
    if min_dim < 100:
        scale = 200 / min_dim
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Ensure good contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    return gray


# ── Tesseract OCR ──────────────────────────────────────────────────────────

def ocr_with_tesseract(
    img: np.ndarray,
    lang: str = TESSERACT_LANG,
    config: str = TESSERACT_CONFIG,
) -> str:
    """
    Run Tesseract OCR on an image region.
    Returns recognized text (Polish + English).
    """
    pytesseract = _get_tesseract()
    if pytesseract is None:
        return ""

    prepared = prepare_for_ocr(img)
    try:
        text = pytesseract.image_to_string(prepared, lang=lang, config=config)
        return text.strip()
    except Exception as e:
        print(f"[OCR] Tesseract error: {e}")
        return ""


def ocr_with_tesseract_data(
    img: np.ndarray,
    lang: str = TESSERACT_LANG,
    config: str = TESSERACT_CONFIG,
) -> dict:
    """
    Run Tesseract and return structured data (text + bounding boxes).
    Useful for understanding the layout.
    """
    pytesseract = _get_tesseract()
    if pytesseract is None:
        return {"text": "", "words": []}

    prepared = prepare_for_ocr(img)
    try:
        data = pytesseract.image_to_data(prepared, lang=lang, config=config, output_type=pytesseract.Output.DICT)
        words = []
        for i in range(len(data["text"])):
            word = data["text"][i].strip()
            if word:
                words.append({
                    "text": word,
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "w": data["width"][i],
                    "h": data["height"][i],
                    "conf": data["conf"][i],
                })
        return {"text": " ".join(w["text"] for w in words), "words": words}
    except Exception as e:
        print(f"[OCR] Tesseract data error: {e}")
        return {"text": "", "words": []}


# ── LaTeX OCR (Pix2Tex) ──────────────────────────────────────────────────

def ocr_with_latex(img: np.ndarray) -> Optional[str]:
    """
    Run Pix2Tex LaTeX OCR on an image region.
    Returns LaTeX string or None if unavailable/failed.
    """
    model = _get_latex_ocr()
    if model is None:
        return None

    prepared = prepare_for_ocr(img)
    # Pix2Tex expects PIL Image
    from PIL import Image
    pil_img = Image.fromarray(prepared)

    try:
        latex_str = model(pil_img)
        return latex_str.strip() if latex_str else None
    except Exception as e:
        print(f"[OCR] LaTeXOCR error: {e}")
        return None


# ── Combined OCR Pipeline ─────────────────────────────────────────────────

def ocr_exercise(
    img: np.ndarray,
    use_latex: bool = True,
) -> dict:
    """
    Full OCR pipeline for a single exercise region.

    Runs both Tesseract (for Polish text) and Pix2Tex (for math expressions),
    then merges the results.

    Args:
        img: Image region (BGR or grayscale).
        use_latex: Whether to attempt LaTeX OCR.

    Returns:
        dict with keys:
          - text: full recognized text (Tesseract)
          - math_latex: LaTeX math expressions (Pix2Tex)
          - words: word-level data from Tesseract
          - merged: merged/structured result
    """
    # Tesseract for general text
    text = ocr_with_tesseract(img)
    word_data = ocr_with_tesseract_data(img)

    # Pix2Tex for math
    math_latex = None
    if use_latex:
        math_latex = ocr_with_latex(img)

    # Merge results
    merged = _merge_ocr_results(text, math_latex)

    return {
        "text": text,
        "math_latex": math_latex,
        "words": word_data.get("words", []),
        "merged": merged,
    }


def _merge_ocr_results(text: str, latex_str: Optional[str]) -> str:
    """
    Merge Tesseract text and LaTeX OCR into a single usable string.

    Strategy:
      - If LaTeX was recognized and contains math symbols, prefer it for math parts
      - Keep Tesseract text for Polish words/instructions
    """
    if not text and not latex_str:
        return ""

    if not latex_str:
        return text

    if not text:
        return latex_str

    # If LaTeX contains equation-like content (=, +, x, etc.), it's likely
    # the math part, and Tesseract has the text part.
    has_math = any(c in latex_str for c in ["=", "+", "-", "x", "\\frac", "\\sqrt", "^"])

    if has_math:
        # Combine: LaTeX for math, Tesseract for context
        return f"{text}\n{latex_str}"

    # Fallback to Tesseract
    return text


# ── Batch OCR ──────────────────────────────────────────────────────────────

def ocr_all_exercises(
    regions: List[np.ndarray],
    use_latex: bool = True,
) -> List[dict]:
    """
    Run OCR on multiple exercise regions.

    Args:
        regions: List of image regions (cropped).
        use_latex: Whether to attempt LaTeX OCR.

    Returns:
        List of OCR result dicts, one per region.
    """
    results = []
    for i, region in enumerate(regions):
        print(f"  [OCR] Processing exercise {i + 1}/{len(regions)}...")
        result = ocr_exercise(region, use_latex=use_latex)
        results.append(result)
    return results


# ── Utility ────────────────────────────────────────────────────────────────

def check_tesseract_installed() -> bool:
    """Check if Tesseract is available on the system."""
    try:
        pytesseract = _get_tesseract()
        if pytesseract is None:
            return False
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def check_latex_ocr_available() -> bool:
    """Check if pix2tex package is installed."""
    try:
        from pix2tex.cli import LatexOCR
        return True
    except ImportError:
        return False


def print_ocr_status():
    """Print status of OCR dependencies."""
    tess_ok = check_tesseract_installed()
    latex_ok = check_latex_ocr_available()

    print("OCR Status:")
    print(f"  Tesseract:    {'✓ Installed' if tess_ok else '✗ Not found — install from https://github.com/UB-Mannheim/tesseract/wiki'}")
    print(f"  LaTeX-OCR:    {'✓ Installed' if latex_ok else '✗ Not installed — run: pip install pix2tex'}")

    if tess_ok:
        try:
            import pytesseract
            ver = pytesseract.get_tesseract_version()
            print(f"                Version: {ver}")
        except Exception:
            pass
