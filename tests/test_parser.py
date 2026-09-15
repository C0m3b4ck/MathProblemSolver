#!/usr/bin/env python3
"""Tests for the math expression parser."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sympy import symbols
from math_parser import (
    clean_ocr_text, parse_math_input, split_equation,
    extract_problem_context, parse_exercise, sympy_to_text,
)


def test_clean_ocr_text():
    """Test OCR text cleaning."""
    assert clean_ocr_text("2 × 3") == "2 * 3"
    assert clean_ocr_text("x² + 1") == "x**2 + 1"
    assert clean_ocr_text("½") == "(1/2)"
    assert clean_ocr_text("3 ÷ 4") == "3 / 4"
    assert clean_ocr_text("  lots   of   spaces  ") == "lots of spaces"
    print("✓ clean_ocr_text works")


def test_parse_math_input():
    """Test math input parsing."""
    expr = parse_math_input("2 + 3")
    assert expr is not None
    assert str(expr) == "5"

    expr = parse_math_input("x^2 + 1")
    assert expr is not None
    x = symbols("x")
    assert expr == x**2 + 1

    print("✓ parse_math_input works")


def test_split_equation():
    """Test equation splitting."""
    result = split_equation("2x + 5 = 13")
    assert result is not None
    assert result[1] == "="
    assert "2x + 5" in result[0]
    assert "13" in result[2]

    result = split_equation("3x > 10")
    assert result is not None
    assert result[1] == ">"

    print("✓ split_equation works")


def test_extract_problem_context():
    """Test problem context extraction."""
    ctx = extract_problem_context("1. Oblicz 25% z 200")
    assert ctx["exercise_number"] == "1"
    assert ctx["has_percentage"] is True

    ctx = extract_problem_context("Rozwiąż równanie: 2x + 5 = 13")
    assert ctx["has_equation"] is True

    ctx = extract_problem_context("Zadanie 3. Pole prostokąta o bokach 5 i 8")
    assert ctx["exercise_number"] == "3"
    assert ctx["has_geometry"] is True

    print("✓ extract_problem_context works")


def test_parse_exercise():
    """Test full exercise parsing."""
    result = parse_exercise("1. Oblicz: 2 + 3 * 4")
    assert len(result["expressions"]) > 0 or len(result["equations"]) > 0
    assert result["context"]["exercise_number"] == "1"
    print(f"✓ parse_exercise: {len(result['expressions'])} expressions, {len(result['equations'])} equations")


def test_sympy_to_text():
    """Test SymPy to text conversion."""
    x = symbols("x")
    assert sympy_to_text(x**2 + 1) == "x^2 + 1"
    assert sympy_to_text(None) == "?"
    print("✓ sympy_to_text works")


def run_all_tests():
    tests = [
        test_clean_ocr_text,
        test_parse_math_input,
        test_split_equation,
        test_extract_problem_context,
        test_parse_exercise,
        test_sympy_to_text,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'=' * 50}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
