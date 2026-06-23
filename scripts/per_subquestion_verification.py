#!/usr/bin/env python3
"""
Per-Subquestion Verification Checker — 逐子问题验证检查器 (M3)

检查每个子问题是否嵌入了灵敏度分析、鲁棒性检验、误差分析。
纯工具脚本，不调用 LLM API。

用法:
  python per_subquestion_verification.py check --subquestion Q1
  python per_subquestion_verification.py check-all --subquestions "Q1,Q2,Q3"
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ═══════════════════════════════════════════════════════════════
# Verification Checks
# ═══════════════════════════════════════════════════════════════

def check_sensitivity_exists(subquestion: str) -> dict:
    """检查子问题是否有灵敏度分析。"""
    sq_dir = WORKSPACE / "sensitivity" / subquestion
    has_config = (sq_dir / "sensitivity_config.json").exists()
    has_results = (sq_dir / "sweep_results.json").exists()
    has_report = (sq_dir / "sensitivity_report.md").exists()

    # 也检查 robustness/ 目录
    rob_dir = WORKSPACE / "robustness" / subquestion
    has_robustness = rob_dir.exists() and any(rob_dir.iterdir()) if rob_dir.exists() else False

    return {
        "sensitivity_config": has_config,
        "sweep_results": has_results,
        "sensitivity_report": has_report,
        "robustness_dir": has_robustness,
        "passed": has_results or has_robustness,
    }

def check_robustness_in_text(text: str) -> dict:
    """检查文本中是否包含鲁棒性/灵敏度分析讨论。"""
    sensitivity_keywords = [
        "灵敏度", "敏感性", "参数扫描", "参数扰动", "鲁棒", "稳健",
        "sensitivity", "robust", "perturbation", "sweep", "parameter sweep",
        "扰动分析", "稳定性分析", "参数变化",
    ]
    robustness_keywords = [
        "鲁棒性", "稳健性", "抗干扰", "容错", "稳定性",
        "robustness", "stability", "resilience",
    ]
    error_keywords = [
        "误差", "置信区间", "标准差", "方差", "RMSE", "MAE", "R²",
        "error", "confidence interval", "standard deviation", "variance",
        "误差分析", "不确定性", "uncertainty",
    ]

    text_lower = text.lower()

    found_sensitivity = [kw for kw in sensitivity_keywords if kw.lower() in text_lower]
    found_robustness = [kw for kw in robustness_keywords if kw.lower() in text_lower]
    found_error = [kw for kw in error_keywords if kw.lower() in text_lower]

    return {
        "has_sensitivity_analysis": len(found_sensitivity) >= 2,
        "sensitivity_keywords_found": found_sensitivity,
        "has_robustness_check": len(found_robustness) >= 1,
        "robustness_keywords_found": found_robustness,
        "has_error_analysis": len(found_error) >= 1,
        "error_keywords_found": found_error,
    }

def check_verification_artifacts(subquestion: str) -> dict:
    """检查验证相关的文件产物。"""
    checks = {}

    # 检查 robustness/ 目录
    rob_dir = WORKSPACE / "robustness" / subquestion
    checks["robustness_dir_exists"] = rob_dir.exists()
    if rob_dir.exists():
        rob_files = list(rob_dir.rglob("*"))
        checks["robustness_files"] = [str(f.relative_to(WORKSPACE)) for f in rob_files if f.is_file()]
    else:
        checks["robustness_files"] = []

    # 检查 sensitivity/ 目录
    sen_dir = WORKSPACE / "sensitivity" / subquestion
    checks["sensitivity_dir_exists"] = sen_dir.exists()
    if sen_dir.exists():
        sen_files = list(sen_dir.rglob("*"))
        checks["sensitivity_files"] = [str(f.relative_to(WORKSPACE)) for f in sen_files if f.is_file()]
    else:
        checks["sensitivity_files"] = []

    # 检查 frozen/ 目录
    frozen_dir = WORKSPACE / "frozen" / subquestion
    checks["frozen_dir_exists"] = frozen_dir.exists()
    checks["frozen_numbers_json"] = (frozen_dir / "frozen_numbers.json").exists() if frozen_dir.exists() else False

    return checks

def check_subquestion(subquestion: str, paper_text: str = None) -> dict:
    """完整检查单个子问题的验证状态。

    Returns:
        {
            "subquestion": str,
            "sensitivity_check": {...},
            "text_check": {...},
            "artifact_check": {...},
            "overall_passed": bool,
            "issues": [str],
        }
    """
    # 灵敏度分析检查
    sensitivity = check_sensitivity_exists(subquestion)

    # 文本检查（如果提供了论文文本）
    text_check = {}
    if paper_text:
        text_check = check_robustness_in_text(paper_text)

    # 产物检查
    artifacts = check_verification_artifacts(subquestion)

    # 综合判定
    issues = []
    if not sensitivity["passed"]:
        issues.append("缺少灵敏度分析结果 (sweep_results.json 或 robustness/ 目录)")
    if text_check and not text_check.get("has_sensitivity_analysis"):
        issues.append("论文中未检测到灵敏度分析讨论 (>=2 个关键词)")
    if text_check and not text_check.get("has_robustness_check"):
        issues.append("论文中未检测到鲁棒性检验讨论")
    if text_check and not text_check.get("has_error_analysis"):
        issues.append("论文中未检测到误差分析")
    if not artifacts.get("frozen_numbers_json"):
        issues.append("缺少冻结数据 (frozen_numbers.json)")

    overall = (
        sensitivity["passed"]
        and (not text_check or (text_check.get("has_sensitivity_analysis") and text_check.get("has_robustness_check")))
        and artifacts.get("frozen_numbers_json", False)
    )

    return {
        "subquestion": subquestion,
        "sensitivity_check": sensitivity,
        "text_check": text_check,
        "artifact_check": artifacts,
        "overall_passed": overall,
        "issues": issues,
        "timestamp": now(),
    }

# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_check(args):
    """检查单个子问题。"""
    paper_text = None
    if args.paper:
        paper_text = Path(args.paper).read_text(encoding="utf-8")
    result = check_subquestion(args.subquestion, paper_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["overall_passed"] else 1)

def cmd_check_all(args):
    """检查所有子问题。"""
    subquestions = [s.strip() for s in args.subquestions.split(",")]
    paper_text = None
    if args.paper:
        paper_text = Path(args.paper).read_text(encoding="utf-8")

    results = []
    all_passed = True
    for sq in subquestions:
        r = check_subquestion(sq, paper_text)
        results.append(r)
        if not r["overall_passed"]:
            all_passed = False

    summary = {
        "subquestions": results,
        "total": len(results),
        "passed": sum(1 for r in results if r["overall_passed"]),
        "all_passed": all_passed,
        "timestamp": now(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(0 if all_passed else 1)

def main():
    p = argparse.ArgumentParser(description="Per-Subquestion Verification Checker (M3)")
    sub = p.add_subparsers(dest="command")

    pc = sub.add_parser("check", help="检查单个子问题验证状态")
    pc.add_argument("--subquestion", "-q", required=True, help="子问题编号 (e.g., Q1)")
    pc.add_argument("--paper", help="论文文件路径 (可选，用于文本检查)")

    pca = sub.add_parser("check-all", help="检查所有子问题验证状态")
    pca.add_argument("--subquestions", "-q", required=True, help="子问题列表，逗号分隔 (e.g., Q1,Q2,Q3)")
    pca.add_argument("--paper", help="论文文件路径 (可选)")

    args = p.parse_args()
    dispatch = {"check": cmd_check, "check-all": cmd_check_all}
    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
