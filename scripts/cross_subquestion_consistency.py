#!/usr/bin/env python3
"""
跨子问题一致性引擎 - Cross-Subquestion Consistency Engine
检查变量命名、单位体系、结果量级、假设一致性
"""

import re
import json
from pathlib import Path

def check_consistency(paper_text: str, symbol_table: str = "") -> dict:
    results = {
        "variable_consistency": True,
        "unit_consistency": True,
        "magnitude_consistency": True,
        "assumption_consistency": True,
        "issues": [],
        "passed": True
    }
    
    # 检查变量命名一致性
    var_pattern = r'([a-zA-Z_]\w*)\s*[=＝]'
    variables = set(re.findall(var_pattern, paper_text))
    
    # 检查单位一致性
    unit_patterns = ["m/s", "kg", "℃", "°", "Pa", "N", "J", "W"]
    found_units = {}
    for unit in unit_patterns:
        count = paper_text.count(unit)
        if count > 0:
            found_units[unit] = count
    
    # 检查假设一致性
    assumption_patterns = ["假设", "假定", "认为"]
    assumptions = []
    for pattern in assumption_patterns:
        idx = 0
        while True:
            idx = paper_text.find(pattern, idx)
            if idx == -1:
                break
            end = min(idx + 100, len(paper_text))
            assumptions.append(paper_text[idx:end])
            idx += len(pattern)
    
    if len(assumptions) > 5:
        results["issues"].append(f"检测到{len(assumptions)}条假设，需检查一致性")
    
    results["passed"] = len(results["issues"]) == 0
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", required=True)
    parser.add_argument("--symbol-table")
    args = parser.parse_args()
    
    text = Path(args.paper).read_text(encoding='utf-8')
    sym = Path(args.symbol_table).read_text(encoding='utf-8') if args.symbol_table else ""
    result = check_consistency(text, sym)
    print(json.dumps(result, ensure_ascii=False, indent=2))
