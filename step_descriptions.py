"""
Polish and English step descriptions for the solver.
Each solver method has localized text for every step.
"""


# ── Method names ───────────────────────────────────────────────────────────

METHOD_NAMES = {
    "pl": {
        "arithmetic": "Obliczenia arytmetyczne",
        "fraction_simplify": "Skracanie ułamka",
        "fraction_add": "Dodawanie ułamków",
        "fraction_sub": "Odejmowanie ułamków",
        "fraction_mul": "Mnożenie ułamków",
        "fraction_div": "Dzielenie ułamków",
        "percentage": "Obliczanie procentów",
        "linear_equation": "Równanie liniowe",
        "quadratic_equation": "Równanie kwadratowe",
        "quadratic_factoring": "Rozkład na czynniki",
        "quadratic_formula": "Wzór kwadratowy",
        "quadratic_complete_square": "Doprowadzanie do kwadratu idealnego",
        "inequality": "Nierówność",
        "power": "Potęgowanie",
        "root": "Pierwiastkowanie",
        "absolute_value": "Wartość bezwzględna",
        "gcd_lcm": "NWW i NWD",
        "unit_conversion": "Przeliczanie jednostek",
        "expression_simplify": "Upraszczanie wyrażenia",
        "expression_expand": "Rozwinięcie nawiasów",
        "expression_factor": "Rozkład na czynniki",
        "system_of_equations": "Układ równań",
        "statistics": "Statystyka",
        "geometry": "Geometria",
    },
    "en": {
        "arithmetic": "Arithmetic",
        "fraction_simplify": "Simplify fraction",
        "fraction_add": "Adding fractions",
        "fraction_sub": "Subtracting fractions",
        "fraction_mul": "Multiplying fractions",
        "fraction_div": "Dividing fractions",
        "percentage": "Percentage calculation",
        "linear_equation": "Linear equation",
        "quadratic_equation": "Quadratic equation",
        "quadratic_factoring": "Factoring",
        "quadratic_formula": "Quadratic formula",
        "quadratic_complete_square": "Completing the square",
        "inequality": "Inequality",
        "power": "Exponentiation",
        "root": "Root extraction",
        "absolute_value": "Absolute value",
        "gcd_lcm": "GCD and LCM",
        "unit_conversion": "Unit conversion",
        "expression_simplify": "Simplify expression",
        "expression_expand": "Expand brackets",
        "expression_factor": "Factor expression",
        "system_of_equations": "System of equations",
        "statistics": "Statistics",
        "geometry": "Geometry",
    },
}


# ── Step templates ─────────────────────────────────────────────────────────
# Each key maps to a dict with "pl" and "en" versions.
# {var} placeholders are filled at runtime.

STEPS = {
    # ── Arithmetic ─────────────────────────────────────────────────────
    "arith_problem": {
        "pl": "Mamy do obliczenia: {expr}",
        "en": "We need to calculate: {expr}",
    },
    "arith_result": {
        "pl": "Wynik: {result}",
        "en": "Result: {result}",
    },
    # ── Fractions ──────────────────────────────────────────────────────
    "frac_find_lcd": {
        "pl": "Szukamy najmniejszej wspólnej mianowników (NWW): {lcd}",
        "en": "Finding the least common denominator (LCD): {lcd}",
    },
    "frac_convert": {
        "pl": "Przekształcamy ułamki: {converted}",
        "en": "Converting fractions: {converted}",
    },
    "frac_simplify_gcd": {
        "pl": "Skracamy przez NWD({num}, {den}) = {gcd}",
        "en": "Simplifying by GCD({num}, {den}) = {gcd}",
    },
    "frac_simplify_result": {
        "pl": "Ułamek po skróceniu: {result}",
        "en": "Simplified fraction: {result}",
    },
    "frac_add_step": {
        "pl": "Dodajemy: {a} + {b} = {result}",
        "en": "Adding: {a} + {b} = {result}",
    },
    "frac_sub_step": {
        "pl": "Odejmujemy: {a} - {b} = {result}",
        "en": "Subtracting: {a} - {b} = {result}",
    },
    "frac_mul_step": {
        "pl": "Mnożymy: {a} · {b} = {result}",
        "en": "Multiplying: {a} · {b} = {result}",
    },
    "frac_div_step": {
        "pl": "Dzielimy: {a} : {b} = {a} · {reciprocal} = {result}",
        "en": "Dividing: {a} ÷ {b} = {a} · {reciprocal} = {result}",
    },
    "frac_to_mixed": {
        "pl": "Zamieniamy na ułamek mieszany: {result}",
        "en": "Converting to mixed number: {result}",
    },
    # ── Percentage ─────────────────────────────────────────────────────
    "pct_formula": {
        "pl": "Wzór: {part} = {rate}% · {whole}",
        "en": "Formula: {part} = {rate}% · {whole}",
    },
    "pct_decimal": {
        "pl": "Zamieniamy procent na ułamek dziesiętny: {rate}% = {decimal}",
        "en": "Converting percentage to decimal: {rate}% = {decimal}",
    },
    "pct_multiply": {
        "pl": "Mnożymy: {decimal} · {whole} = {result}",
        "en": "Multiplying: {decimal} · {whole} = {result}",
    },
    "pct_result": {
        "pl": "Wynik: {result} ({part_name} z {whole})",
        "en": "Result: {result} ({part_name} of {whole})",
    },
    # ── Linear equations ───────────────────────────────────────────────
    "eq_start": {
        "pl": "Równanie: {equation}",
        "en": "Equation: {equation}",
    },
    "eq_move_term": {
        "pl": "Przenosimy {term} {direction}: {result}",
        "en": "Moving {term} {direction}: {result}",
    },
    "eq_move_left": {
        "pl": "na lewą stronę",
        "en": "to the left side",
    },
    "eq_move_right": {
        "pl": "na prawą stronę",
        "en": "to the right side",
    },
    "eq_combine": {
        "pl": "Łączymy wyrażenia: {result}",
        "en": "Combining terms: {result}",
    },
    "eq_divide": {
        "pl": "Dzielimy obie strony przez {divisor}: {result}",
        "en": "Dividing both sides by {divisor}: {result}",
    },
    "eq_multiply": {
        "pl": "Mnożymy obie strony przez {multiplier}: {result}",
        "en": "Multiplying both sides by {multiplier}: {result}",
    },
    "eq_solution": {
        "pl": "Rozwiązanie: {solution}",
        "en": "Solution: {solution}",
    },
    "eq_no_solution": {
        "pl": "Równanie nie ma rozwiązań",
        "en": "The equation has no solution",
    },
    "eq_infinite_solutions": {
        "pl": "Nieskończenie wiele rozwiązań (tożsamość)",
        "en": "Infinitely many solutions (identity)",
    },
    # ── Quadratic equations ────────────────────────────────────────────
    "quad_standard": {
        "pl": "Równanie w postaci_kwadratowej: {equation}",
        "en": "Equation in standard form: {equation}",
    },
    "quad_identify": {
        "pl": "Współczynniki: a = {a}, b = {b}, c = {c}",
        "en": "Coefficients: a = {a}, b = {b}, c = {c}",
    },
    "quad_discriminant": {
        "pl": "Obliczamy deltę: Δ = b² - 4ac = {b}² - 4·{a}·{c} = {delta}",
        "en": "Calculating discriminant: Δ = b² - 4ac = {b}² - 4·{a}·{c} = {delta}",
    },
    "quad_delta_positive": {
        "pl": "Δ > 0 — dwa pierwiastki:",
        "en": "Δ > 0 — two roots:",
    },
    "quad_delta_zero": {
        "pl": "Δ = 0 — jeden pierwiastek podwójny:",
        "en": "Δ = 0 — one double root:",
    },
    "quad_delta_negative": {
        "pl": "Δ < 0 — brak pierwiastków rzeczywistych",
        "en": "Δ < 0 — no real roots",
    },
    "quad_roots": {
        "pl": "x₁ = {x1},  x₂ = {x2}",
        "en": "x₁ = {x1},  x₂ = {x2}",
    },
    "quad_single_root": {
        "pl": "x₀ = {x0}",
        "en": "x₀ = {x0}",
    },
    "quad_factoring_step": {
        "pl": "Szukamy dwóch liczb, których iloczyn to {product}, a suma to {sum}",
        "en": "Finding two numbers whose product is {product} and sum is {sum}",
    },
    "quad_factored": {
        "pl": "Czynniki: (x {factor1})(x {factor2}) = 0",
        "en": "Factors: (x {factor1})(x {factor2}) = 0",
    },
    "quad_zero_product": {
        "pl": "Z twierdzenia o iloczynie zerowym: {result}",
        "en": "By zero product property: {result}",
    },
    # ── Inequalities ───────────────────────────────────────────────────
    "ineq_start": {
        "pl": "Nierówność: {inequality}",
        "en": "Inequality: {inequality}",
    },
    "ineq_move_term": {
        "pl": "Przenosimy {term}: {result}",
        "en": "Moving {term}: {result}",
    },
    "ineq_divide": {
        "pl": "Dzielimy obie strony przez {divisor}: {result}",
        "en": "Dividing both sides by {divisor}: {result}",
    },
    "ineq_divide_negative": {
        "pl": "Dzielimy przez liczbę ujemną — odwracamy znak nierówności: {result}",
        "en": "Dividing by a negative number — flipping inequality sign: {result}",
    },
    "ineq_solution": {
        "pl": "Rozwiązanie: {solution}",
        "en": "Solution: {solution}",
    },
    # ── Powers and roots ───────────────────────────────────────────────
    "power_step": {
        "pl": "{base}^{exp} = {result}",
        "en": "{base}^{exp} = {result}",
    },
    "power_expand": {
        "pl": "Rozpisujemy: {base}^{exp} = {expansion} = {result}",
        "en": "Expanding: {base}^{exp} = {expansion} = {result}",
    },
    "root_step": {
        "pl": "√{value} = {result}",
        "en": "√{value} = {result}",
    },
    "root_simplify": {
        "pl": "Rozkładamy {value} na czynniki: {value} = {factorization}",
        "en": "Factoring {value}: {value} = {factorization}",
    },
    # ── GCD / LCM ─────────────────────────────────────────────────────
    "gcd_prime_factors_a": {
        "pl": "Rozkład {value} na czynniki pierwsze: {factors}",
        "en": "Prime factorization of {value}: {factors}",
    },
    "gcd_result": {
        "pl": "NWD({a}, {b}) = {result}",
        "en": "GCD({a}, {b}) = {result}",
    },
    "lcm_result": {
        "pl": "NWW({a}, {b}) = {result}",
        "en": "LCM({a}, {b}) = {result}",
    },
    # ── Expressions ────────────────────────────────────────────────────
    "expr_simplify": {
        "pl": "Upraszczamy: {original} = {result}",
        "en": "Simplifying: {original} = {result}",
    },
    "expr_expand": {
        "pl": "Rozwijamy nawiasy: {original} = {result}",
        "en": "Expanding: {original} = {result}",
    },
    "expr_factor": {
        "pl": "Wyciągamy wspólny czynnik: {original} = {result}",
        "en": "Factoring out common factor: {original} = {result}",
    },
    # ── Systems of equations ────────────────────────────────────────────
    "sys_start": {
        "pl": "Układ równań:",
        "en": "System of equations:",
    },
    "sys_equation_label": {
        "pl": "  ({num}) {equation}",
        "en": "  ({num}) {equation}",
    },
    "sys_substitute": {
        "pl": "Podstawiamy ({subst_eq}) do ({target_eq}): {result}",
        "en": "Substituting ({subst_eq}) into ({target_eq}): {result}",
    },
    "sys_eliminate": {
        "pl": "Eliminujemy: ({eq1}) {op} ({eq2}): {result}",
        "en": "Eliminating: ({eq1}) {op} ({eq2}): {result}",
    },
    "sys_solution": {
        "pl": "Rozwiązanie: {solution}",
        "en": "Solution: {solution}",
    },
    # ── Geometry ───────────────────────────────────────────────────────
    "geo_pythagoras": {
        "pl": "Twierdzenie Pitagorasa: a² + b² = c²",
        "en": "Pythagorean theorem: a² + b² = c²",
    },
    "geo_area": {
        "pl": "Pole: A = {formula} = {result}",
        "en": "Area: A = {formula} = {result}",
    },
    "geo_perimeter": {
        "pl": "Obwód: P = {formula} = {result}",
        "en": "Perimeter: P = {formula} = {result}",
    },
    "geo_circle_area": {
        "pl": "Pole koła: A = πr² = π·{r}² = {result}",
        "en": "Circle area: A = πr² = π·{r}² = {result}",
    },
    "geo_circle_circumference": {
        "pl": "Obwód koła: C = 2πr = 2π·{r} = {result}",
        "en": "Circle circumference: C = 2πr = 2π·{r} = {result}",
    },
    # ── Statistics ─────────────────────────────────────────────────────
    "stat_mean": {
        "pl": "Średnia: ({values}) / {count} = {result}",
        "en": "Mean: ({values}) / {count} = {result}",
    },
    "stat_median_sort": {
        "pl": "Sortujemy dane: {sorted_data}",
        "en": "Sorting data: {sorted_data}",
    },
    "stat_median_even": {
        "pl": "Liczba danych parzysta — mediana = ({middle1} + {middle2}) / 2 = {result}",
        "en": "Even count — median = ({middle1} + {middle2}) / 2 = {result}",
    },
    "stat_median_odd": {
        "pl": "Mediana = {result}",
        "en": "Median = {result}",
    },
    "stat_mode": {
        "pl": "Moda: {result} (występuje {count} razy)",
        "en": "Mode: {result} (appears {count} times)",
    },
    "stat_range": {
        "pl": "Rozstęp: {max_val} - {min_val} = {result}",
        "en": "Range: {max_val} - {min_val} = {result}",
    },
}


def get_step(step_key: str, lang: str = "pl", **kwargs) -> str:
    """
    Get a localized step description, formatted with kwargs.

    Args:
        step_key: Key from the STEPS dict.
        lang: "pl" or "en".
        **kwargs: Format arguments for the template string.

    Returns:
        Formatted step string.
    """
    templates = STEPS.get(step_key)
    if templates is None:
        return f"[Missing step: {step_key}]"
    template = templates.get(lang, templates.get("en", f"[{step_key}]"))
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def get_method_name(method_key: str, lang: str = "pl") -> str:
    """
    Get a localized method name.

    Args:
        method_key: Key from the METHOD_NAMES dict.
        lang: "pl" or "en".

    Returns:
        Method name string.
    """
    names = METHOD_NAMES.get(lang, METHOD_NAMES.get("en", {}))
    return names.get(method_key, method_key)
