# 通用数值复核 + 9 问背景复核（全部题型必做）

## 第一步：自动化 sanity validate

跑下面这个脚本（先跑脚本, 不依赖人工判定）：

```python

# 程序/sanity_check.py — 自动化结果验证

import json, os, sys, re

# 读取所有结果 JSON

results = {}

for f in sorted(os.listdir('图表')):

    if f.endswith('_results.json') or f == '全部结果.json':

        with open(f'图表/{f}', 'r') as fh:

            results[f] = json.load(fh)

errors = []

warnings = []

suspicious = []  # ⛔ 可疑的"太完美"结果

def verify_value(name, val, context=""):

    """通用数值检查"""

    if val is None:

        errors.append(f"❌ {name} 为 None")

    elif isinstance(val, float):

        import math

        if math.isnan(val):

            errors.append(f"❌ {name} 为 NaN")

        elif math.isinf(val):

            errors.append(f"❌ {name} 为 Inf")

        elif abs(val) > 1e15:

            warnings.append(f"⚠ {name} = {val}, 数值异常大")

def verify_unrealistic(name, val):

    """⛔ 标记可能不合理的数值"""

    if not isinstance(val, (int, float)) or isinstance(val, bool):

        return

    key = name.lower()

    # R² / accuracy / precision / recall / f1 / auc：归一化指标（>0.99 标记）

    if any(w in key for w in ['r2', 'r_squared', 'accuracy', 'acc', 'precision', 'recall', 'f1', 'auc', 'r_score']):

        if val > 0.99:

            suspicious.append(f"🚩 {name} = {val:.4f}（>0.99）, 请确认是否过拟合")

        elif val < 0:

            errors.append(f"❌ {name} = {val} 负值（模型比均值预测还差, 必须换模型）")

        elif val < 0.5 and any(w in key for w in ['r2', 'r_squared', 'r_score']):

            errors.append(f"❌ {name} = {val:.4f}（R² < 0.5, 模型解释力极弱, 必须改进模型或检查数据预处理）")

    # RMSE / MAE / MSE / Loss

    if any(w in key for w in ['rmse', 'mae', 'mse', 'loss', 'error']):

        if val == 0:

            suspicious.append(f"🚩 {name} = 0 完美误差, 请确认训练/测试是否分开")

        elif val < 0:

            errors.append(f"❌ {name} = {val} 误差负值")

    # 提升百分比

    if any(w in key for w in ['improvement', 'speedup', 'gain', '提升', '改进']):

        if val > 1:

            suspicious.append(f"🚩 {name} = {val:.2f}（提升 {val*100:.0f}%）, 请结合题目确认")

    # p-value

    if 'p_value' in key or 'pvalue' in key or 'p值' in key:

        if val == 0:

            suspicious.append(f"🚩 {name} = 0 完美显著（应 > 1e-16）, 请确认")

        elif val > 1:

            errors.append(f"❌ {name} = {val} p 值 > 1 不可能")

def walk_verify(obj, path=""):

    if isinstance(obj, dict):

        for k, v in obj.items():

            walk_verify(v, f"{path}.{k}")

    elif isinstance(obj, list):

        for i, v in enumerate(obj):

            walk_verify(v, f"{path}[{i}]")

    elif isinstance(obj, (int, float)):

        verify_value(path, obj)

        verify_unrealistic(path, obj)

for fname, data in results.items():

    walk_verify(data, fname)

for e in errors:

    print(e)

for w in warnings:

    print(w)

for s in suspicious:

    print(s)

if not errors and not warnings and not suspicious:

    print("✅ 所有数值通过 sanity verify")

elif errors:

    print(f"\n共 {len(errors)} 个错误, {len(warnings)} 个警告, {len(suspicious)} 个可疑点 — 必须修复错误后再继续")

    sys.exit(1)

elif suspicious:

    print(f"\n共 {len(suspicious)} 个可疑的'完美'结果 — ⛔ 必须逐条确认：")

    print("  1. 确认训练集/测试集没有重叠？（过拟合或数据泄漏）")

    print("  2. 确认数据规模合理？（样本量 < 100 时 R² > 0.95 可能过拟合）")

    print("  3. 确认模型没有直接看到标签？（比如回归中自变量包含因变量的函数）")

    print("  4. 如果确实合理（物理仿真、确定性问题）, 在 计算结果.md 中说明原因")

```

## 第二步：问题递进性校验

对比各问题的目标函数值, 核验递进性：

```bash

echo "=== 问题递进性验证 ==="

python3 -c "

import json, os

results = {}

for f in sorted(os.listdir('图表')):

    if f.startswith('problem_') and f.endswith('_results.json'):

        with open(f'图表/{f}', 'r') as fh:

            results[f] = json.load(fh)

        data = results[f]

        key_vals = []

        for k, v in (data.items() if isinstance(data, dict) else []):

            if any(kw in k.lower() for kw in ['objective', 'optimal', 'best', 'total', 'cost', 'time', 'profit', 'makespan']):

                key_vals.append(f'{k}={v}')

        print(f'{f}: {\" | \".join(key_vals) if key_vals else \"(未找到核心指标)\"}')

" 2>/dev/null

```

人工核验：

1. 后续问题的结果是否比前一个有明显变化？

2. 新增的变量/资源是否对目标函数有边际效益？

3. 若某个问题的结果和前一个几乎相同 → 假设可能有问题

## 第三步：递进性违反时的诊断

若识别到 Q(n) 不优于 Q(n-1)（最小化中 Q(n) ≥ Q(n-1), 或最大化中 Q(n) ≤ Q(n-1)）, 按下面诊断树逐步排查：

```python

def diagnose_monotonicity_violation(sol_prev, obj_prev, sol_curr, obj_curr,

                                     objective_func, constraints_curr):

    print("⛔ 递进性违反！开始诊断...")

    # 检查1：Q(n-1) 的解在 Q(n) 的可行域中吗？

    prev_feasible_in_curr = all(c(sol_prev) for c in constraints_curr)

    if not prev_feasible_in_curr:

        print("  诊断结果：Q(n) 的约束比 Q(n-1) 更紧（不是更松）！")

        print("  → 约束定义有误, Q(n) 应该有更大的可行域")

        print("  → 修复：检查 Q(n) 新增的约束是否写反了")

        return "CONSTRAINT_ERROR"

    # 检查2：Q(n-1) 的解代入 Q(n) 的目标函数

    prev_obj_in_curr = objective_func(sol_prev)

    if prev_obj_in_curr < obj_curr:  # 最小化

        print(f"  诊断结果：Q(n-1) 的解在 Q(n) 中目标值 = {prev_obj_in_curr:.4f}")

        print(f"  优于 Q(n) 的'最优解' {obj_curr:.4f}！")

        print("  → Q(n) 的优化器搜索不充分")

        print("  → 修复：增加迭代次数/种群大小, 或用 Q(n-1) 的解作为初始种子")

        return "SEARCH_INSUFFICIENT"

    # 检查3：新增变量是否被利用

    new_vars = set(sol_curr.keys()) - set(sol_prev.keys())

    unused_new = [v for v in new_vars if abs(sol_curr.get(v, 0)) < 1e-6]

    if unused_new:

        print(f"  诊断结果：新增变量 {unused_new} 取值为 0（未被利用）")

        print("  → 目标函数没有正确反映新资源的贡献")

        print("  → 修复：检查目标函数中是否遗漏了新变量的项")

        return "OBJECTIVE_INCOMPLETE"

    # 检查4：目标函数定义一致性

    print("  诊断结果：约束正确、搜索充分、变量被利用, 但结果仍不改善")

    print("  → 建模有结构性问题, 需要回到 建模报告.md 重新设计")

    return "MODEL_STRUCTURAL_ISSUE"

```

诊断后的修复动作（不可跳过）：

- `CONSTRAINT_ERROR` → 调整约束代码, 重跑 Q(n)

- `SEARCH_INSUFFICIENT` → 用 Q(n-1) 的解作为种子, 增加搜索强度, 重跑 Q(n)

- `OBJECTIVE_INCOMPLETE` → 核验目标函数, 补充遗漏项, 重跑 Q(n)

- `MODEL_STRUCTURAL_ISSUE` → 在 计算结果.md 中标注"建模需修正", 不可硬凑结果

## 第四步：物理合理性原则

**关键原则**：物理/业务约束 > 数据忠实度 > 计算正确性

代码没有 bug、数据是题目给的 ≠ 结果就是对的。各个子问题跑完后务必问自己：

**"我的结果在题目描述的物理世界中是否可能发生？"**

⛔ **触发条件（与此同时满足才修正, 防止误杀）**：

1. 求解结果超出了题目清晰标明给定的物理边界（白纸黑字写的, 不是你猜的）

2. 超出幅度显著（不是边界附近的微小浮动, 而是明显不可能）

3. 你能解释为什么会超出（有具体的物理/数学缘由）

⛔ **不触发的情况（保持原始结果）**：

- 结果"看起来大"但题目没给清晰标明上限 → 不修正

- 结果在边界附近（如 59mm vs 60mm 上限）→ 不修正, 可能是正常极端工况

- 你不确定约束是否适用 → 不修正, 在论文中讨论

⛔ **按题型的红旗信号**：

| 题型 | 红旗信号 | 可能缘由 |

|------|---------|---------|

| 物理/工程 | 结果超出题目给定的物理极限 | 数据漂移/截断/模型缺约束 |

| 优化 | 最优解违反约束条件 | 约束未无误加入求解器 |

| 预测 | 预测值超出历史数据界限 5 倍以上 | 模型外推发散/趋势项过强 |

| 预测 | 远期预测单调发散（不收敛不震荡） | 模型不稳定/缺阻尼项 |

| 评价 | 权重之和 ≠ 1（误差 > 0.01） | 归一化环节遗漏 |

| 评价 | 全部方案得分差异 < 1%（无区分度） | 指标选取不当/权重过于均匀 |

| 评价 | 排名与题目暗示的常识严重矛盾 | 正负向指标处理反了 |

| 图论 | 路线长度/成本为负 | 负权边未处理/算法不适用 |

| 图论 | 流量不守恒（流入≠流出） | 模型遗漏节点或边 |

| 统计 | 回归系数方向与全部文献相反 | 变量编码错误/共线性 |

| 动力学 | 运行状态变量单调增长不收敛 | 开环积分漂移/缺反馈 |

⛔ **修正过程（触发后）**：

1. 登记原始结果（不移除, 论文中需对比阐明）

2. 分析超出缘由：数据截断？测量误差？净偏差累积？边界效应？模型假设不完整？

3. 选取最小修正方案（去漂移/加约束/补偿项）, 避免大改模型

4. 重新计算, 校验修正后结果在约束内

5. 在 计算结果.md 中写明：原始结果 → 为什么不合理 → 修正方法 → 修正后结果

6. ⛔ JSON 里只留存修正后的结果（原始结果写在 计算结果.md 的阐明文字里, 不写进 JSON）

⛔ **绝对禁止的行为**：发现结果超出物理约束后"解释缘由"但继续采用超出的结果。

解释缘由 ≠ 处理完毕。发现超出 → 务必修正 → 用修正后的值。

## 第五步：9 问背景复核（最关键）

查阅 问题分析.md（或 选题规划.md）和 计算结果.md, **结合本题的具体背景**逐项自检。

⛔ **复核时务必与此同时对照三个来源**：

1. 赛题原文（问题分析.md / 用户数据/*_extracted.txt）— 题目给的约束和背景

2. 建模报告（建模报告.md）— 此前设计的模型和预期行为

3. 真实结果（图表/全部结果.json）— 代码跑出来的数字

=== 合理性审查（结合题目背景）===

Q1. [数值量级] 每个结果的数值量级是否符合题目实际？

   举例：

   - 一个城市的年用电量应该是几亿度（10^8-10^9）, 不是几千度

   - 一辆货车的载重应该是几吨到几十吨, 不是几克或几千吨

   - 一个班级的学生数应该是 30-50 人, 不是 3 人或 500 人

   - 一天的时间应该是 24 小时内, 不是 200 小时

Q2. [符号方向] 结果的正负/大小方向是否符合直觉？

   举例：

   - 多给的资源应该让目标函数改善, 不是变差

   - 距离越近应该运输成本越低, 不是越高

   - 产品价格上升应该让需求下降（正常商品）

Q3. [约束边界] 结果是否在题目给定的物理/业务边界内？

   ⛔⛔⛔ Q3 判定规则（硬性, 不可变通）：

   - 结果在边界内 → ✅

   - 结果超出边界 → ❌（无论你是否"已讨论"、"已解释原因"）

   - "已在报告中讨论" ≠ ✅, 仍然是 ❌

   - "数学解超出物理范围" = ❌, 不是 ✅

   - 只要有任何一个结果超出题目明确给定的边界 → 整个 Q3 = ❌

   - Q3 = ❌ 时必须：修改代码加入物理约束 → 重跑 → 直到结果在边界内

   - ⛔ 禁止：标 ❌ 后写"但这是合理的因为XXX"然后继续 → 这不是通过

Q4. [结果分布] 多个结果之间的比例/差异是否合理？

Q5. [与赛题相同的场景数据] 如果赛题给了数据样本, 我的结果是否与之量级一致？

Q6. [物理/业务常识] 是否违反了常识性的物理/业务规律？

   - 物理：能量守恒、动量守恒、质量守恒

   - 经济：帕累托改进、边际递减

   - 统计：大数定律、中心极限

Q7. [子问题递进] 后续子问题的结果相对前面有明显变化？

   - 加约束了应该变差

   - 加资源了应该变好

   - 更换策略应该有方向性影响

Q8. [灵敏度合理] 灵敏度分析显示的敏感性是否合理？

   - 关键参数应该敏感

   - 无关参数应该不敏感

Q9. [与建模报告一致] 代码实现是否忠实于 建模报告.md？（⛔ 最关键的一条）

   自动化对照：

   ```bash

   echo "--- 算法对照 ---"

   echo "建模报告承诺的算法："

   grep -i '算法\|方法\|求解.*法\|采用.*法' 建模报告.md | head -10

   echo "代码中真实采用的算法/库："

   grep -rh 'from\|import\|minimize\|solve_ivp\|linprog\|genetic\|simulated' 程序/*.py 2>/dev/null | sort -u | head -15

   echo "--- 约束对照 ---"

   echo "建模报告列出的约束数量："

   grep -c '≤\|≥\|约束\|s\.t\.' 建模报告.md

   echo "代码中实现的约束数量："

   grep -rch 'constraint\|bounds\|<=\|>=' 程序/*.py 2>/dev/null | paste -sd+ | bc 2>/dev/null || echo "(手动检查)"

   echo "--- 参数对照 ---"

   echo "建模报告定义的关键参数："

   grep -oE '[A-Za-z_]+\s*[=:]\s*[0-9]+\.?[0-9]*' 建模报告.md | head -10

   echo "代码中的相应参数值："

   grep -rh '^[A-Z_]*\s*=' 程序/*.py 2>/dev/null | head -10

   ```

   ⛔ Q9 判定规则：

   - 算法被降级（如遗传算法→贪心）→ ❌

   - 约束被省略（建模报告有但代码没实现）→ ❌

   - 参数值不一致（建模报告 L=2.20 但代码 L=1.65）→ ❌

    - 以上任何一条 = ❌ = 必须修改代码重跑

对各个问题务必清晰标明回答 ✅（通过）、⚠️（需阐明）、❌（有问题）。

## 第六步：常见编程 Bug 排查（按题型选做）

```

=== 求解器/算法常见坑 ===

B1. [最大化vs最小化] scipy.optimize.minimize 是最小化器 — 如果要最大化, 目标函数是否取了负号？

B2. [初始值敏感] 优化结果是否依赖初始值？换一组初始值结果是否一致？（局部最优陷阱）

B3. [约束写反] 不等式约束方向是否正确？scipy 的 'ineq' 约束要求 f(x) >= 0

B4. [整数松弛] 用连续优化器解整数规划后, 是否做了取整？取整后是否仍然可行？

B5. [索引越界] 数组索引是否从 0 开始？矩阵维度是否匹配？

B6. [数据泄露] 测试集的数据是否参与了训练/归一化？（StandardScaler 必须只 fit 训练集）

B7. [随机种子] 是否设了 random seed？不同运行结果是否可复现？

=== 数据处理常见坑 ===

D1. [缺失值] 是否处理了 NaN/空值？pandas 的 mean() 默认跳过 NaN 但 numpy 不会

D2. [类型错误] 字符串列是否被当成数值参与了计算？（pandas 读 CSV 可能把数字列读成 str）

D3. [归一化时机] 归一化是在 train/test split 之前还是之后？（应该在之后, 只用训练集的统计量）

D4. [时间序列顺序] 时间序列数据是否按时间排序？是否有重复时间戳？

D5. [编码问题] 中文 CSV 是否用了正确的编码读取？（gbk/utf-8/gb2312）

=== 模型选择常见坑 ===

M1. [线性假设] 用线性回归拟合明显非线性的数据？（看残差图是否有弯曲模式）

M2. [样本不平衡] 分类问题中各类样本量是否严重不平衡？是否用了 class_weight 或过采样？

M3. [特征缩放] SVM/KNN/神经网络等距离敏感模型是否做了特征缩放？

M4. [时序交叉验证] 时间序列是否用了普通 k-fold？（应该用 TimeSeriesSplit）

M5. [多重比较] 做了多次假设检验是否做了 Bonferroni 校正？

```

## ⛔ 强制修复原则（不可跳过）

**检测到问题 = 务必修复。解释缘由 ≠ 处理完毕。当前环节不准许带着已知问题交付结果。**

无论是物理合理性核验、9 问背景复核、还是上面的自检项, 只要发现 ❌：

1. 务必立即调整代码 — 不可写"发现XXX问题, 但由于时间/复杂度缘由暂不处理"

2. 务必重新运行 — 调整后务必重跑代码校验修正有效, 不可只改代码不跑

3. 务必校验修正后结果合理 — 修正后的结果务必通过同理的核验

4. 务必在 计算结果.md 中登记 — 写明"原始结果X → 发现问题Y → 修正方法Z → 修正后结果W"

