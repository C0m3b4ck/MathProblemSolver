"""
Handwriting-style output renderer.
Generates PDF pages that look like handwritten solutions on lined paper.
"""

import os
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

from config import (
    FONTS_DIR, TEMPLATES_DIR, OUTPUT_DIR, ASSETS_DIR,
    LINE_SPACING, PAGE_MARGIN_TOP, PAGE_MARGIN_LEFT, PAGE_MARGIN_RIGHT,
    HANDWRITING_FONT_SIZE, ANSWER_COLOR, STEP_COLOR, TITLE_COLOR,
)
from solver import Solution, Step


# Path to user handwriting sample (created by GUI drawing dialog)
USER_HANDWRITING_SAMPLE_PATH = os.path.join(ASSETS_DIR, "fonts", "user_handwriting_sample.png")


# ── Font loading ───────────────────────────────────────────────────────────

def _find_handwriting_font() -> Optional[str]:
    """
    Find a handwriting font in the assets directory.
    Falls back to any available system font if none found.
    """
    # Check for fonts in assets/fonts/
    if os.path.isdir(FONTS_DIR):
        for name in ["Caveat-Regular.ttf", "Caveat-Bold.ttf",
                      "ArchitectsDaughter-Regular.ttf",
                      "PatrickHand-Regular.ttf",
                      "Kalam-Regular.ttf"]:
            path = os.path.join(FONTS_DIR, name)
            if os.path.isfile(path):
                return path

    # Try system fonts (common locations on Windows/Linux)
    system_font_dirs = [
        "C:/Windows/Fonts",
        "/usr/share/fonts",
        os.path.expanduser("~/.fonts"),
    ]
    preferred = ["Caveat.ttf", "ArchitectsDaughter.ttf", "PatrickHand.ttf"]

    for font_dir in system_font_dirs:
        if not os.path.isdir(font_dir):
            continue
        for name in preferred:
            path = os.path.join(font_dir, name)
            if os.path.isfile(path):
                return path

    return None


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a PIL font at the given size."""
    font_path = _find_handwriting_font()
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass

    # Fallback: default PIL font (not handwritten, but functional)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


# ── Lined paper background ────────────────────────────────────────────────

def _create_lined_paper(
    width: int,
    height: int,
    line_spacing: int = LINE_SPACING,
    bg_color: tuple = (255, 253, 245),
    line_color: tuple = (180, 200, 230),
    margin_color: tuple = (220, 100, 100),
) -> Image.Image:
    """
    Create a lined paper background image.
    """
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw horizontal lines
    y = line_spacing
    while y < height:
        draw.line([(0, y), (width, y)], fill=line_color, width=1)
        y += line_spacing

    # Draw left margin line
    margin_x = 50
    draw.line([(margin_x, 0), (margin_x, height)], fill=margin_color, width=2)

    return img


def _load_lined_paper_template(width: int, height: int) -> Image.Image:
    """Try to load a pre-made lined paper template, fall back to generated."""
    template_path = os.path.join(TEMPLATES_DIR, "lined_paper.png")
    if os.path.isfile(template_path):
        try:
            template = Image.open(template_path)
            template = template.resize((width, height), Image.Resampling.LANCZOS)
            return template
        except Exception:
            pass
    return _create_lined_paper(width, height)


# ── Text rendering helpers ────────────────────────────────────────────────

def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    Word-wrap text to fit within max_width pixels.
    """
    words = text.split()
    if not words:
        return [text]

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _add_char_variation(
    char: str,
    font: ImageFont.FreeTypeFont,
) -> Tuple[str, ImageFont.FreeTypeFont]:
    """
    Optionally return a slightly different character or font for organic feel.
    (Minimal variation — just enough to break uniformity.)
    """
    # For now, return as-is. Could add slight rotation/scaling per character later.
    return char, font


# ── PDF Generation ─────────────────────────────────────────────────────────

def _draw_handwriting_overlay(canvas_obj, page_w, page_h, sample_path=None):
    """
    Draw the user's handwriting sample as a small header in the top-right corner of the page.
    """
    if sample_path is None:
        sample_path = USER_HANDWRITING_SAMPLE_PATH
    if not os.path.isfile(sample_path):
        return
    try:
        from reportlab.lib.utils import ImageReader
        img = ImageReader(sample_path)
        # Small header image in top-right corner
        overlay_w = 120
        overlay_h = 35
        x_pos = page_w - overlay_w - 40
        y_pos = page_h - 30
        canvas_obj.drawImage(img, x_pos, y_pos, width=overlay_w, height=overlay_h,
                             mask='auto', preserveAspectRatio=True)
    except Exception:
        pass  # Silently skip if overlay fails

def render_solutions_pdf(
    solutions: List[Solution],
    output_path: Optional[str] = None,
    title: str = "Rozwiązania",
    lang: str = "pl",
) -> str:
    """
    Render solutions to a PDF file with handwriting-style font on lined paper.

    Args:
        solutions: List of Solution objects.
        output_path: Where to save the PDF. If None, auto-generate in OUTPUT_DIR.
        title: Page title.
        lang: "pl" or "en".

    Returns:
        Path to the generated PDF.
    """
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"solutions_{timestamp}.pdf")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Create the PDF using reportlab
    page_w, page_h = A4
    c = pdf_canvas.Canvas(output_path, pagesize=A4)

    # Try to set a handwriting-like font
    font_name = "Helvetica"  # default
    font_path = _find_handwriting_font()
    if font_path:
        try:
            # Register custom font with reportlab
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont("Handwriting", font_path))
            font_name = "Handwriting"
        except Exception:
            pass

    # Font sizes
    title_size = HANDWRITING_FONT_SIZE + 8
    heading_size = HANDWRITING_FONT_SIZE + 4
    body_size = HANDWRITING_FONT_SIZE
    answer_size = HANDWRITING_FONT_SIZE + 2

    # Create a PIL font for text measurement (used by _wrap_text)
    measure_font = _get_font(body_size)

    margin_left = PAGE_MARGIN_LEFT
    margin_right = PAGE_MARGIN_RIGHT
    margin_top = PAGE_MARGIN_TOP
    usable_width = page_w - margin_left - margin_right

    y = page_h - margin_top  # current y position (top-down)

    # ── Page title ─────────────────────────────────────────────────────
    c.setFont(font_name, title_size)
    c.setFillColorRGB(0, 0, 0.6)
    c.drawString(margin_left, y, title)
    y -= title_size + 15

    # ── Draw lined paper ───────────────────────────────────────────────
    # We draw lines behind the text
    c.setStrokeColorRGB(0.7, 0.78, 0.9)
    c.setLineWidth(0.5)
    line_y = page_h - margin_top - title_size - 30
    while line_y > 40:
        c.line(margin_left - 10, line_y, page_w - margin_right + 10, line_y)
        line_y -= LINE_SPACING

    # Red margin line
    c.setStrokeColorRGB(0.86, 0.39, 0.39)
    c.setLineWidth(1.5)
    c.line(margin_left - 15, page_h - margin_top + 10, margin_left - 15, 40)

    # Draw user handwriting overlay on first page (if sample exists)
    _draw_handwriting_overlay(c, page_w, page_h)

    # ── Render each solution ───────────────────────────────────────────
    for sol_idx, solution in enumerate(solutions):
        # Check for page break
        if y < 120:
            c.showPage()
            y = page_h - margin_top
            # Redraw lines on new page
            c.setStrokeColorRGB(0.7, 0.78, 0.9)
            c.setLineWidth(0.5)
            ly = page_h - margin_top - 15
            while ly > 40:
                c.line(margin_left - 10, ly, page_w - margin_right + 10, ly)
                ly -= LINE_SPACING
            # Draw user handwriting overlay on new page
            _draw_handwriting_overlay(c, page_w, page_h)

        # Method heading
        c.setFont(font_name, heading_size)
        c.setFillColorRGB(0, 0, 0.5)
        method_label = f"#{sol_idx + 1}  [{solution.method}]"
        c.drawString(margin_left, y, method_label)
        y -= heading_size + 5

        # Problem statement
        c.setFont(font_name, body_size)
        c.setFillColorRGB(*[c / 255 for c in TITLE_COLOR])
        problem_text = f"Zadanie: {solution.problem}" if lang == "pl" else f"Problem: {solution.problem}"
        wrapped = _wrap_text(problem_text, measure_font, usable_width)
        for line in wrapped:
            if y < 50:
                c.showPage()
                y = page_h - margin_top
            c.drawString(margin_left, y, line)
            y -= body_size + 4

        y -= 5

        # Steps
        c.setFillColorRGB(*[c / 255 for c in STEP_COLOR])
        for step in solution.steps:
            if y < 50:
                c.showPage()
                y = page_h - margin_top

            c.setFont(font_name, body_size)
            step_text = f"  → {step.text}"
            wrapped = _wrap_text(step_text, measure_font, usable_width - 20)
            for wline in wrapped:
                c.drawString(margin_left + 15, y, wline)
                y -= body_size + 3

        y -= 8

        # Answer
        if y < 50:
            c.showPage()
            y = page_h - margin_top

        c.setFont(font_name, answer_size)
        c.setFillColorRGB(*[c / 255 for c in ANSWER_COLOR])
        answer_label = f"  Odpowiedź: {solution.answer}" if lang == "pl" else f"  Answer: {solution.answer}"
        c.drawString(margin_left, y, answer_label)
        y -= answer_size + 15

        # Separator line between solutions
        if sol_idx < len(solutions) - 1:
            c.setStrokeColorRGB(0.7, 0.78, 0.9)
            c.setLineWidth(1)
            c.line(margin_left, y, page_w - margin_right, y)
            y -= 15

    c.save()
    print(f"[PDF] Saved solutions to: {output_path}")
    return output_path


# ── Image-based rendering (alternative) ───────────────────────────────────

def render_solutions_image(
    solutions: List[Solution],
    output_path: Optional[str] = None,
    title: str = "Rozwiązania",
    lang: str = "pl",
    width: int = 800,
) -> str:
    """
    Render solutions to a PNG image on lined paper background.
    (Alternative to PDF — simpler but lower quality.)

    Returns:
        Path to the generated image.
    """
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"solutions_{timestamp}.png")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    font_size = HANDWRITING_FONT_SIZE
    font = _get_font(font_size)
    title_font = _get_font(font_size + 8)
    answer_font = _get_font(font_size + 2)

    line_h = LINE_SPACING
    margin = PAGE_MARGIN_LEFT

    # Estimate page height
    total_lines = 0
    for sol in solutions:
        total_lines += 3  # heading + problem + answer
        for step in sol.steps:
            total_lines += max(1, len(step.text) // 60 + 1)
        total_lines += 2  # separator

    page_height = max(800, total_lines * line_h + 200)

    # Create lined paper background
    img = _load_lined_paper_template(width, page_height)
    draw = ImageDraw.Draw(img)

    y = PAGE_MARGIN_TOP

    # Title
    draw.text((margin, y), title, font=title_font, fill=TITLE_COLOR)
    y += font_size + 8 + 20

    # Render each solution
    for sol_idx, solution in enumerate(solutions):
        # Method heading
        heading = f"#{sol_idx + 1}  [{solution.method}]"
        draw.text((margin, y), heading, font=font, fill=(0, 0, 150))
        y += font_size + 8

        # Problem
        problem_text = f"Zadanie: {solution.problem}" if lang == "pl" else f"Problem: {solution.problem}"
        for wline in _wrap_text(problem_text, font, width - margin * 2):
            draw.text((margin, y), wline, font=font, fill=TITLE_COLOR)
            y += line_h

        y += 5

        # Steps
        for step in solution.steps:
            step_text = f"  → {step.text}"
            for wline in _wrap_text(step_text, font, width - margin * 2 - 20):
                draw.text((margin + 15, y), wline, font=font, fill=STEP_COLOR)
                y += line_h

        y += 8

        # Answer
        answer_text = f"  Odpowiedź: {solution.answer}" if lang == "pl" else f"  Answer: {solution.answer}"
        draw.text((margin, y), answer_text, font=answer_font, fill=ANSWER_COLOR)
        y += font_size + 2 + 15

        # Separator
        if sol_idx < len(solutions) - 1:
            draw.line([(margin, y), (width - margin, y)], fill=(180, 200, 230), width=1)
            y += 15

    # Crop to actual content
    img = img.crop((0, 0, width, y + 30))
    img.save(output_path)
    print(f"[PDF] Saved solutions image to: {output_path}")
    return output_path
