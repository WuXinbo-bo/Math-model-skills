from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gate_contracts import (  # noqa: E402
    abstract_structure_issues,
    matched_model_families,
    model_definition_contract_issues,
    model_identity_issues,
    result_model_identity_issues,
)


VALID_REPORT = """# 建模报告

## 问题一
模型定义 Q1 | 正式名称: 考虑维护约束的机组承诺混合整数线性规划模型 | 标准模型族: 混合整数线性规划 | 求解算法: HiGHS分支定界算法
模型结构 Q1 | 决策变量/状态量: 机组启停、启动和出力变量 | 目标函数/统计关系: 最小化运行、启动和维护总成本 | 核心约束/方程: 供需平衡、容量、爬坡和最小开停机约束 | 定制机制: 逐台维护窗口与滚动预测
"""


def workspace(root: Path, report: str) -> Path:
    root.mkdir(parents=True)
    (root / "建模报告.md").write_text(report, encoding="utf-8")
    state_dir = root / "状态"
    state_dir.mkdir()
    (state_dir / "工作流状态.json").write_text(
        json.dumps({"competition": "cumcm"}, ensure_ascii=False), encoding="utf-8"
    )
    return root


def main() -> int:
    base = ROOT.parent / "runtime_model_identity_smoke"
    if base.exists():
        shutil.rmtree(base)

    good = workspace(base / "good", VALID_REPORT)
    assert not model_definition_contract_issues(good, 1)
    (good / "图表").mkdir()
    identity_payload = {
        "model_identity": {
            "Q1": {
                "academic_name": "考虑维护约束的机组承诺混合整数线性规划模型",
                "canonical_model_family": "混合整数线性规划",
                "solver_algorithm": "HiGHS分支定界算法",
            }
        }
    }
    (good / "图表" / "全部结果.json").write_text(
        json.dumps(identity_payload, ensure_ascii=False), encoding="utf-8"
    )
    assert not result_model_identity_issues(good, 1)
    identity_payload["model_identity"]["Q1"]["canonical_model_family"] = "优化模型"
    (good / "图表" / "全部结果.json").write_text(
        json.dumps(identity_payload, ensure_ascii=False), encoding="utf-8"
    )
    assert result_model_identity_issues(good, 1)

    vague_report = VALID_REPORT.replace(
        "考虑维护约束的机组承诺混合整数线性规划模型 | 标准模型族: 混合整数线性规划",
        "带启动状态的聚合确定性机组承诺模型 | 标准模型族: 优化模型",
    )
    vague = workspace(base / "vague", vague_report)
    vague_issues = model_definition_contract_issues(vague, 1)
    assert any("canonical model family is vague" in item for item in vague_issues), vague_issues

    algorithm_report = VALID_REPORT.replace(
        "考虑维护约束的机组承诺混合整数线性规划模型 | 标准模型族: 混合整数线性规划",
        "HiGHS分支定界模型 | 标准模型族: 决策模型",
    )
    algorithm = workspace(base / "algorithm", algorithm_report)
    algorithm_issues = model_definition_contract_issues(algorithm, 1)
    assert any("does not expose a canonical" in item for item in algorithm_issues), algorithm_issues

    missing_structure = workspace(
        base / "missing_structure", VALID_REPORT.split("模型结构 Q1", 1)[0]
    )
    structure_issues = model_definition_contract_issues(missing_structure, 1)
    assert any("model structure card is incomplete" in item for item in structure_issues), structure_issues

    english_issues = model_identity_issues(
        "Maintenance-Constrained Unit Commitment Mixed-Integer Linear Programming Model",
        "Mixed-Integer Linear Programming",
        "HiGHS branch-and-bound",
        True,
    )
    assert not english_issues, english_issues
    assert "linear_programming" not in matched_model_families("非线性规划")
    assert "linear_programming" not in matched_model_families("混合整数线性规划")
    assert "integer_programming" not in matched_model_families("混合整数规划")

    good_abstract = r"""\section*{摘要}
本文针对逐小时电力调度问题，建立考虑维护约束的机组承诺混合整数线性规划模型完成计划优化。

针对问题1，建立考虑维护约束的机组承诺混合整数线性规划模型，标准模型族为混合整数线性规划，采用HiGHS分支定界算法求解，得到最优成本100，并通过约束回代验证结果稳健性。

模型结构清晰，具有可解释、可复核和可推广的优点。
\textbf{关键词：} 混合整数线性规划；HiGHS分支定界算法
"""
    assert not abstract_structure_issues(good, good_abstract, 1)
    latex_keywords = good_abstract.replace(
        r"\textbf{关键词：} 混合整数线性规划；HiGHS分支定界算法",
        r"\keywords{混合整数线性规划；HiGHS分支定界算法}",
    )
    assert not abstract_structure_issues(good, latex_keywords, 1)
    kwabstract = good_abstract.replace(
        r"\section*{摘要}",
        r"\begin{kwabstract}{混合整数线性规划；HiGHS分支定界算法}",
    ).replace(
        r"\textbf{关键词：} 混合整数线性规划；HiGHS分支定界算法",
        r"\end{kwabstract}",
    )
    assert not abstract_structure_issues(good, kwabstract, 1)
    bad_keywords = good_abstract.replace(
        "混合整数线性规划；HiGHS分支定界算法", "聚合承诺模型；调度决策"
    )
    keyword_issues = abstract_structure_issues(good, bad_keywords, 1)
    assert any("keywords are not canonical" in item for item in keyword_issues), keyword_issues

    print(
        json.dumps(
            {
                "canonical_identity": "pass",
                "result_identity_alignment": "pass",
                "vague_business_name": "rejected",
                "algorithm_as_model": "rejected",
                "missing_structure": "rejected",
                "english_identity": "pass",
                "family_overlap_guard": "pass",
                "canonical_keywords": "pass",
                "latex_keyword_commands": "pass",
                "vague_keywords": "rejected",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    shutil.rmtree(base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
