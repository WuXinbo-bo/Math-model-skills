#!/usr/bin/env python3
"""
学术表达增强器 - Academic Expression Checker
检测口语化表达，提供学术句式替换建议
"""

import re
import json
from pathlib import Path

FILLER_PHRASES = ["综上所述", "值得注意的是", "总而言之", "不言而喻", "众所周知"]
COLLOQUIAL_PATTERNS = ["我觉得", "应该是", "大概", "差不多", "基本上"]

def check_expression(text: str) -> dict:
    results = {"fillers": [], "colloquial": [], "passed": True, "issues": []}
    
    for phrase in FILLER_PHRASES:
        if phrase in text:
            results["fillers"].append(phrase)
    
    for pattern in COLLOQUIAL_PATTERNS:
        if pattern in text:
            results["colloquial"].append(pattern)
    
    if results["fillers"]:
        results["issues"].append(f"检测到{len(results['fillers'])}个低信息量填充词")
    if results["colloquial"]:
        results["issues"].append(f"检测到{len(results['colloquial'])}个口语化表达")
    
    results["passed"] = len(results["fillers"]) == 0 and len(results["colloquial"]) == 0
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    
    text = Path(args.file).read_text(encoding='utf-8')
    result = check_expression(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
