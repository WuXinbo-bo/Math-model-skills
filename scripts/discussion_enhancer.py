#!/usr/bin/env python3
"""
多维度结果讨论引擎 - Discussion Enhancer
为每个子问题生成7维度讨论框架模板
"""

import json
from pathlib import Path

DISCUSSION_DIMENSIONS = [
    {"name": "敏感性/鲁棒性", "weight": 0.20, "description": "参数扰动影响分析"},
    {"name": "物理/领域意义", "weight": 0.20, "description": "结果是否符合物理直觉"},
    {"name": "基线对比", "weight": 0.15, "description": "与简单方法对比"},
    {"name": "跨子问题一致性", "weight": 0.15, "description": "Q1-Q3结果是否矛盾"},
    {"name": "不确定性/置信区间", "weight": 0.10, "description": "误差范围和置信度"},
    {"name": "实际可操作性", "weight": 0.10, "description": "能否落地应用"},
    {"name": "创新性论证", "weight": 0.10, "description": "为什么比现有方法好"}
]

def generate_discussion_template(subquestion: str) -> str:
    template = f"# 问题{subquestion} 多维度结果讨论\n\n"
    for dim in DISCUSSION_DIMENSIONS:
        template += f"## {dim['name']} (权重: {dim['weight']*100:.0f}%)\n"
        template += f"{dim['description']}\n\n[待填写]\n\n"
    return template

def check_discussion(text: str) -> dict:
    results = {"covered_dimensions": [], "missing_dimensions": [], "passed": False}
    
    for dim in DISCUSSION_DIMENSIONS:
        if dim["name"] in text:
            results["covered_dimensions"].append(dim["name"])
        else:
            results["missing_dimensions"].append(dim["name"])
    
    results["passed"] = len(results["covered_dimensions"]) >= 4
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subquestion", default="Q1")
    parser.add_argument("--check-file")
    args = parser.parse_args()
    
    if args.check_file:
        text = Path(args.check_file).read_text(encoding='utf-8')
        print(json.dumps(check_discussion(text), ensure_ascii=False, indent=2))
    else:
        print(generate_discussion_template(args.subquestion))
