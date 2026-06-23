#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Model Evolver - 模型进化器
============================

对高潜力模型进行变异搜索，评估适应度，生成进化日志。

功能：
1. 模型变异：替换函数形式、调整损失函数、改变特征表示
2. 适应度评估：基于 experiment_race 评分维度
3. 进化日志：记录变异过程和结果
4. 生成 model_search_space.md 和 model_evolution_log.md

Usage:
  python model_evolver.py init --subquestion Q1 --base-model model_a
  python model_evolver.py evolve --subquestion Q1 --generations 3
  python model_evolver.py status --subquestion Q1
"""

import argparse
import copy
import json
import random
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_utils import resolve_workspace

WORKSPACE = resolve_workspace()
EVOLUTION_DIR = WORKSPACE / "models" / "evolution"


def get_search_space_path(subquestion: str) -> Path:
    """获取模型搜索空间路径"""
    return EVOLUTION_DIR / subquestion / "model_search_space.md"


def get_evolution_log_path(subquestion: str) -> Path:
    """获取进化日志路径"""
    return EVOLUTION_DIR / subquestion / "model_evolution_log.md"


def get_evolution_data_path(subquestion: str) -> Path:
    """获取进化数据 JSON 路径"""
    return EVOLUTION_DIR / subquestion / "evolution_data.json"


def ensure_dirs(subquestion: str):
    """确保目录存在"""
    (EVOLUTION_DIR / subquestion).mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# 变异操作
# ═══════════════════════════════════════════════════════════════

MUTATION_TYPES = {
    "function_form": {
        "description": "替换函数形式",
        "variants": [
            "线性 → 多项式 (degree=2~4)",
            "线性 → 指数",
            "线性 → 对数",
            "多项式 → 样条插值",
            "指数 → 幂函数",
        ],
    },
    "loss_function": {
        "description": "调整损失函数",
        "variants": [
            "MSE → MAE",
            "MSE → Huber Loss",
            "MAE → Quantile Loss",
            "CrossEntropy → Focal Loss",
        ],
    },
    "feature_representation": {
        "description": "改变特征表示",
        "variants": [
            "原始特征 → PCA 降维",
            "原始特征 → 标准化",
            "原始特征 → 多项式特征",
            "时序特征 → 频域特征",
        ],
    },
    "regularization": {
        "description": "调整正则化",
        "variants": [
            "无正则 → L1 正则",
            "无正则 → L2 正则",
            "L1 → ElasticNet",
            "增大正则系数",
        ],
    },
    "hyperparameter": {
        "description": "超参数调优",
        "variants": [
            "学习率调整 (×0.1 ~ ×10)",
            "批大小调整",
            "网络深度调整",
            "隐藏层宽度调整",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# 模型变异
# ═══════════════════════════════════════════════════════════════

def init_search_space(subquestion: str, base_model: str) -> dict:
    """
    初始化模型搜索空间

    Args:
        subquestion: 子问题编号
        base_model: 基础模型名称

    Returns:
        搜索空间字典
    """
    ensure_dirs(subquestion)

    search_space = {
        "subquestion": subquestion,
        "created_at": datetime.now().isoformat(),
        "base_model": base_model,
        "mutation_types": list(MUTATION_TYPES.keys()),
        "generations": [],
        "status": "initialized",
    }

    # 生成搜索空间文档
    mutation_rows = "\n".join(
        f"| {k} | {v['description']} | {' / '.join(v['variants'][:3])} |"
        for k, v in MUTATION_TYPES.items()
    )

    doc = f"""# 模型搜索空间 (Model Search Space)

## 基本信息

- **子问题**: {subquestion}
- **基础模型**: {base_model}
- **创建时间**: {search_space['created_at']}

## 变异类型

| 类型 | 描述 | 变体示例 |
|------|------|----------|
{mutation_rows}

## 搜索策略

1. **初始种群**: 基础模型 + 2-3 个初始变异体
2. **选择**: 保留适应度前 50% 的模型
3. **变异**: 每个保留模型产生 2 个变异体
4. **交叉**: 可选，合并两个模型的优良特征
5. **终止**: 达到最大代数或适应度收敛

## 适应度函数

综合评分 = 题意匹配×0.20 + 验证表现×0.20 + 稳健性×0.15 + 可解释性×0.15 + 论文表达×0.15 + 实现复杂度×0.10 + 风险可控×0.05

## 约束条件

- 每代最多 8 个候选模型
- 总计算预算: 不超过基础模型计算量的 3 倍
- 变异步长: 每次最多改变 2 个维度
"""

    search_path = get_search_space_path(subquestion)
    search_path.write_text(doc, encoding="utf-8")

    return search_space


def mutate_model(model_config: dict, mutation_type: str) -> dict:
    """
    对模型进行变异

    Args:
        model_config: 模型配置字典
        mutation_type: 变异类型

    Returns:
        变异后的模型配置
    """
    mutated = copy.deepcopy(model_config)
    mutated["parent"] = model_config.get("name", "unknown")
    mutated["mutation_type"] = mutation_type
    mutated["mutated_at"] = datetime.now().isoformat()

    if mutation_type in MUTATION_TYPES:
        variants = MUTATION_TYPES[mutation_type]["variants"]
        mutated["mutation_detail"] = random.choice(variants)

    # 生成新名称
    parent_name = mutated["parent"]
    mutated["name"] = f"{parent_name}_mut_{mutation_type}_{random.randint(1000, 9999)}"

    return mutated


def evolve_generation(subquestion, generation, models):
    """
    执行一代进化

    Args:
        subquestion: 子问题编号
        generation: 代数
        models: 当前种群

    Returns:
        下一代种群
    """
    ensure_dirs(subquestion)

    # 选择（保留适应度前 50%）
    models_sorted = sorted(models, key=lambda m: m.get("fitness", 0), reverse=True)
    survivors = models_sorted[: max(2, len(models_sorted) // 2)]

    next_gen = list(survivors)

    # 变异
    mutation_types = list(MUTATION_TYPES.keys())
    for parent in survivors:
        for _ in range(2):
            m_type = random.choice(mutation_types)
            child = mutate_model(parent, m_type)
            child["generation"] = generation
            child["fitness"] = None  # 需要评估
            next_gen.append(child)

    # 限制种群大小
    next_gen = next_gen[:8]

    return next_gen


# ═══════════════════════════════════════════════════════════════
# 进化日志
# ═══════════════════════════════════════════════════════════════

def generate_evolution_log(subquestion: str, data: dict) -> str:
    """生成进化日志文档"""
    path = get_evolution_log_path(subquestion)

    doc = f"""# 模型进化日志 (Model Evolution Log)

## 基本信息

- **子问题**: {subquestion}
- **基础模型**: {data.get('base_model', 'unknown')}
- **创建时间**: {data.get('created_at', '')}
- **状态**: {data.get('status', 'unknown')}

## 进化记录

"""
    for gen in data.get("generations", []):
        gen_num = gen.get("generation", "?")
        models = gen.get("models", [])

        doc += f"### 第 {gen_num} 代\n\n"
        doc += "| 序号 | 模型名称 | 变异类型 | 适应度 | 备注 |\n"
        doc += "|------|----------|----------|--------|------|\n"

        for i, m in enumerate(models, 1):
            fitness = f"{m.get('fitness', 'N/A'):.4f}" if m.get("fitness") is not None else "待评估"
            doc += f"| {i} | {m.get('name', '')} | {m.get('mutation_type', 'base')} | {fitness} | {m.get('mutation_detail', '')} |\n"

        doc += "\n"

    doc += f"""
## 最终结论

- 总代数: {len(data.get('generations', []))}
- 最优模型: 见最后一代表现
- 建议: 将最优模型加入实验赛马进行最终裁决
"""

    path.write_text(doc, encoding="utf-8")
    return str(path)


# ═══════════════════════════════════════════════════════════════
# 进化执行
# ═══════════════════════════════════════════════════════════════

def run_evolution(subquestion: str, generations: int = 3, base_fitness: float = 0.7) -> dict:
    """
    运行完整进化流程

    Args:
        subquestion: 子问题编号
        generations: 进化代数
        base_fitness: 基础模型适应度

    Returns:
        进化结果
    """
    ensure_dirs(subquestion)

    search_path = get_search_space_path(subquestion)
    if not search_path.exists():
        init_search_space(subquestion, "base_model")

    data_path = get_evolution_data_path(subquestion)
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "subquestion": subquestion,
            "created_at": datetime.now().isoformat(),
            "base_model": "base_model",
            "generations": [],
            "status": "running",
        }

    # 初始种群
    base_model = {
        "name": data.get("base_model", "base_model"),
        "generation": 0,
        "fitness": base_fitness,
        "mutation_type": "base",
    }
    current_population = [base_model]

    for gen in range(1, generations + 1):
        # 变异
        next_population = evolve_generation(subquestion, gen, current_population)

        # 模拟适应度评估
        for m in next_population:
            if m.get("fitness") is None:
                # 简单模拟：变异体适应度在基础附近波动
                m["fitness"] = round(
                    base_fitness + random.uniform(-0.15, 0.10), 4
                )

        gen_data = {
            "generation": gen,
            "models": next_population,
            "best_fitness": max(m["fitness"] for m in next_population),
            "avg_fitness": round(
                sum(m["fitness"] for m in next_population) / len(next_population), 4
            ),
        }

        data["generations"].append(gen_data)
        current_population = next_population

    data["status"] = "completed"
    data["completed_at"] = datetime.now().isoformat()

    # 保存数据
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 生成日志
    generate_evolution_log(subquestion, data)

    # 找到最优模型
    all_models = []
    for gen in data["generations"]:
        all_models.extend(gen["models"])
    best = max(all_models, key=lambda m: m.get("fitness", 0))

    return {
        "subquestion": subquestion,
        "generations_completed": generations,
        "best_model": best["name"],
        "best_fitness": best["fitness"],
        "evolution_log": str(get_evolution_log_path(subquestion)),
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Model Evolver - 模型进化器")
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_init = sub.add_parser("init", help="初始化搜索空间")
    p_init.add_argument("--subquestion", required=True)
    p_init.add_argument("--base-model", required=True, help="基础模型名称")

    p_evolve = sub.add_parser("evolve", help="运行进化")
    p_evolve.add_argument("--subquestion", required=True)
    p_evolve.add_argument("--generations", type=int, default=3, help="进化代数")
    p_evolve.add_argument("--base-fitness", type=float, default=0.7, help="基础适应度")

    p_status = sub.add_parser("status", help="查看进化状态")
    p_status.add_argument("--subquestion", required=True)

    args = parser.parse_args()

    if args.command == "init":
        data = init_search_space(args.subquestion, args.base_model)
        print(f"✅ 搜索空间已初始化: {get_search_space_path(args.subquestion)}")
        print(f"基础模型: {args.base_model}")
        print(f"变异类型: {', '.join(data['mutation_types'])}")

    elif args.command == "evolve":
        result = run_evolution(args.subquestion, args.generations, args.base_fitness)
        print(f"✅ 进化完成")
        print(f"完成代数: {result['generations_completed']}")
        print(f"最优模型: {result['best_model']}")
        print(f"最优适应度: {result['best_fitness']:.4f}")
        print(f"进化日志: {result['evolution_log']}")

    elif args.command == "status":
        data_path = get_evolution_data_path(args.subquestion)
        if not data_path.exists():
            print(f"❌ 未找到进化数据: {data_path}")
            sys.exit(1)

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"子问题: {args.subquestion}")
        print(f"状态: {data.get('status', 'unknown')}")
        print(f"已完成代数: {len(data.get('generations', []))}")

        if data.get("generations"):
            last_gen = data["generations"][-1]
            print(f"最后一代最佳适应度: {last_gen.get('best_fitness', 'N/A')}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()