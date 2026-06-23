#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assumption_engineer.py - Assumption Engineering Engine v2.0

Features:
  1. analyze   - Extract and classify assumptions from documents
  2. validate  - Validate assumption completeness
  3. report    - Generate assumption engineering report
  4. template  - Generate standard assumption templates

Assumption types:
  - hard  : Violation invalidates model, needs consequence analysis
  - soft  : Simplifies model, needs quantification
  - scope : Defines boundaries, needs out-of-scope notes
  - data  : About data quality, needs verification method
"""
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import re
from pathlib import Path
from datetime import datetime

__version__ = "2.0.0"

ASSUMPTION_TYPES = {
    "hard": {
        "name": "Hard Assumption",
        "desc": "Violation invalidates model entirely",
        "required_fields": ["statement", "rationale", "consequence", "validation"],
        "weight": 3.0,
    },
    "soft": {
        "name": "Soft Assumption",
        "desc": "Reduces complexity, needs error bound",
        "required_fields": ["statement", "rationale", "quantification", "sensitivity"],
        "weight": 2.0,
    },
    "scope": {
        "name": "Scope Assumption",
        "desc": "Defines problem boundary",
        "required_fields": ["statement", "rationale", "boundary", "out_of_scope"],
        "weight": 1.5,
    },
    "data": {
        "name": "Data Assumption",
        "desc": "About data quality/distribution",
        "required_fields": ["statement", "rationale", "verification", "impact"],
        "weight": 2.5,
    },
}

ASSUMPTION_PATTERNS = [
    (r"假设\s*[：:]\s*(.+)", "explicit_cn"),
    (r"我们假设\s*(.+)", "we_assume_cn"),
    (r"假定\s*(.+)", "assume_cn"),
    (r"设\s*(.+?)(?:[，。；])", "let_cn"),
    (r"认为\s*(.+?)(?:[，。；])", "consider_cn"),
    (r"忽略\s*(.+?)(?:[，。；])", "ignore_cn"),
    (r"不考虑\s*(.+?)(?:[，。；])", "not_consider_cn"),
    (r"近似\s*(.+?)(?:[，。；])", "approximate_cn"),
    (r"简化为\s*(.+?)(?:[，。；])", "simplify_cn"),
    (r"[Aa]ssumption\s*\d*\s*[.:]\s*(.+)", "explicit_en"),
    (r"[Ww]e assume\s+(that\s+)?(.+)", "we_assume_en"),
    (r"[Ll]et us assume\s+(.+)", "let_assume_en"),
    (r"[Ii]t is assumed\s+(that\s+)?(.+)", "it_assumed_en"),
    (r"[Ww]e neglect\s+(.+)", "neglect_en"),
    (r"[Ww]e ignore\s+(.+)", "ignore_en"),
    (r"[Ww]e approximate\s+(.+)", "approximate_en"),
]

RATIONALE_INDICATORS = {
    "strong": ["based on", "according to", "due to", "since",
               "because", "proven by", "validated by"],
    "medium": ["reasonable", "typically", "generally", "empirical",
               "common practice", "well-known"],
    "weak": ["for simplicity", "approximately", "roughly"],
}

RATIONALE_CN = {
    "strong": ["based on", "according to", "due to", "since",
               "because", "proven by", "validated by"],
    "medium": ["reasonable", "typically", "generally", "empirical"],
    "weak": ["for simplicity", "approximately"],
}

QUANTIFICATION_PATTERNS = [
    r"\d+%", r"\d+\.\d+", r"O\(.+?\)",
    r"error\s*[<]", r"accuracy\s*[>]",
    r"within\s+\d+", r"less than\s+\d+",
]

CONSEQUENCE_PATTERNS = [
    "if.*not", "violate", "fail", "invalid", "break down",
    "no longer", "inapplicable", "cannot",
]


def extract_assumptions(text):
    """Extract assumptions from text, return structured list."""
    assumptions = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        for pattern, ptype in ASSUMPTION_PATTERNS:
            m = re.search(pattern, line_stripped)
            if m:
                groups = [g for g in m.groups() if g]
                statement = groups[-1].strip() if groups else line_stripped

                ctx_start = max(0, i - 3)
                ctx_end = min(len(lines), i + 4)
                context = "\n".join(lines[ctx_start:ctx_end])

                assumptions.append({
                    "id": "A{:03d}".format(len(assumptions) + 1),
                    "statement": statement,
                    "raw_line": line_stripped,
                    "line_number": i + 1,
                    "pattern_type": ptype,
                    "context": context,
                    "type": _classify_type(statement, context),
                    "has_rationale": _check_rationale(context),
                    "rationale_strength": _rate_rationale(context),
                    "has_quantification": _check_quantification(context),
                    "has_consequence": _check_consequence(context),
                })
                break

    return assumptions


def _classify_type(statement, context):
    """Auto-classify assumption type based on content."""
    combined = (statement + " " + context).lower()

    data_kw = ["data", "sample", "distribution", "missing", "noise",
               "training", "test set"]
    if any(kw in combined for kw in data_kw):
        return "data"

    scope_kw = ["scope", "boundary", "only consider", "limited to",
                "range", "within"]
    if any(kw in combined for kw in scope_kw):
        return "scope"

    soft_kw = ["simplif", "approximat", "neglect", "linear", "uniform",
               "ignore", "assume.*constant"]
    if any(kw in combined for kw in soft_kw):
        return "soft"

    return "hard"


def _check_rationale(context):
    """Check if assumption has rationale."""
    for strength, patterns in RATIONALE_INDICATORS.items():
        for p in patterns:
            if p in context.lower():
                return True
    return False


def _rate_rationale(context):
    """Rate rationale strength."""
    ctx_lower = context.lower()
    for strength in ["strong", "medium", "weak"]:
        for p in RATIONALE_INDICATORS[strength]:
            if p in ctx_lower:
                return strength
    return "none"


def _check_quantification(context):
    """Check for quantification."""
    for p in QUANTIFICATION_PATTERNS:
        if re.search(p, context):
            return True
    return False


def _check_consequence(context):
    """Check for consequence statement."""
    ctx_lower = context.lower()
    for p in CONSEQUENCE_PATTERNS:
        if p in ctx_lower:
            return True
    return False


def validate_assumptions(assumptions, strict=False):
    """Validate assumption completeness and quality."""
    if not assumptions:
        return {
            "total": 0, "by_type": {},
            "quality_score": 0.0,
            "issues": [{"severity": "CRITICAL", "msg": "No assumptions detected"}],
            "passed": False,
        }

    by_type = {}
    issues = []
    total_score = 0.0
    max_score = 0.0

    for a in assumptions:
        atype = a["type"]
        by_type[atype] = by_type.get(atype, 0) + 1
        type_info = ASSUMPTION_TYPES.get(atype, ASSUMPTION_TYPES["hard"])
        weight = type_info["weight"]
        max_score += weight * 100

        a_score = 0.0
        if a["statement"]:
            a_score += 20

        if a["has_rationale"]:
            bonus = {"strong": 30, "medium": 20, "weak": 10, "none": 0}
            a_score += bonus.get(a["rationale_strength"], 0)
        else:
            issues.append({
                "severity": "HIGH", "assumption_id": a["id"],
                "msg": "Missing rationale: " + a["statement"][:50],
            })

        if a["has_quantification"]:
            a_score += 25
        elif atype in ("soft", "data"):
            issues.append({
                "severity": "MEDIUM", "assumption_id": a["id"],
                "msg": "Missing quantification: " + a["statement"][:50],
            })

        if a["has_consequence"]:
            a_score += 25
        elif atype == "hard":
            issues.append({
                "severity": "HIGH", "assumption_id": a["id"],
                "msg": "Missing consequence: " + a["statement"][:50],
            })

        total_score += a_score * weight

    quality_score = (total_score / max_score * 100) if max_score > 0 else 0.0
    total = len(assumptions)

    if total < 3:
        issues.append({
            "severity": "HIGH",
            "msg": "Too few assumptions ({}), need at least 3-5".format(total),
        })

    if "hard" not in by_type:
        issues.append({
            "severity": "MEDIUM",
            "msg": "No hard assumptions; every model needs at least 1",
        })

    passed = quality_score >= 60 and not any(
        i["severity"] == "CRITICAL" for i in issues)
    if strict:
        passed = passed and not any(
            i["severity"] == "HIGH" for i in issues)

    return {
        "total": total, "by_type": by_type,
        "quality_score": round(quality_score, 1),
        "issues": issues, "passed": passed,
    }


def generate_report(assumptions, validation, source_file=""):
    """Generate assumption engineering report in Markdown."""
    lines = []
    lines.append("# Assumption Engineering Report")
    lines.append("> Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    if source_file:
        lines.append("> Source: " + source_file)
    lines.append("")

    lines.append("## 1. Summary")
    lines.append("- Total assumptions: **{}**".format(validation["total"]))
    lines.append("- Quality score: **{}/100**".format(validation["quality_score"]))
    lines.append("- Result: **{}**".format("PASS" if validation["passed"] else "FAIL"))
    lines.append("")

    lines.append("## 2. Type Distribution")
    lines.append("| Type | Count | Description |")
    lines.append("|------|-------|-------------|")
    for atype, info in ASSUMPTION_TYPES.items():
        count = validation["by_type"].get(atype, 0)
        lines.append("| {} | {} | {} |".format(info["name"], count, info["desc"]))
    lines.append("")

    lines.append("## 3. Per-Assumption Analysis")
    for a in assumptions:
        type_info = ASSUMPTION_TYPES.get(a["type"], ASSUMPTION_TYPES["hard"])
        lines.append("### {}: {}".format(a["id"], type_info["name"]))
        lines.append("- **Statement**: " + a["statement"])
        lines.append("- **Line**: {}".format(a["line_number"]))
        ration = "Yes ({})".format(a["rationale_strength"]) if a["has_rationale"] else "No"
        lines.append("- **Rationale**: " + ration)
        quant = "Yes" if a["has_quantification"] else "No"
        lines.append("- **Quantification**: " + quant)
        consq = "Yes" if a["has_consequence"] else "No"
        lines.append("- **Consequence**: " + consq)

        flags = []
        if not a["has_rationale"]:
            flags.append("missing rationale")
        if not a["has_quantification"] and a["type"] in ("soft", "data"):
            flags.append("missing quantification")
        if not a["has_consequence"] and a["type"] == "hard":
            flags.append("missing consequence")
        if flags:
            lines.append("- **Issues**: " + ", ".join(flags))
        lines.append("")

    if validation["issues"]:
        lines.append("## 4. Issues")
        for i, issue in enumerate(validation["issues"], 1):
            aid = issue.get("assumption_id", "")
            lines.append("{}. [{}] {} {}".format(
                i, issue["severity"], aid, issue["msg"]))
        lines.append("")

    lines.append("## 5. Recommendations")
    score = validation["quality_score"]
    if score < 40:
        lines.append("- Assumptions are too brief; use complete sentences")
        lines.append("- Add rationale citing literature or physical laws")
    elif score < 70:
        lines.append("- Add quantification (error bounds, precision ranges)")
        lines.append("- Add consequence analysis for hard assumptions")
    else:
        lines.append("- Quality is good; add sensitivity analysis to validate")
    lines.append("")

    return "\n".join(lines)


TEMPLATES = {
    "optimization": [
        {"type": "hard", "statement": "Decision variables satisfy [constraints]",
         "rationale": "Physical meaning of variables determines feasible range"},
        {"type": "soft", "statement": "[Nonlinear relation] approximated as [linear]",
         "rationale": "Within operating range, nonlinear contribution < X%"},
        {"type": "scope", "statement": "Model considers only [scope]",
         "rationale": "Beyond this scope, [factor] cannot be ignored"},
        {"type": "data", "statement": "Input data [field] missing rate < X%",
         "rationale": "Verified by data quality check"},
    ],
    "prediction": [
        {"type": "hard", "statement": "Statistical features stable over [period]",
         "rationale": "Domain knowledge / statistical test confirms stability"},
        {"type": "soft", "statement": "Noise follows [distribution], mean=0, var=sigma^2",
         "rationale": "CLT / empirical distribution fitting"},
        {"type": "data", "statement": "Train and test sets from same distribution",
         "rationale": "Consistent data collection, no systematic bias"},
        {"type": "scope", "statement": "Prediction limited to [horizon]",
         "rationale": "Long-term trends affected by unmodeled factors"},
    ],
    "evaluation": [
        {"type": "hard", "statement": "Indicator system covers all core dimensions",
         "rationale": "Literature / expert opinion confirms representativeness"},
        {"type": "soft", "statement": "Indicators satisfy [independence condition]",
         "rationale": "Correlation analysis / VIF test confirms"},
        {"type": "data", "statement": "Evaluation data complete, no systematic gaps",
         "rationale": "Data quality report confirms"},
        {"type": "scope", "statement": "Results applicable only to [scenario]",
         "rationale": "Different scenarios may need different weights"},
    ],
    "simulation": [
        {"type": "hard", "statement": "Input parameters follow [distribution]",
         "rationale": "Data fitting / physical mechanism determines distribution"},
        {"type": "soft", "statement": "[Complex process] simplified to [simple]",
         "rationale": "Simplification error within [quantified range]"},
        {"type": "data", "statement": "Simulation runs >= N times, results converge",
         "rationale": "Convergence analysis determines minimum runs"},
        {"type": "scope", "statement": "Simulation limited to [conditions]",
         "rationale": "Extreme scenarios probability < X%"},
    ],
}


def generate_template(problem_type):
    """Generate assumption template for problem type."""
    templates = TEMPLATES.get(problem_type)
    if not templates:
        available = ", ".join(TEMPLATES.keys())
        return "Unknown type: {}. Available: {}".format(problem_type, available)

    lines = []
    lines.append("# Assumption Template: " + problem_type.title())
    lines.append("")
    lines.append("> Modify these templates with your specific content.")
    lines.append("> Each assumption needs: statement + rationale + quantification")
    lines.append("")

    for i, t in enumerate(templates, 1):
        info = ASSUMPTION_TYPES[t["type"]]
        lines.append("## Assumption {}: {}".format(i, info["name"]))
        lines.append("- **Type**: {} ({})".format(t["type"], info["name"]))
        lines.append("- **Statement**: " + t["statement"])
        lines.append("- **Rationale**: " + t["rationale"])
        lines.append("- **Consequence if violated**: [fill in]")
        lines.append("- **Sensitivity**: [how does +/-X% change affect results?]")
        lines.append("")

    return "\n".join(lines)


def cmd_analyze(args):
    """Analyze assumptions in a file."""
    text = Path(args.file).read_text(encoding="utf-8")
    assumptions = extract_assumptions(text)
    validation = validate_assumptions(assumptions, strict=args.strict)

    if args.output:
        report = generate_report(assumptions, validation, source_file=args.file)
        Path(args.output).write_text(report, encoding="utf-8")
        print("[OK] Report saved to " + args.output)
    else:
        print("Extracted {} assumptions from {}".format(len(assumptions), args.file))
        print("Quality score: {}/100".format(validation["quality_score"]))
        print("Result: {}".format("PASS" if validation["passed"] else "FAIL"))
        for a in assumptions:
            info = ASSUMPTION_TYPES.get(a["type"], ASSUMPTION_TYPES["hard"])
            flags = []
            if not a["has_rationale"]:
                flags.append("no-rationale")
            if not a["has_quantification"]:
                flags.append("no-quant")
            if not a["has_consequence"]:
                flags.append("no-conseq")
            flag_str = " [" + ",".join(flags) + "]" if flags else ""
            print("  {} [{}] {}{}".format(a["id"], a["type"], a["statement"][:60], flag_str))

    if not validation["passed"]:
        sys.exit(1)


def cmd_validate(args):
    """Validate assumptions in a file."""
    text = Path(args.file).read_text(encoding="utf-8")
    assumptions = extract_assumptions(text)
    validation = validate_assumptions(assumptions, strict=args.strict)

    print("Validation: {}".format("PASS" if validation["passed"] else "FAIL"))
    print("Score: {}/100".format(validation["quality_score"]))
    print("Total: {} | By type: {}".format(
        validation["total"], json.dumps(validation["by_type"])))

    if validation["issues"]:
        print("\nIssues:")
        for issue in validation["issues"]:
            print("  [{}] {}".format(issue["severity"], issue["msg"]))

    if not validation["passed"]:
        sys.exit(1)


def cmd_report(args):
    """Generate full report."""
    text = Path(args.file).read_text(encoding="utf-8")
    assumptions = extract_assumptions(text)
    validation = validate_assumptions(assumptions, strict=args.strict)
    report = generate_report(assumptions, validation, source_file=args.file)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print("[OK] Report saved to " + args.output)
    else:
        print(report)


def cmd_template(args):
    """Generate assumption template."""
    result = generate_template(args.type)
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print("[OK] Template saved to " + args.output)
    else:
        print(result)


def main():
    parser = argparse.ArgumentParser(
        description="assumption_engineer.py v2.0 - Assumption Engineering Engine")
    sub = parser.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Extract and analyze assumptions")
    p_analyze.add_argument("file", help="Input file path")
    p_analyze.add_argument("--output", "-o", help="Output report path")
    p_analyze.add_argument("--strict", action="store_true", help="Strict mode")
    p_analyze.set_defaults(func=cmd_analyze)

    p_validate = sub.add_parser("validate", help="Validate assumption quality")
    p_validate.add_argument("file", help="Input file path")
    p_validate.add_argument("--strict", action="store_true", help="Strict mode")
    p_validate.set_defaults(func=cmd_validate)

    p_report = sub.add_parser("report", help="Generate full report")
    p_report.add_argument("file", help="Input file path")
    p_report.add_argument("--output", "-o", help="Output path")
    p_report.add_argument("--strict", action="store_true", help="Strict mode")
    p_report.set_defaults(func=cmd_report)

    p_template = sub.add_parser("template", help="Generate assumption template")
    p_template.add_argument("type", choices=list(TEMPLATES.keys()),
                            help="Problem type")
    p_template.add_argument("--output", "-o", help="Output path")
    p_template.set_defaults(func=cmd_template)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
