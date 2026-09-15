"""
Configuration for MathExerciseSolver.
All tunable settings live here.
"""

import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
TEMPLATES_DIR = os.path.join(ASSETS_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")

# ── Language ───────────────────────────────────────────────────────────────
# "pl" for Polish, "en" for English
DEFAULT_LANGUAGE = "pl"

# ── OCR Settings ───────────────────────────────────────────────────────────
# Tesseract
TESSERACT_LANG = "pol+eng"  # language packs to load
TESSERACT_CONFIG = "--psm 6"  # page segmentation mode

# Pix2Tex / LaTeX-OCR
LATEX_OCR_MODEL = None  # None = default pretrained model

# Image preprocessing thresholds
ADAPTIVE_THRESH_BLOCK_SIZE = 11
ADAPTIVE_THRESH_C = 2
GAUSSIAN_BLUR_KSIZE = (3, 3)
DENOISE_STRENGTH = 10

# ── Segmentation ───────────────────────────────────────────────────────────
# Minimum contour area (in pixels²) to consider as an exercise region
MIN_CONTOUR_AREA = 500
# Padding (px) around detected exercise regions
SEGMENT_PADDING = 10
# Expected exercise number patterns (regex)
EXERCISE_NUMBER_PATTERNS = [
    r"^\d{1,2}[\.\)]\s",       # "1. " or "1) "
    r"^\d{1,2}[a-z][\.\)]\s",  # "1a. " or "1a) "
    r"^Zadanie\s+\d+",          # "Zadanie 1" (Polish: "Exercise 1")
    r"^Task\s+\d+",             # English equivalent
]

# ── Solver ─────────────────────────────────────────────────────────────────
# Maximum number of steps to prevent infinite loops
MAX_SOLVER_STEPS = 50
# Precision for decimal results
DECIMAL_PRECISION = 6
# Show fractions as mixed numbers where applicable
SHOW_MIXED_NUMBERS = True

# ── Handwriting Output ─────────────────────────────────────────────────────
# Line spacing on the rendered page (px)
LINE_SPACING = 36
# Margins (px)
PAGE_MARGIN_TOP = 60
PAGE_MARGIN_LEFT = 60
PAGE_MARGIN_RIGHT = 60
# Font size for handwritten output
HANDWRITING_FONT_SIZE = 22
# Answer highlighting
ANSWER_COLOR = (0, 100, 0)  # dark green
STEP_COLOR = (0, 0, 0)      # black
TITLE_COLOR = (0, 0, 150)   # dark blue

# ── GUI ────────────────────────────────────────────────────────────────────
GUI_WINDOW_TITLE = "MathExerciseSolver - Polish Grade 7-8"
GUI_WINDOW_SIZE = "1100x750"
GUI_BG_COLOR = "#f0f0f0"
GUI_PREVIEW_MAX_WIDTH = 500
GUI_PREVIEW_MAX_HEIGHT = 400
