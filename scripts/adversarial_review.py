#!/usr/bin/env python3
"""
adversarial_review.py — 红队对抗审稿引擎 (M4)

模拟评委找漏洞，实现对抗性自省。
纯文件工具，不调用 LLM API。

功能:
  generate  — 对论文执行红队审稿，输出弱点清单 + 严重性评级
  check-rebuttal — 检查反驳/修订是否覆盖了所有高优先级问题
  report    — 生成汇总报告
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace_from_project
OUTPUTS_DIR = resolve_workspace_from_project(PROJECT_ROOT) / "outputs"
AUDITS_DIR = OUTPUTS_DIR / "audits"

# ── 弱点模式定义 ──────────────────────────────────────────────

WEAKNESS_PATTERNS = {
    "unsupported_claim": {
        "name": "无支撑论断",
        "severity": "P0",
        "category": "逻辑缺陷",
        "patterns": [
            r"(?:显然|明显|可以预见|毫无疑问|众所周知|不言而喻)",
            r"(?:显然|明显|必然|一定|肯定|毫无疑问).*(?:正确|合理|最优|准确)",
        ],
        "description": "存在缺乏数据/推理支撑的断言性表述",
    },
    "missing_error_bound": {
        "name": "缺少误差边界",
        "severity": "P0",
        "category": "严谨性缺失",
        "patterns": [
            r"(?:结果|精度|准确率|误差).*?(?:为|是|达到)\s*[\d.]+%(?!.*(?:±|%.*?置信))",
            r"RMSE.*?=.*?[\d.]+(?!.*(?:±|置信区间|标准差|置信度))",
            r"MAE.*?=.*?[\d.]+(?!.*(?:±|置信区间|标准差))",
        ],
        "description": "数值结果未附带误差边界或置信区间",
    },
    "vague_conclusion": {
        "name": "模糊结论",
        "severity": "P1",
        "category": "表述质量",
        "patterns": [
            r"(?:较好的|良好的|令人满意的|不错的|可以接受的)(?:效果|性能|结果|表现)",
            r"(?:一定程度上|在一定程度|有所提升|有所改善)(?!.*(?:\d+%|\d+\.\d+))",
        ],
        "description": "结论缺乏量化支撑，表述模糊",
    },
    "no_comparison": {
        "name": "缺少对比基准",
        "severity": "P1",
        "category": "实验完整性",
        "patterns": [
            r"(?:本文|我们|该方法).*(?:优于|超越|好于|胜过)(?!.*(?:相比|对比|vs|与.*比|基线))",
            r"(?:最优|最佳|最好)(?!.*(?:在.*中|相比|对比|vs|benchmark))",
        ],
        "description": "声称优于其他方法但未给出对比基准",
    },
    "missing_sensitivity": {
        "name": "灵敏度分析缺失",
        "severity": "P1",
        "category": "稳健性缺失",
        "patterns": [
            r"(?:模型|参数).*(?:稳定性|稳健|鲁棒|可靠)(?!.*(?:灵敏度|敏感性|扰动|sweep|perturbation|±))",
        ],
        "description": "声称模型稳健但未提供灵敏度分析证据",
    },
    "logical_gap": {
        "name": "逻辑跳跃",
        "severity": "P1",
        "category": "逻辑缺陷",
        "patterns": [
            r"(?:因此|所以|故而|从而|综上)(?!.*(?:因为|由于|根据|由.*可知|由.*推导))",
            r"(?:由上|由前|前述).*(?:可知|可得|得出)(?!.*(?:公式|方程|推导|计算))",
        ],
        "description": "推理链存在逻辑跳跃，缺少中间推导",
    },
    "formula_without_derivation": {
        "name": "公式无推导",
        "severity": "P1",
        "category": "严谨性缺失",
        "patterns": [
            r"(?:最终模型|目标函数|约束条件).*(?:如下|为|是)\s*[:：]",
            r"(?:式|公式|方程)\s*[\(\（]\d+[\)\）]\s*(?:为|是)",
        ],
        "description": "公式直接给出而无推导过程",
    },
    "missing_boundary": {
        "name": "边界条件缺失",
        "severity": "P2",
        "category": "严谨性缺失",
        "patterns": [
            r"(?:适用|有效|收敛)(?!.*(?:范围|边界|条件|前提|限制))",
        ],
        "description": "未说明模型的适用范围或边界条件",
    },
    "data_no_explanation": {
        "name": "数据处理无说明",
        "severity": "P2",
        "category": "数据质量",
        "patterns": [
            r"(?:剔除|删除|过滤|忽略).*?(?:数据|样本|记录|行)(?!.*(?:因为|由于|理由|原因|标准|原则|异常|缺失))",
        ],
        "description": "数据处理操作缺乏理由说明",
    },
    "overclaim_innovation": {
        "name": "创新性夸大",
        "severity": "P2",
        "category": "学术诚信",
        "patterns": [
            r"(?:首次|创新性|原创|开创性)(?!.*(?:在.*领域|基于|参考|借鉴))",
            r"(?:国内外首创|国内领先|国际先进)(?!.*(?:据.*调研|据.*了解))",
        ],
        "description": "创新性声明缺乏依据",
    },
}

# ── 核心函数 ──────────────────────────────────────────────────


def extract_paper_sections(text: str) -> Dict[str, str]:
    """将论文拆分为章节，用于按章节分析弱点。"""
    sections = {}
    current_section = "全文"
    current_content = []
    section_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

    last_pos = 0
    for match in section_pattern.finditer(text):
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()
        heading = match.group(2).strip()
        current_section = heading
        current_content = []
        last_pos = match.end()

    remaining = text[last_pos:]
    if remaining.strip():
        current_content.append(remaining.strip())
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    if not sections:
        sections["全文"] = text

    return sections


def scan_weaknesses(text: str) -> List[Dict[str, Any]]:
    """扫描论文文本，提取所有弱点。"""
    weaknesses = []
    sections = extract_paper_sections(text)

    for section_name, section_text in sections.items():
        for weakness_id, weakness_def in WEAKNESS_PATTERNS.items():
            for pattern in weakness_def["patterns"]:
                matches = list(re.finditer(pattern, section_text))
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(section_text), match.end() + 50)
                    context = section_text[start:end].replace("\n", " ").strip()
                    weaknesses.append({
                        "id": weakness_id,
                        "name": weakness_def["name"],
                        "severity": weakness_def["severity"],
                        "category": weakness_def["category"],
                        "description": weakness_def["description"],
                        "section": section_name,
                        "context": context,
                        "position": match.start(),
                    })

    weaknesses.sort(key=lambda w: ("P0", "P1", "P2").index(w["severity"]))
    return weaknesses


def generate_review_report(text: str, title: str = "论文") -> Dict[str, Any]:
    """生成完整红队对抗审稿报告。"""
    weaknesses = scan_weaknesses(text)

    severity_counts = {"P0": 0, "P1": 0, "P2": 0}
    category_counts = {}
    for w in weaknesses:
        severity_counts[w["severity"]] = severity_counts.get(w["severity"], 0) + 1
        cat = w["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    gate_thresholds = {"P0": 0, "P1": 3}
    p0_pass = severity_counts["P0"] <= gate_thresholds["P0"]
    p1_pass = severity_counts["P1"] <= gate_thresholds["P1"]
    gate_passed = p0_pass and p1_pass

    report = {
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "total_weaknesses": len(weaknesses),
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "gate_passed": gate_passed,
        "gate_thresholds": gate_thresholds,
        "weaknesses": weaknesses,
    }
    return report


def write_review_report_md(report: Dict[str, Any], output_dir: Optional[Path] = None) -> str:
    """将审稿报告写入 Markdown 文件。"""
    if output_dir is None:
        output_dir = AUDITS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"adversarial_review_{ts}.md"

    lines = [
        f"# 红队对抗审稿报告",
        f"",
        f"- **论文**: {report['title']}",
        f"- **时间**: {report['timestamp']}",
        f"- **弱点总数**: {report['total_weaknesses']}",
        f"- **门禁通过**: {'✅ PASS' if report['gate_passed'] else '❌ FAIL'}",
        f"",
        f"## 严重性分布",
        f"",
        f"| 级别 | 数量 | 阈值 | 状态 |",
        f"|------|------|------|------|",
        f"| P0 (致命) | {report['severity_counts']['P0']} | ≤{report['gate_thresholds']['P0']} | {'✅' if report['severity_counts']['P0'] <= report['gate_thresholds']['P0'] else '❌'} |",
        f"| P1 (严重) | {report['severity_counts']['P1']} | ≤{report['gate_thresholds']['P1']} | {'✅' if report['severity_counts']['P1'] <= report['gate_thresholds']['P1'] else '❌'} |",
        f"| P2 (建议) | {report['severity_counts']['P2']} | - | ℹ️ |",
        f"",
        f"## 按类别分布",
        f"",
    ]
    for cat, count in sorted(report["category_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{cat}**: {count}")

    lines.append("")
    lines.append("## 弱点详情")
    lines.append("")

    for w in report["weaknesses"]:
        lines.append(f"### [{w['severity']}] {w['name']} ({w['category']})")
        lines.append(f"")
        lines.append(f"- **章节**: {w['section']}")
        lines.append(f"- **描述**: {w['description']}")
        lines.append(f"- **上下文**: ...{w['context']}...")
        lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)


# ── 反驳覆盖检查 ──────────────────────────────────────────────


def check_rebuttal_coverage(
    paper_text: str, review_report: Optional[Dict] = None
) -> Dict[str, Any]:
    """检查论文修订是否覆盖了审稿弱点。

    扫描论文中是否存在回应审稿意见的段落（如"审稿意见""回复""修订"等关键词），
    并检查 P0/P1 弱点是否被回应。
    """
    if review_report is None:
        review_report = generate_review_report(paper_text)

    rebuttal_keywords = [
        "审稿", "回复", "修订", "rebuttal", "revision", "针对审稿",
        "修改说明", "回应", "更正",
    ]
    has_rebuttal_section = any(kw in paper_text for kw in rebuttal_keywords)

    addressed_weaknesses = []
    for weakness in review_report["weaknesses"]:
        if weakness["severity"] in ("P0", "P1"):
            weakness_keywords = [
                weakness["name"],
                weakness["category"],
            ]
            is_addressed = any(kw in paper_text for kw in weakness_keywords)
            addressed_weaknesses.append({
                "weakness_id": weakness["id"],
                "name": weakness["name"],
                "severity": weakness["severity"],
                "addressed": is_addressed,
            })

    total_p0p1 = len(addressed_weaknesses)
    addressed_count = sum(1 for w in addressed_weaknesses if w["addressed"])
    coverage_ratio = addressed_count / total_p0p1 if total_p0p1 > 0 else 1.0

    result = {
        "has_rebuttal_section": has_rebuttal_section,
        "total_p0p1_weaknesses": total_p0p1,
        "addressed_count": addressed_count,
        "coverage_ratio": round(coverage_ratio, 2),
        "all_covered": coverage_ratio >= 1.0,
        "details": addressed_weaknesses,
    }
    return result


# ── CLI 入口 ──────────────────────────────────────────────────


def cmd_generate(args):
    """生成红队对抗审稿报告"""
    paper_path = Path(args.file)
    if not paper_path.exists():
        print(f"[adversarial-review] 文件不存在: {paper_path}")
        return

    text = paper_path.read_text(encoding="utf-8")
    title = getattr(args, "title", paper_path.stem)
    report = generate_review_report(text, title)

    output_path = write_review_report_md(report)
    print(f"[adversarial-review] 审稿报告已生成: {output_path}")
    print(f"  总弱点: {report['total_weaknesses']}")
    print(f"  P0: {report['severity_counts']['P0']}, P1: {report['severity_counts']['P1']}, P2: {report['severity_counts']['P2']}")
    print(f"  门禁: {'PASS ✅' if report['gate_passed'] else 'FAIL ❌'}")


def cmd_check_rebuttal(args):
    """检查反驳覆盖度"""
    paper_path = Path(args.file)
    if not paper_path.exists():
        print(f"[adversarial-review] 文件不存在: {paper_path}")
        return

    text = paper_path.read_text(encoding="utf-8")

    review_path = None
    if hasattr(args, "review") and args.review:
        review_path = Path(args.review)
        if review_path.exists():
            review_data = json.loads(review_path.read_text(encoding="utf-8"))
        else:
            print(f"[adversarial-review] 审稿报告不存在: {review_path}")
            return
    else:
        review_data = generate_review_report(text)

    result = check_rebuttal_coverage(text, review_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_report(args):
    """生成汇总报告"""
    output_dir = Path(args.output_dir) if hasattr(args, "output_dir") and args.output_dir else AUDITS_DIR
    reports = sorted(output_dir.glob("adversarial_review_*.md"))

    if not reports:
        print("[adversarial-review] 未找到审稿报告")
        return

    print(f"[adversarial-review] 共 {len(reports)} 份审稿报告:")
    for r in reports:
        print(f"  - {r.name}")
    print(f"最新: {reports[-1]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="红队对抗审稿引擎 (M4)")
    sub = parser.add_subparsers(dest="cmd")

    p_gen = sub.add_parser("generate", help="生成红队对抗审稿报告")
    p_gen.add_argument("--file", "-f", required=True, help="论文文件路径")
    p_gen.add_argument("--title", default="论文", help="论文标题")

    p_reb = sub.add_parser("check-rebuttal", help="检查反驳覆盖度")
    p_reb.add_argument("--file", "-f", required=True, help="论文文件路径")
    p_reb.add_argument("--review", "-r", help="审稿报告 JSON 路径")

    p_rpt = sub.add_parser("report", help="生成汇总报告")
    p_rpt.add_argument("--output-dir", "-d", help="报告目录")

    args = parser.parse_args()
    dispatch = {"generate": cmd_generate, "check-rebuttal": cmd_check_rebuttal, "report": cmd_report}
    if args.cmd in dispatch:
        dispatch[args.cmd](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
