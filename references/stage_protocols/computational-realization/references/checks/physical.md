# 物理/几何类自检（碰撞检测/动力学/ODE/SAT 必读）

## 红旗信号

| 现象 | 可能缘由 |

|------|---------|

| 运行状态变量单调增长不收敛 | 开环积分漂移 / 缺反馈 |

| ODE 求解结果发散 | 步长太大 / 缺阻尼 / 模型不稳定 |

| 碰撞检测从不触发 | SAT 写错 / 用了中心距代替轮廓距 |

| 间隙值出现负数 | 接触约束未加 / 已经穿模 |

| 能量/动量不守恒（孤立系统） | 数值积分误差累积 / 模型缺项 |

## 几何参数引用准则（最高优先级）

代码中涉及碰撞检测、约束校验、目标函数计算时：

**务必采用 建模报告.md 中定义的完整物理参数**（如板凳全长220cm、矩形宽30cm、车身长4.5m）,

**禁止直接复用上游环节为其他目的计算的中间量**（如孔中心距165cm、把手坐标间距、质心偏移量）作为物理实体的几何代理。

**典型错误示例**：

- 板凳碰撞检测用"孔中心距165cm"代替"板凳全长220cm" → 错误（少算了两端各27.5cm）

- 矩形放置约束用"中心坐标差"代替"边缘到边缘距离" → 错误（忽略了物体宽度）

- 车辆避障用"质心距离"代替"车身外轮廓最近点距离" → 错误（可能已经碰撞）

**无误做法**：

```python

# ⛔ 物理参数定义（来源：建模报告.md 第X节）

BENCH_TOTAL_LENGTH = 2.20  # 板凳全长 220cm（题目原文）

BENCH_WIDTH = 0.30          # 板凳宽度 30cm（题目原文）

def verify_collision(bench_a, bench_b):

    """检测两个板凳是否碰撞。

    物理参数来源：建模报告.md 符号说明表

    - 板凳全长: BENCH_TOTAL_LENGTH = 2.20m

    - 板凳宽度: BENCH_WIDTH = 0.30m

    使用完整外轮廓（矩形四角）判断, 非中心点距离。

    """

    # 使用完整矩形碰撞检测（SAT 分离轴定理）

    ...

```

## SAT 碰撞检测自检

若用了 SAT（分离轴定理）：

```python

# 验证 SAT 实现是否正确

def sat_collide(rect_a, rect_b):

    """rect_a, rect_b: 各自 4 个角点的 (x,y) 列表（顺时针或逆时针, 一致即可）"""

    axes = []

    for poly in (rect_a, rect_b):

        for i in range(len(poly)):

            edge = (poly[(i+1)%len(poly)][0]-poly[i][0], poly[(i+1)%len(poly)][1]-poly[i][1])

            normal = (-edge[1], edge[0])  # 法向量

            length = (normal[0]**2 + normal[1]**2)**0.5

            axes.append((normal[0]/length, normal[1]/length))

    for axis in axes:

        proj_a = [p[0]*axis[0] + p[1]*axis[1] for p in rect_a]

        proj_b = [p[0]*axis[0] + p[1]*axis[1] for p in rect_b]

        if max(proj_a) < min(proj_b) or max(proj_b) < min(proj_a):

            return False  # 找到分离轴, 不碰撞

    return True  # 所有轴都重叠, 碰撞

```

⛔ **SAT 自检 unit test**：

```python

# 必跑这 3 组测试再投入使用

# 1) 不重叠

assert sat_collide(

    [(0,0),(1,0),(1,1),(0,1)],

    [(2,0),(3,0),(3,1),(2,1)]

) == False

# 2) 部分重叠

assert sat_collide(

    [(0,0),(2,0),(2,1),(0,1)],

    [(1,0.5),(3,0.5),(3,1.5),(1,1.5)]

) == True

# 3) 旋转

assert sat_collide(

    [(0,0),(1,0),(1,1),(0,1)],

    [(1.5,0.5),(2.5,1.5),(1.5,2.5),(0.5,1.5)]  # 45° 菱形

) == False

print("✅ SAT 自检通过")

```

## ODE / 动力学

### 数值积分参数

⛔ 建模报告说"自适应步长 rtol=1e-8" → 代码务必用 `solve_ivp(..., rtol=1e-8, atol=1e-10)`,

不可改成固定步长 `dt=0.1`（精度严重下降）。

### 漂移检测

```python

# 长时间积分必做 — 检查是否漂移

import numpy as np

def verify_drift(t, state, expected_bound):

    """检查 state 是否在物理上合理的有界范围内"""

    if np.any(np.abs(state) > expected_bound):

        # 找到首次超出

        i = np.argmax(np.abs(state) > expected_bound)

        print(f"⚠ 状态在 t={t[i]:.3f}s 时超出预期边界 {expected_bound}")

        return False

    return True

```

### 守恒量校验

孤立系统应满足能量/动量守恒, 偏差超过 1% 阐明数值有问题：

```python

# 能量守恒

E0 = compute_energy(state[0])

E_final = compute_energy(state[-1])

drift_pct = abs(E_final - E0) / abs(E0) * 100

if drift_pct > 1:

    print(f"⚠ 能量漂移 {drift_pct:.2f}% > 1% — 减小步长或换更高阶积分器")

```

## 接触约束 / 饱和限幅

物理实体（弹簧、阻尼、质量块）务必有接触约束, 不可让位移穿过实体边界：

```python

# 在每步积分后施加约束

def apply_contact_constraint(state, gap_min=0, gap_max=0.06):

    state['gap'] = np.clip(state['gap'], gap_min, gap_max)

    if state['gap'] == gap_min and state['velocity'] < 0:

        state['velocity'] = 0  # 接触瞬间速度归零（弹性: 反向; 塑性: 归零）

    return state

```

## 必产数据

```json

{

  "model": "ODE / RK4 / solve_ivp",

  "rtol": 1e-8,

  "atol": 1e-10,

  "duration_s": 100,

  "drift_pct": 0.5,

  "energy_conservation_pct": 0.3,

  "constraints_active": ["gap_lower_bound", "velocity_saturation"],

  "max_gap": 0.058,

  "max_velocity": 3.2

}

```

