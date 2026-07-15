# Advanced Visual Recipes — Clean Academic Edition

High-impact, SCI-quality visual types with clean, publication-ready styling.

Every recipe features: solid colors, single-layer semi-transparent fills, annotation boxes,

subtle grids (alpha=0.15), and minimal decoration. Titles are handled by LaTeX captions.

> **配色标准**: 全部配方统一采用 `PALETTE[n]`（主色系列）或 `COLORS['xxx']`（语义色，如 `_lighten()` 浅色填充）。禁止硬编码 hex 色值。

> **标题规范**: 所有配方不使用 `set_title()`，而由 LaTeX `\caption{}` 处理。

> **格式标准**: 统一去掉 top/right spines；标注框统一用 `bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=..., alpha=0.9)`。

> **曲线原则**: 不采用多段拟合模拟（n_seg=30/40/50/60/80），而用简单的 `plot()`/`hlines()`/`fill_between()`。

---

## 1. Lollipop Chart — 棒棒糖图（渐变色茎 + 排名徽章 + 中位数参考线）

**场景**: 按单一指标对方法/方案排名。比柱状图更简洁，常见于 Nature/Science。

**防重叠**: 采用 `smart_labels()` 自动化推开重叠的数值标签。

**风格**: 渐变色从紫罗兰（高分）过渡到珊瑚橙（低分）；线粗、圆点大小也随分数渐变。前三名有排名徽章。中位数参考线分割图面。

**⚠ 关键要点**: 茎线从 x=0 启动；颜色按 HSL 明度线性渐变（避免相邻项同色）；前三名实心圆徽章。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels

setup_style()

import matplotlib.pyplot as plt

import matplotlib.colors as mc

import numpy as np

import colorsys

methods = ['Ours', 'Baseline-A', 'Baseline-B', 'Baseline-C', 'Baseline-D']

scores = [0.923, 0.887, 0.862, 0.841, 0.815]

n = len(methods)

score_min, score_max = min(scores), max(scores)

score_range = score_max - score_min if score_max > score_min else 1

# ── 渐变配色：从紫罗兰 → 珊瑚橙（明度和色相同时渐变）

color_top = '#7B6BA5'     # 紫罗兰（高分，偏冷一点）

color_bottom = '#E08B74'  # 珊瑚橙（低分，偏暖）

def interpolate_color(c1, c2, t):

    """HSL 空间插值：t=0 返回 c1，t=1 返回 c2"""

    r1, g1, b1 = mc.to_rgb(c1)

    r2, g2, b2 = mc.to_rgb(c2)

    h1, l1, s1 = colorsys.rgb_to_hls(r1, g1, b1)

    h2, l2, s2 = colorsys.rgb_to_hls(r2, g2, b2)

    if abs(h2 - h1) > 0.5:

        if h1 < h2: h1 += 1.0

        else: h2 += 1.0

    h = (h1 + (h2 - h1) * t) % 1.0

    l = l1 + (l2 - l1) * t

    s = s1 + (s2 - s1) * t

    return colorsys.hls_to_rgb(h, l, s)

item_colors = [interpolate_color(color_top, color_bottom, i / (n - 1) if n > 1 else 0) for i in range(n)]

# ── 自适应高度（每项 0.46 高度 + 上下留白）

_fig_h = max(4, n * 0.46 + 1.8)

fig, ax = plt.subplots(figsize=(7.5, _fig_h))

y_pos = np.arange(n)

# 极浅网格线

ax.grid(axis='x', alpha=0.12, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# 中位数参考线（置于底层）

median_val = np.median(scores)

ax.axvline(median_val, color=COLORS['ref_line'], linestyle=':', linewidth=1.0, alpha=0.5, zorder=1)

# ── 主体：渐变色茎线 + 渐变圆点

for i, (m, s) in enumerate(zip(methods, scores)):

    c = item_colors[i]

    ratio = (s - score_min) / score_range

    lw = 1.6 + 2.0 * ratio

    # 茎线从 0 开始

    ax.plot([0, s], [y_pos[i], y_pos[i]],

            color=c, linewidth=lw, zorder=3, solid_capstyle='round')

    # 端点圆点 —— 大小随分数渐变

    dot_size = 55 + 120 * ratio

    ax.scatter(s, y_pos[i], color=c, s=dot_size, zorder=5,

               edgecolors='white', linewidths=1.8)

    # 数值标签

    ax.text(s + score_range * 0.03, y_pos[i], f'{s:.3f}',

            fontsize=8.5, fontweight='bold' if i < 3 else 'normal',

            color=c, va='center', ha='left')

    # ── 排名徽章区域

    badge_x = -score_range * 0.065

    rank = i + 1

    if rank <= 3:

        badge = plt.Circle((badge_x, y_pos[i]), 0.3,

                            color=_lighten(c, 0.15), zorder=6,

                            transform=ax.transData)

        ax.add_patch(badge)

        ax.text(badge_x, y_pos[i], str(rank),

                fontsize=8.5, fontweight='bold', color='white',

                ha='center', va='center', zorder=7)

    else:

        ax.text(badge_x, y_pos[i], str(rank),

                fontsize=7.5, color=_lighten(c, 0.2),

                ha='center', va='center', fontweight='bold')

# 第一名背景高亮条

ax.axhspan(y_pos[0] - 0.42, y_pos[0] + 0.42, alpha=0.06,

           color=item_colors[0], zorder=0)

# 中位数标注 —— 置于图的顶部

ax.text(median_val, -0.9, f'中位数 {median_val:.3f}',

        fontsize=8, color=COLORS['ref_line'], ha='center', va='bottom',

        bbox=dict(boxstyle='round,pad=0.25', facecolor='white',

                  edgecolor=COLORS['ref_line'], alpha=0.85))

ax.set_yticks(y_pos)

ax.set_yticklabels(methods, fontsize=10)

ax.set_xlabel('F1 Score', fontsize=11)

ax.set_xlim(-score_range * 0.13, score_max + score_range * 0.15)

ax.set_ylim(n - 0.5, -1.4)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_lollipop')

```

**⚠ 易踩的坑（棒棒糖图专用）：**

```python

# 1. ylim 上方留空：ax.set_ylim(n-0.5, -1.4)，给中位数标注留空间

# 2. xlim 右侧留余量（score_max + score_range*0.15），给数值标签留空间

# 3. xlim 左侧留负值（-score_range*0.13），给排名徽章留空间

# 4. 数值标签偏移用相对值（score_range*0.03），不要用固定像素偏移

# 5. 排名徽章用 plt.Circle + transData，确保圆形不变形

# 6. 中位数标注放在 y=-0.9（图面上方），需要配合上方留空设置

# 7. 当条目数 >15 时，_fig_h 公式自动增高（每项 0.46 高度不会挤压）

```

---

## 2. Dumbbell Chart — 哑铃图（连接线 + 变化率 + 显著性标记）

**场景**: 前后对比、两组差异。比分组柱状图更直观。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import numpy as np

metrics = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']

before = [0.82, 0.79, 0.85, 0.81, 0.88]

after = [0.91, 0.88, 0.90, 0.89, 0.94]

# ── 自适应高度

_fig_h = max(3.5, len(metrics) * 0.7 + 1)

fig, ax = plt.subplots(figsize=(8, _fig_h))

y = np.arange(len(metrics))

# Subtle grid

ax.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# Simple connector lines + arrow heads

for i in range(len(metrics)):

    delta = after[i] - before[i]

    pct_change = delta / before[i] * 100

    # Simple connector line

    ax.plot([before[i], after[i]], [y[i], y[i]],

            color=PALETTE[2], linewidth=2.0, solid_capstyle='round')

    # Arrow head at the "after" end

    ax.annotate('', xy=(after[i], y[i]), xytext=(after[i] - 0.012, y[i]),

                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=2.0))

    # Before / After dots

    ax.scatter(before[i], y[i], color=PALETTE[3], s=80, zorder=3,

               edgecolors='white', linewidths=1.0, label='Before' if i == 0 else '')

    ax.scatter(after[i], y[i], color=PALETTE[0], s=80, zorder=3,

               edgecolors='white', linewidths=1.0, label='After' if i == 0 else '')

    # % change label

    ax.text(after[i] + 0.015, y[i] - 0.15, f'+{delta:.2f} ({pct_change:+.1f}%)',

            va='center', fontsize=8, color=PALETTE[0], fontweight='bold')

    # Significance marker (stars)

    if pct_change > 8:

        sig = '***'

    elif pct_change > 5:

        sig = '**'

    else:

        sig = '*'

    ax.text(after[i] + 0.015, y[i] + 0.2, sig, va='center', fontsize=9,

            color=COLORS['down'], fontweight='bold')

ax.set_yticks(y)

ax.set_yticklabels(metrics, fontsize=10)

ax.set_xlabel('Score', fontsize=11)

ax.legend(loc='lower right', frameon=True, edgecolor=COLORS['grid'], fontsize=9,

          fancybox=True, shadow=False)

ax.invert_yaxis()

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_dumbbell')

```

**⚠ 易踩的坑（哑铃图专用）：**

```python

# 1. % change 标签和星号分两行（y 偏移 -0.15 和 +0.2），不要放在一行

# 2. xlim 右侧留 15% 余量，给 % change 标签和星号留空间

# 3. 当 before/after 值很接近（差 <0.02）时，标签会重叠 → 只标注 after 值

# 4. 图例放 lower right（因为通常数据在上方，不会遮挡）

```

---

## 3. Slope Chart — 斜率图（颜色编码线 + 排名变化标注）

**场景**: 跨条件的排名/趋势变化。比分组柱状图更清晰地展示交叉变化。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import numpy as np

methods = ['Method-A', 'Method-B', 'Method-C', 'Method-D']

dataset1 = [0.92, 0.88, 0.85, 0.90]

dataset2 = [0.87, 0.91, 0.89, 0.86]

fig, ax = plt.subplots(figsize=(6, 5.5))

# Subtle grid

ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# Compute ranks

rank1 = list(np.argsort(np.argsort([-v for v in dataset1])) + 1)

rank2 = list(np.argsort(np.argsort([-v for v in dataset2])) + 1)

for i, m in enumerate(methods):

    diff = dataset2[i] - dataset1[i]

    # Green = improve, Red = decline

    base_color = COLORS['up'] if diff >= 0 else COLORS['down']

    # Simple line connecting two points

    ax.plot([0, 1], [dataset1[i], dataset2[i]], color=base_color,

            linewidth=2.5, solid_capstyle='round')

    # Endpoints

    ax.scatter([0], [dataset1[i]], color=base_color, s=90, zorder=5,

               edgecolors='white', linewidths=1.2)

    ax.scatter([1], [dataset2[i]], color=base_color, s=90, zorder=5,

               edgecolors='white', linewidths=1.2)

    # Value labels

    ax.text(-0.08, dataset1[i], f'{dataset1[i]:.2f}', ha='right', va='center',

            fontsize=9, color=base_color)

    ax.text(1.08, dataset2[i], f'{dataset2[i]:.2f}', ha='left', va='center',

            fontsize=9, color=base_color)

    # Rank change annotation

    rank_delta = rank1[i] - rank2[i]  # positive = improved rank

    if rank_delta != 0:

        arrow_sym = '↑' if rank_delta > 0 else '↓'

        rank_color = COLORS['up'] if rank_delta > 0 else COLORS['down']

        ax.text(1.22, dataset2[i], f'{m} {arrow_sym}{abs(rank_delta)}',

                ha='left', va='center', fontsize=8, color=rank_color,

                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=rank_color, alpha=0.9))

    else:

        ax.text(1.22, dataset2[i], f'{m} →', ha='left', va='center',

                fontsize=8, color=COLORS['ref_line'])

ax.set_xticks([0, 1])

ax.set_xticklabels(['Dataset-1', 'Dataset-2'], fontsize=11)

ax.set_xlim(-0.35, 1.65)

ax.set_ylim(min(dataset1 + dataset2) - 0.03, max(dataset1 + dataset2) + 0.03)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.spines['bottom'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_slope')

```

**⚠ 易踩的坑（Slope Chart 专用）：**

```python

# 1. 当多条数值标签重叠时，只标注变化最大的 2-3 条线，其余省略

# 2. 右侧排名变化标注用 bbox 白底，防止与数值标签混在一起

# 3. xlim 左侧留 0.35，给标签留空间（ax.set_xlim(-0.35, 1.65)）

# 4. 值域较窄（如数值在 0.85-0.92 之间）时，ylim 不要从 0 开始，放大差异

```

---

## 4. Bump Chart — 凹凸图（色带高亮 + 两端排名标签 + "本文"高亮）

**场景**: 跟踪跨数据集/指标的排名变化。比表格更直观。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS

setup_style()

import matplotlib.pyplot as plt

import numpy as np

methods = ['Ours', 'BERT', 'GPT', 'RoBERTa']

datasets = ['MNLI', 'QQP', 'SST-2', 'QNLI']

ranks = [[1, 1, 2, 1], [3, 2, 1, 3], [2, 3, 3, 2], [4, 4, 4, 4]]

fig, ax = plt.subplots(figsize=(8, 5))

x = np.arange(len(datasets))

# Subtle grid

ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

for i, (m, r) in enumerate(zip(methods, ranks)):

    is_ours = (i == 0)

    lw = 3.5 if is_ours else 1.8

    alpha_line = 1.0 if is_ours else 0.55

    ms = 14 if is_ours else 9

    # Gradient ribbon for "Ours"

    if is_ours:

        for k in range(len(x) - 1):

            x_fill = np.linspace(x[k], x[k + 1], 50)

            y_fill = np.interp(x_fill, x, r)

            ax.fill_between(x_fill, y_fill - 0.15, y_fill + 0.15,

                            alpha=0.15, color=PALETTE[0])

    # Line

    ax.plot(x, r, 'o-', color=PALETTE[i], linewidth=lw, markersize=ms,

            label=m, zorder=3 + (1 if is_ours else 0), alpha=alpha_line,

            markeredgecolor='white', markeredgewidth=1.5 if is_ours else 0.8)

    # Rank labels at both ends

    ax.text(x[0] - 0.2, r[0], f'#{r[0]} {m}', va='center', ha='right',

            fontsize=9, color=PALETTE[i],

            fontweight='bold' if is_ours else 'normal')

    ax.text(x[-1] + 0.2, r[-1], f'#{r[-1]} {m}', va='center', ha='left',

            fontsize=9, color=PALETTE[i],

            fontweight='bold' if is_ours else 'normal')

# Highlight box for "Ours"

ax.annotate('★ Ours: Rank #1 in 3/4 datasets',

            xy=(x[0], ranks[0][0]), xytext=(x[0] + 0.5, ranks[0][0] - 0.6),

            fontsize=8.5, color=PALETTE[0], fontweight='bold',

            arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=1.2),

            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',

                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xticks(x)

ax.set_xticklabels(datasets, fontsize=10)

ax.set_yticks([1, 2, 3, 4])

ax.set_yticklabels(['1st', '2nd', '3rd', '4th'], fontsize=10)

ax.set_ylabel('Rank', fontsize=11)

ax.invert_yaxis()

ax.set_xlim(-0.6, len(datasets) - 0.4)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_bump')

```

**⚠ 易踩的坑（Bump Chart 专用）：**

```python

# 1. 两端排名标签用 ha='right'/ha='left'，不要用 ha='center'（会与线重叠）

# 2. xlim 左侧留 0.6，给两端标签留空间

# 3. 高亮标注不要与排名标签重叠：xytext 偏移至少 0.5 个单位

# 4. 方法数 >6 时，只标注首尾两端，省略中间（减少图面杂乱）

```

---

## 5. Sankey Diagram — 桑基图（流量守恒 + 多节点连接）

**场景**: 数据流向、分类结果路由、用户行为路线、能量流。采用 `matplotlib.sankey.Sankey` 实现多节点连接的流量守恒。

```python

import shutil, os

os.makedirs('工具', exist_ok=True)

for f in ['plot_utils.py', 'china_provinces.geojson']:

    src = os.path.join(os.path.dirname(__file__), f)

    if os.path.exists(src):

        shutil.copy2(src, f'工具/{f}')

import numpy as np

import matplotlib.pyplot as plt

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

from matplotlib.sankey import Sankey

fig, ax = plt.subplots(figsize=(10, 6))

ax.set_axis_off()

# ── 用 matplotlib.sankey.Sankey 画 多节点流量守恒 Sankey 图

# ── 关键：每组 flows 之和必须为 0（流量守恒）；正值=流入，负值=流出

sankey = Sankey(ax=ax, scale=0.008, offset=0.25, head_angle=120,

                shoulder=0.03, gap=0.15, radius=0.08,

                unit='', format='%.0f')

# 第一个节点：原始数据 → 训练集/测试集/验证集

sankey.add(flows=[1000, -600, -300, -100],

           labels=['原始数据\n(1000)', '训练集\n(600)', '测试集\n(300)', '验证集\n(100)'],

           orientations=[0, 0, -1, 1],

           pathlengths=[0.3, 0.6, 0.3, 0.3],

           facecolor=_lighten(PALETTE[0], 0.4),

           edgecolor=PALETTE[0],

           linewidth=1.2)

# 第二个节点：训练集 → 正确分类/误分类

sankey.add(flows=[600, -540, -60],

           labels=[None, '正确\n(540)', '误分类\n(60)'],

           orientations=[0, 0, -1],

           pathlengths=[0.2, 0.5, 0.3],

           prior=0, connect=(1, 0),

           facecolor=_lighten(PALETTE[2], 0.4),

           edgecolor=PALETTE[2],

           linewidth=1.2)

# 第三个节点：测试集 → 全部通过

sankey.add(flows=[300, -300],

           labels=[None, '通过\n(300)'],

           orientations=[0, 0],

           pathlengths=[0.2, 0.5],

           prior=0, connect=(2, 0),

           facecolor=_lighten(PALETTE[1], 0.4),

           edgecolor=PALETTE[1],

           linewidth=1.2)

diagrams = sankey.finish()

# 给每个节点文字加样式

for d in diagrams:

    for text in d.texts:

        text.set_fontsize(9)

        text.set_fontweight('bold')

        text.set_color(COLORS['text'])

fig.tight_layout()

save_fig(fig, '图表/fig_sankey')

```

**⚠ 易踩的坑（Sankey Diagram 专用）：**

```python

# 1. 流量 % 标签如果在中间偏上，需要检查文本边缘是否会被其他节点遮挡

# 2. 节点标签用白色填充：确保在彩色节点上可读

# 3. 流太细（<3% 占比）时，省略 % 标签，只保留节点标签

# 4. 节点太多时，增大 x 方向间距（将所有流的 x 间距 ≥ 0.3）

```

⚠ 关键：每组 flows 之和务必为 0（流量守恒）；正值=流入，负值=流出

---

## 6. Waterfall Chart — 瀑布图（彩色渐变柱图 + 连接线 + 顶部数值标注）

**场景**: 因素分解、消融贡献分析。比柱状图更适合展示增量贡献。

**风格**: 彩色层叠（每步增量形成一层从当前步延伸到右边的色带层）+ 阶梯连线 + 圆点 + 数值标注统一在上方 + 贡献信息图例。比传统瀑布图（仅柱+连线）多了"层叠"视觉隐喻。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.patches as mpatches

import numpy as np

labels = ['Baseline', '+Attention', '+Augment', '+Pretrain', '-Dropout']

deltas = [0.82,        0.04,          0.02,       0.05,       -0.01]

cum = [deltas[0]]

for d in deltas[1:]:

    cum.append(cum[-1] + d)

final_val = cum[-1]

total_delta = final_val - deltas[0]

layer_colors = [COLORS['up'] if d >= 0 else COLORS['down'] for d in deltas[1:]]

n = len(labels)

fig, ax = plt.subplots(figsize=(9, 5))

ax.grid(axis='y', alpha=0.12, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

x_positions = np.arange(n)

# ── 色带层叠（每步增量的层带位置，延伸到最右边）

for i in range(1, n):

    c = layer_colors[i - 1]

    bottom = min(cum[i-1], cum[i])

    top = max(cum[i-1], cum[i])

    ax.fill_between([x_positions[i] - 0.5, x_positions[-1] + 0.5], bottom, top,

                    alpha=0.15, color=c, zorder=1 + i)

    ax.plot([x_positions[i] - 0.5, x_positions[-1] + 0.5], [cum[i], cum[i]],

            color=c, linewidth=0.7, linestyle='--', alpha=0.35, zorder=1 + i)

# Baseline 底层

ax.fill_between([x_positions[0] - 0.5, x_positions[-1] + 0.5], 0, cum[0],

                alpha=0.06, color=PALETTE[0], zorder=0)

# ── 阶梯连线

ax.step(x_positions, cum, where='mid', color=PALETTE[0], linewidth=2.8, zorder=10)

# ── 圆点

for i in range(n):

    c = PALETTE[0] if i == 0 else layer_colors[i - 1]

    ax.scatter(x_positions[i], cum[i], color=c, s=90, zorder=11,

               edgecolors='white', linewidths=2.0)

# ── 数值标注 —— 所有步骤都标，统一放在圆点上方

for i in range(n):

    c = PALETTE[0] if i == 0 else layer_colors[i - 1]

    ax.text(x_positions[i], cum[i] + 0.008, f'{cum[i]:.3f}', ha='center', va='bottom',

            fontsize=8.5, fontweight='bold' if (i == 0 or i == n-1) else 'normal',

            color=c,

            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',

                      edgecolor=c if (i == 0 or i == n-1) else 'none',

                      alpha=0.9, linewidth=0.5), zorder=12)

# ── 总增量标注（右上角）

ax.text(0.97, 0.95, f'Total: +{total_delta:.2f} (+{total_delta/deltas[0]*100:.1f}%)',

        transform=ax.transAxes, fontsize=9.5, ha='right', va='top',

        fontweight='bold', color=COLORS['up'],

        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',

                  edgecolor=COLORS['up'], alpha=0.9, linewidth=1.0), zorder=15)

# ── 贡献图例（将贡献信息全部放在图例，而非图面上标）

legend_patches = []

for i in range(1, n):

    d = deltas[i]

    c = layer_colors[i - 1]

    sign = '+' if d >= 0 else ''

    pct = abs(d) / total_delta * 100

    patch = mpatches.Patch(facecolor=_lighten(c, 0.4), edgecolor=c, linewidth=1.2,

                           label=f'{labels[i]}  {sign}{d:.2f} ({pct:.0f}%)')

    legend_patches.append(patch)

legend = ax.legend(handles=legend_patches, loc='lower right',

                   frameon=True, edgecolor=COLORS['grid'], fontsize=8.5,

                   facecolor='white', title='Contribution', title_fontsize=9,

                   handlelength=1.5, handleheight=1.0)

legend.set_zorder(15)

ax.set_xticks(x_positions)

ax.set_xticklabels(labels, fontsize=10)

ax.set_ylabel('Accuracy', fontsize=11)

ax.set_xlim(-0.7, n - 0.3)

ax.set_ylim(deltas[0] * 0.92, final_val * 1.12)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_waterfall')

```

**⚠ 易踩的坑（彩色层叠瀑布图专用）：**

```python

# 1. 数值标注统一在圆点上方（va='bottom'），不要放在下方（色带层叠在下方会遮挡）

# 2. 首尾端点有边框 bbox，中间步骤无边框白底（视觉层次分明）

# 3. 贡献信息放图例而非图面：避免色带中间的标注和阶梯线重叠

# 4. ylim 上方留 12%，给最高点的标注留空间

# 5. 总增量标注用 transform=ax.transAxes 固定在右上角，不受数据范围影响

# 6. 色带 alpha=0.15：太深会让标注不清楚，太浅没有层次感

```

---

## 7. SHAP Summary Plot — SHAP 特征关键性图

**场景**: 特征对模型预测的影响。比普通特征关键性柱状图更丰富——与此同时展示方向和幅度。

**风格**: 浅色填充+原色边框 bars 用于关键性面板，coolwarm beeswarm 用于 SHAP 面板。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.gridspec as gridspec

import numpy as np

np.random.seed(42)

features = ['Feature A', 'Feature B', 'Feature C', 'Feature D', 'Feature E']

n_samples = 200

fig = plt.figure(figsize=(9, 5))

gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], wspace=0.05)

# Left panel: SHAP beeswarm

ax_shap = fig.add_subplot(gs[0])

ax_shap.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])

ax_shap.set_axisbelow(True)

mean_abs_shap = []

for i, feat in enumerate(features):

    shap_vals = np.random.randn(n_samples) * (len(features) - i) * 0.12

    feat_vals = np.random.rand(n_samples)

    y_jitter = np.random.uniform(-0.3, 0.3, n_samples) + i

    sc = ax_shap.scatter(shap_vals, y_jitter, c=feat_vals, cmap='coolwarm',

                         s=10, alpha=0.65, vmin=0, vmax=1, edgecolors='none')

    mean_abs_shap.append(np.mean(np.abs(shap_vals)))

ax_shap.set_yticks(range(len(features)))

ax_shap.set_yticklabels(features, fontsize=10)

ax_shap.set_xlabel('SHAP value (impact on prediction)', fontsize=10)

ax_shap.axvline(x=0, color=COLORS['ref_line'], linewidth=0.8, linestyle='--')

ax_shap.spines['top'].set_visible(False)

ax_shap.spines['right'].set_visible(False)

# Colorbar

cbar = plt.colorbar(sc, ax=ax_shap, shrink=0.5, pad=0.02, aspect=20)

cbar.set_label('Feature value', fontsize=8)

cbar.ax.tick_params(labelsize=7)

# Right panel: Mean |SHAP| importance bar —— 浅色填充 + 原色边框

ax_bar = fig.add_subplot(gs[1])

for i, v in enumerate(mean_abs_shap):

    is_top = (v == max(mean_abs_shap))

    c = PALETTE[0] if is_top else PALETTE[2]

    ax_bar.barh(i, v, color=_lighten(c, 0.4), edgecolor=c,

                linewidth=1.5, height=0.5, alpha=0.9)

    ax_bar.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=8, color=COLORS['text'])

ax_bar.set_yticks([])

ax_bar.set_xlabel('Mean |SHAP|', fontsize=9)

ax_bar.spines['top'].set_visible(False)

ax_bar.spines['right'].set_visible(False)

ax_bar.spines['left'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_shap')

```

---

## 8. Bland-Altman Plot — Bland-Altman 一致性图（分层 CI 带 + 比例偏差线 + 异常值标签）

**场景**: 两种测量方法的一致性评估。医学/工程论文的标准图。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

import numpy as np

np.random.seed(42)

method1 = np.random.normal(50, 10, 100)

method2 = method1 + np.random.normal(0.5, 3, 100)

mean_vals = (method1 + method2) / 2

diff_vals = method1 - method2

mean_diff = np.mean(diff_vals)

std_diff = np.std(diff_vals)

fig, ax = plt.subplots(figsize=(7, 5.5))

# Subtle grid

ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# Gradient CI band (fading from center outward)

x_range = np.linspace(mean_vals.min() - 2, mean_vals.max() + 2, 200)

upper = mean_diff + 1.96 * std_diff

lower = mean_diff - 1.96 * std_diff

# Inner band (darker)

ax.fill_between(x_range, mean_diff - 0.5 * std_diff, mean_diff + 0.5 * std_diff,

                alpha=0.15, color=PALETTE[0], label='±0.5 SD')

# Middle band

ax.fill_between(x_range, mean_diff - 1.0 * std_diff, mean_diff + 1.0 * std_diff,

                alpha=0.10, color=PALETTE[0])

# Outer band (lightest)

ax.fill_between(x_range, lower, upper, alpha=0.06, color=PALETTE[3], label='±1.96 SD (95% CI)')

# Scatter points

ax.scatter(mean_vals, diff_vals, color=PALETTE[0], alpha=0.55, s=30,

           edgecolors='white', linewidths=0.5, zorder=3)

# Mean line

ax.axhline(mean_diff, color=PALETTE[0], linestyle='-', linewidth=1.8,

           label=f'Mean bias: {mean_diff:.2f}')

# Limits of agreement

ax.axhline(upper, color=PALETTE[3], linestyle='--', linewidth=1.2,

           label=f'+1.96 SD: {upper:.2f}')

ax.axhline(lower, color=PALETTE[3], linestyle='--', linewidth=1.2,

           label=f'-1.96 SD: {lower:.2f}')

# Proportional bias regression line

z = np.polyfit(mean_vals, diff_vals, 1)

p = np.poly1d(z)

x_fit = np.linspace(mean_vals.min(), mean_vals.max(), 100)

ax.plot(x_fit, p(x_fit), color=COLORS['highlight'], linewidth=1.5, linestyle='-.',

        label=f'Prop. bias (slope={z[0]:.3f})', zorder=4)

# Outlier labels (points beyond ±1.96 SD)

outliers = np.where((diff_vals > upper) | (diff_vals < lower))[0]

for idx in outliers:

    ax.annotate(f'#{idx}', xy=(mean_vals[idx], diff_vals[idx]),

                xytext=(mean_vals[idx] + 1.5, diff_vals[idx] + 0.8),

                fontsize=7, color=COLORS['down'],

                arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=0.8),

                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',

                          edgecolor=COLORS['down'], alpha=0.9))

ax.set_xlabel('Mean of two methods', fontsize=11)

ax.set_ylabel('Difference (Method 1 − Method 2)', fontsize=11)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=7.5, loc='upper left',

          fancybox=True)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_bland_altman')

```

**⚠ 易踩的坑（Bland-Altman Plot 专用）：**

```python

# 1. 异常值标签用 arrowprops 引线，标签不能离点太远也不能紧贴点位置

# 2. 当异常值聚集时，只标注最突出的 3-5 个，其余用红色圆点标记

# 3. 图例放 upper left（因为通常数据在中间偏右，不会遮挡散点）

# 4. CI 带标签放在图右边缘：ax.text(x_max, upper, ..., ha='left')

```

---

## 9. Kaplan-Meier Survival Curve — 生存曲线（CI 带 + 中位数标记 + 风险人数表 + Log-Rank p）

**场景**: 生存分析、设备寿命、用户留存。医学/可靠性论文必备。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.gridspec as gridspec

import numpy as np

np.random.seed(42)

t_treat = np.sort(np.random.exponential(20, 50))

t_ctrl = np.sort(np.random.exponential(12, 50))

def km_curve_data(times):

    n = len(times)

    surv = np.ones(n + 1)

    t_plot = np.zeros(n + 1)

    for i, t in enumerate(times):

        surv[i + 1] = surv[i] * (n - i - 1) / (n - i)

        t_plot[i + 1] = t

    return t_plot, surv

def number_at_risk(times, time_points):

    return [np.sum(times >= tp) for tp in time_points]

fig = plt.figure(figsize=(8, 6))

gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.08)

ax = fig.add_subplot(gs[0])

ax_risk = fig.add_subplot(gs[1])

# Subtle grid

ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# Treatment group

t1, s1 = km_curve_data(t_treat)

ax.step(t1, s1, where='post', color=PALETTE[0], linewidth=2.5, label='Treatment (n=50)')

# Gradient CI band

ci_upper = np.clip(s1 + 0.08 * np.sqrt(np.linspace(1, 0.1, len(s1))), 0, 1)

ci_lower = np.clip(s1 - 0.08 * np.sqrt(np.linspace(1, 0.1, len(s1))), 0, 1)

ax.fill_between(t1, ci_lower, ci_upper, step='post', alpha=0.12, color=PALETTE[0])

# Control group

t2, s2 = km_curve_data(t_ctrl)

ax.step(t2, s2, where='post', color=PALETTE[3], linewidth=2.5, label='Control (n=50)')

ci_upper2 = np.clip(s2 + 0.10 * np.sqrt(np.linspace(1, 0.1, len(s2))), 0, 1)

ci_lower2 = np.clip(s2 - 0.10 * np.sqrt(np.linspace(1, 0.1, len(s2))), 0, 1)

ax.fill_between(t2, ci_lower2, ci_upper2, step='post', alpha=0.12, color=PALETTE[3])

# Median survival markers with dashed lines

def find_median_survival(t_arr, s_arr):

    for i in range(len(s_arr) - 1):

        if s_arr[i] >= 0.5 and s_arr[i + 1] < 0.5:

            return t_arr[i + 1]

    return None

med_treat = find_median_survival(t1, s1)

med_ctrl = find_median_survival(t2, s2)

if med_treat is not None:

    ax.plot([med_treat, med_treat], [0, 0.5], '--', color=PALETTE[0], linewidth=1.0, alpha=0.7)

    ax.plot([0, med_treat], [0.5, 0.5], '--', color=PALETTE[0], linewidth=1.0, alpha=0.7)

    ax.scatter([med_treat], [0.5], color=PALETTE[0], s=60, zorder=5, marker='D',

               edgecolors='white', linewidths=1.0)

    ax.annotate(f'Median = {med_treat:.1f}m', xy=(med_treat, 0.5),

                xytext=(med_treat + 3, 0.58), fontsize=8, color=PALETTE[0],

                arrowprops=dict(arrowstyle='->', color=PALETTE[0], lw=0.8),

                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

if med_ctrl is not None:

    ax.plot([med_ctrl, med_ctrl], [0, 0.5], '--', color=PALETTE[3], linewidth=1.0, alpha=0.7)

    ax.plot([0, med_ctrl], [0.5, 0.5], '--', color=PALETTE[3], linewidth=1.0, alpha=0.7)

    ax.scatter([med_ctrl], [0.5], color=PALETTE[3], s=60, zorder=5, marker='D',

               edgecolors='white', linewidths=1.0)

    ax.annotate(f'Median = {med_ctrl:.1f}m', xy=(med_ctrl, 0.5),

                xytext=(med_ctrl + 3, 0.42), fontsize=8, color=PALETTE[3],

                arrowprops=dict(arrowstyle='->', color=PALETTE[3], lw=0.8),

                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

# Log-rank p-value annotation

ax.annotate('Log-rank p = 0.003',

            xy=(0.98, 0.98), xycoords='axes fraction', ha='right', va='top',

            fontsize=9, fontweight='bold',

            bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),

                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_ylabel('Survival probability', fontsize=11)

ax.set_ylim(0, 1.05)

ax.set_xlim(left=0)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=9, loc='best')

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.set_xticklabels([])

# Number-at-risk table

time_points = np.arange(0, max(t_treat.max(), t_ctrl.max()) + 5, 10)

nar_treat = number_at_risk(t_treat, time_points)

nar_ctrl = number_at_risk(t_ctrl, time_points)

ax_risk.set_xlim(ax.get_xlim())

ax_risk.set_ylim(-0.5, 1.5)

for i, tp in enumerate(time_points):

    ax_risk.text(tp, 1, str(nar_treat[i]), ha='center', va='center',

                 fontsize=8, color=PALETTE[0], fontweight='bold')

    ax_risk.text(tp, 0, str(nar_ctrl[i]), ha='center', va='center',

                 fontsize=8, color=PALETTE[3], fontweight='bold')

ax_risk.text(-2, 1, 'Treatment', ha='right', va='center', fontsize=8,

             color=PALETTE[0], fontweight='bold')

ax_risk.text(-2, 0, 'Control', ha='right', va='center', fontsize=8,

             color=PALETTE[3], fontweight='bold')

ax_risk.set_xlabel('Time (months)', fontsize=11)

ax_risk.set_yticks([])

ax_risk.spines['top'].set_visible(False)

ax_risk.spines['right'].set_visible(False)

ax_risk.spines['left'].set_visible(False)

ax_risk.set_title('Number at risk', fontsize=8, loc='left', fontstyle='italic')

fig.tight_layout()

save_fig(fig, '图表/fig_kaplan_meier')

```

**⚠ 易踩的坑（Kaplan-Meier Survival 专用）：**

```python

# 1. 中位数标注不要重叠：两组的标注分别放在 0.58 和 0.42 的 y 位置

# 2. log-rank p 值放在右上角，用 xycoords='axes fraction'

# 3. number-at-risk 表紧贴主图下方，用 hspace=0.08

# 4. 图例放 upper right（因为生存曲线从左上角开始下降）

```

---

## 10. Volcano Plot — 火山图（基因差异表达：渐变密度背景 + 基因标签 + 倍数变化阴影）

**场景**: 差异表达、特征选取。生物信息学/组学论文的标准图。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

import numpy as np

np.random.seed(42)

n = 2000

log2fc = np.random.normal(0, 1.5, n)

pvals = 10 ** (-np.abs(log2fc) * np.random.uniform(0.5, 3, n))

neg_log_p = -np.log10(pvals)

gene_names = [f'Gene_{i}' for i in range(n)]

sig_up = (log2fc > 1) & (neg_log_p > 2)

sig_down = (log2fc < -1) & (neg_log_p > 2)

ns = ~sig_up & ~sig_down

fig, ax = plt.subplots(figsize=(7, 5.5))

# Gradient density background (hexbin)

hb = ax.hexbin(log2fc, neg_log_p, gridsize=30, cmap='Blues', alpha=0.25,

               mincnt=1, linewidths=0.0, zorder=0)

# Fold-change threshold shading

ax.axvspan(-1, 1, alpha=0.06, color=COLORS['ref_line'], zorder=0, label='|FC| < 2')

ax.axvspan(1, log2fc.max() + 1, alpha=0.04, color=PALETTE[3], zorder=0)

ax.axvspan(log2fc.min() - 1, -1, alpha=0.04, color=PALETTE[0], zorder=0)

# Subtle grid

ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# Scatter points

ax.scatter(log2fc[ns], neg_log_p[ns], c=COLORS['neutral'], alpha=0.35, s=8,

           label=f'NS ({ns.sum()})', zorder=2)

ax.scatter(log2fc[sig_up], neg_log_p[sig_up], c=PALETTE[3], alpha=0.7, s=15,

           label=f'Up ({sig_up.sum()})', edgecolors='white', linewidths=0.3, zorder=3)

ax.scatter(log2fc[sig_down], neg_log_p[sig_down], c=PALETTE[0], alpha=0.7, s=15,

           label=f'Down ({sig_down.sum()})', edgecolors='white', linewidths=0.3, zorder=3)

# Threshold lines

ax.axhline(2, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)

ax.axvline(1, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)

ax.axvline(-1, color=COLORS['ref_line'], linestyle='--', linewidth=0.8, alpha=0.7)

# Gene labels for top hits (top 5 by significance)

all_sig = np.where(sig_up | sig_down)[0]

if len(all_sig) > 0:

    top_idx = all_sig[np.argsort(neg_log_p[all_sig])[-5:]]

    for idx in top_idx:

        ax.annotate(gene_names[idx],

                    xy=(log2fc[idx], neg_log_p[idx]),

                    xytext=(log2fc[idx] + 0.3 * np.sign(log2fc[idx]),

                            neg_log_p[idx] + 0.5),

                    fontsize=7, fontstyle='italic',

                    color=COLORS['text'],

                    arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=0.7),

                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',

                              edgecolor=COLORS['neutral'], alpha=0.85))

ax.set_xlabel('$\\log_2$(Fold Change)', fontsize=11)

ax.set_ylabel('$-\\log_{10}$(p-value)', fontsize=11)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=8, loc='best',

          fancybox=True)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_volcano')

```

**⚠ 易踩的坑（Volcano Plot 专用）：**

```python

# 1. 上调/下调标签建议用 adjustText 或 smart_labels()，避免多个标签重叠遮挡

# 2. 只标注 top-5 最显著的点：不要标注所有显著点

# 3. 标签用 arrowprops 引线 + 白底 bbox，防止与散点混在一起

# 4. 阈值线标签放在图边缘，不要放在数据密集区域

```

---

## 11. Calibration Plot — 校准曲线（渐变 CI 带 + 底部直方图 + Brier Score 标注）

**场景**: 概率校准评估。比 ROC 更能反映模型在真实场景中的可靠性。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.gridspec as gridspec

import numpy as np

np.random.seed(42)

bins = np.linspace(0, 1, 11)

bin_centers = (bins[:-1] + bins[1:]) / 2

model_a = np.clip(bin_centers + np.random.uniform(-0.05, 0.05, 10), 0, 1)

model_b = np.clip(bin_centers ** 0.7 + np.random.uniform(-0.03, 0.03, 10), 0, 1)

# Simulated predicted probabilities for histogram

pred_probs_a = np.clip(np.random.beta(2, 2, 500), 0, 1)

pred_probs_b = np.clip(np.random.beta(1.5, 3, 500), 0, 1)

# Brier scores

brier_a = 0.023

brier_b = 0.089

fig = plt.figure(figsize=(6, 7))

gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.08)

# Top: Calibration curve

ax_cal = fig.add_subplot(gs[0])

ax_cal.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])

ax_cal.set_axisbelow(True)

# Perfect calibration line

ax_cal.plot([0, 1], [0, 1], 'k--', linewidth=0.8, alpha=0.5, label='Perfect')

# Gradient CI band for Model A

ci_width_a = np.random.uniform(0.03, 0.07, 10)

ax_cal.fill_between(bin_centers, model_a - ci_width_a, model_a + ci_width_a,

                     alpha=0.15, color=PALETTE[0])

ax_cal.plot(bin_centers, model_a, 'o-', color=PALETTE[0], linewidth=2.2,

            markersize=7, label=f'Ours (Brier={brier_a:.3f})',

            markeredgecolor='white', markeredgewidth=1.0)

# Gradient CI band for Model B

ci_width_b = np.random.uniform(0.04, 0.09, 10)

ax_cal.fill_between(bin_centers, model_b - ci_width_b, model_b + ci_width_b,

                     alpha=0.12, color=PALETTE[3])

ax_cal.plot(bin_centers, model_b, 's--', color=PALETTE[3], linewidth=2.0,

            markersize=7, label=f'Baseline (Brier={brier_b:.3f})',

            markeredgecolor='white', markeredgewidth=1.0)

# Brier score annotation box

ax_cal.annotate(f'Brier Score\nOurs: {brier_a:.3f}\nBaseline: {brier_b:.3f}',

                xy=(0.05, 0.88), xycoords='axes fraction',

                fontsize=8.5, va='top',

                bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),

                          edgecolor=PALETTE[0], alpha=0.9))

ax_cal.set_ylabel('Fraction of positives', fontsize=11)

ax_cal.set_xlim(0, 1)

ax_cal.set_ylim(0, 1)

ax_cal.set_aspect('equal')

ax_cal.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=8.5, loc='lower right')

ax_cal.spines['top'].set_visible(False)

ax_cal.spines['right'].set_visible(False)

ax_cal.set_xticklabels([])

# Bottom: Histogram of predicted probabilities

ax_hist = fig.add_subplot(gs[1])

ax_hist.hist(pred_probs_a, bins=20, alpha=0.5, color=PALETTE[0], label='Ours',

             edgecolor='white', linewidth=0.5)

ax_hist.hist(pred_probs_b, bins=20, alpha=0.4, color=PALETTE[3], label='Baseline',

             edgecolor='white', linewidth=0.5)

ax_hist.set_xlabel('Mean predicted probability', fontsize=11)

ax_hist.set_ylabel('Count', fontsize=10)

ax_hist.set_xlim(0, 1)

ax_hist.legend(frameon=False, fontsize=8)

ax_hist.spines['top'].set_visible(False)

ax_hist.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_calibration')

```

---

## 12. Funnel Plot — 漏斗图（Meta 分析：渐变 CI 带 90/95/99% + 研究标签 + Egger 检验）

**场景**: Meta 分析中的发表偏倚检测。医学/社会科学综述必备。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import numpy as np

np.random.seed(42)

n_studies = 30

effects = np.random.normal(0.5, 0.3, n_studies)

se = np.random.uniform(0.05, 0.4, n_studies)

effects += np.random.normal(0, se)

study_names = [f'Study {i+1}' for i in range(n_studies)]

fig, ax = plt.subplots(figsize=(7, 5.5))

# Subtle grid

ax.grid(alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

mean_eff = np.mean(effects)

se_range = np.linspace(0, 0.45, 200)

# Gradient CI bands (99%, 95%, 90%)

ci_levels = [

    (2.576, '99% CI', PALETTE[2], 0.06),

    (1.960, '95% CI', PALETTE[1], 0.08),

    (1.645, '90% CI', PALETTE[0], 0.10),

]

for z_val, label, color, alpha in ci_levels:

    ax.fill_betweenx(se_range,

                      mean_eff - z_val * se_range,

                      mean_eff + z_val * se_range,

                      alpha=alpha, color=color, label=label)

# Pooled effect line

ax.axvline(mean_eff, color=PALETTE[0], linestyle='-', linewidth=1.8, alpha=0.6)

# Study points

ax.scatter(effects, se, color=PALETTE[0], s=50, alpha=0.8, edgecolors='white',

           linewidths=0.8, zorder=4)

# Study labels for outliers (outside 95% CI)

for i in range(n_studies):

    if abs(effects[i] - mean_eff) > 1.96 * se[i] * 1.5:

        ax.annotate(study_names[i],

                    xy=(effects[i], se[i]),

                    xytext=(effects[i] + 0.08, se[i] - 0.03),

                    fontsize=7, color=COLORS['down'],

                    arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=0.7),

                    bbox=dict(boxstyle='round,pad=0.15', facecolor=COLORS['bg_box'],

                              edgecolor=COLORS['down'], alpha=0.7))

# Egger's test annotation

ax.annotate("Egger's test: t = 1.42, p = 0.167\nNo significant asymmetry",

            xy=(0.02, 0.02), xycoords='axes fraction',

            fontsize=8, va='bottom',

            bbox=dict(boxstyle='round,pad=0.4', facecolor=_lighten(PALETTE[0], 0.7),

                      edgecolor=PALETTE[0], alpha=0.9))

ax.set_xlabel('Effect size', fontsize=11)

ax.set_ylabel('Standard error', fontsize=11)

ax.invert_yaxis()

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=8, loc='best',

          fancybox=True)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_funnel')

```

---

## 13. Dot Plot with CI — 点图+置信区间（按显著性渐变着色 + 汇总菱形）

**场景**: 多方法多指标对比。比柱状图信息密度更高——与此同时展示显著性、汇总估计和各自的置信区间。Nature/Cell 风格。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

import numpy as np

methods = ['Ours', 'BERT', 'GPT-4', 'LLaMA', 'T5']

metrics = ['Acc', 'F1', 'Prec', 'Rec']

scores = np.array([[0.92, 0.90, 0.91, 0.89],

                    [0.88, 0.86, 0.89, 0.84],

                    [0.90, 0.88, 0.87, 0.90],

                    [0.85, 0.83, 0.86, 0.81],

                    [0.87, 0.85, 0.88, 0.83]])

ci = np.random.uniform(0.01, 0.03, scores.shape)

# Compute p-values (simulated) for gradient coloring

np.random.seed(42)

pvals = np.random.uniform(0.001, 0.1, scores.shape)

pvals[0, :] = np.random.uniform(0.001, 0.01, 4)  # Ours is most significant

fig, ax = plt.subplots(figsize=(8, 5))

# Subtle grid

ax.grid(axis='x', alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

y_base = np.arange(len(methods))

offsets = np.linspace(-0.25, 0.25, len(metrics))

# Gradient colormap for significance

cmap_sig = mcolors.LinearSegmentedColormap.from_list('sig', [COLORS['down'], COLORS['highlight'], COLORS['up']])

for j, metric in enumerate(metrics):

    for i in range(len(methods)):

        # Color by significance (lower p = greener)

        sig_norm = min(pvals[i, j] / 0.1, 1.0)

        dot_color = cmap_sig(1 - sig_norm)

        ax.errorbar(scores[i, j], y_base[i] + offsets[j], xerr=ci[i, j],

                     fmt='o', color=dot_color, markersize=8, capsize=3,

                     linewidth=1.5, markeredgecolor='white', markeredgewidth=0.8,

                     label=metric if i == 0 else '', zorder=3)

# Pooled estimate diamond for each method

pooled = np.mean(scores, axis=1)

pooled_ci = np.mean(ci, axis=1)

for i in range(len(methods)):

    diamond_x = [pooled[i] - pooled_ci[i], pooled[i], pooled[i] + pooled_ci[i], pooled[i]]

    diamond_y = [y_base[i] + 0.35, y_base[i] + 0.42, y_base[i] + 0.35, y_base[i] + 0.28]

    ax.fill(diamond_x, diamond_y, color=PALETTE[0] if i == 0 else COLORS['ref_line'],

            alpha=0.7, zorder=4)

    ax.text(pooled[i] + pooled_ci[i] + 0.008, y_base[i] + 0.35,

            f'{pooled[i]:.3f}', fontsize=7, va='center', color=COLORS['text'])

ax.set_yticks(y_base)

ax.set_yticklabels(methods, fontsize=10)

ax.set_xlabel('Score', fontsize=11)

# Custom legend

from matplotlib.lines import Line2D

legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor=PALETTE[j],

                           markersize=8, label=metrics[j]) for j in range(len(metrics))]

legend_elements.append(Line2D([0], [0], marker='D', color='w', markerfacecolor=COLORS['ref_line'],

                               markersize=8, label='Pooled'))

ax.legend(handles=legend_elements, loc='lower right', frameon=True,

          edgecolor=COLORS['grid'], fontsize=8, ncol=3)

ax.invert_yaxis()

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_dot_ci')

```

**⚠ 易踩的坑（Dot Plot with CI 专用）：**

```python

# 1. 数值标签统一放在 CI 右端再偏右：不要放在 CI 内部

# 2. pooled diamond 的标签放在 diamond 右侧：不要放在上方（避免与数据 CI 重叠）

# 3. 自适应高度：_fig_h = max(5, n_studies * 0.4 + 2)

# 4. 基线指标用虚线 axhline，不要用粗横线

```

---

## 14. Cluster Heatmap — 聚类热力图（带树状图 + 聚类边界 + 轮廓系数标注）

**场景**: 基因表达矩阵、特征有关性 + 层次聚类。增加聚类结构信息。

**⚠ 布局**: 只画列方向树状图（不画行方向树状图），避免遮挡 y 轴标签。采用 `fig.add_axes()` 人工分区（避免用 gridspec）。树状图和热力图的 left/width 参数完全一致。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import numpy as np

from scipy.cluster.hierarchy import dendrogram, linkage, fcluster

from scipy.spatial.distance import pdist

np.random.seed(42)

data = np.random.randn(10, 8)

labels_row = [f'Sample-{i+1}' for i in range(10)]

labels_col = [f'Feat-{i+1}' for i in range(8)]

Z_col = linkage(pdist(data.T), method='ward')

Z_row = linkage(pdist(data), method='ward')

n_clusters = 3

col_clusters = fcluster(Z_col, n_clusters, criterion='maxclust')

row_clusters = fcluster(Z_row, n_clusters, criterion='maxclust')

fig = plt.figure(figsize=(10, 8))

# ── 关键：树状图和热力图的 left 和 width 参数完全一致，否则会对不齐

# ── _left 需要足够容纳色条(左侧) + 间距 + y轴标签区域(至少 0.15)

_left = 0.22   # 长文本标签需要更大左边距

_width = 0.56

_cbar_left = _left + _width + 0.03

# 列树状图（只画列方向，不画行方向，避免遮挡标签）

ax_dendro_top = fig.add_axes([_left, 0.86, _width, 0.10])

dn_col = dendrogram(Z_col, ax=ax_dendro_top, leaf_font_size=0,

                     color_threshold=Z_col[-n_clusters + 1, 2],

                     above_threshold_color=COLORS['ref_line'])

ax_dendro_top.set_axis_off()

# Heatmap —— left 和 width 与树状图完全一致

ax_heat = fig.add_axes([_left, 0.08, _width, 0.76])

col_order = dn_col['leaves']

row_order = list(range(len(labels_row)))

ordered_data = data[row_order][:, col_order]

im = ax_heat.imshow(ordered_data, aspect='auto', cmap='coolwarm', interpolation='nearest')

ax_heat.set_xticks(range(len(labels_col)))

ax_heat.set_xticklabels([labels_col[i] for i in col_order], fontsize=8,

                         rotation=45, ha='right')

ax_heat.set_yticks(range(len(labels_row)))

ax_heat.set_yticklabels([labels_row[i] for i in row_order], fontsize=8)

# Cluster boundary lines

sorted_col_clusters = [col_clusters[i] for i in col_order]

for k in range(1, len(sorted_col_clusters)):

    if sorted_col_clusters[k] != sorted_col_clusters[k - 1]:

        ax_heat.axvline(k - 0.5, color='white', linewidth=2.5)

sorted_row_clusters = [row_clusters[i] for i in row_order]

for k in range(1, len(sorted_row_clusters)):

    if sorted_row_clusters[k] != sorted_row_clusters[k - 1]:

        ax_heat.axhline(k - 0.5, color='white', linewidth=2.5)

# Colorbar

ax_cbar = fig.add_axes([_cbar_left, 0.08, 0.02, 0.76])

cbar = plt.colorbar(im, cax=ax_cbar)

cbar.ax.tick_params(labelsize=8)

# Silhouette score annotation

ax_heat.text(0.98, 0.02, 'Silhouette = 0.42',

             transform=ax_heat.transAxes, fontsize=8, ha='right', va='bottom',

             bbox=dict(boxstyle='round,pad=0.3', facecolor=_lighten(PALETTE[0], 0.7),

                       edgecolor=PALETTE[0], alpha=0.9))

save_fig(fig, '图表/fig_cluster_heatmap')

```

**⚠ 易踩的坑（聚类热力图专用）：**

```python

# 1. _left 取 0.22，给 y 轴标签 + 左侧色条留够空间（长文本标签需要更多）

# 2. 左侧色条放在 _left-0.05，色条右边界与热力图左边界之间留 0.025 间距

# 3. 树状图和热力图的 left/width 参数完全一致，否则会对不齐

# 4. 只画列方向树状图（不画行方向树状图），行方向树状图会遮挡 y 轴标签

# 5. 不要用 fig.tight_layout()（与 add_axes 布局冲突，会导致手动布局失效）

# 6. 数值标注颜色需要适应：abs(val)>0.6 用白色字，其余用深色字

```

---

## 15. Network Graph — 网络图（节点大小映射度 + 社区凸包 + 边权渐变）

**场景**: 引用网络、知识图谱、社交网络、因果关系。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

import numpy as np

try:

    import networkx as nx

except ImportError:

    import subprocess, sys

    subprocess.verify_call([sys.executable, '-m', 'pip', 'install', 'networkx', '-q'])

    import networkx as nx

from scipy.spatial import ConvexHull

G = nx.karate_club_graph()

communities = list(nx.community.greedy_modularity_communities(G))

# Assign community colors

color_map = {}

for i, comm in enumerate(communities):

    for node in comm:

        color_map[node] = i

node_colors = [PALETTE[color_map[n] % len(PALETTE)] for n in G.nodes()]

# Node sizing by degree

degrees = dict(G.degree())

max_deg = max(degrees.values())

node_sizes = [400 * degrees[n] / max_deg + 80 for n in G.nodes()]

fig, ax = plt.subplots(figsize=(8, 7))

pos = nx.spring_layout(G, seed=42, k=0.5)

# Draw convex hulls for communities

for i, comm in enumerate(communities):

    if len(comm) >= 3:

        points = np.array([pos[n] for n in comm])

        try:

            hull = ConvexHull(points)

            hull_points = points[hull.vertices]

            # Close the polygon

            hull_points = np.vstack([hull_points, hull_points[0]])

            # Expand hull slightly

            centroid = points.mean(axis=0)

            expanded = centroid + 1.15 * (hull_points - centroid)

            ax.fill(expanded[:, 0], expanded[:, 1],

                    color=PALETTE[i % len(PALETTE)], alpha=0.08)

            ax.plot(expanded[:, 0], expanded[:, 1],

                    color=PALETTE[i % len(PALETTE)], linewidth=1.5,

                    linestyle='--', alpha=0.4)

        except Exception:

            pass

# Edge weight gradient

edges = G.edges()

edge_weights = [G[u][v].get('weight', 1) for u, v in edges]

max_w = max(edge_weights) if edge_weights else 1

cmap_edge = mcolors.LinearSegmentedColormap.from_list('ew', [_lighten(PALETTE[0], 0.8), COLORS['ref_line']])

for (u, v), w in zip(edges, edge_weights):

    x0, y0 = pos[u]

    x1, y1 = pos[v]

    norm_w = w / max_w

    ax.plot([x0, x1], [y0, y1], color=cmap_edge(norm_w),

            linewidth=0.5 + 1.5 * norm_w, alpha=0.3 + 0.4 * norm_w, zorder=1)

# Draw nodes

nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes,

                        edgecolors='white', linewidths=1.2, alpha=0.9, zorder=3)

# Labels for high-degree nodes only

high_deg_nodes = {n: str(n) for n in G.nodes() if degrees[n] >= 4}

nx.draw_networkx_labels(G, pos, labels=high_deg_nodes, ax=ax,

                         font_size=7, font_color=COLORS['text'], font_weight='bold')

# Legend for communities

from matplotlib.lines import Line2D

legend_elements = [Line2D([0], [0], marker='o', color='w',

                           markerfacecolor=PALETTE[i % len(PALETTE)],

                           markersize=10, label=f'Community {i+1}')

                   for i in range(len(communities))]

ax.legend(handles=legend_elements, loc='upper left', frameon=True,

          edgecolor=COLORS['grid'], fontsize=8, fancybox=True)

ax.set_axis_off()

fig.tight_layout()

save_fig(fig, '图表/fig_network')

```

**⚠ 易踩的坑（Network Graph 专用）：**

```python

# 1. 节点标签用 bbox 白底，防止和边线混在一起

# 2. 边权重标签只标注权重 > 中位数的边，不要每条边都标

# 3. 社区凸包用极浅色填充（alpha=0.08），不要遮挡节点和标签

# 4. 节点太密集时，fontsize 缩到 7，且只标注度数 top-5 的节点

```

---

## 16. Method Comparison Heatmap — 方法对比热力图（排名标注 🥇🥈🥉 + 树状图 + 列最优高亮 + 综合排名）

**场景**: 多方法 × 多指标对比矩阵。比柱状图更紧凑。Nature/Cell 风格。

**风格**: YlOrRd heatmap + 浅色填充+原色边框 用于列最优单元格 + 排名奖牌。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import numpy as np

from scipy.cluster.hierarchy import dendrogram, linkage

from scipy.spatial.distance import pdist

methods = ['Ours', 'LSTM', 'Random Forest', 'Linear Reg']

metrics = ['MAE', 'RMSE', 'R2', 'MAPE(%)', 'Speed']

# Lower is better for MAE/RMSE/MAPE, higher for R2/Speed

data = np.array([

    [0.29, 1.05, 0.987, 2.1, 0.85],

    [72.23, 85.4, 0.812, 15.3, 0.60],

    [0.45, 1.82, 0.965, 3.8, 0.92],

    [137.08, 152.3, 0.421, 48.2, 0.98],

])

higher_better = [False, False, True, False, True]

# Rank medals

rank_symbols = ['🥇', '🥈', '🥉', '④']

# Normalize for color mapping

norm_data = np.zeros_like(data)

for j in range(data.shape[1]):

    col = data[:, j]

    if higher_better[j]:

        norm_data[:, j] = (col - col.min()) / (col.max() - col.min() + 1e-10)

    else:

        norm_data[:, j] = 1 - (col - col.min()) / (col.max() - col.min() + 1e-10)

# Compute overall ranking (average normalized rank)

overall_rank_score = np.mean(norm_data, axis=1)

# Add overall ranking column

metrics_ext = metrics + ['Overall']

data_ext = np.column_stack([data, overall_rank_score])

norm_ext = np.column_stack([norm_data, overall_rank_score / overall_rank_score.max()])

fig = plt.figure(figsize=(9, 4.5))

# Dendrogram on top

ax_dendro = fig.add_axes([0.15, 0.82, 0.65, 0.14])

Z = linkage(pdist(norm_data), method='ward')

dn = dendrogram(Z, labels=methods, ax=ax_dendro, leaf_font_size=0,

                color_threshold=0, above_threshold_color=COLORS['ref_line'])

ax_dendro.set_axis_off()

row_order = dn['leaves']

# Heatmap

ax = fig.add_axes([0.15, 0.12, 0.72, 0.68])

ordered_norm = norm_ext[row_order]

ordered_data = data_ext[row_order]

ordered_methods = [methods[i] for i in row_order]

im = ax.imshow(ordered_norm, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)

ax.set_xticks(range(len(metrics_ext)))

ax.set_xticklabels(metrics_ext, fontsize=10)

ax.set_yticks(range(len(methods)))

ax.set_yticklabels(ordered_methods, fontsize=10)

# Annotate with values, ranks, and 浅色填充+原色边框 for best

for j in range(len(metrics_ext)):

    if j < len(metrics):

        col_vals = data[:, j]

        if higher_better[j]:

            rank_order = np.argsort(-col_vals)

        else:

            rank_order = np.argsort(col_vals)

    else:

        rank_order = np.argsort(-overall_rank_score)

    for i_orig, rank_pos in enumerate(rank_order):

        # Find position in ordered display

        i_display = row_order.index(rank_pos)

        if j < len(metrics):

            val_str = f'{data[rank_pos, j]:.2f}'

        else:

            val_str = f'{overall_rank_score[rank_pos]:.2f}'

        rank_idx = i_orig

        rank_label = rank_symbols[rank_idx] if rank_idx < len(rank_symbols) else ''

        color = 'white' if ordered_norm[i_display, j] > 0.75 or ordered_norm[i_display, j] < 0.25 else 'black'

        weight = 'bold' if rank_idx == 0 else 'normal'

        ax.text(j, i_display, f'{val_str}\n{rank_label}', ha='center', va='center',

                fontsize=8.5, fontweight=weight, color=color)

        # 列最优：浅色填充背景 + 原色粗边框

        if rank_idx == 0:

            rect = plt.Rectangle((j - 0.5, i_display - 0.5), 1, 1,

                                  linewidth=2.5, edgecolor=PALETTE[0],

                                  facecolor=_lighten(PALETTE[0], 0.5),

                                  alpha=0.3, zorder=4)

            ax.add_patch(rect)

            # 原色边框（不透明）

            rect_border = plt.Rectangle((j - 0.5, i_display - 0.5), 1, 1,

                                         linewidth=2.5, edgecolor=PALETTE[0],

                                         facecolor='none', zorder=5)

            ax.add_patch(rect_border)

ax.spines[:].set_visible(False)

# Colorbar

ax_cbar = fig.add_axes([0.89, 0.12, 0.02, 0.68])

cbar = plt.colorbar(im, cax=ax_cbar)

cbar.set_label('Normalized (1=best)', fontsize=8)

cbar.ax.tick_params(labelsize=7)

save_fig(fig, '图表/fig_method_heatmap')

```

---

## 17. Parallel Coordinates — 平行坐标图（实线 + "本文"高亮 + 最优区域阴影）

**场景**: 多方法 × 多指标对比。各个指标是一条纵轴，各个方法是一条折线。交叉和分离一目了然。

```python

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

import matplotlib.pyplot as plt

import numpy as np

methods = ['Ours', 'LSTM', 'Random Forest', 'Linear Reg']

metrics = ['MAE↓', 'RMSE↓', 'R²↑', 'Speed↑', 'Stability↑']

# All normalized to [0,1] where 1=best

data = np.array([

    [0.95, 0.92, 0.987, 0.85, 0.90],

    [0.45, 0.50, 0.812, 0.60, 0.65],

    [0.88, 0.82, 0.965, 0.92, 0.78],

    [0.10, 0.15, 0.421, 0.98, 0.55],

])

fig, ax = plt.subplots(figsize=(9, 5))

x = np.arange(len(metrics))

# Subtle grid

ax.grid(axis='y', alpha=0.15, linestyle='-', color=COLORS['grid'])

ax.set_axisbelow(True)

# Optimal region shading per axis (top 20%)

for j in range(len(metrics)):

    ax.fill_between([j - 0.3, j + 0.3], 0.8, 1.0, alpha=0.06,

                     color=COLORS['up'], zorder=0)

    ax.text(j, 0.82, '最优区', ha='center', fontsize=6, color=COLORS['up'],

            alpha=0.6, fontstyle='italic')

# Draw simple lines per method

for i, (method, row) in enumerate(zip(methods, data)):

    is_ours = (i == 0)

    if is_ours:

        # Thick solid line for "Ours"

        ax.plot(x, row, '-', color=PALETTE[0], linewidth=3.5, zorder=5,

                solid_capstyle='round')

        # Markers

        ax.scatter(x, row, color=PALETTE[0], s=100, zorder=6,

                   edgecolors='white', linewidths=1.5, marker='o')

        # Value labels

        for j, v in enumerate(row):

            ax.text(j, v + 0.04, f'{v:.2f}', ha='center', fontsize=8.5,

                    color=PALETTE[0], fontweight='bold')

        # Highlight label

        ax.text(x[-1] + 0.25, row[-1], f'★ {method}', va='center', fontsize=10,

                color=PALETTE[0], fontweight='bold')

    else:

        # Simple line for other methods

        ax.plot(x, row, '-', color=PALETTE[i], linewidth=1.5, alpha=0.6,

                solid_capstyle='round')

        ax.scatter(x, row, color=PALETTE[i], s=50, zorder=4, alpha=0.7,

                   edgecolors='white', linewidths=0.8)

        ax.text(x[-1] + 0.25, row[-1], method, va='center', fontsize=8.5,

                color=PALETTE[i], alpha=0.8)

ax.set_xticks(x)

ax.set_xticklabels(metrics, fontsize=10.5)

ax.set_ylabel('归一化得分 (1=最优)', fontsize=11)

ax.set_ylim(0, 1.12)

ax.set_xlim(-0.4, len(metrics) - 0.3)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_parallel_coords')

```

---

## 18. PCA Biplot — PCA 双标图（载荷箭头 + 智能标签 + 解释方差）

**场景**: 降维可视化、特征贡献分析。多元分析章节常用。

**防重叠**: 采用 `smart_labels()` 自动化推开重叠的特征名标签——当多个载荷方向相近时尤为关键。

```python

import numpy as np

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

from 工具.plot_utils import setup_style, save_fig, PALETTE, smart_labels, auto_legend

setup_style()

# === Example data (replace with your PCA results) ===

np.random.seed(42)

n_samples, n_features = 80, 12

feature_names = ['市场规模', '供应链成熟度', '短期恢复能力', '响应梯度元素',

                 '长期恢复速度', '研发投入强度', '短期恢复弹性', '产能利用率',

                 '短期集中度', '专利授权量', '产业链完整度', '客户集中度']

# Simulated PCA scores and loadings

scores = np.random.randn(n_samples, 2) * 2

loadings = np.random.randn(n_features, 2)

loadings = loadings / np.abs(loadings).max(axis=0) * 3  # scale to [-3, 3]

explained_var = [66.3, 11.4]  # explained variance %

fig, ax = plt.subplots(figsize=(8, 7))

# Scatter: sample scores (gray, semi-transparent)

ax.scatter(scores[:, 0], scores[:, 1], s=25, alpha=0.35, color=COLORS['gray'],

           edgecolors='white', linewidths=0.3, zorder=2)

# Loading arrows

arrow_colors = []

for i, (name, lx, ly) in enumerate(zip(feature_names, loadings[:, 0], loadings[:, 1])):

    magnitude = np.sqrt(lx**2 + ly**2)

    color = PALETTE[0]

    arrow_colors.append(color)

    ax.annotate('', xy=(lx, ly), xytext=(0, 0),

                arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.7))

# ── 特征名标签 —— smart_labels 自动推开重叠标签

# Offset labels slightly beyond arrow tips

label_xs = [lx * 1.08 for lx in loadings[:, 0]]

label_ys = [ly * 1.08 for ly in loadings[:, 1]]

smart_labels(ax, label_xs, label_ys, feature_names,

             colors=arrow_colors, fontsize=8.5, fontweight='bold',

             offset=(5, 0),

             bbox=dict(boxstyle='round,pad=0.2', facecolor='white',

                       edgecolor=PALETTE[0], alpha=0.8, linewidth=0.5),

             arrowprops=dict(arrowstyle='-', color=COLORS['grid'], lw=0.4),

             force_text=0.8, force_points=0.5)

# Reference lines

ax.axhline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4)

ax.axvline(0, color=COLORS['ref_line'], linewidth=0.5, alpha=0.4)

ax.set_xlabel(f'PC1 ({explained_var[0]:.1f}%)', fontsize=11)

ax.set_ylabel(f'PC2 ({explained_var[1]:.1f}%)', fontsize=11)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(alpha=0.1, linestyle='--')

fig.tight_layout()

save_fig(fig, '图表/fig_pca_biplot.pdf')

```

**⚠ 易踩的坑（PCA Biplot 专用）：**

```python

# 1. Loading 箭头标签必须用 smart_labels()，箭头方向相近时标签一定会重叠

# 2. 箭头标签用白底 bbox，防止与散点混在一起

# 3. 散点用小尺寸（s=15-25）+ 低 alpha（0.4），给箭头和标签腾出视觉空间

# 4. 特征过多时，只标注最长的箭头，其余用数字 text 标注

```

---

## 19. Taylor Diagram — Taylor 图（多模型对比：有关系数 + 标准差 + RMSE）

**场景**: 在一张图中与此同时比较多个模型的三个统计指标（有关系数、标准差、RMSE）。气候科学、水文学、环境建模的标准图。比单纯的 RMSE 柱状图信息量大得多。

**风格**: 浅色填充+原色边框 用于模型标记点，RMSE 弧线用暖橙色。

```python

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.patches import Arc

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels

setup_style()

# === Example data (replace with your model evaluation results) ===

# Reference (observed) statistics

ref_std = 1.0  # normalized

# Model results: (correlation, normalized_std)

models = {

    'Ours':        (0.95, 1.02),

    'LSTM':        (0.88, 0.85),

    'XGBoost':     (0.91, 1.15),

    'SVR':         (0.82, 0.78),

    'Linear Reg':  (0.75, 1.30),

}

fig, ax = plt.subplots(figsize=(7, 7))

# Draw reference arcs (constant correlation lines)

max_std = 1.6

for corr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:

    theta = np.arccos(corr)

    r_vals = np.linspace(0, max_std, 100)

    x_arc = r_vals * np.cos(theta)

    y_arc = r_vals * np.sin(theta)

    ax.plot(x_arc, y_arc, color=COLORS['grid'], linewidth=0.5, alpha=0.6)

    ax.text(max_std * np.cos(theta) * 1.03, max_std * np.sin(theta) * 1.03,

            f'{corr}', fontsize=7, color=COLORS['ref_line'], ha='center', va='center',

            rotation=np.degrees(theta) - 90)

# Draw std arcs (centered at origin)

for s in [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]:

    theta_range = np.linspace(0, np.pi / 2, 100)

    ax.plot(s * np.cos(theta_range), s * np.sin(theta_range),

            color=COLORS['grid'], linewidth=0.5, linestyle='--')

# Draw RMSE arcs (centered at reference point) —— 暖橙色

ref_x, ref_y = ref_std, 0

for rmse in [0.25, 0.5, 0.75, 1.0, 1.25]:

    theta_range = np.linspace(0, np.pi, 200)

    cx = ref_x + rmse * np.cos(theta_range)

    cy = rmse * np.sin(theta_range)

    mask = (cx >= 0) & (cy >= 0) & (np.sqrt(cx**2 + cy**2) <= max_std)

    if mask.any():

        ax.plot(cx[mask], cy[mask], color=COLORS['highlight'], linewidth=0.5,

                alpha=0.4, linestyle=':')

# Reference point

ax.scatter(ref_std, 0, s=150, color=COLORS['text'], marker='*', zorder=10, label='Observed')

# ── 绘制模型点：浅色填充+原色边框 标记

label_xs, label_ys, label_texts, label_colors = [], [], [], []

for i, (name, (corr, std)) in enumerate(models.items()):

    theta = np.arccos(corr)

    x = std * np.cos(theta)

    y = std * np.sin(theta)

    color = PALETTE[i % len(PALETTE)]

    marker = 'D' if i == 0 else 'o'

    size = 140 if i == 0 else 90

    # 浅色填充 + 原色边框

    ax.scatter(x, y, s=size, color=_lighten(color, 0.35), marker=marker, zorder=5,

               edgecolors=color, linewidths=1.8, label=name)

    label_xs.append(x); label_ys.append(y)

    label_texts.append(name); label_colors.append(color)

# Smart labels to avoid overlap

smart_labels(ax, label_xs, label_ys, label_texts, colors=label_colors,

             fontsize=8.5, fontweight='bold', offset=(8, 5))

ax.set_xlim(0, max_std)

ax.set_ylim(0, max_std)

ax.set_aspect('equal')

ax.set_xlabel('标准差（归一化）', fontsize=11)

ax.set_ylabel('标准差（归一化）', fontsize=11)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.legend(loc='upper left', fontsize=9, frameon=True, edgecolor=COLORS['grid'])

fig.tight_layout()

save_fig(fig, '图表/fig_taylor.pdf')

```

---

## 20. Diverging Bar Chart — 发散柱状图（淡色填充 + 原色边框 + 相对基线 + 颜色编码方向 + 数值标签）

**场景**: 展示各个方法/变体相针对基线的表现（正值=更好，负值=更差）。比分组柱状图更清晰地传达"改进 vs 退化"的信息。常见于消融实验和敏感性分析。

**风格**: 方向性颜色背景区 + 浅色填充+原色边框柱体 + 阴影加粗 + 方向标注。

```python

import numpy as np

import matplotlib.pyplot as plt

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten, smart_labels

setup_style()

methods = ['Ours (full)', 'w/o Attention', 'w/o Pretrain', 'w/o Augment',

           'Baseline-A', 'Baseline-B', 'Baseline-C']

deltas = [+5.2, +3.1, +1.8, +0.5, 0.0, -1.3, -2.7]

# ── 自适应高度

_fig_h = max(4, len(methods) * 0.7 + 1)

fig, ax = plt.subplots(figsize=(8, _fig_h))

y_pos = np.arange(len(methods))

# 方向性颜色背景

ax.axvspan(0, max(deltas)*1.3, alpha=0.05, color=COLORS['up'], zorder=0)

ax.axvspan(min(deltas)*1.3, 0, alpha=0.05, color=COLORS['down'], zorder=0)

# Color: positive = up(green), negative = down(red)

base_colors = [COLORS['up'] if d >= 0 else COLORS['down'] for d in deltas]

# 柱体阴影

ax.barh(y_pos + 0.03, deltas, height=0.5, color='#cccccc', alpha=0.1, zorder=1)

# ── 主柱体：浅色填充 + 原色边框

bars = ax.barh(y_pos, deltas, height=0.5,

               color=[_lighten(c, 0.4) for c in base_colors],

               edgecolor=base_colors, linewidth=1.5, zorder=3)

# Zero reference line

ax.axvline(0, color=COLORS['text'], linewidth=1.2, zorder=2)

# Value labels at bar ends（白底保护）

for i, (bar, d) in enumerate(zip(bars, deltas)):

    x_pos = d + (0.2 if d >= 0 else -0.2)

    ha = 'left' if d >= 0 else 'right'

    sign = '+' if d > 0 else ''

    ax.text(x_pos, y_pos[i], f'{sign}{d:.1f}%', va='center', ha=ha,

            fontsize=9, fontweight='bold', color=base_colors[i],

            bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.7))

# Highlight "Ours" row

ax.axhspan(y_pos[0]-0.35, y_pos[0]+0.35, alpha=0.06, color=PALETTE[0], zorder=0)

bars[0].set_edgecolor(PALETTE[0]); bars[0].set_linewidth(2.0)

# 方向标注

ax.text(0.98, 0.02, '更优 →', transform=ax.transAxes, fontsize=8, ha='right',

        color=COLORS['up'], fontweight='bold')

ax.text(0.02, 0.02, '← 更差', transform=ax.transAxes, fontsize=8, ha='left',

        color=COLORS['down'], fontweight='bold')

ax.set_yticks(y_pos)

ax.set_yticklabels(methods, fontsize=10)

ax.set_xlabel('Relative Improvement over Baseline (%)', fontsize=11)

ax.invert_yaxis()

ax.grid(axis='x', alpha=0.12, linestyle='--', color=COLORS['grid'])

ax.spines['left'].set_visible(False)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_diverging_bar.pdf')

```

---

## 21. Back-to-Back Bar Chart — 背靠背柱状图（浅色填充 + 原色边框 + 镜像对比 + 共享 Y 轴 + 差值标签）

**场景**: 两组/两种条件的镜像对比。经典"人口金字塔"风格。适合前后对比、男/女、训练/测试或任何二分对比。

```python

import numpy as np

import matplotlib.pyplot as plt

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

categories = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC', 'MCC']

group_a = [92.3, 89.1, 94.5, 91.7, 96.2, 88.4]  # e.g., "Ours"

group_b = [87.5, 84.2, 90.1, 87.0, 93.1, 82.6]  # e.g., "Baseline"

# ── 自适应高度

_fig_h = max(4, len(categories) * 0.7 + 1)

fig, ax = plt.subplots(figsize=(8, _fig_h))

y_pos = np.arange(len(categories))

# ── 左侧（负方向）= Group B —— 浅色填充 + 原色边框

bars_b = ax.barh(y_pos, [-v for v in group_b], height=0.55,

                 color=_lighten(PALETTE[1], 0.4), edgecolor=PALETTE[1],

                 linewidth=1.2, label='Baseline', zorder=3)

# ── 右侧（正方向）= Group A —— 浅色填充 + 原色边框

bars_a = ax.barh(y_pos, group_a, height=0.55,

                 color=_lighten(PALETTE[0], 0.4), edgecolor=PALETTE[0],

                 linewidth=1.2, label='Ours', zorder=3)

# Value labels

for i in range(len(categories)):

    ax.text(group_a[i] + 0.5, y_pos[i], f'{group_a[i]:.1f}',

            va='center', ha='left', fontsize=8.5, color=PALETTE[0], fontweight='bold')

    ax.text(-group_b[i] - 0.5, y_pos[i], f'{group_b[i]:.1f}',

            va='center', ha='right', fontsize=8.5, color=PALETTE[1], fontweight='bold')

    # Gap label in center

    gap = group_a[i] - group_b[i]

    sign = '+' if gap > 0 else ''

    ax.text(0, y_pos[i], f'{sign}{gap:.1f}', va='center', ha='center',

            fontsize=7.5, fontweight='bold', color=COLORS['text'],

            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',

                      edgecolor=COLORS['grid'], alpha=0.9))

ax.set_yticks(y_pos)

ax.set_yticklabels(categories, fontsize=10)

ax.axvline(0, color=COLORS['text'], linewidth=0.8)

ax.set_xlabel('Score (%)', fontsize=11)

ax.legend(loc='lower right', fontsize=9, frameon=True, edgecolor=COLORS['grid'])

# Clean up x-axis to show absolute values

ticks = ax.get_xticks()

ax.set_xticklabels([f'{abs(t):.0f}' for t in ticks])

ax.invert_yaxis()

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(axis='x', alpha=0.1, linestyle='--')

fig.tight_layout()

save_fig(fig, '图表/fig_back2back.pdf')

```

---

## 22. Paired Dot Plot — 配对点图（个体变化连线 + 均值偏移箭头 + 显著性）

**场景**: 展示配对观测（同一受试者/样本在两种条件下的值）。每条线连接同一实体的前后值，揭示分组柱状图隐藏的个体差异。常见于医学、A/B 测试和实验设计论文。

```python

import numpy as np

import matplotlib.pyplot as plt

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS

setup_style()

np.random.seed(42)

n = 20

labels = ['Before', 'After']

before = np.random.normal(75, 8, n)

after = before + np.random.normal(5, 4, n)  # general improvement with variance

fig, ax = plt.subplots(figsize=(5, 6))

# Individual paired lines

for i in range(n):

    color = PALETTE[0] if after[i] > before[i] else PALETTE[1]

    ax.plot([0, 1], [before[i], after[i]], color=color, alpha=0.35,

            linewidth=1.2, zorder=2)

    ax.scatter([0, 1], [before[i], after[i]], color=color, s=30,

               edgecolors='white', linewidths=0.5, zorder=3, alpha=0.6)

# Mean markers (large, prominent)

mean_before, mean_after = before.mean(), after.mean()

ax.scatter(0, mean_before, s=200, color=PALETTE[1], marker='D',

           edgecolors='white', linewidths=2, zorder=5, label=f'Mean Before: {mean_before:.1f}')

ax.scatter(1, mean_after, s=200, color=PALETTE[0], marker='D',

           edgecolors='white', linewidths=2, zorder=5, label=f'Mean After: {mean_after:.1f}')

# Mean shift arrow

ax.annotate('', xy=(1, mean_after), xytext=(0, mean_before),

            arrowprops=dict(arrowstyle='->', color=COLORS['text'], lw=2.5,

                            connectionstyle='arc3,rad=0.15'))

delta = mean_after - mean_before

ax.text(0.5, (mean_before + mean_after) / 2 + 2,

        f'Δ = +{delta:.1f}', ha='center', fontsize=10, fontweight='bold',

        color=PALETTE[0],

        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',

                  edgecolor=PALETTE[0], alpha=0.9))

# Significance annotation

from scipy import stats

t_stat, p_val = stats.ttest_rel(after, before)

sig_text = f'p = {p_val:.4f}' if p_val >= 0.001 else 'p < 0.001'

ax.text(0.5, max(max(before), max(after)) + 4, sig_text,

        ha='center', fontsize=9, fontstyle='italic', color=COLORS['text'])

ax.set_xticks([0, 1])

ax.set_xticklabels(labels, fontsize=12, fontweight='bold')

ax.set_ylabel('Score', fontsize=11)

ax.set_xlim(-0.4, 1.4)

ax.legend(loc='lower right', fontsize=8, frameon=True, edgecolor=COLORS['grid'])

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(axis='y', alpha=0.1, linestyle='--')

fig.tight_layout()

save_fig(fig, '图表/fig_paired_dot.pdf')

```

**⚠ 易踩的坑（Paired Dot Plot 专用）：**

```python

# 1. 显著性标注不要与数据点重叠：放在 y 位置 = max(data) + offset

# 2. 均值偏移箭头放在图右侧空白区域，不要穿过数据点之间

# 3. 个体变化线用低 alpha（0.3），不要遮挡均值标记

# 4. p 值标注放在数据上方（fontsize=8），不要太大

```

---

## 23. Ridgeline Plot — 山脊图（堆叠分布对比 + 渐变填充 + 中位数线）

**场景**: 在紧凑布局中比较多组（5-15 组）的分布。每组有自己的密度曲线，垂直方向略有重叠。比多个直方图或小提琴图更节省空间。在数据新闻和学术论文中越来越流行。

```python

import numpy as np

import matplotlib.pyplot as plt

from scipy.stats import gaussian_kde

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

np.random.seed(42)

groups = ['Model A', 'Model B', 'Model C', 'Model D', 'Model E',

          'Model F', 'Model G', 'Model H']

n_groups = len(groups)

# Generate sample data (replace with real data)

data = []

for i in range(n_groups):

    center = 70 + i * 3 + np.random.randn() * 2

    spread = 5 + np.random.rand() * 5

    d = np.random.normal(center, spread, 200)

    data.append(d)

fig, ax = plt.subplots(figsize=(8, 6))

overlap = 0.6  # vertical overlap factor

x_grid = np.linspace(min(d.min() for d in data) - 5,

                      max(d.max() for d in data) + 5, 300)

for i in range(n_groups - 1, -1, -1):  # draw back to front

    kde = gaussian_kde(data[i], bw_method=0.3)

    density = kde(x_grid)

    # Normalize density to consistent height

    density = density / density.max() * 0.8

    baseline = i * overlap

    color = PALETTE[i % len(PALETTE)]

    light = _lighten(color, 0.5)

    # Gradient fill

    ax.fill_between(x_grid, baseline, baseline + density,

                    color=light, alpha=0.85, zorder=n_groups - i)

    ax.plot(x_grid, baseline + density, color=color, linewidth=1.5,

            zorder=n_groups - i + 0.5)

    # Median line

    median = np.median(data[i])

    med_density = kde(median)[0] / density.max() * 0.8

    ax.plot([median, median], [baseline, baseline + med_density],

            color=color, linewidth=1.5, linestyle='--', alpha=0.7,

            zorder=n_groups - i + 1)

    ax.text(median, baseline + med_density + 0.02,

            f'{median:.1f}', ha='center', fontsize=7, color=color,

            fontweight='bold', zorder=n_groups + 10)

    # Group label

    ax.text(x_grid[0] - 1, baseline + 0.15, groups[i],

            ha='right', va='center', fontsize=9, fontweight='bold',

            color=color)

ax.set_yticks([])

ax.set_xlabel('Score', fontsize=11)

ax.spines['left'].set_visible(False)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_ridgeline.pdf')

```

**⚠ 易踩的坑（Ridgeline Plot 专用）：**

```python

# 1. 相邻密度曲线的 y 间距 ≥ 2.5：太密会导致曲线互相遮挡

# 2. 中位数线标签放在曲线右侧：不要放在曲线内部

# 3. Shapiro-Wilk 标注放在数据右端再偏右：用 bbox 白底

# 4. 组数 >8 时，自适应高度 _fig_h = max(6, n_groups * 1.2 + 1)

```

---

## 24. Grouped Violin Plot (Multi-Group Distribution Comparison + Median + Quartile Lines)

**Use case**: Compare distribution shapes across 2-4 groups for multiple categories. More compact than Rain Cloud when you have many categories. Shows full distribution shape unlike box plots.

```python

import numpy as np

import matplotlib.pyplot as plt

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

np.random.seed(42)

categories = ['Dataset A', 'Dataset B', 'Dataset C', 'Dataset D']

group_names = ['Ours', 'Baseline-1', 'Baseline-2']

n_groups = len(group_names)

# Generate sample data (replace with real results)

all_data = {}

for g, gname in enumerate(group_names):

    all_data[gname] = []

    for c in range(len(categories)):

        center = 80 + g * (-3) + c * 2 + np.random.randn()

        d = np.random.normal(center, 3 + g, 50)

        all_data[gname].append(d)

fig, ax = plt.subplots(figsize=(9, 5))

width = 0.25

positions_base = np.arange(len(categories))

for g, gname in enumerate(group_names):

    positions = positions_base + (g - n_groups / 2 + 0.5) * width

    color = PALETTE[g % len(PALETTE)]

    light = _lighten(color, 0.4)

    parts = ax.violinplot(all_data[gname], positions=positions,

                          widths=width * 0.85, showmeans=False,

                          showmedians=False, showextrema=False)

    for pc in parts['bodies']:

        pc.set_facecolor(light)

        pc.set_edgecolor(color)

        pc.set_linewidth(1.2)

        pc.set_alpha(0.8)

    # Add median + quartile lines manually

    for i, d in enumerate(all_data[gname]):

        q1, med, q3 = np.percentile(d, [25, 50, 75])

        pos = positions[i]

        # Median dot

        ax.scatter(pos, med, color=color, s=30, zorder=5,

                   edgecolors='white', linewidths=0.8)

        # Quartile whisker

        ax.vlines(pos, q1, q3, color=color, linewidth=2.5, zorder=4)

    # Invisible scatter for legend

    ax.scatter([], [], color=color, s=60, label=gname, edgecolors='white')

ax.set_xticks(positions_base)

ax.set_xticklabels(categories, fontsize=10)

ax.set_ylabel('Score', fontsize=11)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=9)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(axis='y', alpha=0.1, linestyle='--')

fig.tight_layout()

save_fig(fig, '图表/fig_grouped_violin.pdf')

```

