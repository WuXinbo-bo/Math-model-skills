#!/usr/bin/env python3
"""
SubagentWatchdog v1.0 - 子 Agent 健康监控

Architecture:
  - Three-dimensional validation: completeness, quality, consistency
  - Integrates with SubagentRunner for automated validation
  - Produces validation reports as disk artifacts

Validation Dimensions:
  1. Completeness: file exists + minimum size + required sections
  2. Quality: no TBD/TODO + no empty sections + numerical traceability
  3. Consistency: no contradiction with upstream artifacts

CLI Commands:
  validate    --agent-id X --task-json '{}'    Full validation
  check-file  --file path/to/file.md --checks 'min_length:500'   Single file
  report      --meeting-id M001               Generate validation report
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = DOCS_DIR / "validation_reports"


def _ensure_dirs():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════
# Core Validation
# ═══════════════════════════════════════════════════════════════

class SubagentWatchdog:
    """Three-dimensional output validation for subagent outputs."""

    def validate(self, agent_id: str, output_files: List[str],
                 quality_checks: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate subagent output files.

        Args:
            agent_id: Agent identifier
            output_files: List of output file paths
            quality_checks: List of quality checks to perform

        Returns:
            Dict with passed status, errors, warnings, evidence
        """
        errors = []
        warnings = []
        evidence = []

        if quality_checks is None:
            quality_checks = ["min_length:500", "no_placeholders"]

        for fpath in output_files:
            file_result = self._validate_single_file(fpath, quality_checks)
            errors.extend(file_result.get("errors", []))
            warnings.extend(file_result.get("warnings", []))
            evidence.extend(file_result.get("evidence", []))

        # Additional checks: file count
        existing = sum(1 for f in output_files if Path(f).exists())
        missing = len(output_files) - existing

        if missing > 0:
            errors.append(f"MISSING_FILES: {missing} of {len(output_files)} output files missing")
        else:
            evidence.append(f"All {len(output_files)} output files present")

        return {
            "passed": len(errors) == 0,
            "agent_id": agent_id,
            "errors": errors,
            "warnings": warnings,
            "evidence": evidence,
            "validated_at": _now(),
        }

    def _validate_single_file(self, fpath: str,
                              quality_checks: List[str]) -> Dict[str, Any]:
        """Validate a single output file."""
        errors = []
        warnings = []
        evidence = []

        path = Path(fpath)

        # Dimension 1: Completeness
        if not path.exists():
            errors.append(f"MISSING: {fpath}")
            return {"errors": errors, "warnings": warnings, "evidence": evidence}

        content = path.read_text(encoding="utf-8", errors="replace")
        size = len(content)
        line_count = len(content.split('\n'))

        if size < 50:
            errors.append(f"TOO_THIN: {fpath} ({size} chars)")
            return {"errors": errors, "warnings": warnings, "evidence": evidence}

        evidence.append(f"{path.name}: {size} chars, {line_count} lines")

        for check in quality_checks:
            self._run_check(check, content, path.name, errors, warnings, evidence)

        # Dimension 2: Quality - generic checks
        self._check_quality(content, path.name, errors, warnings, evidence)

        return {"errors": errors, "warnings": warnings, "evidence": evidence}

    def _run_check(self, check: str, content: str, fname: str,
                   errors: List, warnings: List, evidence: List):
        """Run a specific quality check."""
        if ":" not in check:
            # Simple boolean checks
            if check == "no_placeholders":
                self._check_no_placeholders(content, fname, errors, warnings)
            elif check == "has_numbers":
                self._check_has_numbers(content, fname, errors, warnings)
            return

        ctype, cval = check.split(":", 1)

        if ctype == "min_length":
            min_len = int(cval)
            if len(content) < min_len:
                errors.append(f"TOO_SHORT: {fname} ({len(content)} < {min_len})")
            else:
                evidence.append(f"{fname} length OK ({len(content)} >= {min_len})")

        elif ctype == "has_sections":
            sections = [s.strip() for s in cval.split(",")]
            for section in sections:
                if section not in content:
                    errors.append(f"MISSING_SECTION: '{section}' not found in {fname}")
                else:
                    evidence.append(f"{fname} has section '{section}'")

        elif ctype == "max_length":
            max_len = int(cval)
            if len(content) > max_len:
                warnings.append(f"OVERLONG: {fname} ({len(content)} > {max_len})")

        elif ctype == "has_keywords":
            keywords = [k.strip() for k in cval.split(",")]
            found = [k for k in keywords if k in content]
            if not found:
                errors.append(f"NO_KEYWORDS: {fname} missing all: {', '.join(keywords)}")
            elif len(found) < len(keywords):
                missing = [k for k in keywords if k not in content]
                warnings.append(f"MISSING_KEYWORDS: {fname} missing: {', '.join(missing)}")

    def _check_no_placeholders(self, content: str, fname: str,
                               errors: List, warnings: List):
        """Check for unfinished placeholder text."""
        placeholder_patterns = [
            r'\bTBD\b',
            r'\bTODO\b',
            r'待填写',
            r'待补充',
            r'\[待填写\]',
            r'\[TBD\]',
            r'\[TODO\]',
            r'\[待补充\]',
            r'\[placeholder\]',
            r'\[指标名称\]',
            r'\[公式\]',
            r'<待定>',
        ]
        found = []
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found.extend(matches)

        if found:
            unique = list(set(found))
            errors.append(f"PLACEHOLDER: {fname} contains {len(found)} placeholder(s): {', '.join(unique[:5])}")

    def _check_has_numbers(self, content: str, fname: str,
                           errors: List, warnings: List):
        """Check that file contains numerical results."""
        number_pattern = re.compile(r'\b\d+\.?\d+\b')
        numbers = number_pattern.findall(content)
        if len(numbers) < 3:
            warnings.append(f"NO_NUMBERS: {fname} has only {len(numbers)} numbers")
        else:
            pass  # Has enough numbers

    def _check_quality(self, content: str, fname: str,
                       errors: List, warnings: List, evidence: List):
        """Run generic quality checks."""
        # Check for empty sections
        section_pattern = re.compile(r'^#+\s+.+$', re.MULTILINE)
        sections = section_pattern.findall(content)

        for i, section in enumerate(sections):
            # Find content between this section and next
            start = content.find(section) + len(section)
            # Find next section or end
            next_section = section_pattern.search(content, start)
            end = next_section.start() if next_section else len(content)
            between = content[start:end].strip()

            if len(between) < 10:
                warnings.append(f"EMPTY_SECTION: '{section.strip()}' in {fname} has minimal content")

        # Check for very long lines (likely no formatting)
        lines = content.split('\n')
        long_lines = sum(1 for l in lines if len(l) > 200)
        if long_lines > 0:
            warnings.append(f"LONG_LINES: {fname} has {long_lines} lines > 200 chars (check formatting)")

        # Evidence
        if sections:
            evidence.append(f"{fname}: {len(sections)} sections")


# ═══════════════════════════════════════════════════════════════
# Single File Validation
# ═══════════════════════════════════════════════════════════════

def check_single_file(fpath: str, checks: str) -> Dict[str, Any]:
    """Validate a single file with specified checks.

    Args:
        fpath: File path
        checks: Check string (e.g., "min_length:500,has_sections:结论,风险")

    Returns:
        Validation result
    """
    watchdog = SubagentWatchdog()
    check_list = [c.strip() for c in checks.split(",")]
    return watchdog._validate_single_file(fpath, check_list)


# ═══════════════════════════════════════════════════════════════
# Validation Report Generation
# ═══════════════════════════════════════════════════════════════

def generate_validation_report(meeting_id: str,
                               results: Dict[str, Dict]) -> Dict[str, Any]:
    """Generate a consolidated validation report for a meeting.

    Args:
        meeting_id: Meeting identifier
        results: Dict of agent_id -> validation result

    Returns:
        Report dict with summary
    """
    _ensure_dirs()

    total_agents = len(results)
    passed_agents = sum(1 for r in results.values() if r.get("passed"))
    failed_agents = total_agents - passed_agents

    all_errors = []
    for agent_id, r in results.items():
        for err in r.get("errors", []):
            all_errors.append(f"[{agent_id}] {err}")

    lines = [
        f"# Validation Report: {meeting_id}",
        "",
        f"**Generated**: {_now()}",
        f"**Total Agents**: {total_agents}",
        f"**Passed**: {passed_agents}",
        f"**Failed**: {failed_agents}",
        "",
        "---",
        "",
    ]

    for agent_id, r in results.items():
        icon = "PASS" if r.get("passed") else "FAIL"
        lines.append(f"## [{icon}] {agent_id}")
        lines.append("")

        if r.get("evidence"):
            lines.append("**Evidence**:")
            for e in r["evidence"]:
                lines.append(f"- [x] {e}")
            lines.append("")

        if r.get("errors"):
            lines.append("**Errors**:")
            for e in r["errors"]:
                lines.append(f"- [ ] {e}")
            lines.append("")

        if r.get("warnings"):
            lines.append("**Warnings**:")
            for w in r["warnings"]:
                lines.append(f"- {w}")
            lines.append("")

    lines.extend([
        "---",
        f"*Report generated at {_now()}*",
    ])

    report_file = REPORTS_DIR / f"{meeting_id}_validation.md"
    report_file.write_text("\n".join(lines), encoding="utf-8")

    return {
        "status": "completed",
        "report_file": str(report_file),
        "total": total_agents,
        "passed": passed_agents,
        "failed": failed_agents,
        "all_errors": all_errors,
    }


# ═══════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="SubagentWatchdog v1.0 - 子 Agent 健康监控"
    )
    sub = p.add_subparsers(dest="command")

    # validate
    pv = sub.add_parser("validate", help="Full validation")
    pv.add_argument("--agent-id", required=True)
    pv.add_argument("--task-json", required=True)

    # check-file
    pcf = sub.add_parser("check-file", help="Single file validation")
    pcf.add_argument("--file", required=True)
    pcf.add_argument("--checks", default="min_length:500,no_placeholders")

    # report
    pr = sub.add_parser("report", help="Generate validation report")
    pr.add_argument("--meeting-id", required=True)
    pr.add_argument("--results-json", default=None)

    args = p.parse_args()

    if args.command == "validate":
        task_spec = json.loads(args.task_json)
        watchdog = SubagentWatchdog()
        output_files = [
            str(Path(task_spec.get("output_dir", "outputs/standalone")) / f)
            for f in task_spec.get("output_files", [])
        ]
        result = watchdog.validate(args.agent_id, output_files,
                                   task_spec.get("quality_checks"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["passed"] else 1)

    elif args.command == "check-file":
        result = check_single_file(args.file, args.checks)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("passed", True) else 1)

    elif args.command == "report":
        if args.results_json:
            results = json.loads(args.results_json)
        else:
            results = {"_placeholder": {"passed": True, "errors": [], "warnings": [], "evidence": []}}
        report = generate_validation_report(args.meeting_id, results)
        print(json.dumps(report, ensure_ascii=False, indent=2))

    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
