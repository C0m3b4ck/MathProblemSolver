#!/usr/bin/env python3
"""
MathExerciseSolver — CLI entry point.
Takes an image of math exercises, performs OCR, solves step-by-step.

Usage:
    python main.py <image_path> [options]

Options:
    --lang {pl,en}      Solver language (default: pl)
    --pdf               Generate handwriting PDF output
    --no-latex          Skip Pix2Tex (use Tesseract only)
    --output PATH       Output path for PDF
    --status            Show OCR dependency status
    --gui               Launch the GUI instead
"""

import sys
import os
import argparse
import textwrap

# Ensure the project directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_LANGUAGE, OUTPUT_DIR


# ── Terminal colors ────────────────────────────────────────────────────────

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_solution(solution: Solution, index: int):
    """Pretty-print a solution to the terminal."""
    print()
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  #{index}  {solution.method}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.CYAN}  Problem: {solution.problem}{Colors.END}")
    print()

    for step in solution.steps:
        print(f"  {Colors.GREEN}→{Colors.END} {step.text}")
        if step.math:
            print(f"    {Colors.YELLOW}{step.math}{Colors.END}")

    print()
    print(f"  {Colors.BOLD}{Colors.GREEN}Odpowiedź: {solution.answer}{Colors.END}")
    print()


def print_no_solutions():
    """Print a message when no exercises could be solved."""
    print(f"\n{Colors.RED}Nie udało się rozwiązać żadnych zadań.{Colors.END}")
    print("Possible reasons:")
    print("  - Image quality too low")
    print("  - Exercises not recognized (try clearer image)")
    print("  - OCR dependencies not installed\n")


# ── Main pipeline ──────────────────────────────────────────────────────────

from dataclasses import dataclass, field


@dataclass
class ExerciseDiagnostic:
    """Diagnostic info for one exercise region."""
    region_index: int
    region_box: tuple = ()          # (x, y, w, h)
    text_ocr: str = ""              # Tesseract output
    math_latex: str = ""            # Pix2Tex output
    parsed_expressions: list = field(default_factory=list)
    parsed_equations: list = field(default_factory=list)
    unparsed: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    solutions: list = field(default_factory=list)
    error: str = ""


@dataclass
class PipelineResult:
    """Full result from the pipeline, including diagnostics."""
    solutions: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    image_path: str = ""
    num_regions: int = 0
    error: str = ""


def run_pipeline(
    image_path: str,
    lang: str = DEFAULT_LANGUAGE,
    use_latex: bool = True,
    generate_pdf: bool = False,
    pdf_output: str = None,
    verbose: bool = True,
    full_image: bool = False,
    solver_verbose: bool = False,
    easy_mode: bool = False,
) -> PipelineResult:
    """
    Run the full solve pipeline on an image.

    Args:
        image_path: Path to the input image.
        lang: Language for solver text ("pl" or "en").
        use_latex: Whether to use Pix2Tex for math OCR.
        generate_pdf: Whether to generate a PDF output.
        pdf_output: Custom PDF output path.
        verbose: Whether to print progress to terminal.

    Returns:
        PipelineResult with solutions and full diagnostics.
    """
    from preprocessing import segment_exercises, crop_region, save_crops, display_regions
    from ocr_engine import ocr_all_exercises, print_ocr_status
    from math_parser import parse_exercise
    from solver import solve_problem, Solution, Step
    from handwriting import render_solutions_pdf

    result = PipelineResult(image_path=image_path)

    # Step 1: Load and segment
    if verbose:
        print(f"\n{Colors.BOLD}Step 1: Loading and segmenting image...{Colors.END}")
        print(f"  File: {image_path}")

    try:
        img, regions, binary = segment_exercises(image_path, full_image=full_image)
    except Exception as e:
        msg = f"Failed to load image: {e}"
        result.error = msg
        if verbose:
            print(f"{Colors.RED}Error: {msg}{Colors.END}")
        return result

    result.num_regions = len(regions)

    if verbose:
        print(f"  Found {len(regions)} exercise region(s)")
        for i, r in enumerate(regions):
            print(f"    Region {i+1}: x={r[0]}, y={r[1]}, w={r[2]}, h={r[3]}")

    # Save crops for debugging
    crop_dir = os.path.join(OUTPUT_DIR, "crops")
    crop_paths = save_crops(img, regions, crop_dir)

    # Step 2: OCR each region
    if verbose:
        print(f"\n{Colors.BOLD}Step 2: Running OCR...{Colors.END}")

    crops = [crop_region(img, r) for r in regions]
    ocr_results = ocr_all_exercises(crops, use_latex=use_latex)

    # Step 3: Parse and solve each exercise
    if verbose:
        print(f"\n{Colors.BOLD}Step 3: Parsing and solving...{Colors.END}")

    for i, ocr_result in enumerate(ocr_results):
        text = ocr_result["text"]
        math_latex = ocr_result.get("math_latex") or ""

        diag = ExerciseDiagnostic(
            region_index=i,
            region_box=regions[i] if i < len(regions) else (),
            text_ocr=text,
            math_latex=math_latex,
        )

        if verbose:
            print(f"\n  --- Exercise {i + 1} ---")
            if text:
                print(f"  Text OCR:    {text[:200]}{'...' if len(text) > 200 else ''}")
            if math_latex:
                print(f"  Math OCR:    {math_latex}")

        # Parse
        parsed = parse_exercise(text, math_latex)
        diag.parsed_expressions = [str(e) for e in parsed["expressions"]]
        diag.parsed_equations = [(str(l), op, str(r)) for l, op, r in parsed["equations"]]
        diag.unparsed = parsed["unparsed"]
        diag.context = {k: v for k, v in parsed["context"].items() if k != "problem_text"}

        if verbose:
            if parsed["expressions"]:
                print(f"  Expressions: {[str(e) for e in parsed['expressions']]}")
            if parsed["equations"]:
                print(f"  Equations:   {[(str(l), op, str(r)) for l, op, r in parsed['equations']]}")
            if parsed["unparsed"]:
                print(f"  Unparsed:    {parsed['unparsed']}")

        # Solve
        solutions = solve_problem(
            parsed["expressions"],
            parsed["equations"],
            parsed["context"],
            lang=lang,
            verbose=solver_verbose,
            easy_mode=easy_mode,
        )

        diag.solutions = solutions
        result.diagnostics.append(diag)
        result.solutions.extend(solutions)

        if verbose:
            for sol in solutions:
                print_solution(sol, len(result.solutions))

    # Print summary
    if verbose:
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
        solved = sum(1 for s in result.solutions if s.is_valid)
        print(f"  Total: {len(result.solutions)} exercise(s), {solved} solved successfully")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

    # Step 4: Generate PDF if requested
    if generate_pdf and result.solutions:
        if verbose:
            print(f"\n{Colors.BOLD}Step 4: Generating handwriting PDF...{Colors.END}")
        pdf_path = render_solutions_pdf(result.solutions, pdf_output, lang=lang)
        if verbose:
            print(f"  Saved to: {pdf_path}")

    return result


# ── CLI argument parsing ──────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="MathExerciseSolver — Solve math exercises from images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
            python main.py exercises.png
            python main.py exercises.png --lang en --pdf
            python main.py --status
        """),
    )
    parser.add_argument("image", nargs="?", help="Path to the exercise image")
    parser.add_argument("--lang", choices=["pl", "en"], default=DEFAULT_LANGUAGE,
                        help="Solver language (default: pl)")
    parser.add_argument("--pdf", action="store_true",
                        help="Generate handwriting PDF output")
    parser.add_argument("--full-image", "-f", action="store_true",
                        help="Skip segmentation, send entire image to OCR (best for screenshots/typeset math)")
    parser.add_argument("--no-latex", action="store_true",
                        help="Skip Pix2Tex (use Tesseract only)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path for PDF")
    parser.add_argument("--status", action="store_true",
                        help="Show OCR dependency status and exit")
    parser.add_argument("--gui", action="store_true",
                        help="Launch the GUI")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress verbose output")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show verbose step-by-step details for linear equations")
    parser.add_argument("--easy", "-e", action="store_true",
                        help="Use easier solutions (clear fractions via LCD before solving)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Status check
    if args.status:
        from ocr_engine import print_ocr_status
        print_ocr_status()
        return

    # GUI mode
    if args.gui:
        from gui import launch_gui
        launch_gui()
        return

    # CLI mode — require image path
    if not args.image:
        print("Error: image path is required in CLI mode.")
        print("Usage: python main.py <image_path> [options]")
        print("       python main.py --gui")
        print("       python main.py --status")
        sys.exit(1)

    if not os.path.isfile(args.image):
        print(f"Error: file not found: {args.image}")
        sys.exit(1)

    result = run_pipeline(
        image_path=args.image,
        lang=args.lang,
        use_latex=not args.no_latex,
        generate_pdf=args.pdf,
        pdf_output=args.output,
        verbose=not args.quiet,
        full_image=args.full_image,
        solver_verbose=args.verbose,
        easy_mode=args.easy,
    )

    if not result.solutions or all(not s.is_valid for s in result.solutions):
        print_no_solutions()
        sys.exit(1)


if __name__ == "__main__":
    main()
