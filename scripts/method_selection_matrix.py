#!/usr/bin/env python3
"""
方法选择决策矩阵 - Method Selection Decision Engine
为每个子问题生成候选方法矩阵，确保选择有理有据
"""

import json
from pathlib import Path

def generate_decision_matrix(subquestion: str, candidates: list) -> dict:
    matrix = {
        "subquestion": subquestion,
        "methods": [],
        "selected": None,
        "backup": None
    }
    
    for c in candidates:
        matrix["methods"].append({
            "name": c.get("name", "unknown"),
            "applicable_score": c.get("applicable_score", 0),
            "suitability": c.get("suitability", "unknown"),
            "advantages": c.get("advantages", []),
            "disadvantages": c.get("disadvantages", []),
            "rejection_reason": c.get("rejection_reason", "")
        })
    
    sorted_methods = sorted(matrix["methods"], key=lambda x: x["applicable_score"], reverse=True)
    if sorted_methods:
        matrix["selected"] = sorted_methods[0]["name"]
    if len(sorted_methods) > 1:
        matrix["backup"] = sorted_methods[1]["name"]
    
    return matrix

def check_decision_matrix(matrix_text: str) -> dict:
    results = {
        "has_multiple_candidates": False,
        "has_comparison": False,
        "has_selection_reason": False,
        "passed": False,
        "issues": []
    }
    
    results["has_multiple_candidates"] = "候选" in matrix_text or "比较" in matrix_text
    results["has_comparison"] = "优势" in matrix_text or "劣势" in matrix_text or "对比" in matrix_text
    results["has_selection_reason"] = "选择" in matrix_text and ("因为" in matrix_text or "由于" in matrix_text or "理由" in matrix_text)
    
    results["passed"] = results["has_multiple_candidates"] and results["has_selection_reason"]
    
    if not results["has_multiple_candidates"]:
        results["issues"].append("缺少多个候选方法的对比")
    if not results["has_selection_reason"]:
        results["issues"].append("缺少选择理由说明")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-file", help="检查方法选择文档")
    args = parser.parse_args()
    
    if args.check_file:
        text = Path(args.check_file).read_text(encoding='utf-8')
        result = check_decision_matrix(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
