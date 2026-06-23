# -*- coding: utf-8 -*-
"""Comprehensive paper review script - Phase 1: Quality Gates"""
import sys, os, re, zipfile, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

_WS = resolve_workspace()
DOCX_PATH = _WS / "output" / "paper_final.docx"
MD_PATH = _WS / "output" / "draft_paper.md"

print("=" * 70)
print("  MATH MODELING CONTEST - PAPER QUALITY REVIEW")
print("=" * 70)

# ---- Gate 1: Table Formula Rendering ----
print("\n[Gate 1] Table Formula Rendering Check")
print("-" * 50)
if DOCX_PATH.exists():
    with zipfile.ZipFile(DOCX_PATH, "r") as z:
        xml = z.read("word/document.xml").decode("utf-8")
    tcs = re.findall(r"<w:tc>(.*?)</w:tc>", xml, re.DOTALL)
    raw_dollar = 0
    omml_cells = 0
    total_formula_cells = 0
    for tc in tcs:
        has_raw = bool(re.search(r"<w:t[^>]*>\$[^<]*\$</w:t>", tc))
        has_omml = "<m:oMath" in tc
        if has_raw: raw_dollar += 1
        if has_omml: omml_cells += 1
        if has_raw or has_omml: total_formula_cells += 1
    
    if total_formula_cells == 0:
        print("  RESULT: PASS - No formula cells in tables")
    else:
        fail_rate = raw_dollar / total_formula_cells
        if fail_rate > 0.05:
            print(f"  RESULT: FAIL - {raw_dollar}/{total_formula_cells} unconverted ({fail_rate*100:.0f}%)")
        elif raw_dollar > 0:
            print(f"  RESULT: WARN - {raw_dollar}/{total_formula_cells} unconverted (under 5%)")
        else:
            print(f"  RESULT: PASS - {omml_cells} OMML cells, 0 unconverted")
else:
    print(f"  RESULT: SKIP - DOCX not found at {DOCX_PATH}")

# ---- Gate 2: Overall OMML check ----
print("\n[Gate 2] Overall Equation Rendering (OMML)")
print("-" * 50)
if DOCX_PATH.exists():
    with zipfile.ZipFile(DOCX_PATH, "r") as z:
        xml = z.read("word/document.xml").decode("utf-8")
    omml_count = len(re.findall(r"<m:oMathPara", xml)) + len(re.findall(r"<m:oMath[^P]", xml))
    raw_dollar_all = len(re.findall(r"<w:t[^>]*>\$[^<]*\$</w:t>", xml))
    print(f"  OMML equation blocks: {omml_count}")
    print(f"  Raw dollar-sign text remaining: {raw_dollar_all}")
    if raw_dollar_all == 0:
        print("  RESULT: PASS - All formulas converted to OMML")
    else:
        print(f"  RESULT: FAIL - {raw_dollar_all} raw dollar-sign formulas remain")
else:
    print(f"  RESULT: SKIP - DOCX not found")

# ---- Gate 3: Content Completeness ----
print("\n[Gate 3] Content Completeness")
print("-" * 50)
if MD_PATH.exists():
    content = MD_PATH.read_text(encoding="utf-8")
    chars = len(content)
    display_eqs = len(re.findall(r'\$\$.*?\$\$', content, re.DOTALL))
    inline_eqs = len(re.findall(r'(?<!\$)\$[^$]+?\$(?!\$)', content))
    total_eqs = display_eqs + inline_eqs
    tables = len(re.findall(r'^\|.*\|$', content, re.MULTILINE)) // 2  # rough count
    refs = len(re.findall(r'\[\d+\]', content))
    
    print(f"  Total characters: {chars:,} (target: >=15,000)")
    print(f"  Display equations ($$): {display_eqs}")
    print(f"  Inline equations ($): {inline_eqs}")
    print(f"  Total equations: {total_eqs} (target: >=20)")
    print(f"  Approx tables: {tables}")
    print(f"  References found: {refs}")
    
    issues = []
    if chars < 15000:
        issues.append(f"Content too short: {chars:,} < 15,000 chars")
    if total_eqs < 20:
        issues.append(f"Too few equations: {total_eqs} < 20")
    if tables < 7:
        issues.append(f"Too few tables: {tables} < 7")
    if refs < 8:
        issues.append(f"Too few references: {refs} < 8")
    
    if issues:
        print(f"  RESULT: FAIL - {len(issues)} issues found:")
        for i in issues:
            print(f"    - {i}")
    else:
        print("  RESULT: PASS")
else:
    print(f"  RESULT: SKIP - Markdown not found")

# ---- Gate 4: Structure Completeness ----
print("\n[Gate 4] Section Structure")
print("-" * 50)
required_sections = [
    ("标题/Title", r"^#\s+"),
    ("摘要/Abstract", r"摘要|Abstract"),
    ("问题重述/Problem Restatement", r"问题重述|Problem\s+Restatement"),
    ("问题分析/Problem Analysis", r"问题分析|Problem\s+Analysis"),
    ("模型假设/Assumptions", r"模型假设|模型基本假设|Assumptions"),
    ("符号说明/Notation", r"符号说明|Notation|符号表"),
    ("模型建立与求解/Model", r"模型.*建立|Model.*(Formulation|Building)"),
    ("模型评价/Evaluation", r"模型评价|模型检验|Model\s+Eval"),
    ("参考文献/References", r"参考|Refer"),
    ("附录/Appendix", r"附录|Append"),
]
if MD_PATH.exists():
    content = MD_PATH.read_text(encoding="utf-8")
    found = []
    missing = []
    for name, pattern in required_sections:
        if re.search(pattern, content, re.IGNORECASE):
            found.append(name)
        else:
            missing.append(name)
    print(f"  Found sections ({len(found)}/10): {', '.join(found)}")
    if missing:
        print(f"  Missing sections: {', '.join(missing)}")
        print(f"  RESULT: WARN - {len(missing)} sections missing")
    else:
        print("  RESULT: PASS - All required sections present")

# ---- Gate 5: Writing Quality Anti-patterns ----
print("\n[Gate 5] Writing Quality - AI Anti-pattern Detection")
print("-" * 50)
anti_patterns = [
    (r'值得注意的是', "AI filler: '值得注意的是'"),
    (r'总而言之', "AI filler: '总而言之'"),
    (r'正如前文所述', "AI filler: '正如前文所述'"),
    (r'毋庸置疑', "AI filler: '毋庸置疑'"),
    (r'显然', "Vague claim: '显然'"),
    (r'不难发现', "Vague claim: '不难发现'"),
    (r'众所周知', "Vague claim: '众所周知'"),
    (r'具有重要的(现实)?意义', "Generic significance claim"),
    (r'为.*提供了.*参考', "Generic conclusion: '提供了参考'"),
]
if MD_PATH.exists():
    content = MD_PATH.read_text(encoding="utf-8")
    total_hits = 0
    for pattern, desc in anti_patterns:
        hits = len(re.findall(pattern, content))
        if hits > 0:
            print(f"  {desc}: {hits} occurrence(s)")
            total_hits += hits
    if total_hits == 0:
        print("  RESULT: PASS - No AI anti-patterns detected")
    elif total_hits <= 3:
        print(f"  RESULT: WARN - {total_hits} anti-pattern(s) detected (minor)")
    else:
        print(f"  RESULT: FAIL - {total_hits} anti-patterns detected (significant)")

# ---- Gate 6: Model Chapter Depth ----
print("\n[Gate 6] Model Chapter Depth (chars per sub-problem)")
print("-" * 50)
if MD_PATH.exists():
    content = MD_PATH.read_text(encoding="utf-8")
    # Find model chapters (sections after 模型建立)
    sections = re.split(r'\n##\s+', content)
    model_sections = [s for s in sections if re.search(r'模型|Model|问题[一二三四五六]|Problem\s*\d', s)]
    for i, sec in enumerate(model_sections):
        header = sec.split('\n')[0][:60] if sec else "(empty)"
        char_count = len(sec)
        status = "OK" if char_count >= 2000 else "SHORT"
        print(f"  Section {i+1} [{header}]: {char_count} chars - {status}")

print("\n" + "=" * 70)
print("  QUALITY GATE REVIEW COMPLETE")
print("=" * 70)
