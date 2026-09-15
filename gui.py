#!/usr/bin/env python3
"""
MathExerciseSolver — Tkinter GUI.
Provides a simple windowed interface for loading images and viewing solutions.
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


# ── Main GUI Class ─────────────────────────────────────────────────────────

class MathSolverGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(GUI_WINDOW_TITLE)
        self.root.geometry(GUI_WINDOW_SIZE)
        self.root.configure(bg=GUI_BG_COLOR)

        self.image_path = None
        self.solutions = []
        self.lang = tk.StringVar(value=DEFAULT_LANGUAGE)
        self.status_var = tk.StringVar(value="Gotowy")

        self._build_ui()

    def _build_ui(self):
        """Build the GUI layout."""
        # ── Top toolbar ────────────────────────────────────────────────
        toolbar = tk.Frame(self.root, bg=GUI_BG_COLOR, pady=5)
        toolbar.pack(fill=tk.X)

        self.open_btn = tk.Button(
            toolbar, text="📂 Otwórz obraz", command=self._open_image,
            font=("Segoe UI", 11), padx=10, pady=3,
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.solve_btn = tk.Button(
            toolbar, text="🔢 Rozwiąż", command=self._solve,
            font=("Segoe UI", 11, "bold"), padx=10, pady=3,
            state=tk.DISABLED,
        )
        self.solve_btn.pack(side=tk.LEFT, padx=5)

        self.pdf_btn = tk.Button(
            toolbar, text="📄 Eksportuj PDF", command=self._export_pdf,
            font=("Segoe UI", 11), padx=10, pady=3,
            state=tk.DISABLED,
        )
        self.pdf_btn.pack(side=tk.LEFT, padx=5)

        # Language toggle
        lang_frame = tk.Frame(toolbar, bg=GUI_BG_COLOR)
        lang_frame.pack(side=tk.RIGHT, padx=10)

        tk.Label(lang_frame, text="Język:", bg=GUI_BG_COLOR, font=("Segoe UI", 10)).pack(side=tk.LEFT)
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

        tk.Label(left, text="Obraz wejściowy", bg="#e0e0e0",
                 font=("Segoe UI", 10, "bold")).pack(pady=5)

        self.preview_label = tk.Label(left, text="Brak obrazu", bg="#e0e0e0",
                                       fg="#888", font=("Segoe UI", 12))
        self.preview_label.pack(expand=True)

        # Right panel: solutions
        right = tk.Frame(content, bg=GUI_BG_COLOR)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        tk.Label(right, text="Rozwiązania", bg=GUI_BG_COLOR,
                 font=("Segoe UI", 10, "bold")).pack(pady=5)

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
        filetypes = [
            ("Obrazy", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Wszystkie pliki", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Wybierz obraz z zadaniami",
            filetypes=filetypes,
        )
        if path:
            self.image_path = path
            self._show_preview(path)
            self.solve_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Załadowano: {os.path.basename(path)}")

    def _show_preview(self, path: str):
        """Display the image in the preview panel."""
        try:
            img = Image.open(path)
            img.thumbnail((GUI_PREVIEW_MAX_WIDTH, GUI_PREVIEW_MAX_HEIGHT), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.preview_label.config(image=photo, text="")
            self.preview_label._photo = photo  # prevent GC
        except Exception as e:
            self.preview_label.config(text=f"Błąd: {e}", image="")

    def _solve(self):
        """Run the solve pipeline in a background thread."""
        if not self.image_path:
            return

        self.solve_btn.config(state=tk.DISABLED)
        self.pdf_btn.config(state=tk.DISABLED)
        self.status_var.set("Przetwarzanie...")

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
            solutions = run_pipeline(
                image_path=self.image_path,
                lang=self.lang.get(),
                use_latex=True,
                generate_pdf=False,
                verbose=False,
            )
            self.root.after(0, self._display_solutions, solutions)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _display_solutions(self, solutions: list):
        """Display solutions in the results text widget."""
        self.solutions = solutions

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)

        if not solutions:
            self.results_text.insert(tk.END, "Nie udało się rozpoznać zadań.\n\n")
            self.results_text.insert(tk.END, "Wskazówki:\n")
            self.results_text.insert(tk.END, "  • Upewnij się, że obraz jest wyraźny\n")
            self.results_text.insert(tk.END, "  • Zadania powinny być numerowane (1., 2., itp.)\n")
            self.results_text.insert(tk.END, "  • Spróbuj przyciąć obraz do samych zadań\n")
        else:
            solved = sum(1 for s in solutions if s.is_valid)
            self.results_text.insert(tk.END, f"═══ Rozwiązano {solved}/{len(solutions)} zadań ═══\n\n", "title")

            for i, sol in enumerate(solutions):
                # Heading
                self.results_text.insert(tk.END, f"#{i + 1}  [{sol.method}]\n", "heading")

                # Problem
                self.results_text.insert(tk.END, f"  Zadanie: {sol.problem}\n", "problem")

                # Steps
                for step in sol.steps:
                    self.results_text.insert(tk.END, f"    → {step.text}\n", "step")
                    if step.math:
                        self.results_text.insert(tk.END, f"      {step.math}\n", "step")

                # Answer
                self.results_text.insert(tk.END, f"\n  ✓ Odpowiedź: {sol.answer}\n\n", "answer")

                # Separator
                if i < len(solutions) - 1:
                    self.results_text.insert(tk.END, "────────────────────────────────────────\n")

        self.results_text.config(state=tk.DISABLED)

        # Update buttons
        self.solve_btn.config(state=tk.NORMAL)
        if solutions:
            self.pdf_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Gotowo — {len(solutions)} zadań")

    def _show_error(self, msg: str):
        """Display an error message."""
        self.solve_btn.config(state=tk.NORMAL)
        self.status_var.set("Błąd")

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, f"Błąd:\n{msg}\n", "error")
        self.results_text.config(state=tk.DISABLED)

        messagebox.showerror("Błąd", f"Wystąpił błąd:\n{msg}")

    def _export_pdf(self):
        """Export solutions to a handwriting-style PDF."""
        if not self.solutions:
            return

        # Ask for save location
        path = filedialog.asksaveasfilename(
            title="Zapisz PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=OUTPUT_DIR,
            initialfile="solutions.pdf",
        )
        if not path:
            return

        self.status_var.set("Generowanie PDF...")
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
        self.pdf_btn.config(state=tk.NORMAL)
        self.status_var.set(f"PDF zapisany: {os.path.basename(path)}")
        messagebox.showinfo("Sukces", f"Plik PDF zapisany:\n{path}")


# ── Launch ─────────────────────────────────────────────────────────────────

def launch_gui():
    """Launch the GUI application."""
    root = tk.Tk()
    MathSolverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
