# 编码阶段防错手册（按题型索引）

## 采用方式

编码启动前，查阅 建模报告.md 末尾的题型标注，随后查阅相应章节。

各个子问题代码写完后，对照"务必校验"条目按项核验。

---

## 一、优化类

### 务必校验

- [ ] `minimize` vs `maximize` 方向是否与建模报告保持一致（scipy 只有 minimize，最大化要取负）

- [ ] 全部约束是否都加入了求解器（逐条对照 建模报告.md 的约束列表）

- [ ] 不等式约束方向是否无误（scipy: `ineq` 要求 f(x)≥0，`eq` 要求 f(x)=0）

- [ ] 决策变量 bounds 是否设定（尤其是非负约束 x≥0）

- [ ] 整数变量是否做了取整？取整后是否仍可行？

- [ ] 多起点校验：换 3-5 组随机初始点，结果是否保持一致？（不一致阐明陷入局部最优）

- [ ] 求解器是否报告收敛？（核验 outcome.success / outcome.message）

- [ ] 最优解是否满足全部约束？（代入约束函数校验，不可只信求解器）

### 常见 Bug

```python

# ❌ 错误：忘记取负号

result = minimize(profit_function, x0)  # 应该是 minimize(lambda x: -profit_function(x), x0)

# ❌ 错误：约束方向写反

constraints = {'type': 'ineq', 'fun': lambda x: capacity - x[0]}  # 这是 capacity >= x[0]

# 如果要 x[0] >= min_val，应该写 lambda x: x[0] - min_val

# ❌ 错误：没设 bounds 导致出现负值

result = minimize(f, x0)  # 应该加 bounds=[(0, None)] * n

# ❌ 错误：整数松弛后不取整

x_opt = result.x  # x_opt = [2.7, 1.3] → 必须取整并验证可行性

```

### ⛔ 算法有效性校验（通用，务必通过）

```python

# ===== 建模与优化有效性检查（优化类必做）=====

# 1. 资源单调性检查

# 后续问题拥有更多决策资源时，结果必须严格更优

for i in range(1, len(problem_results)):

    if has_more_resources(i, i-1) and problem_results[i] <= problem_results[i-1]:

        print(f"⛔ 资源单调性违反: P{i+1}={problem_results[i]} ≤ P{i}={problem_results[i-1]}")

        print("  → 更多资源但结果未改善，建模降维失败，必须重新分解")

# 2. 解析基准下界对标

# 先用几何/贪心/物理推导得到一个可行解作为下界

baseline = compute_analytical_baseline(...)  # 几何解析/贪心/均匀分布

if optimized_result <= baseline:

    print(f"⛔ 优化解 {optimized_result} ≤ 解析基准 {baseline}")

    print("  → 算法失败，检查编码/约束/罚函数/初始化")

# 3. 搜索空间健康度（维度≥6时必做）

if n_dimensions >= 6:

    sample_points = generate_random_points(n=100, bounds=bounds)

    valid_ratio = sum(1 for x in sample_points if fitness(x) > trivial_fitness) / 100

    if valid_ratio < 0.3:

        print(f"⛔ 搜索空间过稀疏: 有效解比例 {valid_ratio:.0%} < 30%")

        print("  → 必须降维/分层/启发式播种后再优化")

# 4. 维度分层检查（维度≥10时必做）

if n_dimensions >= 10:

    print(f"⛔ 决策变量 {n_dimensions} 维 ≥ 10，禁止单层黑箱优化")

    print("  → 必须分层分解（每层≤6维），在建模报告中给出分层依据")

# 5. 离散取整可行性验证

if has_integer_variables:

    x_rounded = np.round(x_continuous)  # 或 np.floor/np.ceil

    for constraint_fn in all_constraints:

        if constraint_fn(x_rounded) < 0:

            print(f"⛔ 取整后约束违反: {constraint_fn.__name__}")

            print("  → 必须用修复启发式（贪心减少/邻域搜索），禁止使用不可行解")

# 6. 多目标归一化验证

if is_multi_objective:

    # 检查各目标的量级

    obj_magnitudes = [abs(obj_i(x)) for obj_i in objectives]

    if max(obj_magnitudes) / min(obj_magnitudes) > 100:

        print(f"⛔ 目标函数量级差异 > 100倍: {obj_magnitudes}")

        print("  → 必须先归一化到[0,1]再加权，否则小量级目标被淹没")

# 7. 步长收敛性验证（时间/空间离散化）

if uses_discretization:

    result_dt = solve(dt=dt)

    result_dt_half = solve(dt=dt/2)

    relative_change = abs(result_dt - result_dt_half) / abs(result_dt_half)

    if relative_change > 0.01:

        print(f"⛔ 步长未收敛: 减半后结果变化 {relative_change:.1%} > 1%")

        print("  → 必须继续减小步长直到变化<1%")

```

---

## 二、微分方程/动力学类

### 务必校验

- [ ] 物理约束是否在 ODE 中实现（事件检测 / 运行状态钳位 / 条件判定）

- [ ] 求解器选取是否合适（刚性系统用 `Radau`/`BDF`，非刚性用 `RK45`）

- [ ] 步长精度是否充足（rtol=1e-8, atol=1e-10 对物理问题）

- [ ] 守恒量是否守恒（计算前后能量/质量差异 < 0.1%）

- [ ] 结果是否在物理界限内（validate_constraints 务必调用）

- [ ] 长时间积分是否有漂移（核验最后时刻的运行状态是否合理）

### 常见 Bug

```python

# ❌ 错误：没有接触约束，位移超出物理极限

sol = solve_ivp(ode_func, t_span, y0)  # 结果可能 gap > 0.06m

# ✅ 正确：加入事件检测

def contact_event(t, y):

    return y[0]  # z_f = 0 时触发（接触轨道）

contact_event.terminal = True

contact_event.direction = -1

sol = solve_ivp(ode_func, t_span, y0, events=contact_event)

# ❌ 错误：刚性系统用 RK45

sol = solve_ivp(stiff_ode, t_span, y0, method='RK45')  # 极慢或发散

# ✅ 正确：

sol = solve_ivp(stiff_ode, t_span, y0, method='Radau')

```

---

## 三、统计/回归/预测类

### 务必校验

- [ ] 数据划分是否无误（时序按时间，非时序可随机但要设 random_state）

- [ ] 归一化/标准化是否只用训练集统计量（fit on train, transform on test）

- [ ] R² 是否合理（物理/工程 >0.8，社科 >0.3，<0.5 务必改进）

- [ ] 残差是否有模式（画残差图，不可有明显弯曲/扇形）

- [ ] 预测值是否在合理界限内（不可出现负价格、超100%概率等）

- [ ] 多重共线性是否处理（VIF>10 的变量需剔除或 PCA）

### 常见 Bug

```python

# ❌ 错误：数据泄露

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)  # 用了全部数据

X_train, X_test = train_test_split(X_scaled)

# ✅ 正确：

X_train, X_test = train_test_split(X)

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)

X_test = scaler.transform(X_test)  # 只 transform，不 fit

# ❌ 错误：时序用随机划分

X_train, X_test = train_test_split(df, test_size=0.2, shuffle=True)  # 未来预测过去！

# ✅ 正确：

split_idx = int(len(df) * 0.8)

train, test = df[:split_idx], df[split_idx:]

```

---

## 四、评价/决策类

### 务必校验

- [ ] 正负向指标处理是否无误（负向指标取倒数或 max-x）

- [ ] 权重之和是否精确等于1（abs(sum(w) - 1) < 0.001）

- [ ] AHP 一致性比率 CR < 0.1

- [ ] 终版得分是否有区分度（最大-最小 > 5%）

- [ ] 排名是否符合常识（明显好的方案排名应靠前）

### 常见 Bug

```python

# ❌ 错误：负向指标没处理

scores = w1 * cost + w2 * quality  # cost 越大越差，不能直接加权！

# ✅ 正确：

scores = w1 * (1 / cost) + w2 * quality  # 或 w1 * (max_cost - cost)

# ❌ 错误：权重不归一

weights = [0.3, 0.3, 0.3]  # sum = 0.9 ≠ 1

```

---

## 五、图论/网络流类

### 务必校验

- [ ] 图的构建是否无误（节点数、边数与题目保持一致）

- [ ] 有向/无向是否无误

- [ ] 负权边是否出现？出现则不可用 Dijkstra

- [ ] 网络流的流量守恒是否满足（各个中间节点：流入=流出）

- [ ] 最短路/最大流结果是否合理（不可为负、不可超过容量）

### 常见 Bug

```python

# ❌ 错误：有负权边用 Dijkstra

dist = dijkstra(graph, source)  # 负权边会导致错误结果

# ✅ 正确：

dist = bellman_ford(graph, source)

# ❌ 错误：忘记加反向边（最大流）

graph.add_edge(u, v, capacity=c)

# ✅ 正确：

graph.add_edge(u, v, capacity=c)

graph.add_edge(v, u, capacity=0)  # 反向边容量为0

```

---

## 六、几何/空间优化类

### 务必校验

- [ ] 碰撞检测用完整外轮廓（不是中心点距离）

- [ ] 物理参数与 建模报告.md 保持一致（逐个对照数值）

- [ ] 坐标系统一（全局坐标，不混用局部坐标）

- [ ] 角度单位统一（全部弧度或全部角度，不混用）

- [ ] 场地边界约束是否加入（物体不可超出边界）

- [ ] 旋转后的碰撞检测是否无误（用 OBB/SAT，不可用 AABB）

### 常见 Bug

```python

# ❌ 错误：用中心距代替实体碰撞

def no_collision(a, b):

    return distance(a.center, b.center) > threshold  # 忽略了实体尺寸！

# ✅ 正确：用分离轴定理（SAT）

def no_collision(rect_a, rect_b):

    """SAT 碰撞检测，使用完整矩形四角坐标。"""

    # 获取两个矩形的所有边的法向量作为分离轴

    ...

# ❌ 错误：弧度角度混用

angle = 90  # 角度

x = r * np.cos(angle)  # np.cos 需要弧度！结果完全错误

# ✅ 正确：

x = r * np.cos(np.radians(angle))

# ❌ 错误：遮蔽/覆盖判定降维为中心点

def is_occluded(smoke_center, missile_pos, target_center):

    """只检查导弹→目标中心的视线被遮蔽 — 错误！"""

    dist = point_to_line_distance(smoke_center, missile_pos, target_center)

    return dist <= smoke_radius  # 只判断了一个点！

# ✅ 正确：对目标完整几何边界做判定

def is_fully_occluded(smoke_center, smoke_radius, missile_pos,

                     target_base_center, target_radius, target_height, N=300):

    """

    圆柱体完全遮蔽判定。

    几何参数来源：建模报告.md 符号说明表

    判定对象：圆柱体上下底面圆周上的 N 个离散点

    等价性依据：[如果有证明 "底面圆周被遮蔽⟹整体被遮蔽"，在此说明]

    """

    for z in [0, target_height]:  # 上下两个底面

        center = target_base_center + np.array([0, 0, z])

        for i in range(N):

            theta = 2 * np.pi * i / N

            point = center + target_radius * np.array([np.cos(theta), np.sin(theta), 0])

            dist = point_to_line_distance(smoke_center, missile_pos, point)

            if dist > smoke_radius:

                return False

    return True

# ⛔ 收敛性验证（必做）

# 用 N=100, 300, 500 分别跑，结果差异 < 1% 才算采样充足

for N in [100, 300, 500]:

    result = is_fully_occluded(..., N=N)

    print(f"N={N}: {result}")

```

---

## 通用校验（全部题型必做）

1. **参数一致性**：代码中的各个物理参数值务必与 建模报告.md 完全一致

2. **单位一致性**：核验全部计算中单位是否统一（不可混用 m/cm/mm）

3. **边界情况**：输入为 0、最大值、边界值时代码是否正常运行

4. **结果可复现**：设定 random seed，多次运行结果保持一致

5. **JSON 交付完整**：各个子问题的关键结果都留存到 JSON，供 evidence-visualization 查阅

