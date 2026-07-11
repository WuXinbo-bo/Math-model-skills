# 评价/决策类自检（TOPSIS/AHP/熵权法/排名打分必读）

## 专项核验清单

```

E1. [权重归一] 权重之和是否等于 1（误差 ≤ 0.01）？

E2. [一致性] AHP 的 CR < 0.1？（如果用了 AHP）

E3. [排名稳定] 权重微调后排名是否稳定？

E4. [指标方向] 正向/负向指标是否正确处理？

E5. [得分区分度] 所有方案得分差异是否 < 1%（无区分度）？

E6. [常识对照] 排名是否与题目暗示的常识严重矛盾（正负向反了）？

```

## 红旗信号

| 现象 | 可能缘由 |

|------|---------|

| 权重之和 ≠ 1（误差 > 0.01） | 归一化环节遗漏 |

| 全部方案得分差异 < 1% | 指标选取不当 / 权重过于均匀 |

| 排名与题目暗示的常识严重矛盾 | 正负向指标处理反了 |

| AHP CR > 0.1 | 判定矩阵不一致, 需修正 |

## 权重稳定性校验

```python

# 微调权重 ±10%, 看排名是否稳定

import numpy as np

base_weights = np.array([0.3, 0.25, 0.2, 0.15, 0.1])

base_rank = compute_rank(base_weights)

shaken_ranks = []

for trial in range(20):

    perturb = 1 + np.random.uniform(-0.1, 0.1, len(base_weights))

    w = base_weights * perturb

    w /= w.sum()

    shaken_ranks.append(compute_rank(w))

# 计算每个方案的排名变化范围

import collections

for idx in range(num_alternatives):

    ranks_at_idx = [r[idx] for r in shaken_ranks]

    span = max(ranks_at_idx) - min(ranks_at_idx)

    if span > 2:

        print(f"⚠ 方案 {idx} 排名波动 {span} 名, 不稳定")

```

## 必产数据

```json

{

  "method": "TOPSIS / AHP / 熵权法",

  "weights": {"指标1": 0.3, "指标2": 0.25, ...},

  "weights_sum": 1.0,

  "ahp_cr": 0.08,

  "scores": {"方案A": 0.85, "方案B": 0.72, ...},

  "ranking": ["方案A", "方案B", "方案C"],

  "stability": {"weight_perturb_pct": 10, "max_rank_change": 1}

}

```

