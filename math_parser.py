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


# ── LaTeX → plain text math converter ──────────────────────────────────────

def _latex_to_text(latex_str: str) -> str:
    """
    Convert LaTeX math to plain-text math that sympy can parse.

    Handles:
      \frac{a}{b}  → (a)/(b)
      \sqrt{a}     → sqrt(a)
      x^{n}        → x**(n)
      x^{2}        → x**2
      \cdot        → *
      \times       → *
      \div         → /
      \left( \right) → ( )
      \mathrm{...} → ...
      \quad, \qquad → (removed)
      ^{...}       → **(...)
    """
    s = latex_str

    # \frac{num}{den} → (num)/(den)
    # Handle nested: \frac{1}{3} → (1)/(3)
    depth = 0
    while r"\frac{" in s and depth < 10:
        depth += 1
        s = re.sub(
            r"\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
            r"(\1)/(\2)",
            s,
        )

    # \sqrt{a} → sqrt(a)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)

    # x^{...} → x**(...)  and  x^{2} → x**2
    s = re.sub(r"\^\{([^{}]+)\}", r"**(\1)", s)
    s = re.sub(r"\^(\d+)", r"**(\1)", s)

    # \cdot, \times → *
    s = s.replace(r"\cdot", "*")
    s = s.replace(r"\times", "*")
    s = s.replace(r"\div", "/")

    # \left( \right) → ( )
    s = s.replace(r"\left(", "(").replace(r"\right)", ")")
    s = s.replace(r"\left[", "[").replace(r"\right]", "]")

    # \mathrm{X} → X
    s = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", s)

    # \quad, \qquad, \; \, \! → space or remove
    s = re.sub(r"\\q?quad\s*", " ", s)
    s = re.sub(r"\\;\s*", " ", s)
    s = re.sub(r"\\,\s*", " ", s)
    s = re.sub(r"\\!\s*", "", s)

    # Remove remaining \commands (common ones)
    s = s.replace(r"\text{", "").replace("}", "")
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)

    # Clean up: **1 → **1 (already fine), but fix **(1) if it's a simple number
    s = re.sub(r"\*\*\((\d+)\)", r"**\1", s)

    # Collapse spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


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
      1. Plain-text parse (if it looks like plain math)
      2. LaTeX parse via sympy
      3. LaTeX → plain text conversion, then parse
      4. Return None if all fail
    """
    cleaned = clean_ocr_text(raw)

    # Skip if no math content at all
    if not re.search(r"[\d=+\-*/^√²³x]", cleaned):
        return None

    # Try plain text first (handles "1/3*x - 2 = x + 2" etc.)
    result = text_to_sympy(cleaned)
    if result is not None:
        return result

    # Try LaTeX parse
    result = latex_to_sympy(raw)
    if result is not None:
        return result

    # Convert LaTeX to plain text and try again
    plain = _latex_to_text(raw)
    if plain != cleaned:
        result = text_to_sympy(plain)
        if result is not None:
            return result

    # Try extracting math from mixed text+math lines
    # e.g., "1. Oblicz: 2 + 3 * 4" → try "2 + 3 * 4"
    math_part = _extract_math_from_text(raw)
    if math_part:
        result = text_to_sympy(math_part)
        if result is not None:
            return result

    # Try stripping surrounding $ signs
    stripped = cleaned.strip("$").strip("\\(").strip("\\)")
    if stripped != cleaned:
        result = text_to_sympy(stripped)
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


# ── Split multi-expression LaTeX ───────────────────────────────────────────

def _split_latex_expressions(latex_str: str) -> List[str]:
    """
    Split a LaTeX string that contains multiple expressions into individual parts.

    Pix2Tex may output something like:
      "a) \\frac{1}{3}x - 2 = x + 2 \\quad d) \\frac{x}{6} - \\frac{1}{6} = 1"
    or:
      "\\frac{1}{3}x - 2 = x + 2 \\\\ \\frac{x}{6} - \\frac{1}{6} = 1"

    This function splits on:
      - LaTeX line breaks: \\\\, \\newline, \\[...\\]
      - Spacing commands: \\quad, \\qquad, \\;, \\, \\!
      - Exercise labels: a), b), 1), 2), (a), etc.
      - Double newlines
    """
    if not latex_str:
        return []

    result = latex_str

    # Split on LaTeX line breaks
    result = re.split(r"\\\\+|\\newline|\\\[.*?\]", result)

    # Further split each part on \quad, \qquad, etc.
    parts = []
    for segment in result:
        segment = segment.strip()
        if not segment:
            continue
        sub_parts = re.split(r"\\q?quad\s*|\\;\s*|\\,\s*|\\!\s*", segment)
        parts.extend(sub_parts)

    # Further split on exercise labels like "a)", "b)", "1.", "Zadanie 3"
    final = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Split on labels: "a) ... b)" → ["...", "..."]
        # But keep the math together — only split if label starts a new equation
        split_parts = re.split(
            r"(?=\b[a-zA-Z]\)\s*(?:\\[a-z]|[\d\-\(\\]))"
            r"|(?=\b\d{1,2}[a-z]?[\.\)]\s*(?:\\[a-z]|[\d\-\(\\]))"
            r"|(?=\\text\{[a-zA-Z]\)\})",
            part
        )
        for sp in split_parts:
            sp = sp.strip()
            if sp:
                final.append(sp)

    # Clean up: remove leading labels like "a) ", "1. "
    cleaned = []
    for expr in final:
        expr = re.sub(r"^[a-zA-Z]\)\s*", "", expr)
        expr = re.sub(r"^\d{1,2}[a-z]?[\.\)]\s*", "", expr)
        expr = re.sub(r"^\\text\{[a-zA-Z]\)\}\s*", "", expr)
        expr = expr.strip()
        if expr and len(expr) > 1:
            cleaned.append(expr)

    return cleaned if cleaned else [latex_str]


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

    # Split multi-expression LaTeX output from Pix2Tex
    # e.g. "a) \frac{1}{3}x - 2 = x + 2 \quad d) \frac{x}{6} = 1"
    # → ["\\frac{1}{3}x - 2 = x + 2", "\\frac{x}{6} = 1"]
    math_parts = []
    if math_ocr_text:
        math_parts = _split_latex_expressions(math_ocr_text)

    # Also split Tesseract text on newlines AND exercise labels
    text_parts = []
    if raw_text:
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Split on exercise labels: a), b), c) etc.
            # Only split when label is at start of line OR after 3+ spaces
            # (column boundary). This avoids splitting "3 - x)" inside equations.
            label_parts = re.split(
                r"(?:^| {3,})(?=[a-z]\)\s)",
                line,
            )
            for lp in label_parts:
                lp = re.sub(r"^[a-z]\)\s*", "", lp.strip())
                if lp:
                    text_parts.append(lp)

    # Combine: math parts first (higher quality for equations), then text parts
    candidates = math_parts + text_parts

    expressions = []
    equations = []
    unparsed = []

    for line in candidates:
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
