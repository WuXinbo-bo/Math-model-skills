#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Assembly Checker v1.0
检查论文各章节是否严格从上游产物文件写作
确保论文内容与建模流程产出一致
"""
import sys
from pathlib import Path
import argparse
import json
import re

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# 章节-产物映射表（根据 paper-writing-rules.md）
SECTION_ARTIFACT_MAP = {
    "问题重述": {
        "required": ["inputs/problem_text.md"],
        "optional": ["outputs/problem_analysis/problem_parse.json"]
    },
    "问题分析": {
        "required": [
            "outputs/problem_analysis/analysis.md",
            "outputs/problem_analysis/subproblems.json",
            "outputs/problem_analysis/literature_review.md"
        ],
        "optional": ["outputs/problem_analysis/question_dependency.md"]
    },
    "模型假设": {
        "required": ["methods/model_assumptions.md"],
        "optional": []
    },
    "符号说明": {
        "required": ["methods/symbol_table.md"],
        "optional": []
    },
    "模型构建": {
        "required": [],
        "optional": []  # 动态生成（Q1/Q2/Q3）
    },
    "灵敏度分析": {
        "required": ["outputs/verification/sensitivity_analysis.md"],
        "optional": ["outputs/verification/tornado_diagram.png"]
    },
    "模型评价": {
        "required": [],
        "optional": ["outputs/evidence/model_evaluation.md"]
    },
    "参考文献": {
        "required": ["outputs/problem_analysis/literature_review.md"],
        "optional": []
    },
    "附录": {
        "required": [],
        "optional": []  # 代码文件动态检查
    }
}


def check_file_exists(file_path: Path) -> bool:
    """检查文件是否存在"""
    return file_path.exists() and file_path.stat().st_size > 0


def extract_section_content(paper_md: Path, section_name: str) -> str:
    """提取论文中指定章节的内容"""
    with open(paper_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找章节标题
    patterns = [
        rf"##\s+{re.escape(section_name)}\s*\n",
        rf"##\s+\d+\.?\s*{re.escape(section_name)}\s*\n",
        rf"###\s+{re.escape(section_name)}\s*\n"
    ]
    
    section_start = -1
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            section_start = match.end()
            break
    
    if section_start == -1:
        return ""
    
    # 查找下一个章节标题
    next_section = re.search(r"\n##\s+", content[section_start:])
    if next_section:
        section_end = section_start + next_section.start()
    else:
        section_end = len(content)
    
    return content[section_start:section_end]


def check_numbers_frozen(section_content: str, frozen_numbers_file: Path) -> list:
    """检查章节中的数值是否在 frozen_numbers.json 中"""
    if not frozen_numbers_file.exists():
        return ["frozen_numbers.json not found"]
    
    with open(frozen_numbers_file, 'r', encoding='utf-8') as f:
        frozen_data = json.load(f)
    
    # 提取所有冻结的数值
    frozen_numbers = set()
    for category, numbers in frozen_data.items():
        if isinstance(numbers, dict):
            frozen_numbers.update(str(v) for v in numbers.values())
        elif isinstance(numbers, list):
            frozen_numbers.update(str(n) for n in numbers)
    
    # 提取章节中的数值
    number_pattern = r'\b\d+\.?\d*\b'
    section_numbers = re.findall(number_pattern, section_content)
    
    # 过滤掉年份、章节号等
    significant_numbers = [
        n for n in section_numbers 
        if not (n.startswith('20') and len(n) == 4)  # 年份
        and not (len(n) <= 2 and float(n) < 20)  # 小章节号
    ]
    
    unfrozen = []
    for num in set(significant_numbers):
        if num not in frozen_numbers:
            unfrozen.append(num)
    
    return unfrozen[:10]  # 最多返回10个


def check_figure_references(section_content: str, figures_dir: Path) -> list:
    """检查章节中引用的图表是否存在"""
    if not figures_dir.exists():
        return []
    
    # 提取图表引用
    fig_patterns = [
        r'图\s*(\d+)',
        r'Figure\s+(\d+)',
        r'fig(\d+)',
        r'\[FIGURE:\s*([^\]]+)\]'
    ]
    
    referenced_figs = set()
    for pattern in fig_patterns:
        matches = re.findall(pattern, section_content, re.IGNORECASE)
        referenced_figs.update(matches)
    
    # 检查图表文件是否存在
    missing = []
    for fig_ref in referenced_figs:
        # 尝试多种文件名模式
        possible_names = [
            f"fig{fig_ref}.png",
            f"fig{fig_ref}*.png",
            f"figure{fig_ref}.png",
            fig_ref if '.' in fig_ref else None
        ]
        
        found = False
        for name in possible_names:
            if name and list(figures_dir.glob(name)):
                found = True
                break
        
        if not found:
            missing.append(fig_ref)
    
    return missing


def check_paper_artifacts(paper_md: Path, mode: str = "standard") -> dict:
    """
    检查论文各章节是否引用了对应产物
    
    Args:
        paper_md: 论文 Markdown 文件路径
        mode: 检查模式 (fast/standard/championship)
    
    Returns:
        检查结果字典
    """
    if not paper_md.exists():
        return {"error": f"Paper file not found: {paper_md}"}
    
    results = {
        "paper": str(paper_md),
        "mode": mode,
        "sections": {},
        "summary": {
            "total": 0,
            "passed": 0,
            "warnings": 0,
            "errors": 0
        }
    }
    
    with open(paper_md, 'r', encoding='utf-8') as f:
        paper_content = f.read()
    
    # 检查每个章节
    for section_name, artifacts in SECTION_ARTIFACT_MAP.items():
        results["sections"][section_name] = {
            "found": False,
            "issues": []
        }
        results["summary"]["total"] += 1
        
        # 检查章节是否存在
        section_content = extract_section_content(paper_md, section_name)
        if not section_content:
            results["sections"][section_name]["issues"].append(
                f"章节缺失或为空"
            )
            results["summary"]["errors"] += 1
            continue
        
        results["sections"][section_name]["found"] = True
        
        # 检查必需产物文件
        for artifact in artifacts["required"]:
            artifact_path = PROJECT_ROOT / artifact
            if not check_file_exists(artifact_path):
                results["sections"][section_name]["issues"].append(
                    f"缺失必需产物: {artifact}"
                )
                results["summary"]["errors"] += 1
        
        # 检查章节字数（Championship 模式）
        if mode == "championship":
            char_count = len(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]', section_content))
            min_chars = 300  # 每章节最低字数
            if char_count < min_chars:
                results["sections"][section_name]["issues"].append(
                    f"字数不足: {char_count} < {min_chars}"
                )
                results["summary"]["warnings"] += 1
        
        # 检查数值冻结（Standard/Championship）
        if mode in ["standard", "championship"]:
            frozen_file = OUTPUTS_DIR / "frozen_numbers.json"
            if section_name in ["模型构建", "灵敏度分析"]:
                unfrozen = check_numbers_frozen(section_content, frozen_file)
                if unfrozen:
                    results["sections"][section_name]["issues"].append(
                        f"发现未冻结数值: {', '.join(unfrozen[:5])}"
                    )
                    results["summary"]["warnings"] += 1
        
        # 检查图表引用
        figures_dir = OUTPUTS_DIR / "figures"
        missing_figs = check_figure_references(section_content, figures_dir)
        if missing_figs:
            results["sections"][section_name]["issues"].append(
                f"引用的图表不存在: {', '.join(missing_figs)}"
            )
            results["summary"]["warnings"] += 1
        
        # 统计通过/失败
        if not results["sections"][section_name]["issues"]:
            results["summary"]["passed"] += 1
    
    return results


def print_report(results: dict):
    """打印检查报告"""
    print("\n" + "="*70)
    print(f"  Paper Assembly Check Report - {results['mode'].upper()} Mode")
    print("="*70)
    print(f"Paper: {results['paper']}")
    print(f"\nSummary:")
    print(f"  Total sections: {results['summary']['total']}")
    print(f"  ✅ Passed: {results['summary']['passed']}")
    print(f"  ⚠️  Warnings: {results['summary']['warnings']}")
    print(f"  ❌ Errors: {results['summary']['errors']}")
    
    # 详细章节报告
    print(f"\n{'Section':<20} {'Status':<10} {'Issues'}")
    print("-"*70)
    
    for section, info in results["sections"].items():
        if not info["found"]:
            status = "❌ MISSING"
        elif info["issues"]:
            status = "⚠️  WARNING"
        else:
            status = "✅ PASS"
        
        print(f"{section:<20} {status:<10}", end="")
        if info["issues"]:
            print(f" {len(info['issues'])} issue(s)")
            for issue in info["issues"]:
                print(f"{'':30} - {issue}")
        else:
            print()
    
    print("="*70)
    
    # 总体判断
    if results["summary"]["errors"] > 0:
        print("\n❌ FAILED: Paper has critical errors. Fix before proceeding.")
        return False
    elif results["summary"]["warnings"] > 0:
        print(f"\n⚠️  WARNING: Paper has {results['summary']['warnings']} warnings. Review recommended.")
        return True
    else:
        print("\n✅ PASSED: Paper assembly check successful.")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Paper Assembly Checker - 检查论文产物映射"
    )
    parser.add_argument("paper", type=str, help="论文 Markdown 文件路径")
    parser.add_argument("--mode", type=str, default="standard",
                       choices=["fast", "standard", "championship"],
                       help="检查模式")
    parser.add_argument("--json", type=str, help="输出 JSON 报告到文件")
    
    args = parser.parse_args()
    
    paper_path = Path(args.paper)
    if not paper_path.is_absolute():
        paper_path = PROJECT_ROOT / paper_path
    
    # 执行检查
    results = check_paper_artifacts(paper_path, mode=args.mode)
    
    # 打印报告
    success = print_report(results)
    
    # 输出 JSON（可选）
    if args.json:
        json_path = Path(args.json)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[JSON] Report saved to: {json_path}")
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
