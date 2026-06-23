#!/usr/bin/env python3
"""
figure_narrative_gate.py — 图表叙事引擎 (D-A-C 强制门禁)

强制每个图表配有 D-A-C (描述-分析-结论) 说明。
"有图必有文，有文必有图"。

纯文件工具，不调用 LLM API。

功能:
  scan       — 扫描论文中的所有图表引用
  check-dac  — 检查每个图表是否配有 D-A-C 叙事
  report     — 生成图表叙事覆盖率报告
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

FIGURE_PATTERNS = [
    re.compile(r"(?:图|Fig\.?|Figure)\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"(?:图|Fig\.?|Figure)\s*([\d一二三四五六七八九十]+)", re.IGNORECASE),
]

TABLE_PATTERNS = [
    re.compile(r"(?:表|Table)\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"(?:表|Table)\s*([\d一二三四五六七八九十]+)", re.IGNORECASE),
]

DAC_SIGNALS = {
    "describe": {
        "name": "描述 (Describe)",
        "patterns": [
            r"(?:如图|从图|图\s*\d+|图中|图表).*(?:可见|显示|表明|展示|呈现)",
            r"(?:该图|此图|上图|下图).*(?:显示|展示|表明|反映)",
            r"(?:横轴|纵轴|坐标轴|图例).*(?:表示|代表|含义)",
            r"(?:从.*?图.{0,20}(?:可以|能够)?(?:看到|观察到|看出|发现))",
        ],
    },
    "analyze": {
        "name": "分析 (Analyze)",
        "patterns": [
            r"(?:分析|分析表明|分析显示|分析结果)",
            r"(?:可以看出|由此可见|从.*?中.*?发现)",
            r"(?:趋势|规律|特征|模式|异常|波动)",
            r"(?:对比|比较|对照|相比).*(?:发现|表明|说明|可知)",
            r"(?:峰值|谷值|极值|拐点|临界|阈值)",
            r"(?:随着|变化|增长|下降|上升|波动|收敛)",
        ],
    },
    "conclude": {
        "name": "结论 (Conclude)",
        "patterns": [
            r"(?:因此|所以|综上|总结|由此可得)",
            r"(?:表明|说明|证明|验证了|证实了)",
            r"(?:说明了|揭示了|反映了|体现了)",
            r"(?:最优|最佳|主要|关键|核心|重要)",
            r"(?:结论|最终|结果是|答案是)",
        ],
    },
}


def scan_figures(text: str) -> List[Dict[str, Any]]:
    """扫描论文中的所有图表引用。"""
    figures = []
    seen = set()

    for pattern in FIGURE_PATTERNS:
        for match in pattern.finditer(text):
            fig_id = f"图{match.group(1)}"
            if fig_id not in seen:
                seen.add(fig_id)
                figures.append({
                    "id": fig_id,
                    "position": match.start(),
                    "type": "figure",
                })

    for pattern in TABLE_PATTERNS:
        for match in pattern.finditer(text):
            tbl_id = f"表{match.group(1)}"
            if tbl_id not in seen:
                seen.add(tbl_id)
                figures.append({
                    "id": tbl_id,
                    "position": match.start(),
                    "type": "table",
                })

    figures.sort(key=lambda x: x["position"])
    return figures


def check_dac_for_item(text: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """检查单个图表是否有 D-A-C 叙事。"""
    pos = item["position"]
    context_start = max(0, pos - 100)
    context_end = min(len(text), pos + 500)
    context = text[context_start:context_end]

    dac_result = {}
    for level, signals in DAC_SIGNALS.items():
        matched = False
        for pattern in signals["patterns"]:
            if re.search(pattern, context, re.IGNORECASE):
                matched = True
                break
        dac_result[level] = matched

    return {
        "id": item["id"],
        "type": item["type"],
        "describe": dac_result["describe"],
        "analyze": dac_result["analyze"],
        "conclude": dac_result["conclude"],
        "has_dac": all(dac_result.values()),
        "coverage": sum(dac_result.values()) / 3,
    }


def check_figures(text: str) -> Dict[str, Any]:
    """检查论文中所有图表的 D-A-C 叙事覆盖。"""
    items = scan_figures(text)
    if not items:
        return {
            "total": 0,
            "with_dac": 0,
            "coverage_ratio": 1.0,
            "passed": True,
            "details": [],
        }

    details = [check_dac_for_item(text, item) for item in items]
    with_dac = sum(1 for d in details if d["has_dac"])
    with_describe = sum(1 for d in details if d["describe"])
    with_analyze = sum(1 for d in details if d["analyze"])
    with_conclude = sum(1 for d in details if d["conclude"])

    return {
        "total": len(items),
        "figures": sum(1 for d in details if d["type"] == "figure"),
        "tables": sum(1 for d in details if d["type"] == "table"),
        "with_dac": with_dac,
        "with_describe": with_describe,
        "with_analyze": with_analyze,
        "with_conclude": with_conclude,
        "coverage_ratio": round(with_dac / len(items), 2) if items else 1.0,
        "passed": with_dac == len(items),
        "details": details,
    }


def write_report_md(result: Dict[str, Any], output_dir: Optional[Path] = None) -> str:
    """将图表叙事报告写入 Markdown 文件。"""
    if output_dir is None:
        output_dir = AUDITS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"figure_narrative_{ts}.md"

    lines = [
        "# 图表叙事覆盖率报告 (D-A-C)",
        "",
        f"- **图表总数**: {result['total']}",
        f"- **完整 D-A-C**: {result['with_dac']}",
        f"- **覆盖率**: {result['coverage_ratio']:.0%}",
        f"- **门禁**: {'PASS' if result['passed'] else 'FAIL'}",
        "",
        "## D-A-C 分项统计",
        "",
        f"| 维度 | 覆盖数 | 总数 | 覆盖率 |",
        f"|------|--------|------|--------|",
        f"| 描述 (D) | {result['with_describe']} | {result['total']} | {result['with_describe']/max(result['total'],1):.0%} |",
        f"| 分析 (A) | {result['with_analyze']} | {result['total']} | {result['with_analyze']/max(result['total'],1):.0%} |",
        f"| 结论 (C) | {result['with_conclude']} | {result['total']} | {result['with_conclude']/max(result['total'],1):.0%} |",
        "",
        "## 逐项详情",
        "",
    ]

    for d in result["details"]:
        status = "PASS" if d["has_dac"] else "FAIL"
        parts = []
        parts.append(f"D{'+' if d['describe'] else '-'}")
        parts.append(f"A{'+' if d['analyze'] else '-'}")
        parts.append(f"C{'+' if d['conclude'] else '-'}")
        lines.append(f"- [{status}] {d['id']} ({d['type']}): {' '.join(parts)}")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)


# ── CLI 入口 ──────────────────────────────────────────────────


def cmd_scan(args):
    """扫描论文中的图表引用"""
    text = Path(args.file).read_text(encoding="utf-8")
    items = scan_figures(text)
    print(json.dumps(items, ensure_ascii=False, indent=2))


def cmd_check_dac(args):
    """检查图表 D-A-C 叙事覆盖"""
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_figures(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_report(args):
    """生成图表叙事报告"""
    text = Path(args.file).read_text(encoding="utf-8")
    result = check_figures(text)
    output_path = write_report_md(result)
    print(f"[figure-narrative] 报告已生成: {output_path}")
    print(f"  图表: {result['total']}, D-A-C覆盖: {result['with_dac']}, 覆盖率: {result['coverage_ratio']:.0%}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="图表叙事引擎 D-A-C (M4)")
    sub = parser.add_subparsers(dest="cmd")

    p_scan = sub.add_parser("scan", help="扫描图表引用")
    p_scan.add_argument("--file", "-f", required=True, help="论文文件路径")

    p_dac = sub.add_parser("check-dac", help="检查 D-A-C 覆盖")
    p_dac.add_argument("--file", "-f", required=True, help="论文文件路径")

    p_rpt = sub.add_parser("report", help="生成报告")
    p_rpt.add_argument("--file", "-f", required=True, help="论文文件路径")

    args = parser.parse_args()
    dispatch = {"scan": cmd_scan, "check-dac": cmd_check_dac, "report": cmd_report}
    if args.cmd in dispatch:
        dispatch[args.cmd](args)
    else:
        parser.print_help()
