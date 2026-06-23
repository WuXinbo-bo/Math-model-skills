#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Metric Guardian v2.0 - 指标守门模块
====================================

确保关键指标有明确的数学公式定义和代码实现，防止指标误用。

功能：
  1. init   — 为指定/全部子问题创建 metric_spec.md 模板
  2. validate — 验证指标规格完整性（5 项必需章节 + 指标/代码/变量表计数）
  3. audit  — 公式符号一致性审计（对比 symbol_table.md）
  4. check  — 单个子问题 G1.5 门控（validate + audit）
  5. check_all — 遍历全部子问题执行 G1.5 门控，汇总输出

Usage:
  python metric_guardian.py init --subquestion Q1
  python metric_guardian.py init --all
  python metric_guardian.py validate --subquestion Q1
  python metric_guardian.py audit --subquestion Q1
  python metric_guardian.py check --subquestion Q1
  python metric_guardian.py check --all
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── 路径解析 ──
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from workspace_utils import resolve_workspace_from_project, resolve_skill_root
SKILL_ROOT = resolve_skill_root()
OUTPUTS_ROOT = SKILL_ROOT / "outputs"

# 产物目录（统一输出到 outputs/S3:models/）
METRIC_GATE_DIR = OUTPUTS_ROOT / "S3:models"
METRIC_SPEC_DIR = METRIC_GATE_DIR / "metric_spec"
FORMULA_AUDIT_DIR = METRIC_GATE_DIR / "formula_audit"

# 上游输入
PROBLEM_ANALYSIS_DIR = OUTPUTS_ROOT / "S1:literature"
VARIABLES_JSON = PROBLEM_ANALYSIS_DIR / "variables.json"
ANALYSIS_MD = PROBLEM_ANALYSIS_DIR / "analysis.md"

# 符号表搜索路径（按优先级）
_SYMBOL_WS = resolve_workspace_from_project(SKILL_ROOT)
SYMBOL_TABLE_CANDIDATES = [
    SKILL_ROOT / "docs" / "symbol_table.md",
    _SYMBOL_WS / "planning" / "symbol_table.md",
    OUTPUTS_ROOT / "S1:literature" / "symbol_table.md",
    OUTPUTS_ROOT / "S3:models" / "symbol_table.md",
]



def detect_symbol_table_path() -> Optional[Path]:
    """自动检测 symbol_table.md 位置"""
    for p in SYMBOL_TABLE_CANDIDATES:
        if p.exists():
            return p
    return None


def detect_subquestions() -> List[str]:
    """
    自动检测子问题列表：
    1) 从 variables.json 读取 subproblems 数组
    2) 从 variables.json 的 key 模式提取 Q1/Q2/...
    3) 从 analysis.md 提取 Q\d+ 模式
    4) 兜底返回 ["Q1"]
    """
    # 方案1: variables.json 含 subproblems 列表
    if VARIABLES_JSON.exists():
        try:
            data = json.loads(VARIABLES_JSON.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # 直接的 subproblems / sub_questions 列表
                for key in ["subproblems", "sub_questions", "problems", "questions"]:
                    val = data.get(key)
                    if isinstance(val, list) and len(val) > 0:
                        result = []
                        for item in val:
                            if isinstance(item, dict) and "id" in item:
                                result.append(str(item["id"]).upper())
                            elif isinstance(item, str):
                                result.append(item.upper().strip())
                            elif isinstance(item, dict) and "name" in item:
                                result.append(str(item["name"]).upper().strip())
                        if result:
                            return result
                # 从 Q1/Q2/... 模式提取
                q_keys = [k for k in data.keys() if re.match(r'^[Qq]\d+$', k)]
                if q_keys:
                    return [k.upper() for k in sorted(q_keys)]
        except Exception:
            pass

    # 方案2: 从 analysis.md 提取
    if ANALYSIS_MD.exists():
        try:
            content = ANALYSIS_MD.read_text(encoding="utf-8")
            qs = sorted(set(re.findall(r'\b[Qq](\d+)\b', content)),
                        key=lambda x: int(x))
            if qs:
                return [f"Q{q}" for q in qs]
        except Exception:
            pass

    return ["Q1"]


def get_metric_spec_path(subquestion: str) -> Path:
    return METRIC_SPEC_DIR / subquestion / "metric_spec.md"


def get_audit_report_path(subquestion: str) -> Path:
    return FORMULA_AUDIT_DIR / subquestion / "formula_audit_report.md"


def ensure_dirs(subquestion: str):
    get_metric_spec_path(subquestion).parent.mkdir(parents=True, exist_ok=True)
    get_audit_report_path(subquestion).parent.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════
# 初始化
# ══════════════════════════════════════════════════════════

def init_metric_spec(subquestion: str, problem_type: str = "evaluation") -> dict:
    """初始化单个子问题的指标规格文件"""
    ensure_dirs(subquestion)
    now = datetime.now().isoformat()

    spec = {
        "subquestion": subquestion,
        "problem_type": problem_type,
        "created_at": now,
        "metrics": [],
        "variables": [],
        "assumptions": [],
        "validation_rules": []
    }

    # 从 variables.json 提取子问题信息
    sub_info = _get_subproblem_info(subquestion)
    description = sub_info.get("description", sub_info.get("name", "[待填写]"))
    sub_type = sub_info.get("type", sub_info.get("problem_type", problem_type))

    template = f"""# 指标规格 (Metric Specification)

## 基本信息

- **子问题**: {subquestion}
- **问题描述**: {description}
- **问题类型**: {sub_type}
- **创建时间**: {now}

## 评价指标

<!-- 每个指标必须包含：1.指标名称 2.数学公式 3.变量含义 4.单位 5.代码函数名 6.有效范围 -->

### 指标 1: [指标名称]

**数学公式**:
```math
\\text{{公式}} = f(x_1, x_2, \\ldots)
```

**变量说明**:

| 变量 | 含义 | 单位 | 有效范围 |
|------|------|------|----------|
| x_1 | 变量1描述 | 单位 | [min, max] |
| x_2 | 变量2描述 | 单位 | [min, max] |

**代码实现**:

```python
def calculate_metric_1(x1, x2):
    r\"\"\"
    计算 [指标名称]

    Args:
        x1: 变量1描述
        x2: 变量2描述

    Returns:
        float: 指标值
    \"\"\"
    return 0.0
```

**有效范围**: [最小值, 最大值]
**目标方向**: maximize / minimize / range

---

## 符号表

| 符号 | 含义 | 单位 | 来源 |
|------|------|------|------|
| | | | |

## 假设条件

1. [假设1描述]
2. [假设2描述]

## 验证规则

1. [规则1: 指标值应在合理范围内]
2. [规则2: 计算结果应可复现]
"""
    spec_path = get_metric_spec_path(subquestion)
    spec_path.write_text(template, encoding="utf-8")
    return spec


def init_all(subquestion_ids: Optional[List[str]] = None) -> List[str]:
    """初始化全部子问题的指标规格，返回初始化的子问题列表"""
    ids = subquestion_ids or detect_subquestions()
    results = []
    for qid in ids:
        info = _get_subproblem_info(qid)
        ptype = info.get("type", info.get("problem_type", "evaluation"))
        init_metric_spec(qid, ptype)
        results.append(qid)
        print(f"  [INIT] {qid} ({ptype}) -> {get_metric_spec_path(qid)}")
    return results


def _get_subproblem_info(subquestion: str) -> Dict[str, Any]:
    """从 variables.json 获取子问题详细信息"""
    if not VARIABLES_JSON.exists():
        return {}
    try:
        data = json.loads(VARIABLES_JSON.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # 直接 key 匹配
            info = data.get(subquestion) or data.get(subquestion.lower())
            if isinstance(info, dict):
                return info
            # 从 subproblems 数组查找
            for key in ["subproblems", "sub_questions", "problems"]:
                val = data.get(key, [])
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            iid = str(item.get("id", "")).upper()
                            if iid == subquestion.upper():
                                return item
    except Exception:
        pass
    return {}


# ══════════════════════════════════════════════════════════
# 验证
# ══════════════════════════════════════════════════════════

def validate_metric_spec(subquestion: str) -> Tuple[bool, List[str]]:
    """
    验证指标规格完整性

    检查：
    1. 文件存在
    2. 5 个必需章节存在
    3. 至少 1 个指标定义
    4. 至少 1 个代码块
    5. 变量说明表格存在
    6. 无模板占位符残留（[指标名称] / [待填写]）
    7. 变量表非空行
    """
    spec_path = get_metric_spec_path(subquestion)

    if not spec_path.exists():
        return False, [f"指标规格文件不存在: {spec_path}"]

    content = spec_path.read_text(encoding="utf-8")
    errors = []

    # 检查必需章节
    required_sections = ["评价指标", "数学公式", "变量说明", "代码实现", "符号表"]
    for section in required_sections:
        if section not in content:
            errors.append(f"缺少必需部分: {section}")

    # 检查指标定义数量
    metrics_found = re.findall(r"### 指标 \d+:\s*\S", content)
    # 过滤掉包含 [指标名称] 等占位符的
    real_metrics = [m for m in metrics_found if "[指标名称]" not in m and "[Metric" not in m]
    if len(real_metrics) == 0:
        errors.append("未找到已填写的指标定义（仅有占位符或为空）")

    # 检查代码块
    code_blocks = re.findall(r"```python", content)
    if len(code_blocks) == 0:
        errors.append("缺少代码实现块")
    elif len(code_blocks) < len(real_metrics):
        errors.append(f"代码块数量({len(code_blocks)})少于指标数量({len(real_metrics)})")

    # 检查变量表
    var_table_rows = re.findall(r"\|\s*\S+\s*\|\s*\S+\s*\|\s*\S+\s*\|\s*\S+\s*\|", content)
    # 过滤表头和分隔符
    real_vars = [r for r in var_table_rows
                 if "---" not in r and "变量" not in r and "含义" not in r and "符号" not in r]
    if len(real_vars) == 0:
        errors.append("变量说明表格为空")

    # 检查占位符残留
    placeholders = re.findall(r"\[指标名称\]|\[待填写\]|\[Metric Name\]|\[formula\]", content)
    if placeholders:
        errors.append(f"存在 {len(placeholders)} 处模板占位符未填写")

    # 检查公式格式（支持多种格式）
    formula_patterns = [
        r"```math",                          # LaTeX math block
        r"\\frac\{",                          # \frac
        r"\\sum|\\int|\\prod|\\lim",         # LaTeX 运算符
        r"公式\s*=\s*f\(",                    # 旧格式
        r"\$\$",                              # 行内 math
        r"\\\[|\\\(",                         # LaTeX display/inline
        r"[=≥≤]\s*.*[+\-*/]",               # 基本等式
    ]
    has_formula = any(re.search(p, content) for p in formula_patterns)
    if not has_formula:
        errors.append("未找到数学公式（需包含 LaTeX 或标准格式公式）")

    return len(errors) == 0, errors


def validate_all(subquestion_ids: Optional[List[str]] = None) -> Dict[str, Tuple[bool, List[str]]]:
    """验证全部子问题，返回 {qid: (passed, errors)}"""
    ids = subquestion_ids or detect_subquestions()
    results = {}
    for qid in ids:
        passed, errors = validate_metric_spec(qid)
        results[qid] = (passed, errors)
    return results


# ══════════════════════════════════════════════════════════
# 公式审计
# ══════════════════════════════════════════════════════════

def audit_formula_consistency(subquestion: str) -> Tuple[bool, Dict]:
    """
    审计公式符号一致性

    检查 metric_spec.md 中的符号是否与 symbol_table.md 一致。
    同时检测维度一致性和参数可追溯性。
    """
    spec_path = get_metric_spec_path(subquestion)
    symbol_table_path = detect_symbol_table_path()

    report: Dict[str, Any] = {
        "subquestion": subquestion,
        "consistent": True,
        "issues": [],
        "metrics_found": 0,
        "symbols_used": [],
        "symbols_in_table": [],
        "missing_symbols": [],
        "dimension_issues": [],
        "param_traceable": True,
    }

    if not spec_path.exists():
        report["consistent"] = False
        report["issues"].append(f"指标规格文件不存在: {spec_path}")
        return False, report

    spec_content = spec_content_raw = spec_path.read_text(encoding="utf-8")

    # ── 提取指标规格中的符号 ──
    # 从变量表提取: | x_1 | ... | ... | ... |
    symbol_pattern = r"\|\s*([a-zA-Z_][a-zA-Z0-9_]*(?:_[a-zA-Z0-9]+)*)\s*\|"
    symbols_in_spec = set()
    for line in spec_content.split("\n"):
        if line.strip().startswith("|") and "---" not in line and "符号" not in line and "变量" not in line and "含义" not in line:
            for m in re.findall(symbol_pattern, line):
                # 过滤掉常见非变量词
                if m.lower() not in ("id", "name", "type", "unit", "min", "max", "range", "source", "description"):
                    symbols_in_spec.add(m)
    report["symbols_used"] = sorted(symbols_in_spec)

    # ── 指标数量 ──
    metrics_raw = re.findall(r"### 指标 \d+:\s*(.+)", spec_content)
    metrics_clean = [m.strip() for m in metrics_raw if "[指标名称]" not in m and "[Metric" not in m]
    report["metrics_found"] = len(metrics_clean)

    # ── 符号表对比 ──
    if symbol_table_path and symbol_table_path.exists():
        table_content = symbol_table_path.read_text(encoding="utf-8")
        symbols_in_table = set()
        for line in table_content.split("\n"):
            if line.strip().startswith("|") and "---" not in line:
                matches = re.findall(symbol_pattern, line)
                for m in matches:
                    if m.lower() not in ("id", "name", "type", "unit", "min", "max", "range", "source", "description", "含义", "单位"):
                        symbols_in_table.add(m)
        report["symbols_in_table"] = sorted(symbols_in_table)

        undefined_symbols = symbols_in_spec - symbols_in_table
        if undefined_symbols:
            report["consistent"] = False
            report["missing_symbols"] = sorted(undefined_symbols)
            report["issues"].append(f"以下符号在 symbol_table.md 中未定义: {', '.join(sorted(undefined_symbols))}")
    else:
        report["issues"].append("symbol_table.md 未找到，跳过符号一致性检查")

    # ── 维度一致性检查（LaTeX 公式中变量下标应匹配） ──
    latex_vars = set(re.findall(r"\\(?:mathrm|text|mathbf)\{([a-zA-Z_]+)\}", spec_content))
    latex_subscripts = set(re.findall(r"([a-zA-Z])_(?:\{([^}]+)\}|(\d))", spec_content))
    if latex_subscripts and symbols_in_spec:
        # 所有 LaTeX 下标变量应在符号表中有定义
        all_sub_vars = set()
        for base, sub_brace, sub_digit in latex_subscripts:
            if sub_brace:
                all_sub_vars.add(f"{base}_{sub_brace}")
            elif sub_digit:
                all_sub_vars.add(f"{base}_{sub_digit}")
        undefined_latex = all_sub_vars - symbols_in_spec
        # 只报告有实际意义的差异（排除常见数学常数）
        real_undefined = {v for v in undefined_latex
                          if not any(c in v for c in ("i", "j", "n", "k"))}
        if real_undefined:
            report["dimension_issues"] = sorted(real_undefined)
            report["issues"].append(f"LaTeX 公式中有 {len(real_undefined)} 个变量未在符号表中定义")

    # ── 参数可追溯性（检查是否有来源标注） ──
    param_rows = [line for line in spec_content.split("\n")
                  if line.strip().startswith("|") and "---" not in line and "符号" not in line]
    if param_rows:
        # 检查是否有 "来源" 或 "source" 列
        has_source_col = "来源" in spec_content or "source" in spec_content.lower()
        if not has_source_col:
            report["param_traceable"] = False
            report["issues"].append("变量表缺少'来源'列，参数无法追溯")

    # ── 写入审计报告 ──
    audit_path = get_audit_report_path(subquestion)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    audit_report = f"""# 公式审计报告 (Formula Audit Report)

## 审计信息

- **子问题**: {subquestion}
- **审计时间**: {datetime.now().isoformat()}
- **一致性检查结果**: {"通过" if report['consistent'] else "未通过"}

## 指标统计

- **指标数量**: {report['metrics_found']}
- **使用的符号**: {', '.join(report['symbols_used']) if report['symbols_used'] else '无'}

## 符号表检查

- **符号表路径**: {symbol_table_path or '未找到'}
- **符号表符号数量**: {len(report['symbols_in_table'])}
- **已定义符号**: {', '.join(report['symbols_in_table'][:20]) if report['symbols_in_table'] else '无'}
- **未定义符号**: {', '.join(report['missing_symbols']) if report['missing_symbols'] else '无'}

## 维度一致性

- **LaTeX 下标变量未定义**: {', '.join(report['dimension_issues']) if report['dimension_issues'] else '无'}

## 参数可追溯性

- **是否有来源标注**: {"是" if report['param_traceable'] else '否'}

## 审计问题

{chr(10).join(f'- {issue}' for issue in report['issues']) if report['issues'] else '- 无问题'}

## 审计结论

{"公式符号一致性检查通过" if report['consistent'] else "公式符号一致性检查未通过，需要修复"}
"""
    audit_path.write_text(audit_report, encoding="utf-8")
    return report["consistent"], report


def audit_all(subquestion_ids: Optional[List[str]] = None) -> Dict[str, Tuple[bool, Dict]]:
    """审计全部子问题"""
    ids = subquestion_ids or detect_subquestions()
    results = {}
    for qid in ids:
        results[qid] = audit_formula_consistency(qid)
    return results


# ══════════════════════════════════════════════════════════
# G1.5 门控检查
# ══════════════════════════════════════════════════════════

def check_metric_guardian(subquestion: str) -> Tuple[bool, str]:
    """单个子问题的 G1.5 门控检查"""
    is_valid, validation_errors = validate_metric_spec(subquestion)
    is_consistent, audit_report = audit_formula_consistency(subquestion)

    if not is_valid:
        return False, (
            f"G1.5 指标守门未通过 [{subquestion}]\n"
            f"原因: 指标规格不完整\n"
            f"错误:\n" + "\n".join(f"  - {e}" for e in validation_errors) + "\n"
            f"修复: 请完善 {get_metric_spec_path(subquestion)}"
        )

    if not is_consistent:
        return False, (
            f"G1.5 指标守门未通过 [{subquestion}]\n"
            f"原因: 公式符号不一致\n"
            f"问题:\n" + "\n".join(f"  - {i}" for i in audit_report['issues']) + "\n"
            f"修复: 请更新 {get_audit_report_path(subquestion)}"
        )

    return True, (
        f"G1.5 指标守门通过 [{subquestion}]\n"
        f"- 指标规格完整: {audit_report['metrics_found']} 个指标已定义\n"
        f"- 公式符号一致: 所有符号在 symbol_table.md 中有定义\n"
        f"- 详细报告: {get_audit_report_path(subquestion)}"
    )


def check_all(subquestion_ids: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    全量子问题 G1.5 门控检查

    返回 (all_passed, summary)
    summary 包含每个子问题的详细结果。
    """
    ids = subquestion_ids or detect_subquestions()
    results = {}
    all_passed = True

    for qid in ids:
        passed, message = check_metric_guardian(qid)
        is_valid, val_errors = validate_metric_spec(qid)
        is_consistent, audit_info = audit_formula_consistency(qid)
        results[qid] = {
            "passed": passed,
            "message": message,
            "validation_errors": val_errors,
            "audit_issues": audit_info.get("issues", []),
            "metrics_found": audit_info.get("metrics_found", 0),
            "symbols_used": audit_info.get("symbols_used", []),
            "missing_symbols": audit_info.get("missing_symbols", []),
        }
        if not passed:
            all_passed = False

    summary = {
        "all_passed": all_passed,
        "subquestions": ids,
        "total": len(ids),
        "passed_count": sum(1 for r in results.values() if r["passed"]),
        "failed_count": sum(1 for r in results.values() if not r["passed"]),
        "details": results,
        "symbol_table_path": str(detect_symbol_table_path() or "未找到"),
        "timestamp": datetime.now().isoformat(),
    }
    return all_passed, summary


# ══════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Metric Guardian v2.0 - 指标守门模块")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init
    init_p = subparsers.add_parser("init", help="初始化指标规格")
    init_p.add_argument("--subquestion", help="子问题编号 (如 Q1)")
    init_p.add_argument("--all", action="store_true", help="初始化全部子问题")
    init_p.add_argument("--type", default="evaluation",
                        choices=["optimization", "prediction", "evaluation", "hybrid"],
                        help="问题类型")

    # validate
    val_p = subparsers.add_parser("validate", help="验证指标规格完整性")
    val_p.add_argument("--subquestion", help="子问题编号")
    val_p.add_argument("--all", action="store_true", help="验证全部子问题")

    # audit
    audit_p = subparsers.add_parser("audit", help="审计公式符号一致性")
    audit_p.add_argument("--subquestion", help="子问题编号")
    audit_p.add_argument("--all", action="store_true", help="审计全部子问题")

    # check
    check_p = subparsers.add_parser("check", help="G1.5 门控检查")
    check_p.add_argument("--subquestion", help="子问题编号")
    check_p.add_argument("--all", action="store_true", help="检查全部子问题")

    args = parser.parse_args()

    if args.command == "init":
        if args.all:
            ids = init_all()
            print(f"\n[OK] 已初始化 {len(ids)} 个子问题的指标规格")
        elif args.subquestion:
            init_metric_spec(args.subquestion, args.type)
            print(f"[OK] 指标规格已初始化: {get_metric_spec_path(args.subquestion)}")
        else:
            print("[ERROR] 需要指定 --subquestion 或 --all")
            sys.exit(1)

    elif args.command == "validate":
        if args.all:
            results = validate_all()
            failed = [q for q, (ok, _) in results.items() if not ok]
            for q, (ok, errs) in results.items():
                status = "PASS" if ok else "FAIL"
                print(f"  [{status}] {q}: {', '.join(errs) if errs else 'OK'}")
            if failed:
                print(f"\n[FAIL] {len(failed)}/{len(results)} 个子问题验证未通过")
                sys.exit(1)
            print(f"\n[PASS] 全部 {len(results)} 个子问题验证通过")
        elif args.subquestion:
            is_valid, errors = validate_metric_spec(args.subquestion)
            if is_valid:
                print(f"[PASS] 指标规格验证通过 [{args.subquestion}]")
            else:
                print(f"[FAIL] 指标规格验证失败 [{args.subquestion}]:")
                for e in errors:
                    print(f"  - {e}")
                sys.exit(1)
        else:
            print("[ERROR] 需要指定 --subquestion 或 --all")
            sys.exit(1)

    elif args.command == "audit":
        if args.all:
            results = audit_all()
            for q, (ok, rpt) in results.items():
                status = "PASS" if ok else "FAIL"
                print(f"  [{status}] {q}: {len(rpt['issues'])} 个问题")
            failed = [q for q, (ok, _) in results.items() if not ok]
            if failed:
                print(f"\n[FAIL] {len(failed)}/{len(results)} 个子问题审计未通过")
                sys.exit(1)
            print(f"\n[PASS] 全部 {len(results)} 个子问题审计通过")
        elif args.subquestion:
            is_consistent, report = audit_formula_consistency(args.subquestion)
            if is_consistent:
                print(f"[PASS] 公式符号一致性检查通过 [{args.subquestion}]")
            else:
                print(f"[FAIL] 公式符号一致性检查未通过 [{args.subquestion}]:")
                for issue in report['issues']:
                    print(f"  - {issue}")
                sys.exit(1)
        else:
            print("[ERROR] 需要指定 --subquestion 或 --all")
            sys.exit(1)

    elif args.command == "check":
        if args.all:
            all_passed, summary = check_all()
            print(f"\n{'='*60}")
            print(f"G1.5 指标守门汇总")
            print(f"{'='*60}")
            print(f"  子问题数: {summary['total']}")
            print(f"  通过: {summary['passed_count']}")
            print(f"  未通过: {summary['failed_count']}")
            print(f"  符号表: {summary['symbol_table_path']}")
            for qid, detail in summary['details'].items():
                status = "PASS" if detail['passed'] else "FAIL"
                print(f"  [{status}] {qid}: 指标={detail['metrics_found']}, "
                      f"缺失符号={len(detail['missing_symbols'])}")
            if not all_passed:
                print(f"\n[RESULT] G1.5 门控未通过")
                sys.exit(1)
            print(f"\n[RESULT] G1.5 门控全部通过")
        elif args.subquestion:
            passed, message = check_metric_guardian(args.subquestion)
            print(message)
            sys.exit(0 if passed else 1)
        else:
            print("[ERROR] 需要指定 --subquestion 或 --all")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
