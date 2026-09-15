"""
Step-by-step math solver for Polish grades 7-8.
Each solver method returns a Solution object with localized steps.
"""

from typing import List, Optional, Tuple, Union
from dataclasses import dataclass, field
from fractions import Fraction
import math

from sympy import (
    symbols, sympify, Eq, S, solve, solve_univariate_inequality,
    Rational, Integer, Float,
    sqrt, Abs, simplify, expand, factor, cancel, together,
    oo, pi, log, ln, degree,
    latex as sympy_latex,
)
from sympy.core.relational import Relational

from step_descriptions import get_step, get_method_name
from math_parser import sympy_to_text
from config import MAX_SOLVER_STEPS, DECIMAL_PRECISION, SHOW_MIXED_NUMBERS


# ── Data structures ────────────────────────────────────────────────────────

@dataclass
class Step:
    """A single step in a solution."""
    text: str
    math: str = ""  # optional math expression to display


@dataclass
class Solution:
    """Complete solution for one problem."""
    problem: str
    method: str
    method_key: str
    steps: List[Step]
    answer: str
    is_valid: bool = True

    def to_dict(self) -> dict:
        return {
            "problem": self.problem,
            "method": self.method,
            "method_key": self.method_key,
            "steps": [{"text": s.text, "math": s.math} for s in self.steps],
            "answer": self.answer,
            "is_valid": self.is_valid,
        }


# ── Helpers ────────────────────────────────────────────────────────────────

def _step(text: str, math: str = "") -> Step:
    return Step(text=text, math=math)


def _frac_to_mixed(num: int, den: int) -> str:
    """Convert improper fraction to mixed number string."""
    if den == 0:
        return "?"
    f = Fraction(num, den)
    if not SHOW_MIXED_NUMBERS or f.denominator == 1:
        return str(f)
    whole = abs(f.numerator) // f.denominator
    remainder_num = abs(f.numerator) % f.denominator
    sign = "-" if f.numerator < 0 else ""
    if remainder_num == 0:
        return f"{sign}{whole}"
    if whole == 0:
        return f"{sign}{remainder_num}/{f.denominator}"
    return f"{sign}{whole} {remainder_num}/{f.denominator}"


def _is_integer(val) -> bool:
    """Check if a SymPy expression is an integer."""
    try:
        return int(val) == val
    except (TypeError, ValueError):
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  ARITHMETIC SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_arithmetic(expr, lang: str = "pl") -> Solution:
    """Solve a pure arithmetic expression step by step."""
    problem = sympy_to_text(expr)
    steps = []

    steps.append(_step(get_step("arith_problem", lang, expr=problem)))

    try:
        result = expr.evalf(DECIMAL_PRECISION)
        steps.append(_step(get_step("arith_result", lang, result=sympy_to_text(result))))
        answer = sympy_to_text(result)
    except Exception:
        answer = sympy_to_text(expr)
        steps.append(_step(f"= {answer}"))

    return Solution(
        problem=problem,
        method=get_method_name("arithmetic", lang),
        method_key="arithmetic",
        steps=steps,
        answer=answer,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  FRACTION SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_fraction_simplify(num: int, den: int, lang: str = "pl") -> Solution:
    """Simplify a fraction step by step."""
    problem = f"{num}/{den}"
    steps = []

    gcd_val = math.gcd(abs(num), abs(den))
    if gcd_val == 1:
        steps.append(_step(get_step("frac_simplify_result", lang, result=problem)))
        return Solution(problem, get_method_name("fraction_simplify", lang),
                        "fraction_simplify", steps, problem)

    steps.append(_step(get_step("frac_simplify_gcd", lang, num=abs(num), den=abs(den), gcd=gcd_val)))

    new_num = num // gcd_val
    new_den = den // gcd_val
    result = f"{new_num}/{new_den}"
    steps.append(_step(get_step("frac_simplify_result", lang, result=result)))

    mixed = _frac_to_mixed(new_num, new_den)
    if mixed != result:
        steps.append(_step(get_step("frac_to_mixed", lang, result=mixed)))

    return Solution(problem, get_method_name("fraction_simplify", lang),
                    "fraction_simplify", steps, mixed if SHOW_MIXED_NUMBERS else result)


def solve_fraction_add(num1: int, den1: int, num2: int, den2: int, lang: str = "pl") -> Solution:
    """Add two fractions step by step."""
    problem = f"{num1}/{den1} + {num2}/{den2}"
    steps = []

    f1 = Fraction(num1, den1)
    f2 = Fraction(num2, den2)

    lcd = f1.denominator * f2.denominator // math.gcd(f1.denominator, f2.denominator)
    steps.append(_step(get_step("frac_find_lcd", lang, lcd=lcd)))

    c1 = lcd // f1.denominator
    c2 = lcd // f2.denominator
    steps.append(_step(get_step("frac_convert", lang, converted=f"{f1.numerator * c1}/{lcd} + {f2.numerator * c2}/{lcd}")))

    result_num = f1.numerator * c1 + f2.numerator * c2
    result = Fraction(result_num, lcd)
    steps.append(_step(get_step("frac_add_step", lang, a=str(f1), b=str(f2), result=str(result))))

    mixed = _frac_to_mixed(result.numerator, result.denominator)
    if mixed != str(result):
        steps.append(_step(get_step("frac_to_mixed", lang, result=mixed)))

    return Solution(problem, get_method_name("fraction_add", lang),
                    "fraction_add", steps, mixed)


def solve_fraction_mul(num1: int, den1: int, num2: int, den2: int, lang: str = "pl") -> Solution:
    """Multiply two fractions step by step."""
    problem = f"{num1}/{den1} · {num2}/{den2}"
    steps = []

    f1 = Fraction(num1, den1)
    f2 = Fraction(num2, den2)
    result = f1 * f2
    steps.append(_step(get_step("frac_mul_step", lang, a=str(f1), b=str(f2), result=str(result))))

    mixed = _frac_to_mixed(result.numerator, result.denominator)
    return Solution(problem, get_method_name("fraction_mul", lang),
                    "fraction_mul", steps, mixed)


# ═══════════════════════════════════════════════════════════════════════════
#  PERCENTAGE SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_percentage(rate: float, whole: float, lang: str = "pl") -> Solution:
    """Calculate: what is rate% of whole?"""
    problem = f"{rate}% z {whole}"
    steps = []

    decimal_val = rate / 100
    steps.append(_step(get_step("pct_decimal", lang, rate=rate, decimal=decimal_val)))

    result = decimal_val * whole
    # Clean up floating point
    if result == int(result):
        result = int(result)

    steps.append(_step(get_step("pct_multiply", lang, decimal=decimal_val, whole=whole, result=result)))
    steps.append(_step(get_step("pct_result", lang, result=result, part_name=str(rate) + "%", whole=whole)))

    return Solution(problem, get_method_name("percentage", lang),
                    "percentage", steps, str(result))


def solve_percentage_reverse(part: float, whole: float, lang: str = "pl") -> Solution:
    """Calculate: what percentage is part of whole?"""
    problem = f"Ile procent {part} stanowi z {whole}?"
    steps = []

    rate = (part / whole) * 100
    if rate == int(rate):
        rate = int(rate)
    else:
        rate = round(rate, 2)

    steps.append(_step(f"{part} / {whole} · 100% = {rate}%"))

    return Solution(problem, get_method_name("percentage", lang),
                    "percentage", steps, f"{rate}%")


# ═══════════════════════════════════════════════════════════════════════════
#  LINEAR EQUATION SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_linear_equation(lhs, rhs, lang: str = "pl", verbose: bool = False) -> Solution:
    """
    Solve a linear equation ax + b = c step by step.
    When verbose=True, shows exact equation state at every intermediate step.
    """
    x = symbols("x")
    problem = f"{sympy_to_text(lhs)} = {sympy_to_text(rhs)}"
    steps = []

    eq = Eq(lhs, rhs)
    solutions = solve(eq, x)

    if not solutions:
        steps.append(_step(get_step("eq_start", lang, equation=problem)))
        steps.append(_step(get_step("eq_no_solution", lang)))
        return Solution(problem, get_method_name("linear_equation", lang),
                        "linear_equation", steps, "Brak rozwiązań" if lang == "pl" else "No solution")

    if verbose:
        # Verbose mode: show every intermediate step with full equation state
        steps.append(_step(get_step("eq_start", lang, equation=problem)))

        # Collect terms: move everything to form coeff*x = constant
        diff = expand(lhs - rhs)
        coeff = diff.coeff(x, 1)
        constant = diff.coeff(x, 0)

        # Step: Move constant terms from LHS to RHS
        if constant != 0:
            direction = get_step("eq_move_right", lang)
            moved = sympy_to_text(constant)
            steps.append(_step(get_step("verbose_move", lang,
                                         term=moved,
                                         direction=direction,
                                         result=f"{sympy_to_text(coeff)}·x = {sympy_to_text(-constant)}")))

        # Step: Show combined form
        if coeff != 1 or constant != 0:
            steps.append(_step(get_step("verbose_combine", lang,
                                         result=f"{sympy_to_text(coeff)}·x = {sympy_to_text(-constant)}")))

        # Step: Divide both sides
        if coeff != 1:
            right_val = simplify(Rational(-constant, coeff))
            steps.append(_step(get_step("verbose_divide_both", lang,
                                         divisor=sympy_to_text(coeff),
                                         left="x",
                                         right=sympy_to_text(right_val))))

        # Step: Final answer
        if len(solutions) == 1:
            steps.append(_step(get_step("eq_solution", lang, solution=f"x = {sympy_to_text(solutions[0])}")))
            answer = f"x = {sympy_to_text(solutions[0])}"
        else:
            sol_strs = [f"x = {sympy_to_text(s)}" for s in solutions]
            steps.append(_step(get_step("eq_solution", lang, solution=",  ".join(sol_strs))))
            answer = ",  ".join(sol_strs)
    else:
        # Non-verbose mode (original behavior, condensed steps)
        steps.append(_step(get_step("eq_start", lang, equation=problem)))

        expanded_lhs = expand(lhs - rhs)
        steps.append(_step(get_step("expr_simplify", lang,
                                    original=f"{sympy_to_text(lhs)} - {sympy_to_text(rhs)}",
                                    result=f"{sympy_to_text(expanded_lhs)} = 0")))

        # Extract coefficient and constant
        coeff = expanded_lhs.coeff(x, 1)
        constant = expanded_lhs.coeff(x, 0)

        if coeff != 0:
            if constant > 0:
                steps.append(_step(get_step("eq_move_term", lang,
                                            term=f"{sympy_to_text(constant)}",
                                            direction=get_step("eq_move_right", lang),
                                            result=f"{sympy_to_text(coeff)}·x = {sympy_to_text(-constant)}")))
            elif constant < 0:
                steps.append(_step(get_step("eq_move_term", lang,
                                            term=f"{sympy_to_text(constant)}",
                                            direction=get_step("eq_move_right", lang),
                                            result=f"{sympy_to_text(coeff)}·x = {sympy_to_text(-constant)}")))

            if coeff != 1:
                steps.append(_step(get_step("eq_divide", lang,
                                            divisor=sympy_to_text(coeff),
                                            result=f"x = {sympy_to_text(-constant)} / {sympy_to_text(coeff)}")))

        # Final answer
        if len(solutions) == 1:
            steps.append(_step(get_step("eq_solution", lang, solution=f"x = {sympy_to_text(solutions[0])}")))
            answer = f"x = {sympy_to_text(solutions[0])}"
        else:
            sol_strs = [f"x = {sympy_to_text(s)}" for s in solutions]
            steps.append(_step(get_step("eq_solution", lang, solution=",  ".join(sol_strs))))
            answer = ",  ".join(sol_strs)

    return Solution(problem, get_method_name("linear_equation", lang),
                    "linear_equation", steps, answer)


# ═══════════════════════════════════════════════════════════════════════════
#  LINEAR EQUATION SOLVER — EASY MODE (fraction clearing)
# ═══════════════════════════════════════════════════════════════════════════

def _has_fractions(lhs, rhs):
    """Check if equation has fractional coefficients."""
    x = symbols('x')
    diff = expand(lhs - rhs)
    # Check if any coefficient is a Rational with denominator > 1
    for term in diff.as_ordered_terms():
        coeff = term.coeff(x, 0) if term.is_number else term.coeff(x, 1)
        if isinstance(coeff, Rational) and coeff.q != 1:
            return True
    return False


def _get_denominators(lhs, rhs):
    """Get all unique denominators from the equation."""
    x = symbols('x')
    diff = expand(lhs - rhs)
    denoms = set()
    for term in diff.as_ordered_terms():
        # Get the rational coefficient
        if term.is_number:
            coeff = Rational(term)
        else:
            coeff = Rational(term.as_independent(x)[0])
        if isinstance(coeff, Rational):
            denoms.add(coeff.q)
    denoms.discard(1)  # Remove trivial denominators
    return denoms


def _compute_lcd(denominators):
    """Compute LCM of a set of denominators."""
    result = 1
    for d in denominators:
        result = result * d // math.gcd(result, d)
    return result


def solve_linear_equation_easy(lhs, rhs, lang: str = "pl") -> Solution:
    """
    Solve a linear equation by first clearing fractions (LCD method).
    If no fractions are detected, falls back to standard solving.

    Example: x/3 + x/6 = 5
      LCD(3,6) = 6
      6·(x/3 + x/6) = 6·5  →  2x + x = 30  →  x = 10
    """
    x = symbols("x")
    problem = f"{sympy_to_text(lhs)} = {sympy_to_text(rhs)}"
    steps = []

    if _has_fractions(lhs, rhs):
        denoms = _get_denominators(lhs, rhs)
        if denoms:
            lcd = _compute_lcd(denoms)

            steps.append(_step(get_step("eq_start", lang, equation=problem)))
            steps.append(_step(get_step("frac_clear_detect", lang)))
            steps.append(_step(get_step("frac_clear_lcd", lang, lcd=lcd)))

            # Show multiplication step
            new_lhs = cancel(lhs * lcd)
            new_rhs = cancel(rhs * lcd)
            steps.append(_step(get_step("frac_clear_multiply", lang,
                                         lcd=lcd,
                                         result=f"{sympy_to_text(new_lhs)} = {sympy_to_text(new_rhs)}")))

            # Show simplified equation
            new_lhs_expanded = expand(new_lhs)
            new_rhs_expanded = expand(new_rhs)
            steps.append(_step(get_step("frac_clear_simplified", lang,
                                         result=f"{sympy_to_text(new_lhs_expanded)} = {sympy_to_text(new_rhs_expanded)}")))

            # Now solve the cleared equation (non-verbose for inner solve)
            inner = solve_linear_equation(new_lhs_expanded, new_rhs_expanded, lang, verbose=False)
            # Append inner steps (skip the eq_start step since we already showed it)
            for step in inner.steps[1:]:
                steps.append(step)

            return Solution(problem, get_method_name("linear_equation_easy", lang),
                            "linear_equation_easy", steps, inner.answer)

    # No fractions — fall back to standard solve
    return solve_linear_equation(lhs, rhs, lang, verbose=False)


# ═══════════════════════════════════════════════════════════════════════════
#  QUADRATIC EQUATION SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_quadratic(lhs, rhs, lang: str = "pl", method: str = "formula") -> Solution:
    """
    Solve a quadratic equation ax² + bx + c = 0.

    Args:
        method: "formula" (quadratic formula), "factoring", or "complete_square"
    """
    x = symbols("x")
    problem = f"{sympy_to_text(lhs)} = {sympy_to_text(rhs)}"
    steps = []

    # Bring to standard form
    standard = expand(lhs - rhs)
    a = standard.coeff(x, 2)
    b = standard.coeff(x, 1)
    c = standard.coeff(x, 0)

    steps.append(_step(get_step("quad_standard", lang, equation=f"{sympy_to_text(standard)} = 0")))
    steps.append(_step(get_step("quad_identify", lang, a=sympy_to_text(a), b=sympy_to_text(b), c=sympy_to_text(c))))

    # Discriminant
    delta = b**2 - 4*a*c
    steps.append(_step(get_step("quad_discriminant", lang,
                                b=sympy_to_text(b), a=sympy_to_text(a), c=sympy_to_text(c),
                                delta=sympy_to_text(delta))))

    if delta < 0:
        steps.append(_step(get_step("quad_delta_negative", lang)))
        answer = "Brak pierwiastków rzeczywistych" if lang == "pl" else "No real roots"
        return Solution(problem, get_method_name("quadratic_equation", lang),
                        "quadratic_equation", steps, answer)

    # Solve using SymPy for exact results
    solutions = solve(Eq(standard, 0), x)

    if delta == 0:
        steps.append(_step(get_step("quad_delta_zero", lang)))
        steps.append(_step(get_step("quad_single_root", lang, x0=sympy_to_text(solutions[0]))))
        answer = f"x₀ = {sympy_to_text(solutions[0])}"
    else:
        steps.append(_step(get_step("quad_delta_positive", lang)))
        x1, x2 = sorted(solutions, key=lambda s: float(s), reverse=True)
        steps.append(_step(get_step("quad_roots", lang,
                                    x1=sympy_to_text(x1), x2=sympy_to_text(x2))))
        answer = f"x₁ = {sympy_to_text(x1)},  x₂ = {sympy_to_text(x2)}"

    return Solution(problem, get_method_name("quadratic_equation", lang),
                    "quadratic_equation", steps, answer)


# ═══════════════════════════════════════════════════════════════════════════
#  INEQUALITY SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_inequality(lhs, op: str, rhs, lang: str = "pl") -> Solution:
    """
    Solve a linear inequality like 2x + 5 > 13.
    """
    x = symbols("x")
    problem = f"{sympy_to_text(lhs)} {op} {sympy_to_text(rhs)}"
    steps = []

    steps.append(_step(get_step("ineq_start", lang, inequality=problem)))

    # Build SymPy relational
    op_map = {"=": Eq, ">": lambda l, r: l > r, "<": lambda l, r: l < r,
              ">=": lambda l, r: l >= r, "≤": lambda l, r: l <= r,
              "!=": lambda l, r: l != r}

    # Move all terms to left side
    if op == "=":
        expr = lhs - rhs
        rel = Eq(expr, 0)
    else:
        expr = expand(lhs - rhs)
        op_fn = op_map.get(op, op_map[">"])
        if op in ("=", "!="):
            rel = op_fn(expr, 0)
        else:
            rel = op_fn(expr, 0)

    # Try to solve with SymPy
    try:
        if isinstance(rel, Eq):
            solutions = solve(rel, x)
            if not solutions:
                answer = "Brak rozwiązań" if lang == "pl" else "No solution"
            else:
                answer = ", ".join(f"x = {sympy_to_text(s)}" for s in solutions)
        else:
            result_set = solve_univariate_inequality(rel, x, relational=False)
            answer = f"x ∈ {result_set}"
            steps.append(_step(f"{result_set}"))
    except Exception:
        # Manual solving for simple linear inequalities
        coeff = expr.coeff(x, 1)
        constant = expr.coeff(x, 0)
        target = -constant

        steps.append(_step(get_step("ineq_move_term", lang,
                                    term=sympy_to_text(constant),
                                    result=f"{sympy_to_text(coeff)}·x {op} {sympy_to_text(target)}")))

        if coeff < 0:
            steps.append(_step(get_step("ineq_divide_negative", lang,
                                        result=f"x {op} {sympy_to_text(target / coeff)}")))
            answer = f"x {op} {sympy_to_text(target / coeff)}"
        elif coeff != 1:
            steps.append(_step(get_step("ineq_divide", lang,
                                        divisor=sympy_to_text(coeff),
                                        result=f"x {op} {sympy_to_text(target / coeff)}")))
            answer = f"x {op} {sympy_to_text(target / coeff)}"
        else:
            answer = f"x {op} {sympy_to_text(target)}"

    steps.append(_step(get_step("ineq_solution", lang, solution=answer)))

    return Solution(problem, get_method_name("inequality", lang),
                    "inequality", steps, answer)


# ═══════════════════════════════════════════════════════════════════════════
#  POWER / ROOT SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_power(base, exponent, lang: str = "pl") -> Solution:
    """Evaluate base^exponent step by step."""
    problem = f"{sympy_to_text(base)}^{sympy_to_text(exponent)}"
    steps = []

    result = base ** exponent
    steps.append(_step(get_step("power_step", lang,
                                base=sympy_to_text(base), exp=sympy_to_text(exponent),
                                result=sympy_to_text(result))))

    return Solution(problem, get_method_name("power", lang),
                    "power", steps, sympy_to_text(result))


def solve_root(value, lang: str = "pl") -> Solution:
    """Evaluate √value step by step."""
    problem = f"√{sympy_to_text(value)}"
    steps = []

    result = sqrt(value)
    simplified = simplify(result)

    steps.append(_step(get_step("root_step", lang,
                                value=sympy_to_text(value),
                                result=sympy_to_text(simplified))))

    return Solution(problem, get_method_name("root", lang),
                    "root", steps, sympy_to_text(simplified))


# ═══════════════════════════════════════════════════════════════════════════
#  GCD / LCM SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_gcd_lcm(a: int, b: int, lang: str = "pl") -> Solution:
    """Find GCD and LCM of two integers."""
    problem = f"NWD({a}, {b}) i NWW({a}, {b})" if lang == "pl" else f"GCD({a}, {b}) and LCM({a}, {b})"
    steps = []

    # Prime factorization
    fa = _prime_factorization(a)
    fb = _prime_factorization(b)
    steps.append(_step(get_step("gcd_prime_factors_a", lang, value=a, factors=fa)))
    steps.append(_step(get_step("gcd_prime_factors_a", lang, value=b, factors=fb)))

    gcd_val = math.gcd(abs(a), abs(b))
    lcm_val = abs(a * b) // gcd_val if gcd_val != 0 else 0

    steps.append(_step(get_step("gcd_result", lang, a=a, b=b, result=gcd_val)))
    steps.append(_step(get_step("lcm_result", lang, a=a, b=b, result=lcm_val)))

    answer = f"NWD = {gcd_val}, NWW = {lcm_val}" if lang == "pl" else f"GCD = {gcd_val}, LCM = {lcm_val}"
    return Solution(problem, get_method_name("gcd_lcm", lang), "gcd_lcm", steps, answer)


def _prime_factorization(n: int) -> str:
    """Return a string like '2³ · 3 · 5²' for prime factorization."""
    if n <= 1:
        return str(n)
    factors = {}
    d = 2
    num = abs(n)
    while d * d <= num:
        while num % d == 0:
            factors[d] = factors.get(d, 0) + 1
            num //= d
        d += 1
    if num > 1:
        factors[num] = factors.get(num, 0) + 1

    parts = []
    for p in sorted(factors.keys()):
        if factors[p] == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{factors[p]}")
    return " · ".join(parts) if parts else "1"


# ═══════════════════════════════════════════════════════════════════════════
#  EXPRESSION SOLVERS
# ═══════════════════════════════════════════════════════════════════════════

def solve_simplify(expr, lang: str = "pl") -> Solution:
    """Simplify an algebraic expression."""
    problem = sympy_to_text(expr)
    result = simplify(expr)
    steps = [_step(get_step("expr_simplify", lang, original=problem, result=sympy_to_text(result)))]
    return Solution(problem, get_method_name("expression_simplify", lang),
                    "expression_simplify", steps, sympy_to_text(result))


def solve_expand(expr, lang: str = "pl") -> Solution:
    """Expand brackets in an expression."""
    problem = sympy_to_text(expr)
    result = expand(expr)
    steps = [_step(get_step("expr_expand", lang, original=problem, result=sympy_to_text(result)))]
    return Solution(problem, get_method_name("expression_expand", lang),
                    "expression_expand", steps, sympy_to_text(result))


def solve_factor(expr, lang: str = "pl") -> Solution:
    """Factor an expression."""
    problem = sympy_to_text(expr)
    result = factor(expr)
    steps = [_step(get_step("expr_factor", lang, original=problem, result=sympy_to_text(result)))]
    return Solution(problem, get_method_name("expression_factor", lang),
                    "expression_factor", steps, sympy_to_text(result))


# ═══════════════════════════════════════════════════════════════════════════
#  STATISTICS SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_statistics(values: List[float], lang: str = "pl") -> Solution:
    """Calculate mean, median, mode, and range."""
    problem = f"Dane: {', '.join(str(v) for v in values)}"
    steps = []

    # Mean
    mean_val = sum(values) / len(values)
    vals_str = " + ".join(str(v) for v in values)
    steps.append(_step(get_step("stat_mean", lang,
                                values=vals_str, count=len(values), result=round(mean_val, 2))))

    # Median
    sorted_data = sorted(values)
    steps.append(_step(get_step("stat_median_sort", lang,
                                sorted_data=", ".join(str(v) for v in sorted_data))))

    n = len(sorted_data)
    if n % 2 == 0:
        m1 = sorted_data[n // 2 - 1]
        m2 = sorted_data[n // 2]
        median_val = (m1 + m2) / 2
        steps.append(_step(get_step("stat_median_even", lang,
                                    middle1=m1, middle2=m2, result=round(median_val, 2))))
    else:
        median_val = sorted_data[n // 2]
        steps.append(_step(get_step("stat_median_odd", lang, result=median_val)))

    # Mode
    from collections import Counter
    counts = Counter(values)
    max_count = max(counts.values())
    modes = [v for v, c in counts.items() if c == max_count]
    if max_count > 1:
        modes_str = ", ".join(str(m) for m in sorted(modes))
        steps.append(_step(get_step("stat_mode", lang, result=modes_str, count=max_count)))

    # Range
    range_val = max(values) - min(values)
    steps.append(_step(get_step("stat_range", lang,
                                max_val=max(values), min_val=min(values), result=range_val)))

    answer = f"Średnia={round(mean_val, 2)}, Mediana={round(median_val, 2)}, Rozstęp={range_val}"
    if lang == "en":
        answer = f"Mean={round(mean_val, 2)}, Median={round(median_val, 2)}, Range={range_val}"

    return Solution(problem, get_method_name("statistics", lang), "statistics", steps, answer)


# ═══════════════════════════════════════════════════════════════════════════
#  GEOMETRY SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_pythagoras(a=None, b=None, c=None, lang: str = "pl") -> Solution:
    """
    Solve a Pythagorean theorem problem.
    Pass the two known sides; the third is calculated.
    """
    x = symbols("x")
    known = {"a": a, "b": b, "c": c}
    unknown = [k for k, v in known.items() if v is None]

    if len(unknown) != 1:
        return Solution("?", get_method_name("geometry", lang), "geometry",
                        [_step("Need exactly two known sides")], "?", is_valid=False)

    steps = [_step(get_step("geo_pythagoras", lang))]

    if unknown[0] == "c":
        result = sqrt(a**2 + b**2)
        formula = f"√({a}² + {b}²)"
        problem = f"c = √({a}² + {b}²)"
        steps.append(_step(f"c = √({a}² + {b}²) = √({a**2} + {b**2}) = √{a**2 + b**2}"))
    elif unknown[0] == "a":
        result = sqrt(c**2 - b**2)
        problem = f"a = √({c}² - {b}²)"
        steps.append(_step(f"a = √({c}² - {b}²) = √({c**2} - {b**2}) = √{c**2 - b**2}"))
    else:  # b
        result = sqrt(c**2 - a**2)
        problem = f"b = √({c}² - {a}²)"
        steps.append(_step(f"b = √({c}² - {a}²) = √({c**2} - {a**2}) = √{c**2 - a**2}"))

    answer = f"{unknown[0]} = {sympy_to_text(simplify(result))}"
    steps.append(_step(answer))

    return Solution(problem, get_method_name("geometry", lang), "geometry", steps, answer)


def solve_triangle_area(base: float, height: float, lang: str = "pl") -> Solution:
    """Calculate area of a triangle: A = (base · height) / 2."""
    problem = f"Pole trójkąta: a = {base}, h = {height}"
    steps = []
    area = (base * height) / 2
    steps.append(_step(get_step("geo_area", lang,
                                formula=f"({base} · {height}) / 2",
                                result=area)))
    return Solution(problem, get_method_name("geometry", lang), "geometry", steps, str(area))


def solve_rectangle(length: float, width: float, lang: str = "pl") -> Solution:
    """Calculate area and perimeter of a rectangle."""
    problem = f"Prostokąt: a = {length}, b = {width}"
    steps = []
    area = length * width
    perimeter = 2 * (length + width)
    steps.append(_step(get_step("geo_area", lang, formula=f"{length} · {width}", result=area)))
    steps.append(_step(get_step("geo_perimeter", lang, formula=f"2 · ({length} + {width})", result=perimeter)))
    answer = f"Pole = {area}, Obwód = {perimeter}" if lang == "pl" else f"Area = {area}, Perimeter = {perimeter}"
    return Solution(problem, get_method_name("geometry", lang), "geometry", steps, answer)


def solve_circle(radius: float, lang: str = "pl") -> Solution:
    """Calculate area and circumference of a circle."""
    problem = f"Koło: r = {radius}"
    steps = []
    area = round(3.14159265 * radius**2, 4)
    circ = round(2 * 3.14159265 * radius, 4)
    steps.append(_step(get_step("geo_circle_area", lang, r=radius, result=area)))
    steps.append(_step(get_step("geo_circle_circumference", lang, r=radius, result=circ)))
    answer = f"Pole = {area}, Obwód = {circ}" if lang == "pl" else f"Area = {area}, Circumference = {circ}"
    return Solution(problem, get_method_name("geometry", lang), "geometry", steps, answer)


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM OF EQUATIONS SOLVER
# ═══════════════════════════════════════════════════════════════════════════

def solve_system(eq1_lhs, eq1_rhs, eq2_lhs, eq2_rhs, lang: str = "pl") -> Solution:
    """Solve a system of two linear equations."""
    x, y = symbols("x y")
    problem = f"({sympy_to_text(eq1_lhs)} = {sympy_to_text(eq1_rhs)}, {sympy_to_text(eq2_lhs)} = {sympy_to_text(eq2_rhs)})"
    steps = []

    steps.append(_step(get_step("sys_start", lang)))
    steps.append(_step(get_step("sys_equation_label", lang, num="1",
                                equation=f"{sympy_to_text(eq1_lhs)} = {sympy_to_text(eq1_rhs)}")))
    steps.append(_step(get_step("sys_equation_label", lang, num="2",
                                equation=f"{sympy_to_text(eq2_lhs)} = {sympy_to_text(eq2_rhs)}")))

    solution = solve([Eq(eq1_lhs, eq1_rhs), Eq(eq2_lhs, eq2_rhs)], [x, y])

    if not solution:
        answer = "Brak rozwiązań" if lang == "pl" else "No solution"
        steps.append(_step(answer))
    elif isinstance(solution, dict):
        answer = ", ".join(f"{k} = {v}" for k, v in solution.items())
        steps.append(_step(get_step("sys_solution", lang, solution=answer)))
    elif isinstance(solution, list) and len(solution) == 1:
        sol = solution[0]
        if isinstance(sol, tuple):
            answer = f"x = {sol[0]}, y = {sol[1]}"
        else:
            answer = str(sol)
        steps.append(_step(get_step("sys_solution", lang, solution=answer)))
    else:
        answer = str(solution)
        steps.append(_step(get_step("sys_solution", lang, solution=answer)))

    return Solution(problem, get_method_name("system_of_equations", lang),
                    "system_of_equations", steps, answer)


# ═══════════════════════════════════════════════════════════════════════════
#  AUTO-DETECT SOLVER (main entry point)
# ═══════════════════════════════════════════════════════════════════════════

def _solve_single_equation(equation_tuple, lang: str = "pl", verbose: bool = False, easy_mode: bool = False) -> List[Solution]:
    """Solve a single equation (lhs, op, rhs) and return a list of solutions."""
    lhs, op, rhs = equation_tuple
    solutions = []

    if op != "=":
        sol = solve_inequality(lhs, op, rhs, lang)
        solutions.append(sol)
        return solutions

    x = symbols("x")
    diff = expand(lhs - rhs)
    try:
        deg = degree(diff, x)
    except (AttributeError, ValueError, TypeError):
        deg = 0

    if deg == 2:
        sol = solve_quadratic(lhs, rhs, lang)
        solutions.append(sol)
    elif deg == 1:
        if easy_mode:
            sol = solve_linear_equation_easy(lhs, rhs, lang)
        else:
            sol = solve_linear_equation(lhs, rhs, lang, verbose=verbose)
        solutions.append(sol)
    elif deg == 0:
        if diff == 0:
            answer = get_step("eq_infinite_solutions", lang)
            solutions.append(Solution(
                f"{sympy_to_text(lhs)} = {sympy_to_text(rhs)}",
                get_method_name("arithmetic", lang), "arithmetic",
                [_step(answer)], answer,
            ))
        else:
            answer = get_step("eq_no_solution", lang)
            solutions.append(Solution(
                f"{sympy_to_text(lhs)} = {sympy_to_text(rhs)}",
                get_method_name("arithmetic", lang), "arithmetic",
                [_step(answer)], answer,
            ))
    else:
        sol = solve(Eq(lhs, rhs), x)
        answer = ", ".join(f"x = {sympy_to_text(s)}" for s in sol)
        solutions.append(Solution(
            f"{sympy_to_text(lhs)} = {sympy_to_text(rhs)}",
            get_method_name("linear_equation", lang), "linear_equation",
            [_step(get_step("eq_solution", lang, solution=answer))], answer,
        ))

    return solutions


def solve_problem(
    expressions: list,
    equations: list,
    context: dict,
    lang: str = "pl",
    verbose: bool = False,
    easy_mode: bool = False,
) -> List[Solution]:
    """
    Given parsed exercise data, determine the problem type and solve it.

    Args:
        expressions: list of parsed SymPy expressions
        equations: list of (lhs, op, rhs) tuples
        context: dict from math_parser.extract_problem_context
        lang: "pl" or "en"

    Returns:
        List of Solution objects (usually 1, but could be more for systems or multi-part exercises)
    """
    solutions = []

    # ── Multiple independent equations — solve each one ────────────────
    if len(equations) > 2:
        for eq in equations:
            sols = _solve_single_equation(eq, lang, verbose=verbose, easy_mode=easy_mode)
            solutions.extend(sols)
        return solutions

    # ── System of equations (exactly 2) ────────────────────────────────
    if len(equations) == 2:
        eq1_lhs, eq1_op, eq1_rhs = equations[0]
        eq2_lhs, eq2_op, eq2_rhs = equations[1]
        if eq1_op == "=" and eq2_op == "=":
            sol = solve_system(eq1_lhs, eq1_rhs, eq2_lhs, eq2_rhs, lang)
            solutions.append(sol)
            return solutions

    # ── Single equation ────────────────────────────────────────────────
    if len(equations) == 1:
        sols = _solve_single_equation(equations[0], lang, verbose=verbose, easy_mode=easy_mode)
        solutions.extend(sols)
        return solutions

    # ── No equations — handle expressions and context ───────────────────

    # Statistics
    if context.get("has_statistics") and expressions:
        # Try to extract a list of numbers
        numbers = context.get("numbers", [])
        if len(numbers) >= 3:
            float_nums = [float(n) for n in numbers]
            sol = solve_statistics(float_nums, lang)
            solutions.append(sol)
            return solutions

    # Fractions — try to detect fraction operations
    # (This is simplified; real OCR would give clearer signals)

    # Pure arithmetic
    for expr in expressions:
        if expr.free_symbols:
            # Has variables — might need simplification
            sol = solve_simplify(expr, lang)
            solutions.append(sol)
        else:
            sol = solve_arithmetic(expr, lang)
            solutions.append(sol)

    # If no expressions were parsed, report failure
    if not solutions:
        raw = context.get("problem_text", "")
        sol = Solution(
            problem=raw,
            method="???",
            method_key="unknown",
            steps=[_step("Nie udało się rozpoznać zadania." if lang == "pl" else "Could not recognize the problem.")],
            answer="Brak danych" if lang == "pl" else "No data",
            is_valid=False,
        )
        solutions.append(sol)

    return solutions
