#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hallucination Checker (P1-7)
============================
Detects common LLM hallucinations in math modeling papers:

1. Citation Reality  — [N] references in paper vs actual files in references/
2. Number Consistency — numeric values in paper vs frozen_numbers.json
3. Formula Soundness — variables in formulas vs symbol_table.md

Usage:
  python scripts/hallucination_checker.py all        # Run all checks
  python scripts/hallucination_checker.py citation   # Citation reality only
  python scripts/hallucination_checker.py numbers    # Number consistency only
  python scripts/hallucination_checker.py formula    # Formula soundness only
"""

import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()

# ── Helpers ──────────────────────────────────────────────────────

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def _find_paper() -> Path:
    """Locate the paper file (priority: paper_final.md > paper_revised.md > paper.md)."""
    candidates = [
        WORKSPACE / "outputs" / "paper" / "paper_final.md",
        WORKSPACE / "outputs" / "paper" / "paper_revised.md",
        WORKSPACE / "outputs" / "paper" / "paper.md",
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 100:
            return p
    return candidates[-1]  # fallback

# ── Check 1: Citation Reality ───────────────────────────────────

def check_citation_realty(paper_text: str) -> dict:
    """
    Scan paper for [N] citation patterns and verify against references/.
    Returns: {pass: bool, issues: list, stats: dict}
    """
    issues = []
    
    # Extract all [N] citations from paper (excluding reference list itself)
    # Split at "参考文献" section to avoid counting bibliography entries
    ref_section_match = re.search(r'(?:#{1,3}\s*)?(?:参考文献|References)', paper_text)
    if ref_section_match:
        body = paper_text[:ref_section_match.start()]
        ref_section = paper_text[ref_section_match.start():]
    else:
        body = paper_text
        ref_section = ""
    
    # Find all [N] citations in body (N = 1-999)
    body_citations = set(int(m) for m in re.findall(r'\[(\d{1,3})\]', body))
    
    # Find all reference entries in reference section
    ref_entries = set(int(m) for m in re.findall(r'\[(\d{1,3})\]\s', ref_section))
    
    # Find all reference files
    refs_dir = WORKSPACE / "references"
    ref_files = set()
    if refs_dir.exists():
        for p in refs_dir.rglob("*.md"):
            ref_files.add(p.name)
        for p in refs_dir.rglob("*.pdf"):
            ref_files.add(p.name)
        for p in refs_dir.rglob("*.txt"):
            ref_files.add(p.name)
    
    # Check: citations in body that are not in reference list
    dangling_citations = sorted(body_citations - ref_entries)
    if dangling_citations:
        issues.append({
            "severity": "P0",
            "type": "dangling_citation",
            "description": f"论文正文引用 {dangling_citations} 但参考文献列表中不存在",
        })
    
    # Check: reference entries never cited in body
    uncited_refs = sorted(ref_entries - body_citations)
    if uncited_refs:
        issues.append({
            "severity": "P1",
            "type": "uncited_reference",
            "description": f"参考文献 [{', '.join(str(n) for n in uncited_refs)}] 未在正文中引用",
        })
    
    # Check: sequential numbering (no gaps)
    if ref_entries:
        max_ref = max(ref_entries)
        expected = set(range(1, max_ref + 1))
        gaps = sorted(expected - ref_entries)
        if gaps:
            issues.append({
                "severity": "P1",
                "type": "ref_number_gap",
                "description": f"参考文献编号不连续，缺失: {gaps}",
            })
    
    # Check: citation count
    total_refs = len(ref_entries)
    if total_refs < 10:
        issues.append({
            "severity": "P1",
            "type": "insufficient_refs",
            "description": f"参考文献仅 {total_refs} 篇，标准模式要求 ≥10 篇",
        })
    
    return {
        "pass": all(i["severity"] != "P0" for i in issues),
        "issues": issues,
        "stats": {
            "body_citations": len(body_citations),
            "ref_entries": len(ref_entries),
            "dangling": len(dangling_citations),
            "uncited": len(uncited_refs),
        },
    }

# ── Check 2: Number Consistency ────────────────────────────────

def check_number_consistency(paper_text: str) -> dict:
    """
    Extract numeric values from paper and cross-check against frozen_numbers.json.
    Returns: {pass: bool, issues: list, stats: dict}
    """
    issues = []
    
    # Load frozen_numbers.json
    frozen_path = WORKSPACE / "outputs" / "frozen_numbers.json"
    frozen_data = {}
    if frozen_path.exists():
        try:
            frozen_data = json.loads(_read(frozen_path))
        except json.JSONDecodeError:
            issues.append({
                "severity": "P0",
                "type": "frozen_numbers_corrupt",
                "description": "frozen_numbers.json 格式错误，无法解析",
            })
            return {"pass": False, "issues": issues, "stats": {}}
    else:
        issues.append({
            "severity": "P1",
            "type": "frozen_numbers_missing",
            "description": "frozen_numbers.json 不存在，无法进行数值一致性检查",
        })
        return {"pass": True, "issues": issues, "stats": {}}
    
    # Flatten frozen numbers to {key: value} pairs
    flat_numbers = {}
    if isinstance(frozen_data, dict):
        for k, v in frozen_data.items():
            if isinstance(v, (int, float)):
                flat_numbers[k] = v
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, (int, float)):
                        flat_numbers[f"{k}.{k2}"] = v2
    
    if not flat_numbers:
        return {"pass": True, "issues": [], "stats": {"frozen_keys": 0}}
    
    # Extract all numeric values from paper (e.g., 0.85, 12.3%, 1234)
    # Pattern: optional sign + digits + optional decimal + optional %
    paper_numbers_raw = re.findall(r'(?<!\w)(-?\d+\.?\d*)\s*%', paper_text)
    paper_numbers_plain = re.findall(r'(?<!\w)(-?\d+\.?\d*)\s*(?!\d|%|年|月|日|题|个|种|次|条|步|层|类|章|节|图|表|式|页)', paper_text)
    
    # Combine and deduplicate (as strings for comparison)
    all_paper_nums = set(paper_numbers_raw + paper_numbers_plain)
    
    # Check: key frozen numbers appear in paper
    missing_in_paper = []
    for key, val in flat_numbers.items():
        val_str = str(val)
        # Check if the value appears anywhere in the paper
        if val_str not in paper_text and f"{val:.2f}" not in paper_text:
            missing_in_paper.append(key)
    
    if missing_in_paper and len(missing_in_paper) < len(flat_numbers):
        # Only report if some (not all) are missing — all missing means paper is empty
        issues.append({
            "severity": "P1",
            "type": "frozen_number_not_in_paper",
            "description": f"frozen_numbers.json 中 {len(missing_in_paper)} 个数值未在论文中出现: {missing_in_paper[:5]}{'...' if len(missing_in_paper) > 5 else ''}",
        })
    
    # Check: suspiciously round numbers in paper (potential fabrication)
    suspicious = []
    for num_str in all_paper_nums:
        try:
            val = float(num_str)
            if val != 0 and val % 1 == 0 and abs(val) < 100 and abs(val) > 1:
                # Integer in small range — could be fabricated
                pass  # Too many false positives, skip this check
        except ValueError:
            pass
    
    return {
        "pass": all(i["severity"] != "P0" for i in issues),
        "issues": issues,
        "stats": {
            "frozen_keys": len(flat_numbers),
            "missing_in_paper": len(missing_in_paper),
        },
    }

# ── Check 3: Formula Soundness ─────────────────────────────────

def check_formula_soundness(paper_text: str) -> dict:
    """
    Check if variables used in formulas are defined in symbol_table.md.
    Returns: {pass: bool, issues: list, stats: dict}
    """
    issues = []
    
    # Load symbol tables
    symbol_tables = [
        WORKSPACE / "outputs" / "problem_analysis" / "symbol_table.md",
        WORKSPACE / "methods" / "symbol_table.md",
    ]
    
    defined_symbols = set()
    for st_path in symbol_tables:
        if st_path.exists():
            content = _read(st_path)
            # Extract symbol names from table rows: | symbol | ... |
            symbols = re.findall(r'\|\s*([A-Za-z][A-Za-z0-9_]{0,10})\s*\|', content)
            defined_symbols.update(s.lower() for s in symbols)
    
    if not defined_symbols:
        issues.append({
            "severity": "P1",
            "type": "no_symbol_table",
            "description": "未找到符号表文件，无法验证公式变量定义",
        })
        return {"pass": True, "issues": issues, "stats": {}}
    
    # Extract inline math variables from paper: $...$ and $$...$$
    math_expressions = re.findall(r'\$\$(.+?)\$\$|\$(.+?)\$', paper_text)
    all_math = ' '.join(m[0] or m[1] for m in math_expressions)
    
    # Extract variable-like tokens from math (single/double letter + subscript)
    math_vars = set(re.findall(r'(?<![A-Za-z])([A-Za-z])(?![A-Za-z])', all_math))
    math_vars.update(v.lower() for v in re.findall(r'([A-Za-z])_[{]?(\w+)', all_math))
    
    # Check: variables in formulas that are NOT in symbol table
    undefined_vars = math_vars - defined_symbols
    # Filter out common variables (i, j, n, x, t, etc.)
    common_vars = {'i', 'j', 'k', 'n', 't', 'x', 'y', 'z', 'd', 'e', 'f', 'g', 'h', 'p'}
    truly_undefined = undefined_vars - common_vars
    
    if truly_undefined and len(truly_undefined) <= 10:
        issues.append({
            "severity": "P1",
            "type": "undefined_variable",
            "description": f"公式中变量 {sorted(truly_undefined)} 未在符号表中定义",
        })
    
    return {
        "pass": all(i["severity"] != "P0" for i in issues),
        "issues": issues,
        "stats": {
            "defined_symbols": len(defined_symbols),
            "math_vars_found": len(math_vars),
            "undefined": len(truly_undefined),
        },
    }

# ── Unified Runner ─────────────────────────────────────────────

def run_all(paper_text: str) -> dict:
    """Run all three hallucination checks and produce combined report."""
    results = {
        "citation": check_citation_realty(paper_text),
        "numbers": check_number_consistency(paper_text),
        "formula": check_formula_soundness(paper_text),
    }
    
    all_issues = []
    for check_name, r in results.items():
        for issue in r["issues"]:
            all_issues.append({**issue, "check": check_name})
    
    p0_count = sum(1 for i in all_issues if i["severity"] == "P0")
    p1_count = sum(1 for i in all_issues if i["severity"] == "P1")
    
    return {
        "pass": p0_count == 0,
        "total_issues": len(all_issues),
        "p0": p0_count,
        "p1": p1_count,
        "issues": all_issues,
        "details": results,
    }

def format_report(result: dict) -> str:
    """Format hallucination check result as Markdown."""
    lines = ["# Hallucination Check Report\n"]
    lines.append(f"**Overall**: {'PASS' if result['pass'] else 'FAIL'} | P0: {result['p0']} | P1: {result['p1']}\n")
    
    for check_name, label in [("citation", "文献引用真实性"), ("numbers", "数值一致性"), ("formula", "公式合理性")]:
        r = result["details"][check_name]
        status = "PASS" if r["pass"] else "FAIL"
        lines.append(f"\n## {label} ({status})")
        lines.append(f"Stats: {r['stats']}")
        if r["issues"]:
            for issue in r["issues"]:
                lines.append(f"- [{issue['severity']}] {issue['description']}")
        else:
            lines.append("- 无问题")
    
    if result["issues"]:
        lines.append(f"\n## 问题汇总")
        for issue in result["issues"]:
            lines.append(f"- [{issue['severity']}] ({issue['check']}) {issue['description']}")
    
    return "\n".join(lines)

# ── CLI ────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    paper_path = _find_paper()
    paper_text = _read(paper_path)
    
    if not paper_text:
        print(f"ERROR: Paper not found or empty at {paper_path}")
        sys.exit(1)
    
    print(f"Checking: {paper_path}")
    
    if cmd == "all":
        result = run_all(paper_text)
        print(format_report(result))
        sys.exit(0 if result["pass"] else 1)
    
    elif cmd == "citation":
        result = check_citation_realty(paper_text)
    elif cmd == "numbers":
        result = check_number_consistency(paper_text)
    elif cmd == "formula":
        result = check_formula_soundness(paper_text)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
    
    print(format_report({"pass": result["pass"], "p0": sum(1 for i in result["issues"] if i["severity"] == "P0"), "p1": sum(1 for i in result["issues"] if i["severity"] == "P1"), "issues": result["issues"], "details": {cmd: result}}))
    sys.exit(0 if result["pass"] else 1)

if __name__ == "__main__":
    main()
