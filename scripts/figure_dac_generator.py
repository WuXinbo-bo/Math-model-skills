#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure D-A-C Narrative Generator v1.0
为图表自动生成 D-A-C (Describe-Analyze-Conclude) 叙事模板
确保每个图表在论文中都有完整的三段论解读
"""
import sys
from pathlib import Path
import argparse
import json

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"


def generate_dac_template(figure_name: str, description: str = "", 
                         analysis: str = "", conclusion: str = "",
                         auto_hints: bool = True) -> Path:
    """
    为指定图表生成 D-A-C 叙事模板
    
    Args:
        figure_name: 图表文件名（含扩展名）
        description: 描述段落（可选）
        analysis: 分析段落（可选）
        conclusion: 结论段落（可选）
        auto_hints: 是否自动生成提示信息
    
    Returns:
        生成的 DAC 文件路径
    """
    stem = Path(figure_name).stem
    dac_file = FIGURES_DIR / f"{stem}_DAC.md"
    
    # 根据文件名自动推断提示
    hints = {}
    if auto_hints:
        hints = infer_hints_from_filename(stem)
    
    with open(dac_file, 'w', encoding='utf-8') as f:
        f.write(f"# {stem} 图表叙事模板 (D-A-C)\n\n")
        f.write(f"**图表文件**: `{figure_name}`\n\n")
        f.write(f"**生成时间**: {Path(FIGURES_DIR / figure_name).stat().st_mtime if (FIGURES_DIR / figure_name).exists() else 'N/A'}\n\n")
        f.write("---\n\n")
        
        # Describe
        f.write("## Describe（描述）\n\n")
        if description:
            f.write(f"{description}\n\n")
        else:
            f.write("**TODO**: 描述图表展示的内容\n\n")
            if hints.get('describe'):
                f.write(f"**提示**: {hints['describe']}\n\n")
            else:
                f.write("示例：\n")
                f.write("- 图X展示了...\n")
                f.write("- 横轴表示...，纵轴表示...\n")
                f.write("- 曲线/柱状/热力图中的颜色/形状代表...\n\n")
        
        # Analyze
        f.write("## Analyze（分析）\n\n")
        if analysis:
            f.write(f"{analysis}\n\n")
        else:
            f.write("**TODO**: 分析图表中的趋势、模式、关键点\n\n")
            if hints.get('analyze'):
                f.write(f"**提示**: {hints['analyze']}\n\n")
            else:
                f.write("示例：\n")
                f.write("- 从图中可见，参数X在区间[a,b]呈线性增长，增长率约为...\n")
                f.write("- 峰值出现在...，表明...\n")
                f.write("- 对比A和B方案，A在...指标上优于B约...%\n\n")
        
        # Conclude
        f.write("## Conclude（结论）\n\n")
        if conclusion:
            f.write(f"{conclusion}\n\n")
        else:
            f.write("**TODO**: 得出结论并说明对模型/决策的指导意义\n\n")
            if hints.get('conclude'):
                f.write(f"**提示**: {hints['conclude']}\n\n")
            else:
                f.write("示例：\n")
                f.write("- 因此，选择参数α=...可最大化...\n")
                f.write("- 该结果验证了模型假设...的合理性\n")
                f.write("- 瓶颈资源在...，应优先优化该环节\n\n")
        
        f.write("---\n\n")
        f.write("## 撰写指南\n\n")
        f.write("**D-A-C 三段论结构**:\n\n")
        f.write("1. **Describe（描述）**: 客观陈述图表内容，不加主观判断\n")
        f.write("   - 说明数据来源、坐标轴含义、图例说明\n")
        f.write("   - 描述图表类型（折线图/柱状图/热力图等）\n\n")
        
        f.write("2. **Analyze（分析）**: 深入分析数据特征和趋势\n")
        f.write("   - 识别峰值、拐点、瓶颈、异常值\n")
        f.write("   - 量化趋势（增长率、变化幅度、比例等）\n")
        f.write("   - 对比不同方案/参数的差异\n\n")
        
        f.write("3. **Conclude（结论）**: 提炼结论并关联模型意义\n")
        f.write("   - 结论必须基于前面的分析\n")
        f.write("   - 说明对模型优化/决策的指导作用\n")
        f.write("   - 验证模型假设或揭示模型局限性\n\n")
        
        f.write("**字数要求**:\n")
        f.write("- Standard 模式: 每段 80-120 字\n")
        f.write("- Championship 模式: 每段 150-200 字\n\n")
        
        f.write("**禁止事项**:\n")
        f.write("- ❌ 禁止使用模糊词: 大概/可能/也许/显著/明显/较好/差不多\n")
        f.write("- ❌ 禁止空洞描述: 如"从图中可以看出效果很好"\n")
        f.write("- ❌ 禁止缺少量化: 必须有具体数值或百分比\n")
    
    print(f"[OK] Generated: {dac_file.name}")
    return dac_file


def infer_hints_from_filename(stem: str) -> dict:
    """根据文件名推断提示信息"""
    hints = {}
    
    # 流程图
    if 'flow' in stem or 'workflow' in stem or 'roadmap' in stem:
        hints['describe'] = "描述流程的各个阶段/步骤，说明起点和终点"
        hints['analyze'] = "分析流程的关键路径、瓶颈环节、并行/串行关系"
        hints['conclude'] = "指出优化方向或流程合理性"
    
    # 收敛曲线
    elif 'convergence' in stem or 'iteration' in stem:
        hints['describe'] = "说明横轴（迭代次数）和纵轴（目标函数值/误差）"
        hints['analyze'] = "分析收敛速度、是否震荡、最终收敛值"
        hints['conclude'] = "验证算法有效性，说明收敛速度是否满足要求"
    
    # 对比图
    elif 'comparison' in stem or 'vs' in stem or 'compare' in stem:
        hints['describe'] = "说明对比的对象（方法/参数/方案）和评价指标"
        hints['analyze'] = "量化差异（A比B优X%），识别各方法优劣势"
        hints['conclude'] = "推荐最优方案或组合策略"
    
    # 灵敏度/鲁棒性
    elif 'sensitivity' in stem or 'robust' in stem or 'tornado' in stem:
        hints['describe'] = "说明变化的参数和观察的输出指标"
        hints['analyze'] = "识别最敏感参数（龙卷风图中最长的条），量化影响程度"
        hints['conclude'] = "指导参数调优优先级，说明模型稳定性"
    
    # 甘特图
    elif 'gantt' in stem or 'schedule' in stem:
        hints['describe'] = "说明任务/资源分配情况，时间跨度"
        hints['analyze'] = "识别空闲时段、资源冲突、关键路径"
        hints['conclude'] = "验证调度方案可行性，指出优化空间"
    
    # 热力图
    elif 'heatmap' in stem or 'correlation' in stem:
        hints['describe'] = "说明行列含义，颜色映射规则"
        hints['analyze'] = "识别高相关/低相关区域，发现模式"
        hints['conclude'] = "解释相关性对模型的影响"
    
    return hints


def batch_generate(figures_dir: Path = None, overwrite: bool = False):
    """批量为目录下所有图表生成 D-A-C 模板"""
    if figures_dir is None:
        figures_dir = FIGURES_DIR
    
    if not figures_dir.exists():
        print(f"[ERROR] Figures directory not found: {figures_dir}")
        return
    
    # 查找所有图表文件
    image_exts = {'.png', '.jpg', '.jpeg', '.svg', '.pdf'}
    figure_files = []
    for ext in image_exts:
        figure_files.extend(figures_dir.glob(f"*{ext}"))
    
    if not figure_files:
        print(f"[WARN] No figure files found in {figures_dir}")
        return
    
    print(f"\n[Batch] Found {len(figure_files)} figures in {figures_dir}")
    generated = 0
    skipped = 0
    
    for fig_file in sorted(figure_files):
        dac_file = figures_dir / f"{fig_file.stem}_DAC.md"
        
        if dac_file.exists() and not overwrite:
            print(f"[SKIP] {fig_file.name} (DAC already exists)")
            skipped += 1
            continue
        
        generate_dac_template(fig_file.name, auto_hints=True)
        generated += 1
    
    print(f"\n[Summary] Generated: {generated}, Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(
        description="Figure D-A-C Narrative Generator - 为图表生成叙事模板"
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # single 子命令
    single_parser = subparsers.add_parser("single", help="为单个图表生成 D-A-C 模板")
    single_parser.add_argument("figure", type=str, help="图表文件名")
    single_parser.add_argument("--describe", type=str, default="", help="描述段落")
    single_parser.add_argument("--analyze", type=str, default="", help="分析段落")
    single_parser.add_argument("--conclude", type=str, default="", help="结论段落")
    single_parser.add_argument("--no-hints", action="store_true", help="不生成自动提示")
    
    # batch 子命令
    batch_parser = subparsers.add_parser("batch", help="批量生成所有图表的 D-A-C 模板")
    batch_parser.add_argument("--dir", type=str, help="图表目录（默认: outputs/figures）")
    batch_parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 DAC 文件")
    
    # check 子命令
    check_parser = subparsers.add_parser("check", help="检查图表是否都有 D-A-C 模板")
    check_parser.add_argument("--dir", type=str, help="图表目录（默认: outputs/figures）")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "single":
        generate_dac_template(
            args.figure,
            description=args.describe,
            analysis=args.analyze,
            conclusion=args.conclude,
            auto_hints=not args.no_hints
        )
    
    elif args.command == "batch":
        figures_dir = Path(args.dir) if args.dir else FIGURES_DIR
        batch_generate(figures_dir, overwrite=args.overwrite)
    
    elif args.command == "check":
        figures_dir = Path(args.dir) if args.dir else FIGURES_DIR
        check_dac_coverage(figures_dir)


def check_dac_coverage(figures_dir: Path):
    """检查图表 D-A-C 覆盖率"""
    if not figures_dir.exists():
        print(f"[ERROR] Directory not found: {figures_dir}")
        return
    
    image_exts = {'.png', '.jpg', '.jpeg', '.svg', '.pdf'}
    figure_files = []
    for ext in image_exts:
        figure_files.extend(figures_dir.glob(f"*{ext}"))
    
    if not figure_files:
        print(f"[WARN] No figures found in {figures_dir}")
        return
    
    missing = []
    incomplete = []
    complete = []
    
    for fig_file in sorted(figure_files):
        dac_file = figures_dir / f"{fig_file.stem}_DAC.md"
        
        if not dac_file.exists():
            missing.append(fig_file.name)
        else:
            # 检查是否完整（没有 TODO）
            with open(dac_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '**TODO**' in content:
                    incomplete.append(fig_file.name)
                else:
                    complete.append(fig_file.name)
    
    total = len(figure_files)
    print(f"\n[D-A-C Coverage Report]")
    print(f"Total figures: {total}")
    print(f"✅ Complete: {len(complete)} ({len(complete)/total*100:.1f}%)")
    print(f"⚠️  Incomplete (has TODO): {len(incomplete)} ({len(incomplete)/total*100:.1f}%)")
    print(f"❌ Missing: {len(missing)} ({len(missing)/total*100:.1f}%)")
    
    if missing:
        print(f"\n[Missing D-A-C templates]:")
        for name in missing:
            print(f"  - {name}")
    
    if incomplete:
        print(f"\n[Incomplete D-A-C templates]:")
        for name in incomplete:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
