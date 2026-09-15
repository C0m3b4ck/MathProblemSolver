# MathExerciseSolver 🧮

Solve math exercises from images — step by step, Wolfram Alpha-style.

Point it at a photo of math homework (or a screenshot from a digital board), and it will:
1. **Recognize** the exercises (OCR with math symbol support)
2. **Solve** each problem with full step-by-step explanations
3. **Output** the solutions to terminal or a handwriting-style PDF

Built for **Polish grades 7-8** (ages 13–15), but works for any basic math.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-green?logo=windows)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Quick Start (Windows)

### Option 1: One-click installer

1. Download or clone this repository
2. Double-click **`install.bat`**
3. Wait for it to finish (~3-5 minutes on first run)
4. Double-click **`MathExerciseSolver.bat`** to launch

The installer handles everything: Python virtual environment, all dependencies, Tesseract OCR, Polish language data, and handwriting fonts.

### Option 2: Manual setup

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Tesseract OCR (Windows installer):
# https://github.com/UB-Mannheim/tesseract/wiki

# Launch
python main.py --gui
```

---

## Usage

### GUI Mode

```bash
python main.py --gui
```

Opens a window where you can:
- Load an image with the 📂 button
- Preview the detected exercises
- Click "Rozwiąż" to solve
- Export results to a handwriting-style PDF

### CLI Mode

```bash
# Basic usage — solve and print to terminal
python main.py exercises.png

# Solve in English and generate PDF
python main.py exercises.png --lang en --pdf

# Specify output path
python main.py exercises.png --pdf --output my_solutions.pdf

# Check dependency status
python main.py --status
```

### Example Output

```
══════════════════════════════════════════════════════════════════════
  #1  Równanie liniowe
══════════════════════════════════════════════════════════════════════
  Problem: 2*x + 5 = 13

  → Równanie: 2*x + 5 = 13
  → Upraszczamy: 2*x + 5 - 13 = 0 → 2*x - 8 = 0
  → Przenosimy -8 na prawą stronę: 2*x = 8
  → Dzielimy obie strony przez 2: x = 4

  ✓ Odpowiedź: x = 4
```

---

## Features

| Feature | Description |
|---------|-------------|
| 📷 **Image input** | Load photos or screenshots of math exercises |
| 🔢 **Math OCR** | Recognizes numbers, variables, operators, fractions, powers, roots |
| 🇵🇱 **Polish support** | Full Polish text recognition + Polish step descriptions |
| 📐 **Step-by-step solver** | Shows every step like a human would solve it |
| ✍️ **Handwriting PDF** | Generates solutions on lined paper with handwriting font |
| 🖥️ **GUI + CLI** | Use the graphical interface or command line |
| 🔌 **Offline** | All processing runs locally — no internet required |

---

## Supported Math Topics

### Grade 7
- Natural numbers, integers, fractions, decimals
- Percentages
- Powers and roots
- Algebraic expressions
- Linear equations
- Basic statistics (mean, median, mode, range)

### Grade 8
- Quadratic equations (discriminant, factoring, formula)
- Polynomials
- Functions (linear, quadratic)
- Systems of equations
- Inequalities
- Geometry (Pythagorean theorem, areas, perimeters)
- Exponentials and logarithms basics

---

## Project Structure

```
MathExerciseSolver/
├── main.py              # CLI entry point
├── gui.py               # Tkinter GUI
├── preprocessing.py     # Image cleanup + exercise segmentation
├── ocr_engine.py        # Pix2Tex (math) + Tesseract (text) OCR
├── math_parser.py       # LaTeX → SymPy conversion
├── solver.py            # Step-by-step solver (15 methods)
├── step_descriptions.py # PL/EN localized step text
├── handwriting.py       # PDF renderer with handwriting font
├── config.py            # All settings in one place
├── requirements.txt     # Python dependencies
├── install.bat          # One-click Windows installer
├── MathExerciseSolver.bat   # GUI launcher (created by installer)
├── MathExerciseSolver-CLI.bat  # CLI launcher (created by installer)
├── assets/
│   ├── fonts/           # Handwriting font (Caveat)
│   └── templates/       # Lined paper background
├── tests/
│   ├── test_parser.py   # Parser unit tests
│   └── test_solver.py   # Solver unit tests
└── output/              # Generated PDFs and crops
```

---

## Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `opencv-python` | Image preprocessing | `pip install opencv-python` |
| `pytesseract` | Tesseract OCR wrapper | `pip install pytesseract` |
| `Pillow` | Image manipulation + rendering | `pip install Pillow` |
| `sympy` | Math parsing + solving | `pip install sympy` |
| `pix2tex` | Math expression OCR (Pix2Tex) | `pip install pix2tex` |
| `numpy` | Numerical arrays | `pip install numpy` |
| `reportlab` | PDF generation | `pip install reportlab` |

**External tool:** [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) — installed automatically by `install.bat`.

---

## Running Tests

```bash
.venv\Scripts\activate
python tests/test_parser.py
python tests/test_solver.py
```

---

## Configuration

All settings are in `config.py`. Key options:

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_LANGUAGE` | `"pl"` | Solver language (`"pl"` or `"en"`) |
| `HANDWRITING_FONT_SIZE` | `22` | Font size in PDF output |
| `LINE_SPACING` | `36` | Line spacing in PDF (pixels) |
| `ADAPTIVE_THRESH_BLOCK_SIZE` | `11` | Image binarization threshold |
| `TESSERACT_LANG` | `"pol+eng"` | OCR languages |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" | Install Python 3.10+ from python.org, check "Add to PATH" |
| "Tesseract not found" | Run `install.bat` again, or install manually |
| Poor OCR accuracy | Use a clearer image, better lighting, straight-on angle |
| Math not recognized | Ensure the math is printed/typed (not handwritten on board) |
| "pix2tex not installed" | Run `pip install pix2tex` in your venv |

---

## License

MIT
