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

def run_pipeline(
    image_path: str,
    lang: str = DEFAULT_LANGUAGE,
    use_latex: bool = True,
    generate_pdf: bool = False,
    pdf_output: str = None,
    verbose: bool = True,
) -> list:
    """
    Run the full solve pipeline on an image.

    Args:
        image_path: Path to the input image.
        lang: Language for solver text ("pl" or "en").
        use_latex: Whether to use Pix2Tex for math OCR.
        generate_pdf: Whether to generate a PDF output.
        pdf_output: Custom PDF output path.
        verbose: Whether to print progress.

    Returns:
        List of Solution objects.
    """
    from preprocessing import segment_exercises, crop_region, save_crops, display_regions
    from ocr_engine import ocr_all_exercises, print_ocr_status
    from math_parser import parse_exercise
    from solver import solve_problem, Solution, Step
    from handwriting import render_solutions_pdf

    all_solutions = []

    # Step 1: Load and segment
    if verbose:
        print(f"\n{Colors.BOLD}Step 1: Loading and segmenting image...{Colors.END}")
        print(f"  File: {image_path}")

    try:
        img, regions, binary = segment_exercises(image_path)
    except FileNotFoundError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return all_solutions
    except ValueError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return all_solutions

    if verbose:
        print(f"  Found {len(regions)} exercise region(s)")

    # Save crops for debugging
    crop_dir = os.path.join(OUTPUT_DIR, "crops")
    crop_paths = save_crops(img, regions, crop_dir)

    # Step 2: OCR each region
    if verbose:
        print(f"\n{Colors.BOLD}Step 2: Running OCR...{Colors.END}")

    # Convert regions to numpy crops
    crops = [crop_region(img, r) for r in regions]
    ocr_results = ocr_all_exercises(crops, use_latex=use_latex)

    # Step 3: Parse and solve each exercise
    if verbose:
        print(f"\n{Colors.BOLD}Step 3: Parsing and solving...{Colors.END}")

    for i, ocr_result in enumerate(ocr_results):
        text = ocr_result["text"]
        math_latex = ocr_result.get("math_latex")

        if verbose:
            print(f"\n  --- Exercise {i + 1} ---")
            if text:
                print(f"  Text OCR:    {text[:100]}{'...' if len(text) > 100 else ''}")
            if math_latex:
                print(f"  Math OCR:    {math_latex}")

        # Parse
        parsed = parse_exercise(text, math_latex)

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
        )

        all_solutions.extend(solutions)

        if verbose:
            for sol in solutions:
                print_solution(sol, len(all_solutions))

    # Print summary
    if verbose:
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
        solved = sum(1 for s in all_solutions if s.is_valid)
        print(f"  Total: {len(all_solutions)} exercise(s), {solved} solved successfully")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

    # Step 4: Generate PDF if requested
    if generate_pdf and all_solutions:
        if verbose:
            print(f"\n{Colors.BOLD}Step 4: Generating handwriting PDF...{Colors.END}")
        pdf_path = render_solutions_pdf(all_solutions, pdf_output, lang=lang)
        if verbose:
            print(f"  Saved to: {pdf_path}")

    return all_solutions


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

    solutions = run_pipeline(
        image_path=args.image,
        lang=args.lang,
        use_latex=not args.no_latex,
        generate_pdf=args.pdf,
        pdf_output=args.output,
        verbose=not args.quiet,
    )

    if not solutions or all(not s.is_valid for s in solutions):
        print_no_solutions()
        sys.exit(1)


if __name__ == "__main__":
    main()
