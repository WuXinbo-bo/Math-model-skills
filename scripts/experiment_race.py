#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Experiment Race - 实验赛马引擎
==============================

自动在同一口径下比较候选模型，生成排行榜，裁决主/备选模型。

功能：
1. 创建 experiment_race_plan.md：赛马计划
2. 统一口径比较：相同数据集、相同评估指标
3. 生成 model_leaderboard.csv：排行榜
4. 裁决逻辑：主模型选择、备选模型标记

评分维度：
- 题意匹配 (20%): 模型与问题目标的契合度
- 验证表现 (20%): 在验证集上的表现
- 稳健性 (15%): 对参数扰动的敏感度
- 可解释性 (15%): 模型结果的可解释程度
- 论文表达价值 (15%): 对论文质量的贡献
- 实现复杂度 (10%): 代码实现难度
- 风险可控性 (5%): 失败风险

Usage:
  python experiment_race.py init --subquestion Q1 --models "model_a,model_b,model_c"
  python experiment_race.py run --subquestion Q1
  python experiment_race.py check --subquestion Q1
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("outputs")
RACE_DIR = WORKSPACE / "experiments" / "race"


def get_race_plan_path(subquestion: str) -> Path:
    """获取赛马计划路径"""
    return RACE_DIR / subquestion / "experiment_race_plan.md"


def get_leaderboard_path(subquestion: str) -> Path:
    """获取排行榜路径"""
    return RACE_DIR / subquestion / "model_leaderboard.csv"


def get_race_results_path(subquestion: str) -> Path:
    """获取赛马详细结果路径"""
    return RACE_DIR / subquestion / "race_results.json"


def ensure_dirs(subquestion: str):
    """确保目录存在"""
    get_race_plan_path(subquestion).parent.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# 评分权重
# ═══════════════════════════════════════════════════════════════

EVAL_WEIGHTS = {
    "problem_alignment":          0.20,
    "validation_performance":     0.20,
    "robustness":                 0.15,
    "interpretability":           0.15,
    "paper_value":                0.15,
    "implementation_complexity":  0.10,
    "risk_control":               0.05,
}

EVAL_LABELS = {
    "problem_alignment":          "题意匹配",
    "validation_performance":     "验证表现",
    "robustness":                 "稳健性",
    "interpretability":           "可解释性",
    "paper_value":                "论文表达价值",
    "implementation_complexity":  "实现复杂度",
    "risk_control":               "风险可控性",
}


# ═══════════════════════════════════════════════════════════════
# 赛马计划
# ═══════════════════════════════════════════════════════════════

def init_race_plan(subquestion, models):
    """
    初始化赛马计划

    Args:
        subquestion: 子问题编号
        models: 候选模型列表

    Returns:
        赛马计划字典
    """
    ensure_dirs(subquestion)

    plan = {
        "subquestion": subquestion,
        "created_at": datetime.now().isoformat(),
        "models": models,
        "evaluation_dimensions": EVAL_WEIGHTS,
        "trigger_conditions": [
            "模型路线前两名分差 <10%",
            "主模型有明显过拟合风险",
            "缺少对照实验",
        ],
        "status": "planned",
    }

    model_rows = "\n".join(
        f"| {i+1} | {m} | pending |" for i, m in enumerate(models)
    )
    dim_rows = "\n".join(
        f"| {EVAL_LABELS[k]} | {v*100:.0f}% | {EVAL_LABELS[k]} |"
        for k, v in EVAL_WEIGHTS.items()
    )
    trigger_lines = "\n".join(f"- {c}" for c in plan["trigger_conditions"])

    template = f"""# 实验赛马计划 (Experiment Race Plan)

## 基本信息

- **子问题**: {subquestion}
- **创建时间**: {plan['created_at']}
- **状态**: {plan['status']}

## 候选模型

| 序号 | 模型名称 | 状态 |
|------|----------|------|
{model_rows}

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
{dim_rows}

## 触发条件

{trigger_lines}

## 赛马流程

1. **数据准备**: 使用相同的数据集划分（训练集/验证集/测试集）
2. **模型训练**: 在相同条件下训练所有候选模型
3. **指标计算**: 计算所有评价指标
4. **评分汇总**: 按权重计算综合得分
5. **裁决决策**: 选择主模型和备选模型

## 执行要求

- 所有模型必须使用相同的随机种子
- 必须记录每个模型的训练时间
- 必须记录每个模型的内存占用
- 必须记录每个模型的收敛情况

## 结果文件

- 排行榜: `model_leaderboard.csv`
- 详细结果: `race_results.json`
"""

    plan_path = get_race_plan_path(subquestion)
    plan_path.write_text(template, encoding="utf-8")

    return plan


# ═══════════════════════════════════════════════════════════════
# 赛马执行
# ═══════════════════════════════════════════════════════════════

def run_race(subquestion, scores):
    """
    执行赛马比较

    Args:
        subquestion: 子问题编号
        scores: 各模型在各维度的得分 {model_name: {dimension: score}}

    Returns:
        赛马结果
    """
    ensure_dirs(subquestion)

    # 计算综合得分
    results = []
    for model_name, dim_scores in scores.items():
        total = sum(
            dim_scores.get(dim, 0) * w for dim, w in EVAL_WEIGHTS.items()
        )
        results.append({
            "model": model_name,
            "scores": dim_scores,
            "total_score": round(total, 4),
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)

    # 写入排行榜 CSV
    lb_path = get_leaderboard_path(subquestion)
    with open(lb_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["Rank", "Model", "Total_Score"] + list(EVAL_WEIGHTS.keys())
        writer.writerow(header)
        for i, r in enumerate(results, 1):
            row = [i, r["model"], f"{r['total_score']:.4f}"]
            for dim in EVAL_WEIGHTS:
                row.append(f"{r['scores'].get(dim, 0):.4f}")
            writer.writerow(row)

    # 裁决
    primary = results[0]["model"]
    backups = [r["model"] for r in results[1:3]]

    if len(results) >= 2 and results[1]["total_score"] > 0:
        gap_pct = (
            (results[0]["total_score"] - results[1]["total_score"])
            / results[1]["total_score"]
            * 100
        )
    else:
        gap_pct = 100.0

    race_result = {
        "subquestion": subquestion,
        "completed_at": datetime.now().isoformat(),
        "rankings": results,
        "primary_model": primary,
        "backup_models": backups,
        "score_gap_percentage": round(gap_pct, 2),
        "recommendation": (
            "primary_selected" if gap_pct >= 10 else "close_competition"
        ),
    }

    results_path = get_race_results_path(subquestion)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(race_result, f, ensure_ascii=False, indent=2)

    return race_result


# ═══════════════════════════════════════════════════════════════
# G2.5 门控
# ═══════════════════════════════════════════════════════════════

def check_experiment_race(subquestion):
    """
    G2.5 门控检查：实验赛马

    Returns:
        (passed, message)
    """
    plan_path = get_race_plan_path(subquestion)
    lb_path = get_leaderboard_path(subquestion)
    results_path = get_race_results_path(subquestion)

    errors = []
    if not plan_path.exists():
        errors.append(f"赛马计划不存在: {plan_path}")
    if not lb_path.exists():
        errors.append(f"排行榜不存在: {lb_path}")
    if not results_path.exists():
        errors.append(f"赛马结果不存在: {results_path}")

    if errors:
        return False, (
            f"G2.5 实验赛马未通过\n"
            f"原因: 缺少必要文件\n"
            + "\n".join(f"  - {e}" for e in errors)
            + f"\n修复: 请运行 'python experiment_race.py run --subquestion {subquestion}'"
        )

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    primary = data.get("primary_model", "unknown")
    backups = data.get("backup_models", [])
    gap = data.get("score_gap_percentage", 0)

    return True, (
        f"G2.5 实验赛马通过\n"
        f"- 主模型: {primary}\n"
        f"- 备选模型: {', '.join(backups)}\n"
        f"- 分差: {gap:.1f}%\n"
        f"- 排行榜: {lb_path}"
    )


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Experiment Race - 实验赛马引擎")
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_init = sub.add_parser("init", help="初始化赛马计划")
    p_init.add_argument("--subquestion", required=True)
    p_init.add_argument("--models", required=True, help="候选模型列表，逗号分隔")

    p_run = sub.add_parser("run", help="执行赛马比较")
    p_run.add_argument("--subquestion", required=True)
    p_run.add_argument("--scores-file", help="评分文件路径 (JSON)")

    p_check = sub.add_parser("check", help="G2.5 门控检查")
    p_check.add_argument("--subquestion", required=True)

    args = parser.parse_args()

    if args.command == "init":
        models = [m.strip() for m in args.models.split(",")]
        init_race_plan(args.subquestion, models)
        print(f"✅ 赛马计划已初始化: {get_race_plan_path(args.subquestion)}")
        print(f"候选模型: {', '.join(models)}")

    elif args.command == "run":
        if args.scores_file:
            with open(args.scores_file, "r", encoding="utf-8") as f:
                scores = json.load(f)
        else:
            scores = {}
            print("⚠️  未提供 --scores-file，使用空评分")

        result = run_race(args.subquestion, scores)
        print(f"✅ 赛马完成")
        print(f"主模型: {result['primary_model']}")
        print(f"备选模型: {', '.join(result['backup_models'])}")
        print(f"分差: {result['score_gap_percentage']:.1f}%")
        print(f"排行榜: {get_leaderboard_path(args.subquestion)}")

    elif args.command == "check":
        passed, msg = check_experiment_race(args.subquestion)
        print(msg)
        sys.exit(0 if passed else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()