#!/usr/bin/env python3
"""
第一性原理推导链检查器 - Derivation Chain Checker
检查每个子问题的数学推导链完整性
"""

import re
import json
from pathlib import Path

def check_derivation_chain(model_text: str) -> dict:
    results = {
        "has_background": False,
        "has_governing_equation": False,
        "has_boundary_conditions": False,
        "has_derivation": False,
        "has_final_form": False,
        "chain_complete": False,
        "issues": []
    }
    
    bg_patterns = ["背景", "原理", "基础", "前提", "假设", "物理"]
    results["has_background"] = any(p in model_text for p in bg_patterns)
    
    eq_patterns = [r"式\(", r"方程", r"控制方程", r"objective", r"约束", r"目标函数"]
    results["has_governing_equation"] = any(re.search(p, model_text) for p in eq_patterns)
    
    bc_patterns = ["边界条件", "约束条件", "限制", "取值范围"]
    results["has_boundary_conditions"] = any(p in model_text for p in bc_patterns)
    
    deriv_patterns = ["推导", "求解", "化简", "展开", "联立"]
    results["has_derivation"] = any(p in model_text for p in deriv_patterns)
    
    final_patterns = ["最终模型", "最终形式", "得到", "综上", "因此"]
    results["has_final_form"] = any(p in model_text for p in final_patterns)
    
    checks = ["has_background", "has_governing_equation", "has_boundary_conditions", "has_derivation", "has_final_form"]
    passed = sum(1 for c in checks if results[c])
    results["chain_complete"] = passed >= 4
    
    if not results["has_background"]:
        results["issues"].append("缺少物理/实际背景描述")
    if not results["has_governing_equation"]:
        results["issues"].append("缺少控制方程/目标函数")
    if not results["has_derivation"]:
        results["issues"].append("缺少推导过程")
    if not results["has_final_form"]:
        results["issues"].append("缺少最终模型形式")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    
    text = Path(args.file).read_text(encoding='utf-8')
    result = check_derivation_chain(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
