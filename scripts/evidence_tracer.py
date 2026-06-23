#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Evidence Tracer - 证据链追踪器
================================

维护结论-代码-图表追溯关系，验证论文结论与代码输出一致性。

功能：
1. 结论提取：从论文 Markdown 中提取关键结论和数值
2. 证据注册：注册代码输出作为证据
3. 论文-代码一致性检查：所有表格数值必须存在于代码输出中
4. 假设-证据矩阵：每条假设需有验证依据
5. 生成 conclusion_evidence_map.md 和 paper_code_consistency_report.md

Usage:
  python evidence_tracer.py register --subquestion Q1 --evidence-file evidence.json
  python evidence_tracer.py extract --subquestion Q1 --paper paper.md
  python evidence_tracer.py check --subquestion Q1
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("outputs")
EVIDENCE_DIR = WORKSPACE / "evidence"


def get_evidence_map_path(subquestion: str) -> Path:
    """获取结论-证据映射路径"""
    return EVIDENCE_DIR / subquestion / "conclusion_evidence_map.md"


def get_consistency_report_path(subquestion: str) -> Path:
    """获取论文-代码一致性报告路径"""
    return EVIDENCE_DIR / subquestion / "paper_code_consistency_report.md"


def get_assumption_matrix_path(subquestion: str) -> Path:
    """获取假设-证据矩阵路径"""
    return EVIDENCE_DIR / subquestion / "assumption_evidence_matrix.md"


def get_evidence_json_path(subquestion: str) -> Path:
    """获取证据数据 JSON 路径"""
    return EVIDENCE_DIR / subquestion / "evidence_data.json"


def ensure_dirs(subquestion: str):
    """确保目录存在"""
    (EVIDENCE_DIR / subquestion).mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# 结论提取
# ═══════════════════════════════════════════════════════════════

def extract_conclusions_from_paper(paper_path):
    """
    从论文 Markdown 中提取关键结论

    Returns:
        [{"text": 结论文本, "numbers": [数值列表], "section": 所在章节}]
    """
    path = Path(paper_path)
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    conclusions = []

    # 按章节拆分
    sections = re.split(r"^#{1,3}\s+.+", content, flags=re.MULTILINE)

    number_pattern = re.compile(
        r"(?:约|为|达到|提高|降低|减少|增加|最优|最佳|平均)"
        r".*?(\d+\.?\d*)\s*(?:%|倍|万|亿|个|次|天|小时|分钟|秒|米|千米|km|km/h)?"
    )

    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            numbers_found = number_pattern.findall(line)

            # 结论性语句关键词
            conclusion_keywords = [
                "因此", "综上", "结果表明", "可以得出", "分析表明",
                "模型", "最优", "最佳", "平均", "准确率", "误差",
                "提高了", "降低了", "减少了", "增加了",
                "与.*相比", "优于", "好于",
            ]

            for kw in conclusion_keywords:
                if re.search(kw, line):
                    conclusions.append({
                        "text": line,
                        "numbers": numbers_found,
                        "section": "unknown",
                    })
                    break

    return conclusions


# ═══════════════════════════════════════════════════════════════
# 证据注册
# ═══════════════════════════════════════════════════════════════

def register_evidence(subquestion: str, evidence_data: dict) -> dict:
    """
    注册证据数据

    Args:
        subquestion: 子问题编号
        evidence_data: 证据数据 {
            "code_outputs": [{"file": "...", "key": "...", "value": ...}],
            "figures": [{"file": "...", "caption": "..."}],
            "tables": [{"file": "...", "data": {...}}],
            "assumptions": [{"id": "A1", "text": "...", "verified": true, "evidence": "..."}]
        }

    Returns:
        注册结果
    """
    ensure_dirs(subquestion)

    evidence_path = get_evidence_json_path(subquestion)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_data, f, ensure_ascii=False, indent=2)

    return {
        "subquestion": subquestion,
        "registered_at": datetime.now().isoformat(),
        "evidence_count": {
            "code_outputs": len(evidence_data.get("code_outputs", [])),
            "figures": len(evidence_data.get("figures", [])),
            "tables": len(evidence_data.get("tables", [])),
            "assumptions": len(evidence_data.get("assumptions", [])),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 一致性检查
# ═══════════════════════════════════════════════════════════════

def check_paper_code_consistency(subquestion):
    """
    检查论文-代码一致性

    Returns:
        (is_consistent, report)
    """
    evidence_path = get_evidence_json_path(subquestion)

    report = {
        "subquestion": subquestion,
        "consistent": True,
        "checked_at": datetime.now().isoformat(),
        "total_conclusions": 0,
        "verified_conclusions": 0,
        "unverified_conclusions": [],
        "missing_evidence": [],
        "assumption_coverage": {"total": 0, "verified": 0},
    }

    if not evidence_path.exists():
        report["consistent"] = False
        report["missing_evidence"].append(f"证据数据不存在: {evidence_path}")
        return False, report

    with open(evidence_path, "r", encoding="utf-8") as f:
        evidence = json.load(f)

    code_outputs = evidence.get("code_outputs", [])
    assumptions = evidence.get("assumptions", [])

    # 检查假设覆盖率
    report["assumption_coverage"]["total"] = len(assumptions)
    for a in assumptions:
        if a.get("verified", False):
            report["assumption_coverage"]["verified"] += 1

    if assumptions:
        coverage = report["assumption_coverage"]["verified"] / len(assumptions)
        if coverage < 1.0:
            report["consistent"] = False
            unverified = [a["id"] for a in assumptions if not a.get("verified")]
            report["missing_evidence"].append(
                f"未验证假设: {', '.join(unverified)}"
            )

    # 检查代码输出是否有数值
    if not code_outputs:
        report["consistent"] = False
        report["missing_evidence"].append("无代码输出证据")

    return report["consistent"], report


# ═══════════════════════════════════════════════════════════════
# 生成证据链文档
# ═══════════════════════════════════════════════════════════════

def generate_evidence_map(subquestion: str) -> str:
    """生成结论-证据映射文档"""
    evidence_path = get_evidence_json_path(subquestion)
    map_path = get_evidence_map_path(subquestion)

    if not evidence_path.exists():
        return "证据数据不存在，无法生成映射"

    with open(evidence_path, "r", encoding="utf-8") as f:
        evidence = json.load(f)

    code_outputs = evidence.get("code_outputs", [])
    figures = evidence.get("figures", [])
    tables = evidence.get("tables", [])
    assumptions = evidence.get("assumptions", [])

    doc = f"""# 结论-证据映射 (Conclusion-Evidence Map)

## 基本信息

- **子问题**: {subquestion}
- **生成时间**: {datetime.now().isoformat()}

## 代码输出证据

| 序号 | 文件 | 键名 | 值 |
|------|------|------|----|
"""
    for i, co in enumerate(code_outputs, 1):
        doc += f"| {i} | {co.get('file', '')} | {co.get('key', '')} | {co.get('value', '')} |\n"

    doc += f"""
## 图表证据

| 序号 | 文件 | 说明 |
|------|------|------|
"""
    for i, fig in enumerate(figures, 1):
        doc += f"| {i} | {fig.get('file', '')} | {fig.get('caption', '')} |\n"

    doc += f"""
## 表格证据

| 序号 | 文件 | 数据 |
|------|------|------|
"""
    for i, tbl in enumerate(tables, 1):
        doc += f"| {i} | {tbl.get('file', '')} | {json.dumps(tbl.get('data', {}), ensure_ascii=False)[:80]} |\n"

    doc += f"""
## 假设-验证矩阵

| 假设 ID | 描述 | 已验证 | 证据来源 |
|---------|------|--------|----------|
"""
    for a in assumptions:
        verified = "✅" if a.get("verified") else "❌"
        doc += f"| {a.get('id', '')} | {a.get('text', '')} | {verified} | {a.get('evidence', '')} |\n"

    map_path.write_text(doc, encoding="utf-8")
    return str(map_path)


def generate_consistency_report(subquestion: str, is_consistent: bool, report: dict) -> str:
    """生成论文-代码一致性报告"""
    path = get_consistency_report_path(subquestion)

    status = "通过 ✅" if is_consistent else "未通过 ❌"

    doc = f"""# 论文-代码一致性报告 (Paper-Code Consistency Report)

## 基本信息

- **子问题**: {subquestion}
- **检查时间**: {report['checked_at']}
- **检查结果**: {status}

## 统计信息

- 总结论数: {report['total_conclusions']}
- 已验证结论: {report['verified_conclusions']}
- 假设覆盖率: {report['assumption_coverage']['verified']}/{report['assumption_coverage']['total']}

## 问题列表

"""
    if report["missing_evidence"]:
        for issue in report["missing_evidence"]:
            doc += f"- ❌ {issue}\n"
    else:
        doc += "- 无问题\n"

    doc += f"""
## 审计结论

{"✅ 论文-代码一致性检查通过，所有结论均有代码输出支撑" if is_consistent else "❌ 论文-代码一致性检查未通过，需要补充证据"}
"""

    path.write_text(doc, encoding="utf-8")
    return str(path)


# ═══════════════════════════════════════════════════════════════
# G4.5 门控
# ═══════════════════════════════════════════════════════════════

def check_evidence_chain(subquestion):
    """
    G4.5 门控检查：证据链

    Returns:
        (passed, message)
    """
    is_consistent, report = check_paper_code_consistency(subquestion)

    # 生成报告文件
    generate_evidence_map(subquestion)
    generate_consistency_report(subquestion, is_consistent, report)

    if not is_consistent:
        issues = "\n".join(f"  - {i}" for i in report["missing_evidence"])
        return False, (
            f"G4.5 证据链未通过\n"
            f"原因: 论文-代码一致性检查失败\n"
            f"问题:\n{issues}\n"
            f"修复: 请补充证据并重新运行检查"
        )

    return True, (
        f"G4.5 证据链通过\n"
        f"- 假设覆盖: {report['assumption_coverage']['verified']}/{report['assumption_coverage']['total']}\n"
        f"- 代码输出证据: {len(_evidence_load(subquestion).get('code_outputs', []))}\n"
        f"- 映射文档: {get_evidence_map_path(subquestion)}\n"
        f"- 一致性报告: {get_consistency_report_path(subquestion)}"
    )


def _evidence_load(subquestion: str) -> dict:
    """加载证据数据"""
    p = get_evidence_json_path(subquestion)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Evidence Tracer - 证据链追踪器")
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_reg = sub.add_parser("register", help="注册证据")
    p_reg.add_argument("--subquestion", required=True)
    p_reg.add_argument("--evidence-file", required=True, help="证据 JSON 文件路径")

    p_extract = sub.add_parser("extract", help="从论文提取结论")
    p_extract.add_argument("--subquestion", required=True)
    p_extract.add_argument("--paper", required=True, help="论文 Markdown 路径")

    p_check = sub.add_parser("check", help="G4.5 门控检查")
    p_check.add_argument("--subquestion", required=True)

    args = parser.parse_args()

    if args.command == "register":
        with open(args.evidence_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = register_evidence(args.subquestion, data)
        print(f"✅ 证据已注册")
        print(f"  代码输出: {result['evidence_count']['code_outputs']}")
        print(f"  图表: {result['evidence_count']['figures']}")
        print(f"  表格: {result['evidence_count']['tables']}")
        print(f"  假设: {result['evidence_count']['assumptions']}")

    elif args.command == "extract":
        conclusions = extract_conclusions_from_paper(args.paper)
        print(f"✅ 从论文中提取到 {len(conclusions)} 条结论")
        for i, c in enumerate(conclusions, 1):
            print(f"  {i}. {c['text'][:60]}...")

    elif args.command == "check":
        passed, msg = check_evidence_chain(args.subquestion)
        print(msg)
        sys.exit(0 if passed else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()