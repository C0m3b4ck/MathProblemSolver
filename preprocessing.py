"""
Image preprocessing and exercise segmentation.
Cleans the input image and splits it into individual exercise regions.
Supports both segmented and full-image OCR modes.
"""

import os
import re
from typing import List, Tuple, Optional

import cv2
import numpy as np
from PIL import Image

from config import (
    ADAPTIVE_THRESH_BLOCK_SIZE,
    ADAPTIVE_THRESH_C,
    GAUSSIAN_BLUR_KSIZE,
    DENOISE_STRENGTH,
    MIN_CONTOUR_AREA,
    SEGMENT_PADDING,
    EXERCISE_NUMBER_PATTERNS,
)


# ── Image Cleaning ─────────────────────────────────────────────────────────

def load_image(image_path: str) -> Optional[np.ndarray]:
    """Load an image from disk. Returns BGR numpy array or None."""
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert BGR image to grayscale."""
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def denoise(gray: np.ndarray, strength: int = DENOISE_STRENGTH) -> np.ndarray:
    """Apply non-local means denoising."""
    return cv2.fastNlMeansDenoising(gray, h=strength)


def sharpen(gray: np.ndarray) -> np.ndarray:
    """Apply unsharp masking to sharpen text edges."""
    blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_KSIZE, 0)
    return cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    """Apply adaptive Gaussian thresholding for binarization."""
    block = ADAPTIVE_THRESH_BLOCK_SIZE
    if block % 2 == 0:
        block += 1
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block, ADAPTIVE_THRESH_C,
    )


def deskew(binary: np.ndarray) -> np.ndarray:
    """Correct small rotations (deskew)."""
    coords = np.column_stack(np.where(binary < 128))
    if len(coords) < 50:
        return binary

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) > 15:
        return binary

    h, w = binary.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        binary, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def clean_image(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Full preprocessing pipeline: BGR image → (cleaned_binary, cleaned_gray).
    """
    gray = to_grayscale(img)
    gray = denoise(gray)
    gray_sharp = sharpen(gray)
    binary = adaptive_threshold(gray_sharp)
    binary = deskew(binary)
    return binary, gray_sharp


# ── Exercise Segmentation ──────────────────────────────────────────────────

def find_exercise_regions(binary: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Find rectangular regions that likely contain exercises.
    """
    h, w = binary.shape

    regions = _detect_by_lines(binary)
    if regions:
        return _merge_and_sort(regions, w, h)

    regions = _detect_by_contours(binary)
    if regions:
        return _merge_and_sort(regions, w, h)

    return [(0, 0, w, h)]


def _detect_by_lines(binary: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Detect horizontal ruled lines and extract regions between them."""
    h, w = binary.shape

    kernel_len = max(w // 8, 50)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    horizontal = cv2.morphologyEx(
        cv2.bitwise_not(binary), cv2.MORPH_OPEN, horizontal_kernel, iterations=2
    )

    line_projection = np.sum(horizontal, axis=1)
    threshold = w * 128
    line_rows = np.where(line_projection > threshold)[0]

    if len(line_rows) < 2:
        return []

    lines = []
    group_start = line_rows[0]
    for i in range(1, len(line_rows)):
        if line_rows[i] - line_rows[i - 1] > 5:
            lines.append((group_start + line_rows[i - 1]) // 2)
            group_start = line_rows[i]
    lines.append((group_start + line_rows[-1]) // 2)

    regions = []
    for i in range(len(lines) - 1):
        y_top = lines[i] + 3
        y_bot = lines[i + 1] - 3
        if y_bot - y_top > 20:
            regions.append((0, y_top, w, y_bot - y_top))

    return regions


def _detect_by_contours(binary: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Detect exercise regions using contour detection."""
    h, w = binary.shape

    inverted = cv2.bitwise_not(binary)

    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // 4, 3))
    dilated = cv2.dilate(inverted, dilate_kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        area = cw * ch

        if area < MIN_CONTOUR_AREA:
            continue
        if ch < 15 or cw < 30:
            continue
        if cw > w * 0.98:
            continue

        regions.append((x, y, cw, ch))

    return regions


def _merge_and_sort(
    regions: List[Tuple[int, int, int, int]],
    img_width: int,
    img_height: int,
) -> List[Tuple[int, int, int, int]]:
    """Merge overlapping/nearby regions and sort top-to-bottom."""
    if not regions:
        return []

    regions.sort(key=lambda r: r[1])

    merged = [regions[0]]
    for x, y, w, h in regions[1:]:
        px, py, pw, ph = merged[-1]
        if y <= py + ph + 30:
            nx = min(px, x)
            ny = min(py, y)
            nw = max(px + pw, x + w) - nx
            nh = max(py + ph, y + h) - ny
            merged[-1] = (nx, ny, nw, nh)
        else:
            merged.append((x, y, w, h))

    padded = []
    for x, y, w, h in merged:
        x1 = max(0, x - SEGMENT_PADDING)
        y1 = max(0, y - SEGMENT_PADDING)
        x2 = min(img_width, x + w + SEGMENT_PADDING)
        y2 = min(img_height, y + h + SEGMENT_PADDING)
        padded.append((x1, y1, x2 - x1, y2 - y1))

    return padded


# ── Full-image mode ────────────────────────────────────────────────────────

def should_use_full_image(binary: np.ndarray, regions: List[Tuple[int, int, int, int]]) -> bool:
    """
    Decide whether segmentation produced useful results, or if we should
    fall back to full-image OCR.

    Returns True if:
      - Only 1 region found AND it covers < 50% of the image height
      - Or only 1 region AND it's very short (< 15% of image height)
    """
    if len(regions) == 0:
        return True

    if len(regions) == 1:
        _, _, _, rh = regions[0]
        _, ih = binary.shape
        coverage = rh / ih if ih > 0 else 0
        if coverage < 0.50:
            return True
        if rh < ih * 0.15:
            return True

    return False


def get_full_image_region(binary: np.ndarray) -> Tuple[int, int, int, int]:
    """Return a region covering the entire image."""
    h, w = binary.shape
    return (0, 0, w, h)


# ── Pipeline helpers ───────────────────────────────────────────────────────

def segment_exercises(
    image_path: str,
    full_image: bool = False,
) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]], np.ndarray]:
    """
    Full segmentation pipeline: load image, clean, segment.

    Args:
        image_path: Path to the input image.
        full_image: If True, skip segmentation and return the whole image.

    Returns:
        Tuple of (original image, list of regions, cleaned binary image).
    """
    img = load_image(image_path)
    binary, _ = clean_image(img)

    if full_image:
        regions = [get_full_image_region(binary)]
        return img, regions, binary

    regions = find_exercise_regions(binary)

    # Auto-detect: if segmentation produced a tiny region, use full image
    if should_use_full_image(binary, regions):
        print("  [Preprocessing] Segmentation produced poor results — using full image")
        regions = [get_full_image_region(binary)]

    return img, regions, binary


def crop_region(
    img: np.ndarray,
    region: Tuple[int, int, int, int],
) -> np.ndarray:
    """Crop a region from an image."""
    x, y, w, h = region
    return img[y : y + h, x : x + w]


def save_crops(
    img: np.ndarray,
    regions: List[Tuple[int, int, int, int]],
    output_dir: str,
    prefix: str = "exercise",
) -> List[str]:
    """Save cropped exercise regions to disk. Returns list of file paths."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i, region in enumerate(regions):
        crop = crop_region(img, region)
        path = os.path.join(output_dir, f"{prefix}_{i + 1}.png")
        cv2.imwrite(path, crop)
        paths.append(path)
    return paths


def display_regions(
    img: np.ndarray,
    regions: List[Tuple[int, int, int, int]],
) -> np.ndarray:
    """Draw detected regions on a copy of the image (for debugging)."""
    preview = img.copy()
    for i, (x, y, w, h) in enumerate(regions):
        cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            preview, f"#{i + 1}", (x + 5, y + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2,
        )
    return preview
