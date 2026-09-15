"""
Math expression parser — converts OCR output (LaTeX or plain text)
into SymPy expressions and structured problem objects.
"""

import re
from typing import Optional, Tuple, List

from sympy import (
    symbols, sympify, Eq, S,
    Rational, Integer, Float,
    latex, sqrt, Abs, Pow,
)
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


# ── Transformations for plain-text math parsing ────────────────────────────

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


# ── Known OCR misreads / substitutions ─────────────────────────────────────

_OCR_SUBSTITUTIONS = {
    "×": "*",
    "÷": "/",
    "·": "*",
    "∶": "/",
    "—": "-",
    "–": "-",
    "−": "-",
    "＋": "+",
    "＝": "=",
    "＞": ">",
    "＜": "<",
    "≥": ">=",
    "≤": "<=",
    "≠": "!=",
    "≈": "~",
    "∞": "oo",
    "π": "pi",
    "√": "sqrt",
    "²": "**2",
    "³": "**3",
    "⁰": "**0",
    "¹": "**1",
    "⁴": "**4",
    "⁵": "**5",
    "⁶": "**6",
    "⁷": "**7",
    "⁸": "**8",
    "⁹": "**9",
    "½": "(1/2)",
    "⅓": "(1/3)",
    "⅔": "(2/3)",
    "¼": "(1/4)",
    "¾": "(3/4)",
}


def clean_ocr_text(text: str) -> str:
    """
    Clean common OCR misreads and normalize math notation.
    """
    result = text.strip()
    for old, new in _OCR_SUBSTITUTIONS.items():
        result = result.replace(old, new)
    # Collapse multiple spaces
    result = re.sub(r"\s+", " ", result).strip()
    return result


def latex_to_sympy(latex_str: str):
    """
    Convert a LaTeX math string to a SymPy expression.

    Handles cases like:
      x^{2} + 3x - 4 = 0
      \\frac{1}{2} + \\frac{3}{4}
      \\sqrt{16}
      2^{3}
    """
    cleaned = clean_ocr_text(latex_str)
    try:
        expr = parse_latex(cleaned)
        return expr
    except Exception:
        # Try stripping surrounding $ signs
        stripped = cleaned.strip("$").strip("\\(").strip("\\)")
        try:
            return parse_latex(stripped)
        except Exception:
            return None


def text_to_sympy(text: str):
    """
    Convert plain-text math (possibly with Unicode) to a SymPy expression.
    """
    cleaned = clean_ocr_text(text)
    try:
        return parse_expr(cleaned, transformations=_TRANSFORMATIONS)
    except Exception:
        return None


def parse_math_input(raw: str) -> Optional[object]:
    """
    Try multiple strategies to parse OCR output into SymPy.

    Strategy order:
      1. LaTeX parse
      2. Plain-text parse
      3. Extract math from mixed text+math lines
      4. Return None if all fail
    """
    # Try LaTeX first (Pix2Tex output)
    result = latex_to_sympy(raw)
    if result is not None:
        return result

    # Fall back to plain text parse
    result = text_to_sympy(raw)
    if result is not None:
        return result

    # Try to extract math from mixed text+math lines
    # e.g., "1. Oblicz: 2 + 3 * 4" → try "2 + 3 * 4"
    math_part = _extract_math_from_text(raw)
    if math_part:
        result = text_to_sympy(math_part)
        if result is not None:
            return result
        result = latex_to_sympy(math_part)
        if result is not None:
            return result

    return None


def _extract_math_from_text(text: str) -> Optional[str]:
    """
    Extract the math portion from a line that mixes text and math.
    
    Strategy: find the last colon, period, or similar delimiter and take
    everything after it. Also try removing exercise numbers and common
    Polish/English instruction words.
    """
    # Remove exercise number prefix like "1. ", "3a) ", "Zadanie 5: "
    cleaned = re.sub(r"^\d{1,2}[a-z]?[\.\)]\s*", "", text)
    cleaned = re.sub(r"^(?:Zad(?:anie)?\.?\s*\d+[a-z]?\.?\s*[:\s]*)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(?:Task\s*\d+\.?\s*[:\s]*)", "", cleaned, flags=re.IGNORECASE)
    
    # Try after common instruction words
    instruction_words = [
        r"Oblicz\s*:?\s*",
        r"Obliczanie\s*:?\s*",
        r"Rozwiąż\s*:?\s*",
        r"Policz\s*:?\s*",
        r"Znajdź\s*:?\s*",
        r"Oblicz\s+wartość\s*:?\s*",
        r"Solve\s*:?\s*",
        r"Calculate\s*:?\s*",
        r"Find\s*:?\s*",
        r"Compute\s*:?\s*",
    ]
    
    for pattern in instruction_words:
        m = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if m:
            remaining = cleaned[m.end():].strip()
            if remaining and re.search(r"\d", remaining):
                return remaining
    
    # If nothing matched, try the full cleaned text
    if cleaned != text.strip() and re.search(r"[=+\-*/^]", cleaned):
        return cleaned
    
    return None


# ── Equation detection ─────────────────────────────────────────────────────

_EQ_PATTERNS = [
    # "2x + 5 = 13"
    (r"^(.+?)\s*=\s*(.+)$", "eq"),
    # "2x + 5 > 13"  or  "2x + 5 < 13"  or  ">=, <="
    (r"^(.+?)\s*([><=!]+)\s*(.+)$", "ineq"),
]


def split_equation(raw: str) -> Optional[Tuple[str, str, str]]:
    """
    Split 'left = right' into (left_str, '=', right_str).
    Returns (left_str, op, right_str) or None.
    """
    cleaned = clean_ocr_text(raw)

    # Try explicit '=' split first
    if "=" in cleaned and "<=" not in cleaned and ">=" not in cleaned and "!=" not in cleaned:
        parts = cleaned.split("=", 1)
        if len(parts) == 2:
            return (parts[0].strip(), "=", parts[1].strip())

    # Try inequality patterns
    for pattern, kind in _EQ_PATTERNS:
        if kind == "ineq":
            m = re.match(pattern, cleaned)
            if m:
                return (m.group(1).strip(), m.group(2).strip(), m.group(3).strip())

    return None


def extract_problem_context(text: str) -> dict:
    """
    Extract structured information from Polish/English exercise text.

    Returns dict with keys like:
      - problem_text: the original text
      - numbers: extracted numbers
      - has_percentage: bool
      - has_equation: bool
      - exercise_number: extracted exercise number (e.g., "1", "3a")
    """
    result = {
        "problem_text": text,
        "numbers": [],
        "has_percentage": False,
        "has_equation": False,
        "has_fraction": False,
        "has_power": False,
        "has_root": False,
        "has_geometry": False,
        "has_statistics": False,
        "exercise_number": None,
    }

    # Extract exercise number
    num_match = re.search(r"^(?:Zad(?:anie)?\.?\s*)?(\d{1,2}[a-z]?)\s*[\.\)]", text)
    if num_match:
        result["exercise_number"] = num_match.group(1)

    # Extract all numbers (integers and decimals)
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    result["numbers"] = [n.replace(",", ".") for n in numbers]

    # Keyword detection
    lower = text.lower()
    result["has_percentage"] = any(w in lower for w in ["%", "procent", "percent"])
    result["has_equation"] = "=" in text or any(w in lower for w in ["równanie", "equation", "rozwiąż", "solve"])
    result["has_fraction"] = any(w in text for w in ["/", "frac", "⅓", "½", "¼", "¾", "⅔"])
    result["has_power"] = any(w in text for w in ["²", "³", "^", "**", "potęg", "power"])
    result["has_root"] = any(w in text for w in ["√", "pierwiast", "root", "sqrt"])
    result["has_geometry"] = any(w in lower for w in [
        "pole", "obwód", "kąt", "trójkąt", "prostokąt", "koło",
        "area", "perimeter", "angle", "triangle", "rectangle", "circle",
        "pitagor", "przystaj",
    ])
    result["has_statistics"] = any(w in lower for w in [
        "średnia", "mediana", "moda", "rozkład",
        "mean", "median", "mode", "range",
    ])

    return result


# ── Parsing a single exercise (combines everything) ────────────────────────

def parse_exercise(raw_text: str, math_ocr_text: Optional[str] = None) -> dict:
    """
    Parse a single exercise into a structured dict ready for the solver.

    Args:
        raw_text: Full OCR text (may contain Polish instructions + math).
        math_ocr_text: Dedicated math OCR output (LaTeX), if available.

    Returns:
        dict with keys:
          - raw: original text
          - context: extracted context info
          - expressions: list of parsed SymPy expressions
          - equations: list of (lhs, op, rhs) tuples
          - unparsed: list of strings that failed to parse
    """
    context = extract_problem_context(raw_text)

    # Collect all potential math expressions from both OCR sources
    candidates = []
    if math_ocr_text:
        candidates.append(math_ocr_text)
    candidates.append(raw_text)

    expressions = []
    equations = []
    unparsed = []

    for source in candidates:
        # Split on common delimiters (newlines, semicolons, commas)
        lines = re.split(r"[\n;]+", source)
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue

            # Skip pure text lines (no digits or math symbols)
            if not re.search(r"[\d=+\-*/^√²³]", line):
                continue

            # Check if it's an equation/inequality
            eq_split = split_equation(line)
            if eq_split:
                lhs_str, op, rhs_str = eq_split
                lhs = parse_math_input(lhs_str)
                rhs = parse_math_input(rhs_str)
                if lhs is not None and rhs is not None:
                    equations.append((lhs, op, rhs))
                    continue

            # Try to parse as expression
            expr = parse_math_input(line)
            if expr is not None:
                expressions.append(expr)
            else:
                unparsed.append(line)

    return {
        "raw": raw_text,
        "context": context,
        "expressions": expressions,
        "equations": equations,
        "unparsed": unparsed,
    }


# ── Utility: pretty-print a SymPy expression ──────────────────────────────

def sympy_to_text(expr) -> str:
    """Convert a SymPy expression to human-readable text."""
    if expr is None:
        return "?"
    s = str(expr)
    # Replace ** with ^ for readability
    s = s.replace("**", "^")
    return s


def sympy_to_latex(expr) -> str:
    """Convert a SymPy expression to LaTeX string."""
    if expr is None:
        return "?"
    return latex(expr)
