#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX to PDF Compiler — 编译 LaTeX 为 PDF

Detects available LaTeX engine (xelatex > pdflatex) and compiles the paper.
Supports both CUMCM (Chinese) and MCM/ICM (English) templates.

Usage:
    python main.py compile-pdf paper.tex
    python main.py compile-pdf paper.tex --engine xelatex
    python main.py compile-pdf paper.tex --output-dir ./output
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_latex_engine() -> str:
    """Find available LaTeX engine. Prefer xelatex for Unicode support."""
    for engine in ["xelatex", "pdflatex", "lualatex"]:
        if shutil.which(engine):
            return engine
    return ""


def compile_pdf(main_file: str, engine: str = "", output_dir: str = None) -> bool:
    """
    Compile LaTeX to PDF. Returns True on success.
    
    Args:
        main_file: Path to .tex file
        engine: LaTeX engine (auto-detected if empty)
        output_dir: Output directory for PDF (default: same as .tex)
    """
    main_path = Path(main_file).resolve()
    if not main_path.exists():
        print(f"[compile] ERROR: File not found: {main_path}")
        return False

    tex_dir = main_path.parent
    tex_name = main_path.stem

    if not engine:
        engine = find_latex_engine()
        if not engine:
            print("[compile] ERROR: No LaTeX engine found.")
            print("  Install TeX Live (https://tug.org/texlive/) or MiKTeX (https://miktex.org/)")
            return False

    print(f"[compile] Using engine: {engine}")
    print(f"[compile] Source: {main_path}")

    # Run LaTeX twice for proper cross-references
    for run in range(1, 3):
        print(f"[compile] Pass {run}/2...")

        result = subprocess.run(
            [engine,
             "-synctex=1",
             "-interaction=nonstopmode",
             "-file-line-error",
             "-output-directory", str(tex_dir),
             str(main_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(tex_dir),
        )

        if result.returncode != 0:
            errors = []
            for line in result.stdout.split("\n") + result.stderr.split("\n"):
                if line.startswith("!"):
                    errors.append(line.strip())
            if errors:
                print(f"[compile] Errors in pass {run}:")
                for e in errors[:10]:
                    print(f"  {e}")
            print(f"[compile] Full log: {tex_dir}/{tex_name}.log")
            return False

        print(f"[compile] Pass {run} OK")

    # Copy PDF to output directory
    pdf_src = tex_dir / f"{tex_name}.pdf"
    if pdf_src.exists():
        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            pdf_dst = out / f"{tex_name}.pdf"
            shutil.copy(pdf_src, pdf_dst)
            print(f"[compile] SUCCESS: PDF -> {pdf_dst}")
            print(f"[compile] Size: {pdf_dst.stat().st_size / 1024:.1f} KB")
        else:
            print(f"[compile] SUCCESS: {pdf_src}")
            print(f"[compile] Size: {pdf_src.stat().st_size / 1024:.1f} KB")

        # Auto-cleanup compile artifacts
        for ext in [".aux", ".log", ".toc", ".synctex.gz", ".out"]:
            artifact = tex_dir / f"{tex_name}{ext}"
            if artifact.exists():
                try:
                    os.remove(str(artifact))
                except Exception:
                    pass

        return True
    else:
        print(f"[compile] ERROR: PDF not generated at {pdf_src}")
        return False


def cmd_compile_pdf(args):
    """CLI: Compile LaTeX to PDF."""
    success = compile_pdf(args.file, args.engine, args.output_dir)
    sys.exit(0 if success else 1)
