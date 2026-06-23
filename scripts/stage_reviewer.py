#!/usr/bin/env python3
"""
stage_reviewer.py — 闭环评分引擎 (M4) v2.0

读取 config/rubric.yaml，基于关键词/模式匹配自动评分，
生成评分卡并检查门禁阈值。

v2.0 新增: 竞赛 100 分制映射（CUMCM / 51MCM / MCM_ICM）

纯文件工具，不调用 LLM API。

功能:
  score       — 对论文文档按 7 维度自动评分
  report      — 生成评分卡 Markdown 报告
  check       — 检查指定门禁阈值是否满足
  competition — 竞赛适配评分（100 分制 + 奖项预估）
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace_from_project
OUTPUTS_DIR = resolve_workspace_from_project(PROJECT_ROOT) / "outputs"
AUDITS_DIR = OUTPUTS_DIR / "audits"

# ── 评分维度关键词映射 ────────────────────────────────────────

DIMENSION_SIGNALS = {
    "problem_understanding": {
        "keywords": [
            r"(?:问题\s*[一二三四五六七八九十1-5]|子问题\s*[Qq]?\d)",
            r"(?:输入|输出).*(?:变量|数据|参数)",
            r"(?:约束条件|限制条件|边界条件)",
            r"(?:评价指标|目标函数|优化目标)",
            r"(?:问题重述|问题分析|问题拆解)",
        ],
        "section_hints": ["问题", "分析", "重述", "拆解"],
        "weight_evidence": 0.10,
    },
    "data_processing": {
        "keywords": [
            r"(?:数据清洗|数据预处理|数据处理)",
            r"(?:缺失值|异常值|离群值).*(?:处理|剔除|填充|说明)",
            r"(?:单位|表头).*(?:统一|转换|说明|标注)",
            r"(?:数据画像|数据分布|相关性分析|统计描述)",
            r"(?:箱线图|直方图|散点图|热力图)",
        ],
        "section_hints": ["数据", "预处理", "清洗"],
        "weight_evidence": 0.15,
    },
    "model_rationality": {
        "keywords": [
            r"(?:假设).*(?:合理|明确|建立|前提)",
            r"(?:推导|推演|推算).*(?:过程|步骤|链)",
            r"(?:备选|候选|对比).*(?:模型|方法|算法)",
            r"(?:选择理由|弃用理由|对比分析)",
            r"(?:第一性原理|物理意义|数学依据|理论基础)",
            r"(?:可解释|解释性|可理解)",
        ],
        "section_hints": ["模型", "假设", "推导", "建模"],
        "weight_evidence": 0.25,
    },
    "solving_reproducibility": {
        "keywords": [
            r"(?:代码|程序|算法).*(?:可运行|可执行|复现)",
            r"(?:误差|精度).*(?:MRE|RMSE|MAE|计算|评估)",
            r"(?:结果|数值).*(?:可追溯|与代码|一致|匹配)",
            r"(?:灵敏度|鲁棒性|稳健性|扰动|参数扫描|sweep)",
            r"(?:置信区间|标准差|误差分析)",
        ],
        "section_hints": ["求解", "结果", "验证", "代码"],
        "weight_evidence": 0.20,
    },
    "figure_table": {
        "keywords": [
            r"(?:图|Fig)\s*[\d.]+",
            r"(?:表|Table)\s*[\d.]+",
            r"(?:描述|分析|结论).*(?:图|表|结果)",
            r"(?:D-A-C|DAC|描述-分析-结论)",
            r"(?:标注|标题|坐标轴|图例)",
        ],
        "section_hints": ["图表", "结果", "可视化"],
        "weight_evidence": 0.10,
    },
    "paper_writing": {
        "keywords": [
            r"(?:摘要).*(?:问题|方法|结果|关键词)",
            r"(?:结构|目录|章节).*(?:完整|完整|规范)",
            r"(?:参考文献|引用|bibliography)",
            r"(?:符号表|符号说明|变量说明)",
            r"(?:假设|评价|讨论|结论)",
        ],
        "section_hints": ["摘要", "结论", "参考文献"],
        "weight_evidence": 0.15,
    },
    "adversarial_revision": {
        "keywords": [
            r"(?:审稿|质疑|反驳|rebuttal|revision)",
            r"(?:修订|修改|更正|改进)",
            r"(?:P0|P1|高优先级).*(?:关闭|解决|回应)",
        ],
        "section_hints": ["审稿", "修订", "回复"],
        "weight_evidence": 0.05,
    },
}


# ── 评分函数 ──────────────────────────────────────────────────


def load_rubric() -> Dict[str, Any]:
    """加载 rubric.yaml 评分标准。"""
    rubric_path = CONFIG_DIR / "rubric.yaml"
    if not rubric_path.exists():
        return {"dimensions": [], "gates": {}}
    with open(rubric_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def score_dimension(text: str, dim_id: str) -> Dict[str, Any]:
    """对单个维度评分。返回分数 0.0-1.0 + 匹配详情。"""
    signals = DIMENSION_SIGNALS.get(dim_id)
    if not signals:
        return {"score": 0.0, "matches": 0, "details": []}

    matches = []
    for pattern in signals["keywords"]:
        found = re.findall(pattern, text, re.IGNORECASE)
        if found:
            matches.extend(found[:3])

    section_hits = 0
    for hint in signals["section_hints"]:
        if hint in text:
            section_hits += 1

    keyword_score = min(len(matches) / 3.0, 1.0)
    section_score = min(section_hits / max(len(signals["section_hints"]), 1), 1.0)
    raw_score = 0.6 * keyword_score + 0.4 * section_score

    return {
        "score": round(raw_score, 2),
        "matches": len(matches),
        "match_samples": matches[:5],
        "section_hits": section_hits,
    }


def score_paper(text: str) -> Dict[str, Any]:
    """对论文进行 7 维度评分，返回加权总分和各维度详情。"""
    rubric = load_rubric()

    dimension_weights = {}
    for dim in rubric.get("dimensions", []):
        dimension_weights[dim["id"]] = dim.get("weight", 0.1)

    results = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for dim_id, signals in DIMENSION_SIGNALS.items():
        dim_result = score_dimension(text, dim_id)
        weight = dimension_weights.get(dim_id, signals["weight_evidence"])
        dim_result["weight"] = weight
        dim_result["weighted_score"] = round(dim_result["score"] * weight, 4)
        results[dim_id] = dim_result
        weighted_sum += dim_result["weighted_score"]
        total_weight += weight

    total_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

    return {
        "total_score": total_score,
        "dimensions": results,
        "timestamp": datetime.now().isoformat(),
    }


def score_competition(text: str, competition: str = "CUMCM") -> Dict[str, Any]:
    """竞赛适配评分：将 7 维度内部评分映射到竞赛 100 分制。

    Args:
        text: 论文文本
        competition: 竞赛类型（CUMCM / 51MCM / MCM_ICM）

    Returns:
        包含总分(0-100)、各官方维度得分、奖项预估的字典
    """
    rubric = load_rubric()
    mapping = rubric.get("competition_mapping", {}).get(competition)
    if not mapping:
        return {"error": f"竞赛类型 {competition} 未定义映射"}

    # 先计算内部 7 维度评分
    internal = score_paper(text)

    # 获取分数分配
    allocations = mapping.get("dim_allocations", {})

    # 计算竞赛总分（0-100）
    competition_total = 0.0
    dim_scores = {}
    for dim_id, alloc_points in allocations.items():
        dim_result = internal["dimensions"].get(dim_id, {})
        raw_score = dim_result.get("score", 0.0)
        earned = round(raw_score * alloc_points, 2)
        dim_scores[dim_id] = {
            "raw_score": raw_score,
            "allocation": alloc_points,
            "earned": earned,
        }
        competition_total += earned

    competition_total = round(min(competition_total, 100.0), 2)

    # 按官方维度聚合
    ownership = mapping.get("dimension_ownership", {})
    official_scores = {}
    for official_dim, dim_list in ownership.items():
        official_total = 0.0
        for dim_id, points in dim_list:
            earned = dim_scores.get(dim_id, {}).get("earned", 0.0)
            # 按比例分配到该官方维度
            alloc = allocations.get(dim_id, 1)
            ratio = points / alloc if alloc > 0 else 0
            official_total += round(earned * ratio, 2)
        official_scores[official_dim] = round(official_total, 2)

    # 奖项预估
    thresholds = mapping.get("award_thresholds", {})
    award_level = "未获奖"
    if competition_total >= thresholds.get("first_prize", 999):
        award_level = "一等奖"
    elif competition_total >= thresholds.get("second_prize", 999):
        award_level = "二等奖"
    elif competition_total >= thresholds.get("third_prize", 999):
        award_level = "三等奖"

    return {
        "competition": competition,
        "competition_name": mapping.get("name", competition),
        "total_score": competition_total,
        "award_estimate": award_level,
        "dimension_scores": dim_scores,
        "official_scores": official_scores,
        "internal_score": internal["total_score"],
        "thresholds": thresholds,
        "timestamp": datetime.now().isoformat(),
    }


def check_gate_threshold(text: str, gate_id: str) -> Dict[str, Any]:
    """检查指定门禁的评分阈值是否满足。"""
    rubric = load_rubric()
    gate = rubric.get("gates", {}).get(gate_id)
    if not gate:
        return {"error": f"门禁 {gate_id} 未定义"}

    scores = score_paper(text)
    total = scores["total_score"]
    min_score = gate.get("min_score", 0.8)
    mandatory = gate.get("mandatory_checks", [])

    passed = total >= min_score

    return {
        "gate_id": gate_id,
        "total_score": total,
        "min_score": min_score,
        "gate_passed": passed,
        "mandatory_checks": mandatory,
        "timestamp": datetime.now().isoformat(),
    }


# ── 报告生成 ──────────────────────────────────────────────────


def write_scorecard_md(scores: Dict[str, Any], output_dir: Optional[Path] = None) -> str:
    """将评分卡写入 Markdown 文件。"""
    if output_dir is None:
        output_dir = AUDITS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"scorecard_{ts}.md"

    dim_names = {
        "problem_understanding": "题意理解",
        "data_processing": "数据处理",
        "model_rationality": "模型合理性",
        "solving_reproducibility": "求解与复现",
        "figure_table": "图表表达",
        "paper_writing": "论文写作",
        "adversarial_revision": "对抗修订",
    }

    lines = [
        f"# 论文质量评分卡",
        f"",
        f"- **总分**: {scores['total_score']:.2f}",
        f"- **时间**: {scores['timestamp']}",
        f"",
        f"## 维度评分",
        f"",
        f"| 维度 | 权重 | 得分 | 加权分 | 匹配数 |",
        f"|------|------|------|--------|--------|",
    ]

    for dim_id, dim_result in scores["dimensions"].items():
        name = dim_names.get(dim_id, dim_id)
        lines.append(
            f"| {name} | {dim_result['weight']:.0%} | {dim_result['score']:.2f} "
            f"| {dim_result['weighted_score']:.4f} | {dim_result['matches']} |"
        )

    lines.append("")
    lines.append("## 门禁检查")
    lines.append("")

    rubric = load_rubric()
    for gate_id, gate_def in rubric.get("gates", {}).items():
        min_s = gate_def.get("min_score", 0)
        met = "✅" if scores["total_score"] >= min_s else "❌"
        lines.append(f"| {gate_id} | ≥{min_s:.2f} | {scores['total_score']:.2f} | {met} |")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)


def write_competition_scorecard(result: Dict[str, Any], output_dir: Optional[Path] = None) -> str:
    """将竞赛适配评分卡写入 Markdown 文件。"""
    if output_dir is None:
        output_dir = AUDITS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"competition_scorecard_{ts}.md"

    dim_names = {
        "problem_understanding": "题意理解",
        "data_processing": "数据处理",
        "model_rationality": "模型合理性",
        "solving_reproducibility": "求解与复现",
        "figure_table": "图表表达",
        "paper_writing": "论文写作",
        "adversarial_revision": "对抗修订",
    }

    official_names = {
        "model_quality": "模型质量",
        "problem_solving": "问题解决",
        "paper_standards": "论文规范",
        "verification": "验证与检验",
    }

    lines = [
        f"# 竞赛适配评分卡 — {result['competition_name']}",
        f"",
        f"- **竞赛总分**: {result['total_score']:.1f} / 100",
        f"- **奖项预估**: {result['award_estimate']}",
        f"- **内部质量分**: {result['internal_score']:.2f}",
        f"- **时间**: {result['timestamp']}",
        f"",
        f"## 官方维度得分",
        f"",
        f"| 官方维度 | 得分 |",
        f"|----------|------|",
    ]

    for dim_key, score in result["official_scores"].items():
        name = official_names.get(dim_key, dim_key)
        lines.append(f"| {name} | {score:.1f} |")

    lines.extend([
        f"",
        f"## 内部维度明细",
        f"",
        f"| 维度 | 原始分(0-1) | 分配分数 | 得分 |",
        f"|------|-------------|----------|------|",
    ])

    for dim_id, info in result["dimension_scores"].items():
        name = dim_names.get(dim_id, dim_id)
        lines.append(
            f"| {name} | {info['raw_score']:.2f} | {info['allocation']} | {info['earned']:.1f} |"
        )

    lines.extend([
        f"",
        f"## 奖项参考线",
        f"",
    ])
    for level, threshold in result.get("thresholds", {}).items():
        lines.append(f"- {level}: ≥ {threshold} 分")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)


# ── CLI 入口 ──────────────────────────────────────────────────


def cmd_score(args):
    """对论文进行自动评分"""
    paper_path = Path(args.file)
    if not paper_path.exists():
        print(f"[stage-reviewer] 文件不存在: {paper_path}")
        return

    text = paper_path.read_text(encoding="utf-8")
    scores = score_paper(text)
    print(json.dumps(scores, ensure_ascii=False, indent=2))


def cmd_report(args):
    """生成评分卡报告"""
    paper_path = Path(args.file)
    if not paper_path.exists():
        print(f"[stage-reviewer] 文件不存在: {paper_path}")
        return

    text = paper_path.read_text(encoding="utf-8")
    scores = score_paper(text)
    output_path = write_scorecard_md(scores)
    print(f"[stage-reviewer] 评分卡已生成: {output_path}")
    print(f"  总分: {scores['total_score']:.2f}")


def cmd_check(args):
    """检查指定门禁阈值"""
    paper_path = Path(args.file)
    if not paper_path.exists():
        print(f"[stage-reviewer] 文件不存在: {paper_path}")
        return

    text = paper_path.read_text(encoding="utf-8")
    result = check_gate_threshold(text, args.gate_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if "error" in result:
        return
    print(f"\n门禁 {args.gate_id}: {'PASS ✅' if result['gate_passed'] else 'FAIL ❌'}")


def cmd_competition(args):
    """竞赛适配评分（100 分制）"""
    paper_path = Path(args.file)
    if not paper_path.exists():
        print(f"[stage-reviewer] 文件不存在: {paper_path}")
        return

    text = paper_path.read_text(encoding="utf-8")
    result = score_competition(text, competition=args.competition)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.report:
        output_path = write_competition_scorecard(result)
        print(f"\n[stage-reviewer] 竞赛评分卡已生成: {output_path}")
        print(f"  总分: {result['total_score']:.1f} / 100")
        print(f"  奖项预估: {result['award_estimate']}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="闭环评分引擎 (M4) v2.0")
    sub = parser.add_subparsers(dest="cmd")

    p_score = sub.add_parser("score", help="自动评分（内部 7 维度 0-1）")
    p_score.add_argument("--file", "-f", required=True, help="论文文件路径")

    p_rpt = sub.add_parser("report", help="生成评分卡")
    p_rpt.add_argument("--file", "-f", required=True, help="论文文件路径")

    p_chk = sub.add_parser("check", help="检查门禁阈值")
    p_chk.add_argument("--file", "-f", required=True, help="论文文件路径")
    p_chk.add_argument("--gate-id", "-g", required=True, help="门禁 ID (e.g., G6_audit_layer_passed)")

    p_comp = sub.add_parser("competition", help="竞赛适配评分（100 分制 + 奖项预估）")
    p_comp.add_argument("--file", "-f", required=True, help="论文文件路径")
    p_comp.add_argument("--competition", "-c", default="CUMCM",
                        choices=["CUMCM", "51MCM", "MCM_ICM"],
                        help="竞赛类型 (默认: CUMCM)")
    p_comp.add_argument("--report", "-r", action="store_true", help="同时生成评分卡 Markdown")

    args = parser.parse_args()
    dispatch = {
        "score": cmd_score,
        "report": cmd_report,
        "check": cmd_check,
        "competition": cmd_competition,
    }
    if args.cmd in dispatch:
        dispatch[args.cmd](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
