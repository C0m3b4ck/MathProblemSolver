#!/usr/bin/env python3
"""Tests for the step-by-step solver."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sympy import symbols, Eq, sqrt
from solver import (
    solve_arithmetic, solve_linear_equation, solve_quadratic,
    solve_percentage, solve_gcd_lcm, solve_statistics,
    solve_simplify, solve_system, solve_inequality,
    solve_pythagoras, solve_circle, solve_rectangle,
    solve_fraction_simplify, solve_fraction_add, solve_fraction_mul,
    solve_power, solve_root,
)
from step_descriptions import get_step, get_method_name


def test_arithmetic():
    """Test basic arithmetic solving."""
    x = symbols("x")
    sol = solve_arithmetic(2 + 3 * 4, lang="pl")
    assert sol.is_valid
    assert "14" in sol.answer
    print(f"✓ Arithmetic: {sol.problem} = {sol.answer}")


def test_linear_equation():
    """Test linear equation solving."""
    x = symbols("x")
    sol = solve_linear_equation(2*x + 5, 13, lang="pl")
    assert sol.is_valid
    assert "4" in sol.answer
    print(f"✓ Linear: {sol.problem} → {sol.answer}")


def test_linear_equation_negative():
    """Test linear equation with negative coefficient."""
    x = symbols("x")
    sol = solve_linear_equation(3*x - 7, 2*x + 5, lang="pl")
    assert sol.is_valid
    assert "12" in sol.answer
    print(f"✓ Linear (neg): {sol.problem} → {sol.answer}")


def test_quadratic_equation():
    """Test quadratic equation solving."""
    x = symbols("x")
    sol = solve_quadratic(x**2 - 5*x + 6, 0, lang="pl")
    assert sol.is_valid
    assert "2" in sol.answer and "3" in sol.answer
    print(f"✓ Quadratic: {sol.problem} → {sol.answer}")


def test_percentage():
    """Test percentage calculation."""
    sol = solve_percentage(25, 200, lang="pl")
    assert sol.is_valid
    assert "50" in sol.answer
    print(f"✓ Percentage: {sol.problem} → {sol.answer}")


def test_gcd_lcm():
    """Test GCD and LCM."""
    sol = solve_gcd_lcm(12, 18, lang="pl")
    assert sol.is_valid
    assert "6" in sol.answer  # GCD
    assert "36" in sol.answer  # LCM
    print(f"✓ GCD/LCM: {sol.problem} → {sol.answer}")


def test_statistics():
    """Test statistics calculation."""
    sol = solve_statistics([2, 4, 6, 8, 10], lang="pl")
    assert sol.is_valid
    assert "6" in sol.answer  # mean and median
    print(f"✓ Statistics: {sol.problem} → {sol.answer}")


def test_simplify():
    """Test expression simplification."""
    x = symbols("x")
    sol = solve_simplify(2*x + 3*x - x, lang="pl")
    assert sol.is_valid
    # Accept both "4x" and "4*x" depending on SymPy version
    assert "4" in sol.answer and ("x" in sol.answer or "*" in sol.answer)
    print(f"✓ Simplify: {sol.problem} → {sol.answer}")


def test_system():
    """Test system of equations."""
    x, y = symbols("x y")
    sol = solve_system(x + y, 10, x - y, 4, lang="pl")
    assert sol.is_valid
    assert "7" in sol.answer and "3" in sol.answer
    print(f"✓ System: → {sol.answer}")


def test_fraction_simplify():
    """Test fraction simplification."""
    sol = solve_fraction_simplify(12, 18, lang="pl")
    assert sol.is_valid
    assert "2/3" in sol.answer
    print(f"✓ Fraction simplify: {sol.problem} → {sol.answer}")


def test_fraction_add():
    """Test fraction addition."""
    sol = solve_fraction_add(1, 4, 1, 3, lang="en")
    assert sol.is_valid
    print(f"✓ Fraction add: {sol.problem} → {sol.answer}")


def test_power():
    """Test power evaluation."""
    sol = solve_power(2, 3, lang="pl")
    assert sol.is_valid
    assert "8" in sol.answer
    print(f"✓ Power: {sol.problem} → {sol.answer}")


def test_root():
    """Test root evaluation."""
    sol = solve_root(16, lang="pl")
    assert sol.is_valid
    assert "4" in sol.answer
    print(f"✓ Root: {sol.problem} → {sol.answer}")


def test_step_descriptions():
    """Test that step descriptions work in both languages."""
    s1 = get_step("eq_start", "pl", equation="2x + 5 = 13")
    s2 = get_step("eq_start", "en", equation="2x + 5 = 13")
    assert "Równanie" in s1
    assert "Equation" in s2
    print(f"✓ Step descriptions PL: {s1}")
    print(f"✓ Step descriptions EN: {s2}")


def test_method_names():
    """Test method names in both languages."""
    assert get_method_name("linear_equation", "pl") == "Równanie liniowe"
    assert get_method_name("linear_equation", "en") == "Linear equation"
    print("✓ Method names work in both languages")


def run_all_tests():
    """Run all solver tests."""
    tests = [
        test_arithmetic,
        test_linear_equation,
        test_linear_equation_negative,
        test_quadratic_equation,
        test_percentage,
        test_gcd_lcm,
        test_statistics,
        test_simplify,
        test_system,
        test_fraction_simplify,
        test_fraction_add,
        test_power,
        test_root,
        test_step_descriptions,
        test_method_names,
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
