#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagram Generator v1.0
自动生成论文必备的架构图、流程图、技术路线图
支持: Mermaid → PNG、Graphviz DOT → PNG
"""
import sys
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"

# 确保输出目录存在
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def check_dependencies():
    """检查必需的依赖工具"""
    missing = []
    
    # 检查 mmdc (mermaid-cli)
    try:
        result = subprocess.run(["mmdc", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            missing.append("mmdc (mermaid-cli)")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        missing.append("mmdc (install: npm install -g @mermaid-js/mermaid-cli)")
    
    # 检查 dot (graphviz) - 可选
    try:
        subprocess.run(["dot", "-V"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[WARN] Graphviz not found (optional). Install: https://graphviz.org/download/")
    
    if missing:
        print(f"[ERROR] Missing dependencies: {', '.join(missing)}")
        print("\nInstall instructions:")
        print("  npm install -g @mermaid-js/mermaid-cli")
        print("  Or use Docker: docker pull minlag/mermaid-cli")
        sys.exit(1)


def render_mermaid(mermaid_code: str, output_path: Path, theme: str = "default") -> bool:
    """
    渲染 Mermaid 图表为 PNG
    
    Args:
        mermaid_code: Mermaid 语法代码
        output_path: 输出 PNG 路径
        theme: 主题 (default/forest/dark/neutral)
    
    Returns:
        是否成功
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
        f.write(mermaid_code)
        temp_mmd = f.name
    
    try:
        cmd = [
            "mmdc",
            "-i", temp_mmd,
            "-o", str(output_path),
            "-t", theme,
            "-b", "white",
            "-w", "1200",
            "-H", "800"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and output_path.exists():
            print(f"[OK] Generated: {output_path.name}")
            return True
        else:
            print(f"[ERROR] Mermaid render failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("[ERROR] Mermaid render timeout (>30s)")
        return False
    finally:
        if os.path.exists(temp_mmd):
            os.remove(temp_mmd)


def generate_technical_roadmap(stages: list, output_name: str = "fig1_technical_roadmap.png") -> Path:
    """
    生成技术路线图（论文 Figure 1）
    
    Args:
        stages: 阶段列表，如 ["S0", "S1", "S3", "S5", "S6", "S8", "S9", "S10"]
        output_name: 输出文件名
    
    Returns:
        输出文件路径
    """
    stage_labels = {
        "S0": "问题接收",
        "S1": "问题分析",
        "S2": "数据预处理",
        "S3": "模型选择",
        "S4": "实验设计",
        "S5": "建模求解",
        "S5.5": "统一内核",
        "S6": "鲁棒性检验",
        "S7": "评价指标",
        "S7.5": "内核归纳",
        "S8": "论文撰写",
        "S9": "红队审查",
        "S10": "论文封装"
    }
    
    # 生成 Mermaid flowchart
    mermaid = ["graph TD"]
    mermaid.append("    classDef stageClass fill:#e1f5ff,stroke:#0078d4,stroke-width:2px")
    mermaid.append("    classDef keyClass fill:#fff4e6,stroke:#f59e0b,stroke-width:3px")
    
    for i, stage in enumerate(stages):
        label = stage_labels.get(stage, stage)
        node_id = stage.replace(".", "_")
        mermaid.append(f'    {node_id}["{stage}<br/>{label}"]')
        
        # 关键阶段高亮
        if stage in ["S1", "S3", "S5", "S8"]:
            mermaid.append(f"    class {node_id} keyClass")
        else:
            mermaid.append(f"    class {node_id} stageClass")
        
        # 添加连接
        if i > 0:
            prev_id = stages[i-1].replace(".", "_")
            mermaid.append(f"    {prev_id} --> {node_id}")
    
    mermaid_code = "\n".join(mermaid)
    output_path = FIGURES_DIR / output_name
    
    print(f"\n[Generating] Technical Roadmap: {stages}")
    if render_mermaid(mermaid_code, output_path, theme="default"):
        return output_path
    else:
        return None


def generate_model_architecture(model_type: str, config_path: Path = None, 
                               output_name: str = "model_architecture.png") -> Path:
    """
    生成模型架构图
    
    Args:
        model_type: 模型类型 (optimization/evaluation/prediction/network)
        config_path: 配置文件路径（JSON格式）
        output_name: 输出文件名
    
    Returns:
        输出文件路径
    """
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # 使用默认模板
        config = get_default_architecture(model_type)
    
    # 生成 Mermaid graph
    mermaid = ["graph TB"]
    mermaid.append("    classDef inputClass fill:#e8f5e9,stroke:#4caf50,stroke-width:2px")
    mermaid.append("    classDef processClass fill:#fff3e0,stroke:#ff9800,stroke-width:2px")
    mermaid.append("    classDef outputClass fill:#fce4ec,stroke:#e91e63,stroke-width:2px")
    
    for layer_id, layer_info in config.items():
        label = layer_info.get("label", layer_id)
        layer_type = layer_info.get("type", "process")
        
        mermaid.append(f'    {layer_id}["{label}"]')
        mermaid.append(f"    class {layer_id} {layer_type}Class")
        
        # 添加连接
        for target in layer_info.get("connects_to", []):
            edge_label = layer_info.get("edge_label", "")
            if edge_label:
                mermaid.append(f'    {layer_id} -->|{edge_label}| {target}')
            else:
                mermaid.append(f'    {layer_id} --> {target}')
    
    mermaid_code = "\n".join(mermaid)
    output_path = FIGURES_DIR / output_name
    
    print(f"\n[Generating] Model Architecture ({model_type})")
    if render_mermaid(mermaid_code, output_path, theme="neutral"):
        return output_path
    else:
        return None


def generate_algorithm_flowchart(steps_file: Path, output_name: str = "algorithm_flowchart.png") -> Path:
    """
    生成算法流程图
    
    Args:
        steps_file: 算法步骤定义文件（JSON格式）
        output_name: 输出文件名
    
    Returns:
        输出文件路径
    """
    with open(steps_file, 'r', encoding='utf-8') as f:
        steps = json.load(f)
    
    mermaid = ["flowchart TD"]
    mermaid.append("    classDef startEnd fill:#c8e6c9,stroke:#388e3c,stroke-width:2px")
    mermaid.append("    classDef process fill:#bbdefb,stroke:#1976d2,stroke-width:2px")
    mermaid.append("    classDef decision fill:#ffe0b2,stroke:#f57c00,stroke-width:2px")
    
    for step in steps:
        step_id = step["id"]
        step_type = step.get("type", "process")
        label = step["label"]
        
        # 根据类型选择节点形状
        if step_type == "start" or step_type == "end":
            mermaid.append(f'    {step_id}(["{label}"])')
            mermaid.append(f"    class {step_id} startEnd")
        elif step_type == "decision":
            mermaid.append(f'    {step_id}{{{label}}}')
            mermaid.append(f"    class {step_id} decision")
        else:
            mermaid.append(f'    {step_id}["{label}"]')
            mermaid.append(f"    class {step_id} process")
        
        # 添加连接
        for edge in step.get("edges", []):
            target = edge["to"]
            condition = edge.get("condition", "")
            if condition:
                mermaid.append(f'    {step_id} -->|{condition}| {target}')
            else:
                mermaid.append(f'    {step_id} --> {target}')
    
    mermaid_code = "\n".join(mermaid)
    output_path = FIGURES_DIR / output_name
    
    print(f"\n[Generating] Algorithm Flowchart")
    if render_mermaid(mermaid_code, output_path, theme="default"):
        return output_path
    else:
        return None


def generate_data_flow_diagram(stages: list, output_name: str = "data_flow_diagram.png") -> Path:
    """
    生成数据流图
    
    Args:
        stages: 数据处理阶段列表
        output_name: 输出文件名
    
    Returns:
        输出文件路径
    """
    mermaid = ["graph LR"]
    mermaid.append("    classDef dataClass fill:#e3f2fd,stroke:#1976d2,stroke-width:2px")
    mermaid.append("    classDef processClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
    
    for i, stage in enumerate(stages):
        stage_id = f"stage{i}"
        mermaid.append(f'    {stage_id}["{stage}"]')
        mermaid.append(f"    class {stage_id} processClass")
        
        if i > 0:
            prev_id = f"stage{i-1}"
            mermaid.append(f"    {prev_id} --> {stage_id}")
    
    mermaid_code = "\n".join(mermaid)
    output_path = FIGURES_DIR / output_name
    
    print(f"\n[Generating] Data Flow Diagram")
    if render_mermaid(mermaid_code, output_path, theme="default"):
        return output_path
    else:
        return None


def get_default_architecture(model_type: str) -> dict:
    """获取默认模型架构模板"""
    templates = {
        "optimization": {
            "input": {"label": "输入数据/约束", "type": "input", "connects_to": ["preprocess"]},
            "preprocess": {"label": "数据预处理", "type": "process", "connects_to": ["model"]},
            "model": {"label": "优化模型\n(目标函数+约束)", "type": "process", "connects_to": ["solver"]},
            "solver": {"label": "求解器\n(算法)", "type": "process", "connects_to": ["output"]},
            "output": {"label": "最优解", "type": "output", "connects_to": []}
        },
        "evaluation": {
            "input": {"label": "评价对象", "type": "input", "connects_to": ["indicators"]},
            "indicators": {"label": "指标体系", "type": "process", "connects_to": ["weight"]},
            "weight": {"label": "权重分配\n(AHP/熵权)", "type": "process", "connects_to": ["aggregate"]},
            "aggregate": {"label": "综合评价", "type": "process", "connects_to": ["output"]},
            "output": {"label": "评价结果", "type": "output", "connects_to": []}
        },
        "prediction": {
            "input": {"label": "历史数据", "type": "input", "connects_to": ["feature"]},
            "feature": {"label": "特征工程", "type": "process", "connects_to": ["model"]},
            "model": {"label": "预测模型", "type": "process", "connects_to": ["validate"]},
            "validate": {"label": "模型验证", "type": "process", "connects_to": ["output"]},
            "output": {"label": "预测结果", "type": "output", "connects_to": []}
        }
    }
    return templates.get(model_type, templates["optimization"])


def main():
    parser = argparse.ArgumentParser(description="Diagram Generator - 生成论文必备图表")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # roadmap 子命令
    roadmap_parser = subparsers.add_parser("roadmap", help="生成技术路线图")
    roadmap_parser.add_argument("--stages", type=str, required=True,
                               help="阶段列表，逗号分隔，如: S0,S1,S3,S5,S8")
    roadmap_parser.add_argument("--output", type=str, default="fig1_technical_roadmap.png",
                               help="输出文件名")
    
    # model-arch 子命令
    arch_parser = subparsers.add_parser("model-arch", help="生成模型架构图")
    arch_parser.add_argument("--type", type=str, required=True,
                            choices=["optimization", "evaluation", "prediction", "network"],
                            help="模型类型")
    arch_parser.add_argument("--config", type=str, help="配置文件路径（JSON格式）")
    arch_parser.add_argument("--output", type=str, default="model_architecture.png",
                            help="输出文件名")
    
    # flowchart 子命令
    flow_parser = subparsers.add_parser("flowchart", help="生成算法流程图")
    flow_parser.add_argument("--steps", type=str, required=True,
                            help="算法步骤定义文件（JSON格式）")
    flow_parser.add_argument("--output", type=str, default="algorithm_flowchart.png",
                            help="输出文件名")
    
    # dataflow 子命令
    dataflow_parser = subparsers.add_parser("dataflow", help="生成数据流图")
    dataflow_parser.add_argument("--stages", type=str, required=True,
                                help="数据处理阶段，逗号分隔")
    dataflow_parser.add_argument("--output", type=str, default="data_flow_diagram.png",
                                help="输出文件名")
    
    # check 子命令
    subparsers.add_parser("check", help="检查依赖工具")
    
    args = parser.parse_args()
    
    if args.command == "check":
        print("[Checking] Dependencies...")
        check_dependencies()
        print("[OK] All dependencies satisfied")
        return
    
    if not args.command:
        parser.print_help()
        return
    
    check_dependencies()
    
    if args.command == "roadmap":
        stages = [s.strip() for s in args.stages.split(",")]
        result = generate_technical_roadmap(stages, args.output)
        if result:
            print(f"\n[SUCCESS] {result}")
        else:
            sys.exit(1)
    
    elif args.command == "model-arch":
        config_path = Path(args.config) if args.config else None
        result = generate_model_architecture(args.type, config_path, args.output)
        if result:
            print(f"\n[SUCCESS] {result}")
        else:
            sys.exit(1)
    
    elif args.command == "flowchart":
        steps_file = Path(args.steps)
        if not steps_file.exists():
            print(f"[ERROR] Steps file not found: {steps_file}")
            sys.exit(1)
        result = generate_algorithm_flowchart(steps_file, args.output)
        if result:
            print(f"\n[SUCCESS] {result}")
        else:
            sys.exit(1)
    
    elif args.command == "dataflow":
        stages = [s.strip() for s in args.stages.split(",")]
        result = generate_data_flow_diagram(stages, args.output)
        if result:
            print(f"\n[SUCCESS] {result}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
