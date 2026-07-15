# 优化类自检（调度/选址/路线/分配/规划类必读）

若当前子问题是优化类（有清晰标明的目标函数需最大化或最小化）, 按以下分层策略求解 + 自检。

## 层级 1：建立可行解（必做）

先保证能定位一个满足全部约束的可行解, 不追求最优。

```python

# 伪代码框架

def solve_problem():

    # 1. 从 问题分析.md 提取所有约束

    constraints = extract_constraints()  # 容量、预算、时间窗、数量限制等

    # 2. 用最简单的方法找一个可行解（贪心/随机/启发式）

    solution = greedy_initial_solution()

    # 3. 逐条验证约束

    for c in constraints:

        assert c.verify(solution), f"约束违反: {c.name}"

    # 4. 记录基准目标函数值

    baseline_obj = objective(solution)

    print(f"基准可行解: obj={baseline_obj}")

    return solution, baseline_obj

```

**约束强制校验（每一次求解后必做）**：

```bash

echo "=== 约束验证 ==="

grep -i '约束\|限制\|不超过\|不少于\|上限\|下限\|容量\|预算\|≤\|≥\|<=\|>=' 问题分析.md 2>/dev/null | head -20

echo "--- 逐条核对上述约束是否满足 ---"

```

查阅代码交付的结果, 逐条对照题目约束。**任何一条不满足 → 务必调整代码重跑, 不可跳过。**

## 层级 2：选取求解路线

| 问题特征 | 推荐路线 | 求解器 |

|---------|---------|-------|

| 线性目标 + 线性约束 | 精确求解 | `scipy.optimize.linprog` → PuLP → OR-Tools |

| 整数/0-1 变量 | 精确求解（小规模）或启发式（大规模） | PuLP(CBC) → OR-Tools(SCIP) |

| 非线性目标或约束 | 启发式 + 局部搜索 | scipy.optimize.minimize → 遗传算法 → 模拟退火 |

| 组合优化（TSP/VRP/排程） | 启发式 + 改进 | 贪心构造 → 2-opt/3-opt → 遗传/蚁群 |

| 多目标优化 | Pareto 前沿 | NSGA-II (pymoo/deap) |

**精确求解路线**（能用就用, 结果是全局最优）：

```python

from scipy.optimize import linprog

# 或

import pulp

prob = pulp.LpProblem("name", pulp.LpMinimize)

# 定义变量时明确类型：LpInteger / LpBinary / LpContinuous

# 求解后检查 prob.status == 1 (Optimal)

```

若精确求解器返回 Optimal, **不需多轮调优**——这已经是全局最优。直接转入层级 4。

**启发式求解路线**（精确求解不可行时用）：

启发式不保证全局最优, 务必通过自动化调参逼近最优解。**避免人工写死参数——用代码自动化搜索最优参数组合。**

策略：先快速试探（30 秒内）, 再自动化调参, 最后多算法对比

```python

import time, itertools

def auto_tune(solve_func, param_grid, time_budget=None):

    """

    自动参数搜索框架。

    solve_func(params) -> (objective, feasible, solution)

    param_grid: dict, 如 {'pop_size': [50, 100, 200], 'n_gen': [200, 500, 1000], 'cx_rate': [0.7, 0.8, 0.9]}

    time_budget: 总时间预算（秒）, 由 Meta-model-agent 根据问题规模自行决定

    """

    first_params = {k: v[0] for k, v in param_grid.items()}

    t0 = time.time()

    obj, feasible, sol = solve_func(first_params)

    single_time = time.time() - t0

    if time_budget is None:

        total_combos = 1

        for v in param_grid.values():

            total_combos *= len(v)

        time_budget = max(single_time * total_combos * 1.5, single_time * 20, 120)

    total_combos = 1

    for v in param_grid.values():

        total_combos *= len(v)

    if single_time * total_combos < time_budget:

        strategy = "grid_search"

    elif single_time * len(param_grid) * 3 < time_budget:

        strategy = "coordinate_search"

    else:

        n_samples = max(5, int(time_budget / single_time / 2))

        strategy = f"random_search_{n_samples}"

    best_obj, best_params, best_sol = obj, first_params, sol

    results_log = [{"params": first_params, "objective": obj, "feasible": feasible}]

    start_time = time.time()

    def _time_ok():

        return time.time() - start_time < time_budget

    if strategy == "grid_search":

        keys = list(param_grid.keys())

        for combo in itertools.product(*param_grid.values()):

            if not _time_ok(): break

            params = dict(zip(keys, combo))

            if params == first_params: continue

            obj, feasible, sol = solve_func(params)

            results_log.append({"params": params, "objective": obj, "feasible": feasible})

            if feasible and obj < best_obj:

                best_obj, best_params, best_sol = obj, params, sol

    elif strategy == "coordinate_search":

        current_best = dict(first_params)

        for key in param_grid:

            if not _time_ok(): break

            for val in param_grid[key]:

                if not _time_ok(): break

                params = dict(current_best)

                params[key] = val

                obj, feasible, sol = solve_func(params)

                results_log.append({"params": params, "objective": obj, "feasible": feasible})

                if feasible and obj < best_obj:

                    best_obj, best_params, best_sol = obj, params, sol

                    current_best = dict(params)

    else:  # random_search

        import random

        n = int(strategy.split("_")[-1])

        for _ in range(n):

            if not _time_ok(): break

            params = {k: random.choice(v) for k, v in param_grid.items()}

            obj, feasible, sol = solve_func(params)

            results_log.append({"params": params, "objective": obj, "feasible": feasible})

            if feasible and obj < best_obj:

                best_obj, best_params, best_sol = obj, params, sol

    return best_obj, best_params, best_sol, results_log

```

参考 param_grid：

- 遗传算法：`{'pop_size': [50, 100, 200, 500], 'n_gen': [200, 500, 1000], 'cx_rate': [0.7, 0.8, 0.9], 'mut_rate': [0.05, 0.1, 0.2]}`

- 模拟退火：`{'T0': [500, 1000, 5000], 'alpha': [0.99, 0.995, 0.999], 'n_restarts': [1, 3, 5]}`

- 粒子群：`{'n_particles': [30, 50, 100], 'n_iter': [200, 500], 'w': [0.5, 0.7, 0.9]}`

## 层级 3：结果改进（启发式专用）

```python

def local_search(solution, max_iter=1000, time_limit=None):

    import time

    if time_limit is None:

        time_limit = float('inf')

    best = solution.copy()

    best_obj = objective(best)

    t0 = time.time()

    improved = 0

    for i in range(max_iter):

        if time.time() - t0 > time_limit:

            break

        neighbor = generate_neighbor(best)

        if all(c.verify(neighbor) for c in constraints):

            obj = objective(neighbor)

            if obj < best_obj:

                best, best_obj = neighbor, obj

                improved += 1

    return best, best_obj

```

## 层级 4：登记求解过程（全部优化类必做）

```json

{

  "solve_method": "GA + 2-opt local search",

  "solve_route": "heuristic",

  "rounds": [

    {"round": 1, "params": "pop=50, gen=200", "objective": 12345, "feasible": true, "time_sec": 30},

    {"round": 2, "params": "pop=200, gen=1000", "objective": 11890, "feasible": true, "time_sec": 120},

    {"round": 3, "method": "SA_compare", "objective": 12100, "feasible": true, "time_sec": 45}

  ],

  "local_search": {"before": 11890, "after": 11650, "improvement_pct": 2.0},

  "best_objective": 11650,

  "all_constraints_satisfied": true,

  "is_exact_optimal": false,

  "convergence": {"converged": true, "metric": "last_50_gen_improvement<0.1%", "final_improvement": 0.02},

  "bounds": {"lower_bound": 10500, "upper_bound": 15000, "gap_pct": 25.6},

  "stability": {"n_runs": 5, "objectives": [11650, 11720, 11680, 11690, 11650], "cv_pct": 0.24},

  "constraint_activity": {"active": ["capacity_A", "budget"], "inactive": ["time_limit", "min_demand"]},

  "robustness": {"max_sensitivity_var": "x3", "max_obj_change_pct": 8.5, "fragile_vars": ["x3"]}

}

```

## 层级 5：优化结果结构性校验（⛔ 全部优化类必做）

**问题本质**：结果在约束内、目标函数值看起来合理, 但解本身是"伪最优"——要么不稳定（换个种子就变了）, 要么物理上不可解释（某些资源完全闲置）, 要么约束形同虚设（全部不活跃）。

```python

# ===== 层级 5：优化结果结构性验证 =====

# 在保存 problem_N_结果.json 之前执行, 不通过则禁止保存

def structural_validation(solution, objective_func, constraints, decision_vars_info,

                          solve_func=None, n_stability_runs=5):

    """优化结果结构性验证。返回 (passed: bool, report: str)。"""

    issues = []

    warnings = []

    best_obj = objective_func(solution)

    # ===== 验证 1：约束活跃性分析 =====

    active_constraints = []

    inactive_constraints = []

    tol = 1e-4

    for name, (func, bound, direction) in constraints.items():

        value = func(solution)

        if direction == 'le':

            slack = bound - value

        elif direction == 'ge':

            slack = value - bound

        else:

            slack = abs(value - bound)

        if abs(slack) < tol:

            active_constraints.append(name)

        else:

            inactive_constraints.append((name, slack))

    if len(active_constraints) == 0 and len(constraints) > 2:

        warnings.append(

            f"⚠ 所有 {len(constraints)} 个约束均不活跃（解在可行域内部）。"

            f"可能原因：约束太松/遗漏关键约束。请回查题目是否有未建模的限制条件。"

        )

    if len(active_constraints) > len(constraints) * 0.5 and len(constraints) >= 4:

        warnings.append(

            f"⚠ {len(active_constraints)}/{len(constraints)} 个约束同时活跃（角点解）。"

            f"角点解对参数微扰极其敏感。"

        )

    # ===== 验证 2：决策变量边界检查（防止"死变量"）=====

    boundary_vars = []

    interior_vars = []

    for var_name, (value, lb, ub, desc) in decision_vars_info.items():

        range_width = ub - lb if ub != lb else 1

        if abs(value - lb) < tol * range_width:

            boundary_vars.append(f"{var_name}={value:.4f} (at lower bound {lb})")

        elif abs(value - ub) < tol * range_width:

            boundary_vars.append(f"{var_name}={value:.4f} (at upper bound {ub})")

        else:

            interior_vars.append(var_name)

    if boundary_vars:

        if len(boundary_vars) == len(decision_vars_info):

            issues.append(

                f"❌ 所有决策变量都取到了边界值！这通常意味着：\n"

                f"  1. 目标函数是单调的（不需要优化, 直接取边界就行）\n"

                f"  2. 约束定义有误（bounds 太紧）\n"

                f"  3. 优化器没有真正搜索（初始值就在边界, 没动过）"

            )

    # ===== 验证 4：解的可解释性（资源利用率）=====

    for var_name, (value, lb, ub, desc) in decision_vars_info.items():

        if '数量' in desc or '分配' in desc or '利用' in desc:

            if value == 0 and ub > 0:

                warnings.append(

                    f"⚠ {var_name}({desc}) = 0（完全未使用）, 但上界为 {ub}。"

                )

    # ===== 验证 5：稳定性验证（启发式算法必做）=====

    if solve_func is not None and n_stability_runs > 1:

        import numpy as np

        objectives = []

        for seed in range(42, 42 + n_stability_runs):

            try:

                obj_i, _ = solve_func(seed)

                objectives.append(obj_i)

            except Exception:

                pass

        if len(objectives) >= 3:

            obj_mean = np.mean(objectives)

            obj_std = np.std(objectives)

            cv = obj_std / abs(obj_mean) if abs(obj_mean) > 1e-10 else 0

            if cv > 0.05:

                issues.append(

                    f"❌ 优化结果不稳定！CV={cv:.2%} > 5%。"

                    f"必须：增加种群大小/迭代次数, 或做变量降维后重新优化。"

                )

            elif cv > 0.01:

                warnings.append(f"⚠ 优化结果有一定波动 CV={cv:.2%}。取最优的那次作为最终结果。")

    if issues:

        return False, "\n".join(issues)

    elif warnings:

        return True, "\n".join(warnings)

    else:

        return True, ""

```

⛔ **采用方式**：

```python

decision_vars_info = {

    'x1': (solution[0], 0, 100, '机器1分配量'),

    'x2': (solution[1], 0, 100, '机器2分配量'),

    'x3': (solution[2], 0, 50, '加班时间(h)'),

}

constraints_verify = {

    '产能约束': (lambda s: s[0] + s[1], 150, 'le'),

    '需求约束': (lambda s: s[0] + s[1], 80, 'ge'),

    '预算约束': (lambda s: cost_func(s), budget, 'le'),

}

passed, report = structural_validation(

    solution, objective, constraints_verify, decision_vars_info,

    solve_func=lambda seed: solve_with_seed(seed),

    n_stability_runs=5

)

if not passed:

    raise ValueError(f"结构性验证失败, 必须修正：\n{report}")

```

⛔ **结构性校验失败的修正过程**：

1. 约束全不活跃 → 回查题目, 补充遗漏的约束条件

2. 全部变量在边界 → 核验目标函数是否无误（是否遗漏了非线性项/交互项）

3. 资源闲置 → 核验目标函数是否无误反映了该资源的贡献

4. 结果不稳定 → 增加搜索强度或做变量降维

5. 修正后务必重跑优化 + 重新校验, 不可只改报告

## 优化类专项自检清单

```

O1. [约束满足] 最优解是否满足题目所有约束？

O2. [变量类型] 整数/0-1 变量是否满足类型要求？

O3. [收敛性] 优化算法是否收敛？

O4. [优于基准] 最优解是否优于简单基准方法？

O5. [解的稳定性] 不同随机种子的结果是否一致？

O6. [约束活跃性] 哪些约束活跃（取等号）？是否与建模报告的预期一致？

O7. [分量贡献度] 多目标加权求和时, 各分量贡献比例是否合理？

O8. [资源利用率] 所有可用资源是否都被合理利用？

O9. [解的可解释性] 最优解能否用自然语言合理解释？

O10. [松弛间隙] 如果用了连续松弛+取整, 松弛解与整数解的 gap 是多少？

O11. [收敛判据] 算法是真正收敛了还是只是跑够了迭代次数？

```

## ⛔ 时间预算 / 求解器超时

避免设太短的超时（如 120 秒）。竞赛数据量可能很大, 求解器需充足时间。

- 小规模问题（变量 <100）：`timeout=300`（5 分钟）

- 中规模问题（变量 100-1000）：`timeout=600`（10 分钟）

- 大规模问题（变量 >1000）：`timeout=1200`（20 分钟）

- 全部求解器都务必打印进度（每 30 秒输出一次当前最优解）, 防止无交付超时被系统杀掉

