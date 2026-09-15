#!/usr/bin/env python3
"""
MathExerciseSolver — Tkinter GUI.
Provides a simple windowed interface for loading images and viewing solutions.
Supports Polish and English via radio button toggle.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

# Ensure project directory is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    GUI_WINDOW_TITLE, GUI_WINDOW_SIZE, GUI_BG_COLOR,
    GUI_PREVIEW_MAX_WIDTH, GUI_PREVIEW_MAX_HEIGHT, DEFAULT_LANGUAGE, OUTPUT_DIR,
)
from main import run_pipeline
from solver import Solution


# ── GUI string translations ────────────────────────────────────────────────

_STRINGS = {
    "pl": {
        # Window
        "window_title": "MathExerciseSolver — Rozwiązywanie zadań matematycznych",
        # Toolbar buttons
        "open_btn": "📂 Otwórz obraz",
        "solve_btn": "🔢 Rozwiąż",
        "pdf_btn": "📄 Eksportuj PDF",
        # Language label
        "lang_label": "Język:",
        # Preview panel
        "preview_title": "Obraz wejściowy",
        "preview_empty": "Brak obrazu",
        # Results panel
        "results_title": "Rozwiązania",
        # File dialogs
        "open_title": "Wybierz obraz z zadaniami",
        "filetype_images": "Obrazy",
        "filetype_all": "Wszystkie pliki",
        "save_pdf_title": "Zapisz PDF",
        # Status messages
        "status_ready": "Gotowy",
        "status_loaded": "Załadowano: {name}",
        "status_processing": "Przetwarzanie...",
        "status_done": "Gotowo — {n} zadań",
        "status_error": "Błąd",
        "status_pdf_done": "PDF zapisany: {name}",
        "status_pdf_gen": "Generowanie PDF...",
        # Results display
        "result_summary": "═══ Rozwiązano {solved}/{total} zadań ═══",
        "result_problem": "Zadanie: {text}",
        "result_answer": "✓ Odpowiedź: {text}",
        # No results
        "no_results": "Nie udało się rozpoznać zadań.",
        "tips_title": "Wskazówki:",
        "tip_1": "  • Upewnij się, że obraz jest wyraźny",
        "tip_2": "  • Zadania powinny być numerowane (1., 2., itp.)",
        "tip_3": "  • Spróbuj przyciąć obraz do samych zadań",
        # Errors
        "error_title": "Błąd",
        "error_msg": "Wystąpił błąd:\n{text}",
        # PDF success
        "pdf_success_title": "Sukces",
        "pdf_success_msg": "Plik PDF zapisany:\n{text}",
        # Image error
        "image_error": "Błąd: {text}",
    },
    "en": {
        # Window
        "window_title": "MathExerciseSolver — Math Problem Solver",
        # Toolbar buttons
        "open_btn": "📂 Open Image",
        "solve_btn": "🔢 Solve",
        "pdf_btn": "📄 Export PDF",
        # Language label
        "lang_label": "Language:",
        # Preview panel
        "preview_title": "Input Image",
        "preview_empty": "No image loaded",
        # Results panel
        "results_title": "Solutions",
        # File dialogs
        "open_title": "Select an image with exercises",
        "filetype_images": "Images",
        "filetype_all": "All files",
        "save_pdf_title": "Save PDF",
        # Status messages
        "status_ready": "Ready",
        "status_loaded": "Loaded: {name}",
        "status_processing": "Processing...",
        "status_done": "Done — {n} exercise(s)",
        "status_error": "Error",
        "status_pdf_done": "PDF saved: {name}",
        "status_pdf_gen": "Generating PDF...",
        # Results display
        "result_summary": "═══ Solved {solved}/{total} exercise(s) ═══",
        "result_problem": "Problem: {text}",
        "result_answer": "✓ Answer: {text}",
        # No results
        "no_results": "Could not recognize any exercises.",
        "tips_title": "Tips:",
        "tip_1": "  • Make sure the image is clear and well-lit",
        "tip_2": "  • Exercises should be numbered (1., 2., etc.)",
        "tip_3": "  • Try cropping the image to just the exercises",
        # Errors
        "error_title": "Error",
        "error_msg": "An error occurred:\n{text}",
        # PDF success
        "pdf_success_title": "Success",
        "pdf_success_msg": "PDF saved to:\n{text}",
        # Image error
        "image_error": "Error: {text}",
    },
}


def _t(key: str, lang: str, **kwargs) -> str:
    """Get a translated GUI string, formatted with kwargs."""
    strings = _STRINGS.get(lang, _STRINGS["en"])
    template = strings.get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


# ── Main GUI Class ─────────────────────────────────────────────────────────

class MathSolverGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.image_path = None
        self.solutions = []
        self._last_diagnostics = []
        self.lang = tk.StringVar(value=DEFAULT_LANGUAGE)
        self.status_var = tk.StringVar()

        # Trace language changes to update all labels
        self.lang.trace_add("write", self._on_lang_change)

        self._build_ui()
        self._update_labels()

    def _on_lang_change(self, *_args):
        """Called when the language radio button changes."""
        self._update_labels()
        # Re-display existing results in the new language
        if self.solutions or self._last_diagnostics:
            self._redisplay()

    def _redisplay(self):
        """Re-render current results with the new language."""
        lang = self.lang.get()
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)

        if self.solutions:
            solved = sum(1 for s in self.solutions if s.is_valid)
            summary = _t("result_summary", lang, solved=solved, total=len(self.solutions))
            self.results_text.insert(tk.END, summary + "\n\n", "title")

            for i, sol in enumerate(self.solutions):
                self.results_text.insert(tk.END, f"#{i + 1}  [{sol.method}]\n", "heading")
                problem_line = _t("result_problem", lang, text=sol.problem)
                self.results_text.insert(tk.END, f"  {problem_line}\n", "problem")
                for step in sol.steps:
                    self.results_text.insert(tk.END, f"    → {step.text}\n", "step")
                    if step.math:
                        self.results_text.insert(tk.END, f"      {step.math}\n", "step")
                answer_line = _t("result_answer", lang, text=sol.answer)
                self.results_text.insert(tk.END, f"\n  {answer_line}\n\n", "answer")
                if i < len(self.solutions) - 1:
                    self.results_text.insert(tk.END, "────────────────────────────────────────\n")

        if self._last_diagnostics:
            self.results_text.insert(tk.END, "\n" + ("─" * 50) + "\n")
            self._insert_diagnostics(self._last_diagnostics, lang)

        self.results_text.config(state=tk.DISABLED)

    def _update_labels(self):
        """Update all GUI labels to match the current language."""
        lang = self.lang.get()

        self.root.title(_t("window_title", lang))
        self.status_var.set(_t("status_ready", lang))

        # Toolbar buttons
        self.open_btn.config(text=_t("open_btn", lang))
        self.solve_btn.config(text=_t("solve_btn", lang))
        self.pdf_btn.config(text=_t("pdf_btn", lang))

        # Language label
        self.lang_label.config(text=_t("lang_label", lang))

        # Panel titles
        self.preview_title_label.config(text=_t("preview_title", lang))
        self.results_title_label.config(text=_t("results_title", lang))

        # Preview placeholder (only if no image loaded)
        if not self.image_path:
            self.preview_label.config(text=_t("preview_empty", lang))

    def _build_ui(self):
        """Build the GUI layout."""
        # ── Top toolbar ────────────────────────────────────────────────
        toolbar = tk.Frame(self.root, bg=GUI_BG_COLOR, pady=5)
        toolbar.pack(fill=tk.X)

        self.open_btn = tk.Button(
            toolbar, text=_t("open_btn", self.lang.get()), command=self._open_image,
            font=("Segoe UI", 11), padx=10, pady=3,
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.solve_btn = tk.Button(
            toolbar, text=_t("solve_btn", self.lang.get()), command=self._solve,
            font=("Segoe UI", 11, "bold"), padx=10, pady=3,
            state=tk.DISABLED,
        )
        self.solve_btn.pack(side=tk.LEFT, padx=5)

        self.pdf_btn = tk.Button(
            toolbar, text=_t("pdf_btn", self.lang.get()), command=self._export_pdf,
            font=("Segoe UI", 11), padx=10, pady=3,
            state=tk.DISABLED,
        )
        self.pdf_btn.pack(side=tk.LEFT, padx=5)

        # Language toggle
        lang_frame = tk.Frame(toolbar, bg=GUI_BG_COLOR)
        lang_frame.pack(side=tk.RIGHT, padx=10)

        self.lang_label = tk.Label(
            lang_frame, text=_t("lang_label", self.lang.get()),
            bg=GUI_BG_COLOR, font=("Segoe UI", 10),
        )
        self.lang_label.pack(side=tk.LEFT)
        tk.Radiobutton(lang_frame, text="PL", variable=self.lang, value="pl",
                       bg=GUI_BG_COLOR, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        tk.Radiobutton(lang_frame, text="EN", variable=self.lang, value="en",
                       bg=GUI_BG_COLOR, font=("Segoe UI", 10)).pack(side=tk.LEFT)

        # ── Main content area ──────────────────────────────────────────
        content = tk.Frame(self.root, bg=GUI_BG_COLOR)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel: image preview
        left = tk.Frame(content, bg="#e0e0e0", width=GUI_PREVIEW_MAX_WIDTH + 20)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left.pack_propagate(False)

        self.preview_title_label = tk.Label(
            left, text=_t("preview_title", self.lang.get()),
            bg="#e0e0e0", font=("Segoe UI", 10, "bold"),
        )
        self.preview_title_label.pack(pady=5)

        self.preview_label = tk.Label(
            left, text=_t("preview_empty", self.lang.get()),
            bg="#e0e0e0", fg="#888", font=("Segoe UI", 12),
        )
        self.preview_label.pack(expand=True)

        # Right panel: solutions
        right = tk.Frame(content, bg=GUI_BG_COLOR)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.results_title_label = tk.Label(
            right, text=_t("results_title", self.lang.get()),
            bg=GUI_BG_COLOR, font=("Segoe UI", 10, "bold"),
        )
        self.results_title_label.pack(pady=5)

        self.results_text = scrolledtext.ScrolledText(
            right, wrap=tk.WORD, font=("Consolas", 11),
            bg="white", state=tk.DISABLED,
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for coloring
        self.results_text.tag_configure("title", foreground="#0000AA", font=("Consolas", 13, "bold"))
        self.results_text.tag_configure("heading", foreground="#000088", font=("Consolas", 12, "bold"))
        self.results_text.tag_configure("step", foreground="#333333")
        self.results_text.tag_configure("answer", foreground="#006600", font=("Consolas", 11, "bold"))
        self.results_text.tag_configure("error", foreground="#CC0000")
        self.results_text.tag_configure("problem", foreground="#000099")

        # ── Status bar ─────────────────────────────────────────────────
        status_bar = tk.Frame(self.root, bg="#d0d0d0", pady=2)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(status_bar, textvariable=self.status_var, bg="#d0d0d0",
                 font=("Segoe UI", 9), anchor=tk.W).pack(fill=tk.X, padx=10)

    # ── Actions ────────────────────────────────────────────────────────

    def _open_image(self):
        """Open a file dialog to select an image."""
        lang = self.lang.get()
        filetypes = [
            (_t("filetype_images", lang), "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            (_t("filetype_all", lang), "*.*"),
        ]
        path = filedialog.askopenfilename(
            title=_t("open_title", lang),
            filetypes=filetypes,
        )
        if path:
            self.image_path = path
            self._show_preview(path)
            self.solve_btn.config(state=tk.NORMAL)
            self.status_var.set(_t("status_loaded", lang, name=os.path.basename(path)))

    def _show_preview(self, path: str):
        """Display the image in the preview panel."""
        lang = self.lang.get()
        try:
            img = Image.open(path)
            img.thumbnail((GUI_PREVIEW_MAX_WIDTH, GUI_PREVIEW_MAX_HEIGHT), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.preview_label.config(image=photo, text="")
            self.preview_label._photo = photo  # prevent GC
        except Exception as e:
            self.preview_label.config(text=_t("image_error", lang, text=str(e)), image="")

    def _solve(self):
        """Run the solve pipeline in a background thread."""
        if not self.image_path:
            return

        lang = self.lang.get()
        self.solve_btn.config(state=tk.DISABLED)
        self.pdf_btn.config(state=tk.DISABLED)
        self.status_var.set(_t("status_processing", lang))

        # Clear results
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state=tk.DISABLED)

        # Run in background thread
        thread = threading.Thread(target=self._solve_thread, daemon=True)
        thread.start()

    def _solve_thread(self):
        """Background solve thread."""
        try:
            result = run_pipeline(
                image_path=self.image_path,
                lang=self.lang.get(),
                use_latex=True,
                generate_pdf=False,
                verbose=False,
            )
            self.root.after(0, self._display_result, result)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _display_result(self, result):
        """Display a PipelineResult (solutions + diagnostics) in the results pane."""
        lang = self.lang.get()

        if hasattr(result, 'error') and result.error:
            self.solutions = []
            self._display_error_text(result.error)
            return

        self.solutions = result.solutions
        self._last_diagnostics = getattr(result, 'diagnostics', [])

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)

        if not result.solutions:
            self.results_text.insert(tk.END, _t("no_results", lang) + "\n\n")
            self.results_text.insert(tk.END, _t("tips_title", lang) + "\n")
            self.results_text.insert(tk.END, _t("tip_1", lang) + "\n")
            self.results_text.insert(tk.END, _t("tip_2", lang) + "\n")
            self.results_text.insert(tk.END, _t("tip_3", lang) + "\n")

            # Show diagnostics even when no solutions found
            if result.diagnostics:
                self.results_text.insert(tk.END, "\n" + ("─" * 50) + "\n")
                self._insert_diagnostics(result.diagnostics, lang)
        else:
            solved = sum(1 for s in result.solutions if s.is_valid)
            summary = _t("result_summary", lang, solved=solved, total=len(result.solutions))
            self.results_text.insert(tk.END, summary + "\n\n", "title")

            for i, sol in enumerate(result.solutions):
                # Heading
                self.results_text.insert(tk.END, f"#{i + 1}  [{sol.method}]\n", "heading")

                # Problem
                problem_line = _t("result_problem", lang, text=sol.problem)
                self.results_text.insert(tk.END, f"  {problem_line}\n", "problem")

                # Steps
                for step in sol.steps:
                    self.results_text.insert(tk.END, f"    → {step.text}\n", "step")
                    if step.math:
                        self.results_text.insert(tk.END, f"      {step.math}\n", "step")

                # Answer
                answer_line = _t("result_answer", lang, text=sol.answer)
                self.results_text.insert(tk.END, f"\n  {answer_line}\n\n", "answer")

                # Separator
                if i < len(result.solutions) - 1:
                    self.results_text.insert(tk.END, "────────────────────────────────────────\n")

            # Show diagnostics at the bottom
            if result.diagnostics:
                self.results_text.insert(tk.END, "\n" + ("─" * 50) + "\n")
                self._insert_diagnostics(result.diagnostics, lang)

        self.results_text.config(state=tk.DISABLED)

        # Update buttons
        self.solve_btn.config(state=tk.NORMAL)
        if result.solutions:
            self.pdf_btn.config(state=tk.NORMAL)
        self.status_var.set(_t("status_done", lang, n=len(result.solutions)))

    def _insert_diagnostics(self, diagnostics, lang):
        """Insert OCR/parse diagnostics into the results text."""
        diag_title = "🔍 Debug Info" if lang == "en" else "🔍 Informacje diagnostyczne"
        self.results_text.insert(tk.END, f"\n{diag_title}\n\n", "heading")

        for diag in diagnostics:
            idx = diag.region_index + 1
            box = diag.region_box
            self.results_text.insert(
                tk.END, f"  Region {idx}: x={box[0]} y={box[1]} w={box[2]} h={box[3]}\n", "step"
            )

            # Tesseract OCR
            tess_label = "Tesseract:" if lang == "en" else "Tesseract:"
            text_preview = (diag.text_ocr or "(empty)")[:300]
            self.results_text.insert(tk.END, f"    {tess_label} {text_preview}\n", "step")

            # Pix2Tex
            if diag.math_latex:
                self.results_text.insert(tk.END, f"    Pix2Tex:  {diag.math_latex}\n", "step")
            else:
                self.results_text.insert(tk.END, f"    Pix2Tex:  (none)\n", "step")

            # Parsed expressions
            if diag.parsed_expressions:
                self.results_text.insert(
                    tk.END, f"    Expressions: {diag.parsed_expressions}\n", "step"
                )

            # Parsed equations
            if diag.parsed_equations:
                self.results_text.insert(
                    tk.END, f"    Equations:   {diag.parsed_equations}\n", "step"
                )

            # Context flags
            ctx = diag.context
            flags = []
            if ctx.get("has_equation"): flags.append("equation")
            if ctx.get("has_percentage"): flags.append("percentage")
            if ctx.get("has_fraction"): flags.append("fraction")
            if ctx.get("has_power"): flags.append("power")
            if ctx.get("has_root"): flags.append("root")
            if ctx.get("has_geometry"): flags.append("geometry")
            if ctx.get("has_statistics"): flags.append("statistics")
            if ctx.get("exercise_number"): flags.append(f"#{ctx['exercise_number']}")
            if flags:
                self.results_text.insert(
                    tk.END, f"    Detected:    {', '.join(flags)}\n", "step"
                )

            # Unparsed
            if diag.unparsed:
                self.results_text.insert(
                    tk.END, f"    Unparsed:    {diag.unparsed}\n", "step"
                )

            self.results_text.insert(tk.END, "\n")

    def _display_error_text(self, msg: str):
        """Display an error message in the results pane."""
        lang = self.lang.get()
        self.solutions = []

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, _t("error_title", lang) + f":\n{msg}\n", "error")
        self.results_text.config(state=tk.DISABLED)

        self.solve_btn.config(state=tk.NORMAL)
        self.status_var.set(_t("status_error", lang))

    def _show_error(self, msg: str):
        """Display an error message."""
        lang = self.lang.get()
        self.solve_btn.config(state=tk.NORMAL)
        self.status_var.set(_t("status_error", lang))

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, _t("error_title", lang) + f":\n{msg}\n", "error")
        self.results_text.config(state=tk.DISABLED)

        messagebox.showerror(
            _t("error_title", lang),
            _t("error_msg", lang, text=msg),
        )

    def _export_pdf(self):
        """Export solutions to a handwriting-style PDF."""
        if not self.solutions:
            return

        lang = self.lang.get()

        # Ask for save location
        path = filedialog.asksaveasfilename(
            title=_t("save_pdf_title", lang),
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=OUTPUT_DIR,
            initialfile="solutions.pdf",
        )
        if not path:
            return

        self.status_var.set(_t("status_pdf_gen", lang))
        self.pdf_btn.config(state=tk.DISABLED)

        def _export_thread():
            try:
                from handwriting import render_solutions_pdf
                render_solutions_pdf(self.solutions, path, lang=self.lang.get())
                self.root.after(0, self._pdf_done, path)
            except Exception as e:
                self.root.after(0, self._show_error, str(e))

        thread = threading.Thread(target=_export_thread, daemon=True)
        thread.start()

    def _pdf_done(self, path: str):
        """Called when PDF export completes."""
        lang = self.lang.get()
        self.pdf_btn.config(state=tk.NORMAL)
        self.status_var.set(_t("status_pdf_done", lang, name=os.path.basename(path)))
        messagebox.showinfo(
            _t("pdf_success_title", lang),
            _t("pdf_success_msg", lang, text=path),
        )


# ── Launch ─────────────────────────────────────────────────────────────────

def launch_gui():
    """Launch the GUI application."""
    root = tk.Tk()
    MathSolverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
