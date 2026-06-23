#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-flight check for paper build. Run before build_docx.py to catch issues early."""

import sys, os, re, argparse

def check_encoding():
    """Verify stdout can handle UTF-8."""
    sys.stdout.reconfigure(encoding="utf-8")
    return True, "UTF-8 stdout configured"

def check_dependencies():
    """Check all required Python packages."""
    deps = {
        "docx": "python-docx",
        "latex2mathml.converter": "latex2mathml",
        "mathml2omml": "mathml2omml",
        "lxml": "lxml",
    }
    missing = []
    for mod, pkg in deps.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        return False, f"Missing packages: {', '.join(missing)}\n  Install: pip install {' '.join(missing)}"
    return True, "All dependencies installed"

def check_markdown(path):
    """Validate markdown file exists, is UTF-8, and has minimum content."""
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return False, f"File is not UTF-8 encoded: {path}"
    
    if not content.strip():
        return False, "File is empty"
    
    # Check basic structure
    issues = []
    
    # Has abstract
    if "摘要" not in content:
        issues.append("Missing abstract section")
    
    # Has equations
    eq_count = content.count("$$")
    if eq_count < 4:
        issues.append(f"Only {eq_count//2} display equations (suspiciously low)")
    
    # Has tables
    tables = len(re.findall(r"^\|.*\|$", content, re.MULTILINE))
    if tables < 3:
        issues.append(f"Only {tables} table rows (suspiciously low)")
    
    # Content length
    chars = len(re.sub(r"\s", "", content))
    pages_est = chars / 900
    result = {
        "chars": chars,
        "pages": round(pages_est),
        "equations": eq_count // 2,
        "tables": tables,
        "issues": issues,
    }
    
    if chars < 15000:
        return False, f"Content too short: {chars} chars (need 15000+)  Estimated {pages_est:.0f} pages"
    
    if issues:
        return True, f"OK ({chars} chars, ~{pages_est:.0f} pages) with warnings: {'; '.join(issues)}"
    
    return True, f"OK ({chars} chars, ~{pages_est:.0f} pages, {eq_count//2} eqs, {tables} table rows)"

def check_images(md_path):
    """Check [FIGURE:] references point to existing files."""
    base_dir = os.path.dirname(os.path.abspath(md_path))
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    figures = re.findall(r"\[FIGURE:\s*(.+?)\s*\|", content)
    missing = []
    for fig in figures:
        # Try relative to base_dir, then absolute
        if not os.path.exists(fig) and not os.path.exists(os.path.join(base_dir, fig)):
            missing.append(fig)
    
    if missing:
        return False, f"Missing images: {', '.join(missing)}"
    return True, f"All {len(figures)} figures found"

def check_formulas(md_path):
    """Quick check for common LaTeX issues in the markdown."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    issues = []
    
    # Check for unclosed $$
    opens = len(re.findall(r"(?<!\$)\$\$(?!\$)", content))
    if opens % 2 != 0:
        issues.append(f"Unclosed $$ display math ({opens} occurrences)")
    
    # Check for raw aligned that would fail
    aligned_count = content.count(r"\begin{aligned}")
    if aligned_count > 0:
        issues.append(f"Found {aligned_count} \\begin{{aligned}} (will be auto-converted to align*)")
    
    # Check for potential encoding problems
    for char, name in [("\u00b2", "superscript 2"), ("\u00b0", "degree sign")]:
        if char in content:
            issues.append(f"Contains {name} - ensure UTF-8 encoding")
    
    if issues:
        return True, "Minor notes: " + "; ".join(issues)
    return True, "No formula issues detected"

def main():
    ap = argparse.ArgumentParser(description="Pre-flight check for paper build")
    ap.add_argument("markdown", help="Path to markdown paper")
    ap.add_argument("--strict", action="store_true", help="Fail on warnings")
    args = ap.parse_args()
    
    print("=" * 60)
    print("  PRE-FLIGHT CHECK - Paper Build Verification")
    print("=" * 60)
    
    checks = [
        ("Encoding", check_encoding),
        ("Dependencies", check_dependencies),
        ("Markdown file", lambda: check_markdown(args.markdown)),
        ("Images", lambda: check_images(args.markdown)),
        ("Formulas", lambda: check_formulas(args.markdown)),
    ]
    
    passed = 0
    failed = 0
    for name, check_fn in checks:
        ok, msg = check_fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    if failed == 0:
        print(f"  ALL CHECKS PASSED ({passed}/{len(checks)}). Ready to build.")
        print(f"  Run: python scripts/build_docx.py {args.markdown} output/paper.docx")
        return 0
    else:
        print(f"  {failed} CHECK(S) FAILED. Fix issues above before building.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
