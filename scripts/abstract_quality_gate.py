#!/usr/bin/env python3
"""
摘要质量引擎 - Abstract Quality Gate
检查摘要是否包含4要素：模型、结果、公式、标注
"""

import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def check_abstract(abstract_text: str, competition_type: str = "CUMCM") -> dict:
    results = {
        "has_model": False,
        "has_result": False,
        "has_formula": False,
        "has_reference": False,
        "word_count": 0,
        "issues": [],
        "passed": False
    }
    
    # 1. 模型描述检查
    model_patterns = ["模型", "方法", "算法", "构建了", "建立了", "提出了", "构造了"]
    results["has_model"] = any(p in abstract_text for p in model_patterns)
    if not results["has_model"]:
        results["issues"].append("摘要缺少模型/方法描述")
    
    # 2. 量化结果检查
    number_pattern = r'\d+\.?\d*[%℃mL°]?'
    numbers = re.findall(number_pattern, abstract_text)
    results["has_result"] = len(numbers) >= 2
    if not results["has_result"]:
        results["issues"].append("摘要缺少量化结果（需要至少2个具体数值）")
    
    # 3. 公式检查
    formula_pattern = r'[\$\\].*?[\$\\]|式\(\d+\)|公式|Algorithm|Model'
    results["has_formula"] = bool(re.search(formula_pattern, abstract_text))
    if not results["has_formula"]:
        results["issues"].append("摘要缺少公式/模型标注")
    
    # 4. 引用标注检查
    ref_pattern = r'详见|见[表图P]|如[表图]|Fig\.|Table|P\d+'
    results["has_reference"] = bool(re.search(ref_pattern, abstract_text))
    if not results["has_reference"]:
        results["issues"].append("摘要缺少图表/页码引用标注")
    
    # 5. 字数检查
    results["word_count"] = len(abstract_text)
    if competition_type in ["CUMCM", "51MCM"]:
        if results["word_count"] < 400:
            results["issues"].append(f"摘要字数不足（当前{results['word_count']}字，建议400-550字）")
        elif results["word_count"] > 550:
            results["issues"].append(f"摘要字数过多（当前{results['word_count']}字，建议400-550字）")
    
    results["passed"] = results["has_model"] and results["has_result"]
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="摘要文件路径")
    parser.add_argument("--competition", default="CUMCM")
    args = parser.parse_args()
    
    text = Path(args.file).read_text(encoding='utf-8')
    result = check_abstract(text, args.competition)
    print(json.dumps(result, ensure_ascii=False, indent=2))
