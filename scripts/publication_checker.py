#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publication Readiness Checker v1.0 — S9.5 出版规范审查
====================================================
检测 AI 痕迹、非正式表达、图文排布、格式规范、学术规范性、竞赛特定规范。

用法：
  python scripts/publication_checker.py check <paper.md> --mode standard
  python scripts/publication_checker.py ai-traces <paper.md>
  python scripts/publication_checker.py informal <paper.md>
  python scripts/publication_checker.py figure-layout <paper.md>
  python scripts/publication_checker.py format <paper.md>
  python scripts/publication_checker.py academic <paper.md>
  python scripts/publication_checker.py competition <paper.md> --mode championship
  python scripts/publication_checker.py report <paper.md> --mode standard --output report.md
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Tuple


class Severity(Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass
class Issue:
    category: str
    severity: Severity
    line: int
    message: str
    context: str = ""
    suggestion: str = ""


@dataclass
class CheckResult:
    category: str
    passed: bool
    issues: List[Issue] = field(default_factory=list)
    summary: str = ""


# ═══════════════════════════════════════════════════════════════
# AI 痕迹检测 (P0)
# ═══════════════════════════════════════════════════════════════

AI_PHRASES_P0 = [
    "显著提升", "有效解决", "充分考虑", "深入分析", "全面评估",
    "取得了显著", "显著改善", "显著提高", "显著降低", "显著减少",
    "有效提高", "有效降低", "有效改善", "有效减少",
    "充分说明", "充分验证", "充分证明", "充分体现", "充分利用",
    "全面分析", "全面考虑", "全面研究",
    "高度一致", "高度吻合", "高度相关", "高度匹配",
    "综上所述", "总而言之", "总的来说",
    "值得注意的是", "需要指出的是", "需要强调的是",
    "不言而喻", "显而易见", "毋庸置疑", "众所周知",
    "具有重要意义", "具有重要价值", "具有重大意义",
    "取得了良好的效果", "取得了令人满意的结果",
    "为...提供了理论依据", "为...奠定了坚实基础",
]

AI_CONNECTORS_P0 = [
    "与此同时", "值得注意的是，", "需要指出的是，",
    "由此可见，", "由此可知，", "由此可见",
    "进一步而言", "进一步地，", "除此之外，",
]

AI_OVERSTATEMENT_P1 = [
    "非常有效", "极为重要", "极其重要",
    "取得了突破性进展", "实现了质的飞跃",
    "具有开创性意义", "开创了",
    "极大地推动了", "有力地促进了",
    "完美地解决了", "圆满地完成了",
    "具有广泛的应用前景", "应用前景广阔",
]

VAGUE_QUANTIFIERS_P1 = [
    "大幅度", "明显提升", "明显提高", "明显改善", "明显降低",
    "较好地", "一定程度上", "基本实现", "基本达到", "基本满足",
    "相对较高", "相对较低", "相对较好",
    "比较大", "比较明显", "比较显著",
]


def check_ai_traces(text: str, lines: List[str]) -> CheckResult:
    issues = []

    # AI 套话检测
    p0_counts = {}
    for phrase in AI_PHRASES_P0:
        count = text.count(phrase)
        if count > 0:
            p0_counts[phrase] = count
    p0_total = sum(p0_counts.values())

    if p0_total >= 3:
        for phrase, count in p0_counts.items():
            for i, line in enumerate(lines, 1):
                if phrase in line:
                    issues.append(Issue("AI痕迹/套话", Severity.P0, i,
                        f"AI套话「{phrase}」（同类共 {p0_total} 处）",
                        line.strip()[:80], "替换为具体量化描述"))
                    break
    elif p0_total > 0:
        for phrase in p0_counts:
            for i, line in enumerate(lines, 1):
                if phrase in line:
                    issues.append(Issue("AI痕迹/套话", Severity.P1, i,
                        f"AI套话「{phrase}」（累计 {p0_total} 处，临界值3）",
                        line.strip()[:80], "建议替换"))
                    break

    # 万能连接词
    conn_count = sum(1 for c in AI_CONNECTORS_P0 for line in lines if c in line)
    if conn_count >= 5:
        for c in AI_CONNECTORS_P0:
            for i, line in enumerate(lines, 1):
                if c in line:
                    issues.append(Issue("AI痕迹/连接词", Severity.P0, i,
                        f"万能连接词过度使用（共 {conn_count} 处）",
                        line.strip()[:60], "精简连接词"))
                    break

    # 过度修饰
    overstate = sum(1 for p in AI_OVERSTATEMENT_P1 for line in lines if p in line)
    if overstate >= 3:
        for p in AI_OVERSTATEMENT_P1:
            for i, line in enumerate(lines, 1):
                if p in line:
                    issues.append(Issue("AI痕迹/过度修饰", Severity.P1, i,
                        f"过度修饰「{p}」", line.strip()[:80], "使用客观学术表达"))
                    break

    # 模糊量化
    vague = sum(1 for p in VAGUE_QUANTIFIERS_P1 for line in lines if p in line)
    if vague >= 5:
        issues.append(Issue("AI痕迹/模糊量化", Severity.P0, 0,
            f"模糊量化词过多（共 {vague} 处）", "", "必须替换为精确数值"))
    elif vague >= 3:
        for p in VAGUE_QUANTIFIERS_P1:
            for i, line in enumerate(lines, 1):
                if p in line:
                    issues.append(Issue("AI痕迹/模糊量化", Severity.P1, i,
                        f"模糊量化「{p}」", line.strip()[:80], "替换为精确数值"))
                    break

    p0 = sum(1 for i in issues if i.severity == Severity.P0)
    return CheckResult("AI痕迹检测", p0 == 0, issues,
        f"AI痕迹: P0={p0}, 总={len(issues)} {'❌' if p0 else '✅'}")


# ═══════════════════════════════════════════════════════════════
# 非正式表达检测 (P1)
# ═══════════════════════════════════════════════════════════════

def check_informal_language(text: str, lines: List[str]) -> CheckResult:
    issues = []

    # 找摘要范围
    abs_start, abs_end = -1, -1
    for i, line in enumerate(lines):
        if re.match(r'^#{1,3}\s*(摘要|Summary|ABSTRACT)', line):
            abs_start = i
        elif abs_start >= 0 and abs_end < 0 and re.match(r'^#{1,3}\s+', line):
            abs_end = i
    if abs_start >= 0 and abs_end < 0:
        abs_end = len(lines)

    # 第一人称
    first_person = ["我们认为", "我们发现", "我们选择", "我们采用", "我们使用", "笔者认为"]
    for phrase in first_person:
        for i, line in enumerate(lines, 1):
            if phrase in line:
                is_abs = abs_start >= 0 and abs_start < i <= abs_end
                sev = Severity.P0 if is_abs else Severity.P1
                issues.append(Issue("非正式/第一人称", sev, i,
                    f"「{phrase}」" + ("（摘要中）" if is_abs else ""),
                    line.strip()[:80], "改为「本文」「本模型」"))

    # 口语化
    informal = ["可以看出", "不难发现", "显而易见", "毋庸置疑",
                "简单来说", "简单地说", "不得不说", "说实话"]
    for phrase in informal:
        for i, line in enumerate(lines, 1):
            if phrase in line:
                issues.append(Issue("非正式/口语化", Severity.P1, i,
                    f"口语化「{phrase}」", line.strip()[:80],
                    "改为「实验结果表明」等学术表达"))
                break

    # 非学术缩写
    for pat, orig, repl in [(r'\betc\.?\b', "etc.", "等"),
                             (r'\bi\.e\.?\b', "i.e.", "即"),
                             (r'\be\.g\.?\b', "e.g.", "例如")]:
        for i, line in enumerate(lines, 1):
            if re.search(pat, line):
                issues.append(Issue("非正式/缩写", Severity.P2, i,
                    f"「{orig}」→「{repl}」", line.strip()[:80], ""))

    p0 = sum(1 for i in issues if i.severity == Severity.P0)
    return CheckResult("非正式表达检测", p0 == 0, issues,
        f"非正式: P0={p0}, 总={len(issues)} {'❌' if p0 else '✅'}")


# ═══════════════════════════════════════════════════════════════
# 图文排布规范 (P1)
# ═══════════════════════════════════════════════════════════════

def check_figure_layout(text: str, lines: List[str]) -> CheckResult:
    issues = []

    # 提取图定义
    fig_defs = []
    for i, line in enumerate(lines, 1):
        m = re.search(r'图\s*(\d+)', line)
        if m and (re.match(r'^\s*图\s*\d+', line) or '![ ' in line or '![' in line):
            fig_defs.append((i, int(m.group(1))))

    # 提取图引用
    fig_refs = []
    ref_pats = [r'如图\s*(\d+)', r'见图\s*(\d+)', r'图\s*(\d+)\s*展示',
                r'图\s*(\d+)\s*表明', r'图\s*(\d+)\s*显示',
                r'Figure\s*(\d+)', r'fig\s*(\d+)']
    for i, line in enumerate(lines, 1):
        for pat in ref_pats:
            for m in re.finditer(pat, line, re.IGNORECASE):
                fig_refs.append((i, int(m.group(1))))

    # 表定义和引用
    tbl_defs = []
    for i, line in enumerate(lines, 1):
        m = re.search(r'表\s*(\d+)', line)
        if m and re.match(r'^\s*表\s*\d+', line):
            tbl_defs.append((i, int(m.group(1))))

    tbl_refs = []
    tbl_ref_pats = [r'见表\s*(\d+)', r'如表\s*(\d+)', r'Table\s*(\d+)']
    for i, line in enumerate(lines, 1):
        for pat in tbl_ref_pats:
            for m in re.finditer(pat, line, re.IGNORECASE):
                tbl_refs.append((i, int(m.group(1))))

    # 先文后图检查
    for def_line, fid in fig_defs:
        refs_before = [r for r, id_ in fig_refs if id_ == fid and r < def_line]
        if not refs_before:
            issues.append(Issue("图文/先文后图", Severity.P1, def_line,
                f"图{fid}无前置引用", "", "添加「如图X所示」"))

    # 引用完整性
    for def_line, fid in fig_defs:
        if not any(id_ == fid for _, id_ in fig_refs):
            issues.append(Issue("图文/引用", Severity.P1, def_line,
                f"图{fid}无正文引用", "", "添加正文引用"))
    for def_line, tid in tbl_defs:
        if not any(id_ == tid for _, id_ in tbl_refs):
            issues.append(Issue("图文/引用", Severity.P1, def_line,
                f"表{tid}无正文引用", "", "添加正文引用"))

    p0 = sum(1 for i in issues if i.severity == Severity.P0)
    return CheckResult("图文排布规范", p0 == 0, issues,
        f"图文: 总={len(issues)} {'✅' if not issues else '⚠️'}")


# ═══════════════════════════════════════════════════════════════
# 格式合规性 (P1)
# ═══════════════════════════════════════════════════════════════

def check_format_compliance(text: str, lines: List[str]) -> CheckResult:
    issues = []

    # 公式编号连续性
    formula_nums = []
    for i, line in enumerate(lines, 1):
        m = re.search(r'\((\d+)\)\s*$', line.strip())
        if m:
            formula_nums.append((i, int(m.group(1))))

    if formula_nums:
        nums = [n for _, n in formula_nums]
        for idx in range(1, len(nums)):
            if nums[idx] != nums[idx - 1] + 1:
                issues.append(Issue("格式/公式编号", Severity.P1, formula_nums[idx][0],
                    f"编号不连续: ({nums[idx-1]})→({nums[idx]})",
                    "", f"应为 ({nums[idx-1]})→({nums[idx-1]+1})"))

    # 图编号连续性
    fig_nums = []
    seen = set()
    for i, line in enumerate(lines, 1):
        m = re.search(r'图\s*(\d+)', line)
        if m:
            n = int(m.group(1))
            if n not in seen:
                seen.add(n)
                fig_nums.append((i, n))

    if fig_nums:
        nums = [n for _, n in fig_nums]
        for idx in range(1, len(nums)):
            if nums[idx] != nums[idx - 1] + 1:
                issues.append(Issue("格式/图表编号", Severity.P1, fig_nums[idx][0],
                    f"图编号不连续: 图{nums[idx-1]}→图{nums[idx]}", "", ""))

    # 章节层级超过3级
    for i, line in enumerate(lines, 1):
        m = re.match(r'^(#{1,6})\s+([\d.]+)\s', line)
        if m and len(m.group(2).split('.')) > 3:
            issues.append(Issue("格式/章节层级", Severity.P2, i,
                f"超过3级编号: {m.group(2)}", "", ""))

    # 三线表检测
    in_table = False
    table_lines = []
    table_start = 0
    for i, line in enumerate(lines, 1):
        if re.match(r'^\s*\|.*\|', line):
            if not in_table:
                in_table = True
                table_start = i
                table_lines = []
            table_lines.append(line)
        else:
            if in_table and table_lines:
                sep = sum(1 for tl in table_lines if re.match(r'^\s*\|[\s\-:|]+\|', tl))
                if sep > 1:
                    issues.append(Issue("格式/三线表", Severity.P2, table_start,
                        f"表格有{sep}条分隔线（三线表应仅1条）", "", ""))
                in_table = False
                table_lines = []

    p0 = sum(1 for i in issues if i.severity == Severity.P0)
    return CheckResult("格式合规性", p0 == 0, issues,
        f"格式: 总={len(issues)} {'✅' if p0 == 0 else '❌'}")


# ═══════════════════════════════════════════════════════════════
# 学术规范性 (P1)
# ═══════════════════════════════════════════════════════════════

def check_academic_norms(text: str, lines: List[str]) -> CheckResult:
    issues = []

    # 悬空引用检测
    ref_in_text = set(int(m.group(1)) for m in re.finditer(r'\[(\d+)\]', text))

    ref_start = -1
    for i, line in enumerate(lines):
        if re.match(r'^#{1,3}\s*(参考文献|References|Bibliography)', line):
            ref_start = i
            break

    if ref_start >= 0:
        refs_in_list = set(int(m.group(1))
            for m in re.finditer(r'\[(\d+)\]', "\n".join(lines[ref_start:])))
        dangling = ref_in_text - refs_in_list
        for rn in sorted(dangling):
            for i, line in enumerate(lines, 1):
                if f"[{rn}]" in line and i < ref_start:
                    issues.append(Issue("学术/悬空引用", Severity.P1, i,
                        f"[{rn}] 在参考文献列表中不存在", line.strip()[:60], ""))
                    break

    # 引用格式统一性
    has_bracket = bool(re.search(r'\[\d+\]', text))
    has_author = bool(re.search(r'\([A-Z][a-z]+,\s*\d{4}\)', text))
    if has_bracket and has_author:
        issues.append(Issue("学术/引用格式", Severity.P2, 0,
            "混用[编号]和(Author, Year)引用格式", "", "统一使用一种"))

    # 公式引用格式统一性
    has_gongshi = bool(re.search(r'公式\s*\(', text))
    has_shi = bool(re.search(r'式\s*\(', text))
    if has_gongshi and has_shi:
        issues.append(Issue("学术/公式引用", Severity.P2, 0,
            "混用「公式(N)」和「式(N)」", "", "统一使用一种"))

    # 术语一致性（常见混用）
    term_pairs = [
        ("目标函数", "代价函数", "目标函数/代价函数"),
        ("损失函数", "代价函数", "损失函数/代价函数"),
        ("约束条件", "限制条件", "约束条件/限制条件"),
    ]
    for t1, t2, desc in term_pairs:
        if t1 in text and t2 in text:
            issues.append(Issue("学术/术语一致", Severity.P1, 0,
                f"混用 {desc}", "", "全文统一术语"))

    p0 = sum(1 for i in issues if i.severity == Severity.P0)
    return CheckResult("学术规范性", p0 == 0, issues,
        f"学术: 总={len(issues)} {'✅' if p0 == 0 else '❌'}")


# ═══════════════════════════════════════════════════════════════
# 竞赛特定规范 (P0)
# ═══════════════════════════════════════════════════════════════

MODE_THRESHOLDS = {
    "fast":        {"min_words": 8000,  "min_figs": 4,  "min_refs": 4,  "rework_max": 2},
    "standard":    {"min_words": 12000, "min_figs": 6,  "min_refs": 6,  "rework_max": 3},
    "championship": {"min_words": 15000, "min_figs": 10, "min_refs": 10, "rework_max": 5},
}


def check_competition_rules(text: str, lines: List[str], mode: str = "standard") -> CheckResult:
    issues = []
    thresh = MODE_THRESHOLDS.get(mode, MODE_THRESHOLDS["standard"])

    # 匿名性检测（不应出现具体学校/姓名）
    anon_patterns = [
        (r'(?:我们|我)来自\s*[\u4e00-\u9fff]+大学', "泄露学校名称"),
        (r'(?:队员|组员)\s*[:：]\s*[\u4e00-\u9fff]+', "泄露队员姓名"),
        (r'(?:指导老师|指导教师)\s*[:：]\s*[\u4e00-\u9fff]+', "泄露指导教师"),
        (r'(?:队伍|队伍编号)\s*[:：]?\s*[A-Z]?\d{4,}', "泄露队伍编号"),
    ]
    for pat, desc in anon_patterns:
        for i, line in enumerate(lines, 1):
            if re.search(pat, line):
                issues.append(Issue("竞赛/匿名性", Severity.P0, i,
                    f"匿名性违规: {desc}", line.strip()[:80],
                    "删除个人信息，竞赛论文必须匿名"))

    # 字数检测
    # 只统计中文字符和英文单词（排除代码块和公式）
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 简化计算：中文字符数 + 英文单词数
    total_words = chinese_chars + english_words
    if total_words < thresh["min_words"]:
        issues.append(Issue("竞赛/字数", Severity.P0, 0,
            f"总字数不足: {total_words} < {thresh['min_words']} ({mode}模式)",
            "", f"必须达到 {thresh['min_words']} 字"))

    # 图表数量检测
    fig_count = len(set(int(m.group(1))
        for m in re.finditer(r'图\s*(\d+)', text)
        if int(m.group(1)) <= 50))  # 排除大数字误匹配
    if fig_count < thresh["min_figs"]:
        issues.append(Issue("竞赛/图表数量", Severity.P0, 0,
            f"图表数量不足: {fig_count} < {thresh['min_figs']} ({mode}模式)",
            "", f"至少需要 {thresh['min_figs']} 张图"))

    # 参考文献数量
    refs_found = set(int(m.group(1))
        for m in re.finditer(r'\[(\d+)\]', text))
    max_ref = max(refs_found) if refs_found else 0
    if max_ref < thresh["min_refs"]:
        issues.append(Issue("竞赛/参考文献", Severity.P0, 0,
            f"参考文献不足: {max_ref} < {thresh['min_refs']} ({mode}模式)",
            "", f"至少需要 {thresh['min_refs']} 篇参考文献"))

    # 占位符检测
    placeholders = ["TBD", "TODO", "待填写", "待补充", "[待", "FIXME", "PLACEHOLDER"]
    for ph in placeholders:
        for i, line in enumerate(lines, 1):
            if ph.lower() in line.lower():
                issues.append(Issue("竞赛/占位符", Severity.P0, i,
                    f"发现占位符「{ph}」", line.strip()[:60],
                    "必须填写实际内容"))

    p0 = sum(1 for i in issues if i.severity == Severity.P0)
    return CheckResult("竞赛特定规范", p0 == 0, issues,
        f"竞赛规范: P0={p0}, 总={len(issues)} {'❌' if p0 else '✅'}")


# ═══════════════════════════════════════════════════════════════
# 综合报告
# ═══════════════════════════════════════════════════════════════

def run_all_checks(paper_path: str, mode: str = "standard") -> dict:
    """运行所有检查，返回完整报告"""
    path = Path(paper_path)
    if not path.exists():
        print(f"ERROR: 文件不存在: {paper_path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    results = [
        check_ai_traces(text, lines),
        check_informal_language(text, lines),
        check_figure_layout(text, lines),
        check_format_compliance(text, lines),
        check_academic_norms(text, lines),
        check_competition_rules(text, lines, mode),
    ]

    all_issues = []
    for r in results:
        all_issues.extend(r.issues)

    p0 = sum(1 for i in all_issues if i.severity == Severity.P0)
    p1 = sum(1 for i in all_issues if i.severity == Severity.P1)
    p2 = sum(1 for i in all_issues if i.severity == Severity.P2)

    overall = p0 == 0 and p1 <= 2

    return {
        "paper_path": paper_path,
        "mode": mode,
        "results": results,
        "overall_passed": overall,
        "p0_count": p0,
        "p1_count": p1,
        "p2_count": p2,
    }


def format_report(report: dict) -> str:
    """格式化为 Markdown 报告"""
    lines = []
    lines.append("# Publication Readiness Report — 出版规范审查报告")
    lines.append(f"\n**文件**: `{report['paper_path']}`")
    lines.append(f"**模式**: {report['mode']}")
    lines.append(f"**结果**: {'✅ PASS' if report['overall_passed'] else '❌ FAIL'}")
    lines.append(f"**统计**: P0={report['p0_count']}, P1={report['p1_count']}, P2={report['p2_count']}")

    # 门禁标准
    lines.append("\n## 门禁标准")
    lines.append("- P0 问题 = 0")
    lines.append("- P1 问题 ≤ 2")
    lines.append("- P2 问题 ≤ 5")

    lines.append("\n## 检查结果")
    for r in report["results"]:
        lines.append(f"\n### {r.category} {'✅' if r.passed else '❌'}")
        lines.append(f"{r.summary}")
        if r.issues:
            for issue in r.issues:
                sev = issue.severity.value
                loc = f"L{issue.line}" if issue.line > 0 else "全文"
                lines.append(f"- **[{sev}]** {loc}: {issue.message}")
                if issue.suggestion:
                    lines.append(f"  - 建议: {issue.suggestion}")

    # 打回决策
    lines.append("\n## 决策")
    if report["overall_passed"]:
        lines.append("✅ **PASSED** — 论文可进入 S10 最终交付")
    else:
        lines.append("❌ **FAILED** — 必须修复后重新检查")
        if report["p0_count"] > 0:
            lines.append(f"- P0 问题 {report['p0_count']} 个，必须全部清零")
        if report["p1_count"] > 2:
            lines.append(f"- P1 问题 {report['p1_count']} 个，必须降至 ≤ 2")
        lines.append("- 运行 `python scripts/stage_executor.py rework S9.5 --reason \"出版规范未通过\"`")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(
        description="Publication Readiness Checker v1.0 — S9.5 出版规范审查")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("check", help="运行所有检查")
    sp.add_argument("paper", help="论文 Markdown 文件路径")
    sp.add_argument("--mode", "-m", default="standard",
                    choices=["fast", "standard", "championship"])

    sp = sub.add_parser("ai-traces", help="仅检测 AI 痕迹")
    sp.add_argument("paper", help="论文文件路径")

    sp = sub.add_parser("informal", help="仅检测非正式表达")
    sp.add_argument("paper", help="论文文件路径")

    sp = sub.add_parser("figure-layout", help="仅检测图文排布")
    sp.add_argument("paper", help="论文文件路径")

    sp = sub.add_parser("format", help="仅检测格式合规")
    sp.add_argument("paper", help="论文文件路径")

    sp = sub.add_parser("academic", help="仅检测学术规范")
    sp.add_argument("paper", help="论文文件路径")

    sp = sub.add_parser("competition", help="仅检测竞赛规范")
    sp.add_argument("paper", help="论文文件路径")
    sp.add_argument("--mode", "-m", default="standard",
                    choices=["fast", "standard", "championship"])

    sp = sub.add_parser("report", help="生成完整报告")
    sp.add_argument("paper", help="论文文件路径")
    sp.add_argument("--mode", "-m", default="standard",
                    choices=["fast", "standard", "championship"])
    sp.add_argument("--output", "-o", default=None, help="报告输出文件")

    args = p.parse_args()

    if not args.cmd:
        p.print_help()
        sys.exit(0)

    path = Path(args.paper)
    if not path.exists():
        print(f"ERROR: 文件不存在: {args.paper}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    dispatch = {
        "check": lambda: _run_all(args),
        "ai-traces": lambda: _print_result(check_ai_traces(text, lines)),
        "informal": lambda: _print_result(check_informal_language(text, lines)),
        "figure-layout": lambda: _print_result(check_figure_layout(text, lines)),
        "format": lambda: _print_result(check_format_compliance(text, lines)),
        "academic": lambda: _print_result(check_academic_norms(text, lines)),
        "competition": lambda: _print_result(check_competition_rules(text, lines, args.mode)),
        "report": lambda: _run_report(args),
    }

    dispatch[args.cmd]()


def _print_result(result: CheckResult):
    icon = "✅" if result.passed else "❌"
    print(f"\n{icon} {result.category}: {result.summary}")
    for issue in result.issues:
        sev = issue.severity.value
        loc = f"L{issue.line}" if issue.line > 0 else "全文"
        print(f"  [{sev}] {loc}: {issue.message}")
        if issue.suggestion:
            print(f"         → {issue.suggestion}")

    sys.exit(0 if result.passed else 1)


def _run_all(args):
    report = run_all_checks(args.paper, args.mode)
    icon = "✅ PASS" if report["overall_passed"] else "❌ FAIL"
    print(f"\n{'='*60}")
    print(f"  Publication Readiness Check — {icon}")
    print(f"{'='*60}")
    print(f"  P0={report['p0_count']}, P1={report['p1_count']}, P2={report['p2_count']}")
    print(f"{'='*60}\n")

    for r in report["results"]:
        _print_result(r)

    if not report["overall_passed"]:
        print(f"\n❌ PUBLICATION NOT READY — 必须修复后重新检查")
        print(f"  运行: python scripts/stage_executor.py rework S9.5 --reason '出版规范未通过'")
    else:
        print(f"\n✅ PUBLICATION READY — 可进入 S10 最终交付")

    sys.exit(0 if report["overall_passed"] else 1)


def _run_report(args):
    report = run_all_checks(args.paper, args.mode)
    md = format_report(report)
    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"报告已保存: {args.output}")
    else:
        print(md)

    sys.exit(0 if report["overall_passed"] else 1)


if __name__ == "__main__":
    main()
