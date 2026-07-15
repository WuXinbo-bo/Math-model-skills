# 科研图形与表格风格指南

Meta-model-agent 画图时参考此文件。全部图形与表格务必达到可核验、可读、克制且适合竞赛论文印刷的水准；禁止用渐变、阴影、圆角卡片和无必要多层叠加模拟所谓“顶刊高级感”。

## 按图形与表格类别的配色策略（⛔ 务必遵循）

<figure_selection_guide>

## Data → Visual Type Decision Table

Prior to choosing a visual type, analyze the data characteristics, then match using this table. Consult the full implementation from the corresponding recipes file.

<selection_priority>

### Selection priority: match data shape, not visual novelty

Choose the visual type that best communicates your data, not the fanciest one available. The decision order is:

1. **First validate the "By data shape" table below** — match your data characteristics to the recommended visual type

2. **If multiple options fit**, prefer the one your target audience (competition judges, reviewers) will instantly understand

3. **Use advanced recipes** (Lollipop, Dumbbell, Waterfall, SHAP, etc.) when they genuinely add information that basic charts cannot show — e.g., Waterfall shows incremental contribution, SHAP shows feature direction

4. **Use basic recipes** (grouped bar, line, scatter) when they are the clearest way to present the data — a well-made grouped bar chart is better than a confusing Bump chart

A manuscript needs consistent visual grammar. Reuse the same familiar chart type whenever the reader task is the same; variety is not an independent quality target.

**Hard rule**: choose by reader task and data shape. Never replace a clear bar, line, scatter plot, or three-line table merely to avoid repetition.

</selection_priority>

### By data shape

| Data characteristic | Best visual type | Recipes file | Avoid |

|---|---|---|---|

| ≤3 methods × 1-2 metrics | Three-line table | — | Any chart — too few data points for a meaningful visual |

| 4+ methods × 1 metric | Lollipop Chart or Grouped Bar | advanced #1, basic #1 | — |

| A vs B (2 methods, multiple metrics) | Dumbbell Chart | advanced #2 | heatmap — 2 rows looks like a traffic light |

| A vs B vs C (3-5 methods, multiple metrics) | Grouped Bar Chart or Radar chart | basic #1, competition #5 | — |

| Methods × Metrics matrix (≤5×5) | Method Comparison Heatmap or Grouped Bar | advanced #16, basic #1 | — |

| Methods × Metrics (show trends across metrics) | Parallel Coordinates | advanced #17 | multiple separate charts |

| Methods × Metrics matrix (>5×5) | Heatmap with values | basic #5 | — |

| Methods × Datasets ranking | Bump Chart or Grouped Bar | advanced #4, basic #1 | — |

| Prior to/following comparison | Dumbbell Chart or Grouped Bar | advanced #2, basic #1 | — |

| Prior to/following (paired samples) | Paired Dot Plot | advanced #22 | grouped bar (hides individual variation) |

| Relative to baseline (±%) | Diverging Bar Chart | advanced #20 | grouped bar (doesn't show direction clearly) |

| Two-group mirror comparison | Back-to-Back Bar Chart | advanced #21 | — |

| Multi-model statistical comparison | Taylor Diagram | advanced #19 | separate RMSE/R²/StdDev bar charts |

| Distribution comparison (5-15 groups) | Ridgeline Plot | advanced #23 | multiple histograms (wastes space) |

| Distribution comparison (2-4 groups × categories) | Grouped Violin Plot | advanced #24 | box plot (hides distribution shape) |

| Module contribution (ablation) | Waterfall Chart | advanced #6 | bar chart |

| Time series (1-3 lines) | Line plot with CI band | basic #3 | — |

| Time series (4+ lines) | Small multiples (subplot grid) | basic #12 | spaghetti plot |

| Distribution (1 group) | Violin + strip | basic #11 | histogram |

| Distribution (2-5 groups) | Rain Cloud Plot | academic #4 | box plot |

| Proportion/composition | Donut Chart or Stacked Area | basic #6, #8 | pie chart |

| Correlation matrix | Heatmap + dendrogram | advanced #14 | plain heatmap |

| 2D scatter + relationship | Scatter + regression + R² | basic #4 | — |

| 2D joint distribution (large N) | Hexbin + marginal histograms | competition #24 | plain scatter (overplotting) |

| 2D joint distribution (small N, clusters) | KDE contour + marginal density | competition #25 | plain scatter |

| 2D relationship + distribution | Scatter + regression + marginal density | competition #26 | scatter without marginals |

| High-dim features | t-SNE/UMAP scatter | academic #2 | — |

| 3D clustering outcomes (3 features) | 3D scatter + centroids | competition #27 | 2D scatter (loses dimension) |

| Multi-criteria evaluation | Radar chart | competition #5 | — |

| Feature importance | SHAP Summary Plot | advanced #7 | horizontal bar |

| Classification outcome | Confusion matrix | competition #10 | — |

| Binary classifier comparison | ROC + AUC | competition #11 | — |

| Probability reliability | Calibration Plot | advanced #11 | — |

### By problem domain (competition)

| Problem type | Recommended visuals | Recipes |

|---|---|---|

| Optimization (GA/PSO/SA) | Convergence curve + 3D surface + Pareto front | comp #1, #6, #3 |

| Scheduling/routing | Gantt chart + Network path | comp #15, #16 |

| Classification/clustering | Confusion matrix + ROC + 3D cluster scatter | comp #10, #11, #13 |

| Regression/prediction | Prediction vs Actual with CI band + Error Rain Cloud + Multi-step decay + Model accuracy heatmap | empirical #12, #14, #16, #13 |

| Sensitivity analysis | Tornado chart + Contour + 3D surface | comp #2, #14, #6 |

| Spatial data | China province choropleth + Spatiotemporal matrix | comp #7, #18 |

| Multi-objective | 2D Pareto + 3D Pareto surface | comp #3, #19 |

| Factor decomposition | Waterfall chart | comp #20, advanced #6 |

### By problem domain (academic/empirical)

| Manuscript type | Recommended visuals | Recipes |

|---|---|---|

| DID/causal inference | Parallel trends + Event study + Placebo | empirical #2, #3, #4 |

| Regression analysis | Forest plot + Heterogeneity forest + Marginal effects | empirical #1, #10, #15 |

| Prediction/forecasting | Prediction with CI band + Error Rain Cloud + Multi-step decay + Model heatmap | empirical #12, #14, #16, #13 |

| Deep learning | Training curves + Attention map + t-SNE | academic #3, #6, #2 |

| Model comparison | Grouped Bar + Method Comparison Heatmap + Radar | basic #1, advanced #16, comp #5 |

| Hyperparameter tuning | Sensitivity grid + 3D loss landscape | academic #7, #8 |

| Meta-analysis | Forest plot + Funnel plot | empirical #1, advanced #12 |

| Survival analysis | Kaplan-Meier curve | advanced #9 |

| Genomics/omics | Volcano plot + Cluster heatmap | advanced #10, #14 |

| Method agreement | Bland-Altman plot | advanced #8 |

### Anti-patterns (validate prior to generating — but use judgment)

Not every "enhancement" is appropriate. Validate this table, but choose based on clarity for your audience.

| ❌ If you were going to use... | ✅ Consider this instead | Why | When to enhancement |

|---|---|---|---|

| Single-metric bar chart for ranking | Lollipop Chart | Less visual noise for pure ranking | When showing 5+ items ranked by one metric |

| Horizontal bar for feature importance | SHAP Summary Plot | Shows direction + magnitude | When you have SHAP values available |

| Bar chart for ablation | Waterfall Chart | Shows incremental contribution | Always — waterfall is strictly better for ablation |

| Bar chart for prior to/following (2 groups) | Dumbbell Chart | Shows direction and magnitude of change | When comparing without deviation 2 conditions |

| Plain box plot | Rain Cloud Plot | Distribution shape + box stats + raw data | When sample size > 20 and distribution shape matters |

| Pie chart | Donut Chart | More modern, less visual distortion | Always |

| Plain heatmap | Heatmap + dendrogram | Adds clustering structure | When row/column ordering matters |

| Stacked bar (non-temporal) | Sankey Diagram | Shows flow direction | When data represents flow/routing |

| RdYlGn colormap | coolwarm or YlOrRd | Red-yellow-green = traffic light | Always |

**Keep using grouped bar chart when:**

- Comparing 3-5 methods across 2-5 metrics (this is what grouped bar charts are designed for)

- Your audience is competition judges or non-specialist reviewers who expect familiar chart types

- The data has clear, discrete categories on the x-axis

- You already have too many advanced charts in the manuscript and need visual variety

**Keep using line chart when:**

- Showing trends over time or continuous x-axis

- Comparing convergence curves or training progress

</figure_selection_guide>

<bar_chart_alternatives>

### 柱状图采用指南

柱状图是最通用、最易读的图形与表格类别之一。避免回避采用它。

**适合用柱状图的场景（直接用，不需替代）：**

- 3-5 个方法在 2-5 个指标上的对比 → 分组柱状图

- 类别数据的频次/计数对比 → 普通柱状图

- 需评委/读者一眼看懂的关键结果 → 分组柱状图

- 论文中已经有多个高级图形与表格，需平衡 → 柱状图

**适合用替代方案的场景：**

| 场景 | 替代方案 | 缘由 |

|------|---------|------|

| 单指标排名（5+项） | Lollipop Chart | 纯排名场景，棒棒糖更简洁 |

| 消融实验 | Waterfall Chart | 展示增量贡献，柱状图做不到 |

| 前后两组对比 | Dumbbell Chart | 展示变化方向和幅度 |

| 特征关键性（有SHAP值） | SHAP Summary Plot | 与此同时展示关键性和方向 |

| 多数据集排名变化 | Bump Chart | 展示排名交叉 |

**全篇一致性准则：** 同一读者任务优先采用同一图形语法。只有数据结构或比较任务改变时才更换图形类别，禁止为了“多样性”改用棒棒糖、雷达图或其他装饰性图形。

</bar_chart_alternatives>

不同图形与表格类别有不同的最优配色策略，不可一刀切：

### ⛔ 颜色采用通用准则

**数据颜色**（柱子、线条、散点等）：务必用 `PALETTE[i]` 或 `PALETTE_LIGHT[i]`，避免硬编码 hex 颜色。

**语义颜色**（上升/下降/中性等）：用 `COLORS['up']`、`COLORS['down']`、`COLORS['neutral']`，避免硬编码 `#27ae60` 或 `#e74c3c`。

**装饰颜色**（网格线/文字/标注框）：用 `COLORS['grid']`、`COLORS['text']`、`COLORS['bg_box']`。

**浅色变体**：仅在区分置信区间或同一语义层级时使用 `_lighten(PALETTE[0], 0.6)`，不得作为装饰背景。

这样切换配色方案（journal/soft/npg/colorblind）时，全部颜色自动化跟随。

配方代码中的硬编码颜色是历史遗留，写新代码时用上述变量替代。

### 柱状图（Bar Chart）

- **2 组对比**：用同色系深浅（如 `PALETTE[0]` + `PALETTE_LIGHT[0]`），避免用两种完全不同的颜色

- **3-5 组对比**：用 PALETTE 前 3-5 色，饱和度统一

- **单组多类别**：默认使用同一填充色；只高亮与结论直接相关的一项，避免每根柱子不同颜色或装饰渐变

- **⛔ 禁止**：plt.cm 渐变色、matplotlib 默认蓝色、超过 6 种不同颜色

### 折线图（Line Chart）

- **2-3 条线**：用高对比色（如 PALETTE[0] 实线 + PALETTE[1] 虚线），线宽 2pt，加标记点

- **4+ 条线**：用 PALETTE 前 n 色，不同线型（实线/虚线/点线/点划线）区分

- **带 CI 带**：主线用 PALETTE[0]，CI 带用同色 alpha=0.15

- **⛔ 禁止**：全部线同色、线宽 <1.5pt、无标记点

### 饼图（Pie Chart）

- 用 PALETTE 前 n 色 + `wedgeprops={'edgecolor':'white', 'linewidth':2}`

- 最大扇区用 PALETTE[0]，其余按大小排序用后续色

- 小于 5% 的扇区合并为"其他"

- **⛔ 禁止**：超过 7 个扇区、无白色分隔线、3D 效果

### 热力图（Heatmap）

- 有关性矩阵（正负对比）：`cmap='coolwarm'`，`center=0`，下三角 mask。**⛔ 避免用 `RdBu_r`**——深红深蓝太沉重，`coolwarm` 更柔和

- 方法对比热力图（归一化性能）：`cmap='YlGnBu'` 或 `cmap='coolwarm'`，浅色背景+深色高亮，配合白色数值标注

- 频率/计数：`cmap='YlOrRd'` 或 `cmap='Blues'`

- **⛔ 禁止**：`jet` colormap、`RdBu_r`（太深沉）、无数值标注、全矩阵（不 mask）

- **⛔ 反模式**：≤5 行的方法对比避免用深色热力图，改用 Radar chart 或 Dumbbell chart

### 散点图（Scatter）

- 单组：PALETTE[0]，`alpha=0.6`，`s=20-40`

- 多组：PALETTE 前 n 色，不同标记形状（o/s/^/D）

- 加回归线：`color=PALETTE[1]`，虚线

### 箱线图/小提琴图

- 用 PALETTE_LIGHT 填充 + PALETTE 边框

- 中位线用深色加粗

## 配色方案

**默认采用 Journal 配色方案。** 整体保持白底、低饱和、细网格和有限强调色；同一张图一般不超过 3 个主色，同一篇论文保持统一。只有类别确实较多时才扩展色数，并优先结合线型、标记和纹理区分。

`plot_utils.py` 给出了 7 组精选配色方案，通过 `setup_style(palette='名称')` 选取：

**Soft（★ 默认推荐）**

```python

setup_style()  # 默认就是 soft

# ['#5B9BD5', '#ED7D7D', '#7BC8A4', '#B0B0B0', '#9B8EC4', '#F4A261']

# 柔蓝 + 珊瑚粉 + 薄荷绿 + 浅灰 + 淡紫 + 暖杏

```

柔和明亮，适合有限类别对比。默认纯白背景，不使用大面积半透明装饰填充。

**Tableau 10（需 >6 色区分度时）**

```python

setup_style(palette='tableau')

# ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948', '#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC']

```

现代清新，10 色区分度最高，多组对比/折线图/散点图通用。

**NPG / Nature（自然科学）**

```python

setup_style(palette='npg')

# ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', ...]

```

鲜明对比，适合生物/化学/自然科学类论文。

**NEJM（统计/医学类）**

```python

setup_style(palette='nejm')

# ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91', '#EE4C97']

```

柔和优雅，适合统计分析、医学、实证研究类论文。

**SciencePlots（工程类）**

```python

setup_style(palette='science')

# ['#0C5DA5', '#00B945', '#FF9500', '#FF2C00', '#845B97', '#474747', '#9e9e9e']

```

经典学术风格，适合 IEEE/ACM/工程类论文。

**色盲友好（无障碍要求时）**

```python

setup_style(palette='colorblind')

```

**按场景选取推荐**：

| 场景 | 推荐配色 |

|------|---------|

| 竞赛论文 / 经管 / 统计建模 | soft（默认） |

| 多组对比（>6 组） | tableau |

| 自然科学 / 生物 / 化学 | npg |

| 医学 / 统计分析 / 实证研究 | nejm |

| IEEE / ACM / 工程类 | science |

| 无障碍要求 | colorblind |

| 论文印刷 / 低饱和克制表达 | journal |

**⛔ 已移除的土色配色**：jama（深灰绿+土灰）、lancet（深海蓝+暗红）、aaas（深紫+纯红+近黑）、morandi（灰调脏色）已从可选列表中移除。若旧代码使用这些名称，`setup_style()` 会自动回退到 Journal。

**渐变色（热力图/填充）**：用 `cmap='coolwarm'`（红蓝对比，柔和版）或 `cmap='YlOrRd'`（暖色渐变），避免用 `jet` 或 `RdBu_r`（太深沉）。

## 字体与排版

```python

plt.rcParams.update({

    'font.size': 11,                    # 正文字号

    'axes.labelsize': 12,               # 坐标轴标签稍大

    'axes.titlesize': 13,               # 标题再大一号

    'xtick.labelsize': 10,

    'ytick.labelsize': 10,

    'legend.fontsize': 10,

    'font.family': 'sans-serif',

    'mathtext.fontset': 'stix',         # 数学字体用 STIX（接近 Times）

})

```

## 提高图形信息效率的技巧

### 1. 去掉顶部和右侧边框（已在 plot_utils 中默认）

```python

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

```

### 2. 柱状图加数值标注

```python

for bar in bars:

    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,

            f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)

```

### 3. 折线图加标记点 + 置信带

```python

ax.plot(x, y, 'o-', markersize=5, linewidth=1.5, color=NATURE[0])

ax.fill_between(x, y_low, y_high, alpha=0.15, color=NATURE[0])

```

### 4. 热力图用 mask 只呈现下三角

```python

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', center=0)

```

### 5. 回归系数森林图（实证论文关键图）

```python

ax.errorbar(coefs, y_pos, xerr=[coefs-ci_low, ci_high-coefs],

            fmt='o', color=NATURE[3], ecolor='#95A5A6', capsize=4, markersize=6)

ax.axvline(x=0, color=NATURE[0], linestyle='--', linewidth=0.8, alpha=0.7)

```

### 6. 分组柱状图加误差棒

```python

bars = ax.bar(x + offset, vals, width, yerr=errs, capsize=3,

              color=NATURE[i], edgecolor='white', linewidth=0.5)

```

### 7. 多面板子图对齐

```python

fig, axes = plt.subplots(2, 2, figsize=(10, 8))

fig.tight_layout(pad=0.5)

# 每个子图加 (a) (b) (c) (d) 标签 — 用 set_title 紧贴子图顶部

for i, ax in enumerate(axes.flat):

    ax.set_title(f'({chr(97+i)})', fontsize=12, fontweight='bold', loc='left', pad=3)

```

> **⛔ tight_layout 的 pad 值务必 ≤ 0.5。**

> `pad=2.0` 在 SciencePlots 样式下会导致子图被压缩到极小（由于 SciencePlots 设定了紧凑的 subplot margins，

> 大 pad 值会继续挤压子图空间）。推荐值：`pad=0.5`（默认）、`pad=0.3`（紧凑多面板）。

> 若需子图间距更大，用 `hspace`/`wspace` 参数而不是增大 pad。

> **⛔ 子图标注务必用 `ax.set_title()` 而不是 `ax.text(transAxes)`。**

> 缘由：`ax.text(-0.08, 1.05, ..., transform=ax.transAxes)` 的坐标是相针对 axes 逻辑区域的，

> 但 `set_aspect('equal')` 或 `constrained_layout` 会让真实绘图区域在分配空间内缩小，

> 导致 `y=1.05` 看起来离图很远。`set_title(loc='left', pad=3)` 会自动化贴着真实渲染出的

> axes 边框上方，不受 aspect ratio 影响。

### 8. 留存时保证高质量

```python

fig.savefig('图表/fig_xxx.pdf', dpi=300, bbox_inches='tight', pad_inches=0.05)

```

## 避免的常见丑图

- ❌ 默认蓝色单色（用多色配色方案）

- ❌ 图内加 `plt.title()`（标题只在 LaTeX caption 中）

- ❌ 默认灰色网格线（去掉或用极淡的虚线）

- ❌ 图例遮挡数据（放在空白区域或图外）

- ❌ 坐标轴标签用变量名（如 `col_1`，应改为有意义的中文/英文标签）

- ❌ 字体太小（打印后看不清）

- ❌ 用 `jet` colormap（色盲不友好，用 `coolwarm` 或 `viridis`）

## ⛔ 防遮挡准则（文字/数据/曲线互相遮挡是最常见的图形与表格质量问题）

### 图例位置

- **首选**：`ax.legend(loc='best')` 让 matplotlib 自动化找空白区域

- **若 best 还是遮挡**：移到图外 `ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')`

- **折线图 4+ 条线**：用图外图例，避免挤在图内

- **永远避免**：把图例放在数据密集区域的正中间

### 数值标注

- **柱状图标注**：放在柱子顶部上方（`va='bottom'`），避免放在柱子内部

- **若柱子太矮标注会重叠**：只标注最大值和最小值，或用 `rotation=45` 斜着标

- **散点图标注**：用 `adjustText` 库自动化避免重叠（`from adjustText import adjust_text`），或人工设 `xytext` 偏移

- **热力图数值**：字号用 8-9pt，若格子太小就不标数值

- **⛔ 标注避免放在坐标轴刻度区域**：竖线标注（如 Makespan 线）的文字标签放在图内顶部（`y=0.95, transform=ax.transAxes`），避免放在 X 轴附近。X 轴附近是刻度标签的区域，文字会重叠。无误做法：

  ```python

  # ❌ 错误：标注放在 X 轴附近，和刻度重叠

  ax.text(makespan, 0, f'Makespan={makespan}', color='red')

  # ✅ 正确：标注放在图内顶部，用 transform 定位

  ax.axvline(makespan, color='red', ls='--', lw=1.5)

  ax.text(makespan, 0.97, f'Makespan={makespan}', color='red',

          transform=ax.get_xaxis_transform(), ha='right', va='top', fontsize=9)

  ```

- **⛔ 多个标注在同一区域时**：用 `adjustText` 或人工错开 y 坐标，避免让文字叠在一起

### 曲线/数据点重叠

- **多条折线重叠**：用不同线型（实线/虚线/点线/点划线）+ 不同标记（o/s/^/D）区分

- **散点图数据密集**：降低 `alpha=0.5-0.7`，或用 hexbin/KDE 等高线代替

- **多组箱线图/小提琴图**：保证组间间距充足，`width` 避免超过 0.8

### 坐标轴标签

- **长标签**：用 `rotation=45, ha='right'` 斜着呈现，或换行 `'第一行\n第二行'`

- **中文标签**：各个标签不超过 6 个字，超过就缩写或换行

- **刻度太密**：用 `ax.xaxis.set_major_locator(MaxNLocator(nbins=6))` 减少刻度数

### 通用技巧

```python

# 保存时确保不裁切标签

fig.savefig('xxx.pdf', bbox_inches='tight', pad_inches=0.1)

# 自动调整子图间距

fig.tight_layout()

# 散点标注防重叠（需要 pip install adjustText）

from adjustText import adjust_text

texts = [ax.text(x[i], y[i], labels[i], fontsize=8) for i in range(len(x))]

adjust_text(texts, arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

```

## SciencePlots 库（可选）

若环境中安装了 `SciencePlots`，可一行代码切换到 Nature/IEEE 风格：

```python

# pip install SciencePlots

import scienceplots

plt.style.use(['science', 'no-latex'])  # 不依赖 LaTeX 的科学风格

# plt.style.use(['science', 'ieee'])    # IEEE 风格

# plt.style.use(['science', 'nature'])  # Nature 风格（需要 LaTeX）

```

注意：SciencePlots 的 `science` 和 `nature` 风格默认需 LaTeX，用 `no-latex` 可避免依赖。

## TikZ 技术路线图/架构图模板

TikZ 画出来丑的根本缘由：没有颜色分层、没有分阶段色块、节点样式太朴素。好的技术路线图应是分阶段分色、自上而下清晰流动的。

### 设计原则

1. **分阶段着色**：各个研究阶段用不同的背景色块（浅色填充 + 深色边框），一眼看出层次

2. **直角矩形**：全部矩形节点使用直角方框，不设置 `rounded corners`；菱形、圆形、六边形、圆柱等其他形状保持原有语义

3. **箭头统一**：用 `-{Stealth[length=6pt]}`，粗细 `line width=0.8pt`

4. **留白充足**：节点间距 ≥1cm，避免挤在一起

5. **字体统一**：节点内文字用 `\small` 或 `\footnotesize`，避免太大

6. **禁止装饰阴影**：流程图节点不使用 `drop shadow`，层次通过位置、边框粗细和少量强调色表达

### 模板 1/2/3：已废弃（被模板 4/9/10/11 替代）

模板 1（纵向路线图）、模板 2（问题关系图）、模板 3（模型架构图）是早期简单版本，出现左侧文字重叠、线穿过节点等问题。**⛔ 避免采用模板 1/2/3，改用模板 4/9/10/11。**

- 模板 1 的场景 → 用模板 4 或模板 9

- 模板 2 的场景 → 用模板 10（管道式）

- 模板 3 的场景 → Meta-model-agent 自由画架构图，遵守防遮挡准则即可

### 模板 4：通用研究技术路线图（全部论文类别通用）

白底 + 浅灰分组 + 直角主节点 + 白色子节点 + 深灰箭头。仅对关键节点使用一个低饱和强调色，不依赖阴影制造层次。

**完整代码**：

- 通用版：见 `demo_roadmap_template4.tex`

- 竞赛专用版（多问题双行+星号标注）：见 `demo_roadmap_competition.tex`

**竞赛论文必须参考 `demo_roadmap_competition.tex`**：每个问题可有 2 行主节点+子节点，子节点 4 个一排，用 `$^{\bigstar}$` 标注最优方法。

**采用准则：复制下面的完整代码，只改节点文字和数量。**

**关键样式定义**（直接复制到 tikzpicture 参数）：

```latex

\begin{tikzpicture}[scale=1.0,

    main/.style={rectangle, minimum width=5.5cm, minimum height=0.7cm,

        draw=blue!80, line width=0.7pt, fill=blue!6,

        font=\small\bfseries, align=center,

        drop shadow={opacity=0.15, shadow xshift=0.5pt, shadow yshift=-0.5pt}},

    sub/.style={rectangle, minimum width=2.4cm, minimum height=0.6cm,

        draw=teal!70, line width=0.5pt, fill=white,

        font=\footnotesize, align=center},

    dashbox/.style={rectangle, draw=gray!40, dashed, line width=0.7pt, fill=gray!2},

    bigarrow/.style={-stealth, line width=1.4pt, color=blue!70},

    smarrow/.style={-stealth, line width=0.5pt, color=gray!50},

    label/.style={font=\small\bfseries, color=black!70},

]

```

**各个阶段的结构模式**（重复此模式，改文字和子节点数量）：

```latex

% === 阶段 N ===

% 1. 虚线框（先画，节点覆盖在上面）

\node[dashbox, minimum width=13cm, minimum height=2cm] (boxN) at (0, Y) {};

\node[label, anchor=north west] at (boxN.north west) {\scriptsize 阶段名称};

% 2. 主节点（蓝色，居中）

\node[main] (mN) at (0, Y+0.35) {主步骤名称};

% 3. 子节点（白色，一行排列，间距 2.8cm）

\node[sub] (sNa) at (-4.2, Y-0.65) {方法A};

\node[sub] (sNb) at (-1.4, Y-0.65) {方法B};

\node[sub] (sNc) at (1.4, Y-0.65) {方法C};

\node[sub] (sNd) at (4.2, Y-0.65) {方法D};

\foreach \x in {sNa,sNb,sNc,sNd} {\draw[smarrow] (mN) -- (\x);}

% 4. 阶段间粗箭头

\draw[bigarrow] (0, Y-1.4) -- (0, Y-2.0);

```

**双层阶段**（一个阶段有两行主节点时，虚线框高度改为 4.2cm）：

```latex

\node[dashbox, minimum width=13cm, minimum height=4.2cm] (boxN) at (0, Y) {};

% 第一行主节点 + 子节点

\node[main] (mN) at (0, Y+1.7) {第一步};

\node[sub] ... % 子节点

% 第二行主节点 + 子节点

\node[main] (mNb) at (0, Y-0.5) {第二步};

\node[sub] ... % 子节点

```

**关键参数**：

- 虚线框宽度统一 13cm，单层高度 2cm，双层高度 4.2cm

- 子节点 x 坐标：4 个时用 -4.2, -1.4, 1.4, 4.2；3 个时用 -2.8, 0, 2.8

- 阶段间粗箭头间距 0.6cm

- 标注最佳方法用 `$^{\bigstar}$` 上标

**采用准则：复制下面的完整代码，只改节点文字和数量。从下方 5 套配色中选一套替换 primary/.style 和 sub/.style 的颜色值。**

<tikz_color_schemes>

#### TikZ 架构图配色方案（5 套，按论文类别选取）

**方案 A：低饱和蓝灰+淡青（★ 默认，适合经管/统计/社科/竞赛）**

```latex

main/.style={fill={rgb,255:red,200;green,218;blue,235},

    draw={rgb,255:red,140;green,170;blue,200}, ...},

sub/.style={fill={rgb,255:red,218;green,232;blue,220},

    draw={rgb,255:red,165;green,200;blue,175}, ...},

bigarrow: color={rgb,255:red,74;green,144;blue,184}

```

**方案 B：钢蓝+浅灰蓝（适合 CS/AI/工程类）**

```latex

main/.style={fill={rgb,255:red,180;green,210;blue,235},

    draw={rgb,255:red,120;green,160;blue,200}, ...},

sub/.style={fill={rgb,255:red,220;green,230;blue,240},

    draw={rgb,255:red,170;green,190;blue,210}, ...},

bigarrow: color={rgb,255:red,70;green,100;blue,150}

```

**方案 C：薰衣草紫+淡粉（适合医学/生物/心理学）**

```latex

main/.style={fill={rgb,255:red,210;green,195;blue,230},

    draw={rgb,255:red,170;green,150;blue,200}, ...},

sub/.style={fill={rgb,255:red,235;green,215;blue,225},

    draw={rgb,255:red,200;green,175;blue,195}, ...},

bigarrow: color={rgb,255:red,130;green,100;blue,160}

```

**方案 D：青绿+薄荷（适合环境/地理/生态）**

```latex

main/.style={fill={rgb,255:red,175;green,220;blue,210},

    draw={rgb,255:red,120;green,185;blue,170}, ...},

sub/.style={fill={rgb,255:red,215;green,235;blue,225},

    draw={rgb,255:red,170;green,205;blue,190}, ...},

bigarrow: color={rgb,255:red,60;green,130;blue,120}

```

**方案 E：暖灰+赭石（适合人文/历史/法学，低调沉稳）**

```latex

main/.style={fill={rgb,255:red,225;green,210;blue,195},

    draw={rgb,255:red,190;green,170;blue,150}, ...},

sub/.style={fill={rgb,255:red,235;green,230;blue,220},

    draw={rgb,255:red,200;green,195;blue,180}, ...},

bigarrow: color={rgb,255:red,140;green,120;blue,100}

```

**选取推荐**：

| 论文类别 | 推荐方案 |

|---------|---------|

| 经管/统计/社科/竞赛 | A（低饱和蓝灰+淡青）★ 默认 |

| CS/AI/电子/通信 | B（钢蓝+浅灰蓝） |

| 医学/生物/心理 | C（薰衣草紫+淡粉） |

| 环境/地理/生态/农学 | D（青绿+薄荷） |

| 人文/历史/法学/哲学 | E（暖灰+赭石） |

All schemes share the same structural rules: white background, straight-corner rectangles, restrained grouping, and clear draw order. Color changes must carry meaning rather than decoration.

</tikz_color_schemes>

```latex

\begin{figure}[htbp]

\centering

\begin{tikzpicture}[scale=0.85, every node/.style={scale=0.85},

    main/.style={fill={rgb,255:red,200;green,218;blue,235},

        draw={rgb,255:red,140;green,170;blue,200}, minimum width=4.5cm, minimum height=0.6cm, align=center,

        font=\small, line width=0.4pt},

    sub/.style={fill={rgb,255:red,218;green,232;blue,220},

        draw={rgb,255:red,165;green,200;blue,175}, minimum width=2cm, minimum height=0.5cm, align=center,

        font=\footnotesize, line width=0.3pt},

    bigarrow/.style={-{Stealth[length=7pt,width=5pt]}, line width=1.8pt,

        color={rgb,255:red,74;green,144;blue,184}},

    smarrow/.style={-{Stealth[length=3pt]}, line width=0.3pt, color=gray!40},

    lbl/.style={font=\small\bfseries, color=black},

    dashbox/.style={draw=gray!40, dashed, fill={rgb,255:red,248;green,249;blue,250}},

]

% 第一步：虚线框（先画，节点覆盖在上面）

\node[dashbox, minimum width=10.5cm, minimum height=1.6cm] (b1) at (0, -0.3) {};

\node[lbl, anchor=east] at ([xshift=-6pt]b1.west) {综述};

\node[dashbox, minimum width=10.5cm, minimum height=5.2cm] (b2) at (0, -3.15) {};

\node[lbl, anchor=east] at ([xshift=-6pt]b2.west) {模型构建};

\node[dashbox, minimum width=10.5cm, minimum height=2.2cm] (b3) at (0, -6.65) {};

\node[lbl, anchor=east] at ([xshift=-6pt]b3.west) {实证分析};

\node[dashbox, minimum width=10.5cm, minimum height=2.2cm] (b4) at (0, -9.35) {};

\node[lbl, anchor=east] at ([xshift=-6pt]b4.west) {策略应用};

\node[dashbox, minimum width=10.5cm, minimum height=2.2cm] (b5) at (0, -12.05) {};

\node[lbl, anchor=east] at ([xshift=-6pt]b5.west) {结论};

% 第二步：节点和箭头

% 阶段1

\node[main] (m1) at (0, 0) {绪论};

\draw[bigarrow] (0,-0.7) -- (0,-1.3);

% 阶段2

\node[main] (m2) at (0,-1.8) {理论基础};

\node[sub] (s2a) at (-2.8,-2.7) {文献回顾};

\node[sub] (s2b) at (-0.9,-2.7) {概念定义};

\node[sub] (s2c) at (0.9,-2.7) {理论框架};

\node[sub] (s2d) at (2.8,-2.7) {研究假设};

\foreach \x in {s2a,s2b,s2c,s2d} {\draw[smarrow] (m2) -- (\x);}

\node[main] (m2b) at (0,-3.6) {模型设定};

\foreach \x in {s2b,s2c} {\draw[smarrow] (\x) -- (m2b);}

\node[sub] (s2e) at (-2.2,-4.5) {变量定义};

\node[sub] (s2f) at (0,-4.5) {计量模型};

\node[sub] (s2g) at (2.2,-4.5) {识别策略};

\foreach \x in {s2e,s2f,s2g} {\draw[smarrow] (m2b) -- (\x);}

\draw[bigarrow] (0,-5.2) -- (0,-5.8);

% 阶段3

% 阶段3 — 以下节点文字仅为示例，根据实际研究内容替换

% Example nodes shown below. Replace with actual research content:

% 预测类：数据预处理/模型构建/模型对比/预测应用

% 分类类：特征工程/模型训练/分类评估/模型解释

% 评价类：指标构建/权重确定/综合评价/结果分析

% 因果推断类：描述统计/回归分析/稳健检验/异质分析

\node[main] (m3) at (0,-6.3) {模型构建与分析};

\node[sub] (s3a) at (-3.2,-7.2) {数据预处理};

\node[sub] (s3b) at (-1.1,-7.2) {模型构建};

\node[sub] (s3c) at (1.1,-7.2) {模型对比};

\node[sub] (s3d) at (3.2,-7.2) {结果分析};

\foreach \x in {s3a,s3b,s3c,s3d} {\draw[smarrow] (m3) -- (\x);}

\draw[bigarrow] (0,-7.9) -- (0,-8.5);

% 阶段4

\node[main] (m4) at (0,-9) {策略应用};

\node[sub] (s4a) at (-2.2,-9.9) {制度优化};

\node[sub] (s4b) at (0,-9.9) {实施路径};

\node[sub] (s4c) at (2.2,-9.9) {保障措施};

\foreach \x in {s4a,s4b,s4c} {\draw[smarrow] (m4) -- (\x);}

\draw[bigarrow] (0,-10.6) -- (0,-11.2);

% 阶段5

\node[main] (m5) at (0,-11.7) {结论};

\node[sub] (s5a) at (-2.2,-12.6) {主要结论};

\node[sub] (s5b) at (0,-12.6) {创新点};

\node[sub] (s5c) at (2.2,-12.6) {研究展望};

\foreach \x in {s5a,s5b,s5c} {\draw[smarrow] (m5) -- (\x);}

\end{tikzpicture}

\caption{研究技术路线图}

\label{fig:research-roadmap}

\end{figure}

```

**架构要点（Meta-model-agent 画技术路线图时务必遵循）：**

1. **不依赖 `backgrounds` 和 `fit` 库**——只用 `tikz` + `arrows.meta` + `positioning` + `shapes.geometric` + `calc`

2. **避免灰色大背景 `\fill`**——白底最安全，不会出现黑色外围

3. 虚线框用 `dashbox` 样式（人工坐标 + minimum width/height），极浅灰填充 `rgb(248,249,250)`

4. **先画虚线框，再画节点**——利用绘制次序，节点的 fill 自然覆盖虚线框

5. 左侧标签用 `lbl` 样式，**颜色务必是 `color=black`**，避免蓝色

6. 主节点统一橙色（`rgb(240,195,150)`），子节点统一绿色（`rgb(185,215,180)`）

7. 阶段间用蓝色粗箭头 `bigarrow`，节点间用灰色细箭头 `smarrow`

8. `scale=0.85` 保证一页放得下，阶段控制在 4-5 个

9. 子节点间距不少于 1.5cm，超过 4 个分两行

10. **禁止用 `on background layer`、`fit=()`、灰色大背景 `\fill`**

#### 虚线框坐标计算准则（⛔ 防止框重叠）

虚线框用人工坐标，务必按以下准则计算，不可靠猜：

**单层阶段**（1 个主节点 + 1 行子节点）：

- 主节点 y 坐标 = `Y`

- 子节点 y 坐标 = `Y - 0.9`

- 虚线框中心 y = `(Y + Y-0.9) / 2 = Y - 0.45`

- 虚线框高度 = `1.6cm`

- 粗箭头从 `Y - 1.6` 到 `Y - 2.2`（间距 0.6）

- 下一阶段主节点 y = `Y - 2.7`（间距 = 上一阶段底部 + 0.5）

**双层阶段**（2 个主节点 + 2 行子节点）：

- 第一主节点 y = `Y`，第一行子节点 y = `Y - 0.9`

- 第二主节点 y = `Y - 1.8`，第二行子节点 y = `Y - 2.7`

- 虚线框中心 y = `(Y + Y-2.7) / 2 = Y - 1.35`

- 虚线框高度 = `3.4cm`

- 粗箭头从 `Y - 3.4` 到 `Y - 4.0`

- 下一阶段主节点 y = `Y - 4.5`

**三层阶段**（主节点 + 子节点 + 第二主节点 + 第二行子节点 + 第三行子节点）：

- 虚线框高度 = `5.2cm`，按真实内容界限计算

**关键公式**：

```

dashbox_center_y = (最高节点y + 最低节点y) / 2

dashbox_height = (最高节点y - 最低节点y) + 1.4cm  (上下各留 0.7cm padding)

bigarrow_start_y = 最低节点y - 0.7

bigarrow_end_y = bigarrow_start_y - 0.6

next_stage_main_y = bigarrow_end_y - 0.5

```

**校验方法**：各个虚线框的底边 y = `center_y - height/2`，下一个虚线框的顶边 y = `next_center_y + next_height/2`。两者之间务必有 ≥ 0.3cm 的间距，反之会重叠。

```latex

    % 阶段间粗箭头（灰蓝色，和竖条同色系）

    bigarrow/.style={-{Stealth[length=8pt, width=6pt]}, line width=2pt,

        color={rgb,255:red,90;green,120;blue,150}},

    % 节点间细箭头

    arrow/.style={-{Stealth[length=4pt]}, line width=0.5pt, color=gray!60},

]

% ========== 阶段一：研究设计 ==========

\node[stagelabel, rotate=90] (L1) at (-6.5, 0) {研究设计};

\node[stagebox] (B1) at (0, 0) {};

\node[main] (m1) at (0, 0.8) {研究问题确定};

\node[sub] (s1a) at (-3, -0.3) {文献梳理};

\node[sub] (s1b) at (-1, -0.3) {理论分析};

\node[sub] (s1c) at (1, -0.3) {假设提出};

\node[sub] (s1d) at (3, -0.3) {研究设计};

\draw[arrow] (m1) -- (s1a); \draw[arrow] (m1) -- (s1b);

\draw[arrow] (m1) -- (s1c); \draw[arrow] (m1) -- (s1d);

% 阶段间箭头

\draw[bigarrow] (0, -1.8) -- (0, -2.5);

% ========== 阶段二：数据与变量 ==========

\node[stagelabel, rotate=90] (L2) at (-6.5, -4.2) {数据与变量};

\node[stagebox] (B2) at (0, -4.2) {};

\node[main] (m2) at (0, -3.4) {数据收集与处理};

\node[sub] (s2a) at (-3.5, -4.5) {数据来源};

\node[sub] (s2b) at (-1.2, -4.5) {变量构建};

\node[sub] (s2c) at (1.2, -4.5) {描述性统计};

\node[sub] (s2d) at (3.5, -4.5) {相关性分析};

\draw[arrow] (m2) -- (s2a); \draw[arrow] (m2) -- (s2b);

\draw[arrow] (m2) -- (s2c); \draw[arrow] (m2) -- (s2d);

% 阶段间箭头

\draw[bigarrow] (0, -6) -- (0, -6.7);

% ========== 阶段三：实证分析 ==========

\node[stagelabel, rotate=90] (L3) at (-6.5, -8.8) {实证分析};

\node[stagebox, minimum height=3.8cm] (B3) at (0, -8.8) {};

\node[main] (m3) at (0, -7.6) {模型构建};

% 子节点分两行 — 以下节点文字仅为示例，依据真实研究内容替换

\node[sub] (s3a) at (-3.5, -8.8) {数据预处理};

\node[sub] (s3b) at (-1.2, -8.8) {模型构建};

\node[sub] (s3c) at (1.2, -8.8) {模型对比};

\node[sub] (s3d) at (3.5, -8.8) {结果分析};

\draw[arrow] (m3) -- (s3a); \draw[arrow] (m3) -- (s3b);

\draw[arrow] (m3) -- (s3c); \draw[arrow] (m3) -- (s3d);

\node[main] (m3b) at (0, -10.1) {模型诊断与检验};

% 阶段间箭头

\draw[bigarrow] (0, -11) -- (0, -11.7);

% ========== 阶段四：结论 ==========

\node[stagelabel, rotate=90] (L4) at (-6.5, -12.8) {结论建议};

\node[stagebox, minimum height=2cm] (B4) at (0, -12.8) {};

\node[main] (m4) at (0, -12.4) {研究结论};

\node[sub] (s4a) at (-2, -13.4) {政策建议};

\node[sub] (s4b) at (0, -13.4) {研究局限};

\node[sub] (s4c) at (2, -13.4) {未来展望};

\draw[arrow] (m4) -- (s4a); \draw[arrow] (m4) -- (s4b); \draw[arrow] (m4) -- (s4c);

\end{tikzpicture}

\caption{研究技术路线图}

\label{fig:research-roadmap}

\end{figure}

```

**架构要点（模板 4 通用规则）：**

1. **绘制顺序决定层级**：先画灰色大背景 → 再画白色虚线框 → 最后画节点和箭头。Avoid use `on background layer` or `fit` library

2. 虚线框用 `dashbox` 样式（手动坐标，白色填充），不用 `fit`

3. 左侧阶段标签水平书写，放在虚线框外面左侧

4. 从上方 5 套配色方案中选一套，整张图统一使用。Avoid mix schemes or use a different color per stage

5. 阶段之间用粗箭头（`bigarrow`），节点之间用灰色细箭头（`smarrow`）

6. 纵向布局，从上到下流动

7. 配色必须低饱和协调，禁止纯蓝/纯绿/纯红高饱和色

8. 子节点间距至少 1.2cm，超过 4 个分两行

### 常见丑图 vs 好图对比

| 丑图特征 | 改进方法 |

|----------|---------|

| 每个阶段不同颜色 | 选一套配色方案，整张图统一 main+sub 两色 |

| 用了 `on background layer` 导致黑底 | 用绘制顺序控制层级 |

| 圆角方框 | 删除 `rounded corners`，使用直角矩形 |

| 箭头太细看不清 | 阶段间用 `bigarrow`（1.8pt） |

| 节点挤在一起 | 子节点间距至少 1.2cm |

| 没有层次感 | 灰色大背景 + 白色虚线框 |

| 箭头交叉乱 | 用 `|-` 和 `-|` 走直角路径，避免斜线交叉 |

| 字体太大 | 节点内用 `\small`，标签用 `\footnotesize` |

### 模板 9：圆形编号 + 卡片分层（高级经管/实证风格）

**视觉特征**：左侧圆形编号+阶段名称 + 浅色卡片区域 + 方法节点/工具节点双层信息 + 右侧胶囊输出标签。适合方法论丰富的实证研究。

**完整代码**（复制后只改节点文字和阶段数量）：

```latex

\begin{figure}[htbp]

\centering

\begin{tikzpicture}[

    phasenum/.style={circle, fill={rgb,255:red,#1}, minimum size=22pt,

        font=\footnotesize\bfseries, text=white, inner sep=0pt},

    phasename/.style={font=\small\bfseries, color={rgb,255:red,#1}, anchor=west},

    method/.style={fill={rgb,255:red,#1}, draw={rgb,255:red,#2},

        minimum width=3.4cm, minimum height=0.85cm,

        align=center, font=\small, line width=0.5pt},

    tool/.style={fill={rgb,255:red,248;green,248;blue,248},

        draw={rgb,255:red,210;green,210;blue,210}, minimum width=1.8cm, minimum height=0.5cm, align=center,

        font=\scriptsize, line width=0.3pt},

    outputtag/.style={fill={rgb,255:red,#1}, minimum width=1.6cm, minimum height=0.4cm, align=center,

        font=\tiny\bfseries, text=white, inner sep=2pt},

    pipe/.style={-{Stealth[length=7pt, width=5pt]}, line width=1.8pt,

        color={rgb,255:red,200;green,210;blue,225}},

    inner/.style={-{Stealth[length=3pt]}, line width=0.4pt, color=gray!45},

    card/.style={fill={rgb,255:red,#1}, line width=0pt},

]

% Phase 1: 研究设计（蓝色）

\fill[card={245;green,250;blue,255}] (-1, 2.3) rectangle (15.5, -0.8);

\node[phasenum={100;green,160;blue,210}] at (-0.2, 1.7) {1};

\node[phasename={80;green,140;blue,190}] at (0.4, 1.7) {研究设计};

\node[method={232;green,243;blue,252}{165;green,200;blue,230}] (rq) at (3.2, 1.0) {研究问题提出};

\node[method={232;green,243;blue,252}{165;green,200;blue,230}] (lit) at (7.2, 1.0) {系统文献综述};

\node[method={232;green,243;blue,252}{165;green,200;blue,230}] (hypo) at (11.2, 1.0) {假设与框架构建};

\draw[inner] (rq) -- (lit); \draw[inner] (lit) -- (hypo);

\node[tool] at (3.2, -0.05) {文献计量}; \node[tool] at (5.5, -0.05) {知识图谱};

\node[tool] at (8.2, -0.05) {理论推演}; \node[tool] at (11.2, -0.05) {概念模型};

\node[outputtag={100;green,160;blue,210}] at (14.2, 1.0) {理论模型};

\draw[pipe] (7.2, -0.8) -- (7.2, -1.6);

% Phase 2: 数据准备（绿色）— 同理结构，换色

% Phase 3: 实证分析（橙色）— 三行：模型设定→机制检验→稳健性

% Phase 4: 结论推荐（紫色）

% 每阶段重复：卡片背景 → 编号+名称 → 方法节点行 → 工具节点行 → 交付标签 → 管道箭头

\end{tikzpicture}

\caption{研究技术路线图}

\end{figure}

```

**四阶段配色**（蓝→绿→橙→紫）：

- 研究设计：编号 `rgb(100,160,210)`，卡片 `rgb(245,250,255)`，方法节点 `rgb(232,243,252)`

- 数据准备：编号 `rgb(80,170,130)`，卡片 `rgb(245,252,248)`，方法节点 `rgb(230,246,237)`

- 实证分析：编号 `rgb(215,155,75)`，卡片 `rgb(255,251,243)`，方法节点 `rgb(255,244,228)`

- 结论建议：编号 `rgb(150,120,180)`，卡片 `rgb(250,247,255)`，方法节点 `rgb(242,237,252)`

**架构要点**：

1. 不依赖 `backgrounds`/`fit` 库，用绘制顺序控制层级

2. 左侧圆形编号 + 阶段名称文字（不要用色带竖条）

3. 方法节点和工具节点形成双层信息，方法节点 y 间距 ≥ 1.0cm

4. 工具节点间距 ≥ 2.2cm，一行最多 5 个

5. 右侧胶囊标签标注每阶段输出物

6. 完整示例见 `demo_roadmap_research_premium.tex`

---

### 模板 10：管道分段 + 并行分支 + 汇聚（数据科学/竞赛风格）

**视觉特征**：5段管道色块 + 白色卡片带顶部彩色装饰条 + 并行三分支建模 + 汇聚节点 + 圆角胶囊方法标签 + 左侧圆形编号。适合多模型对比、数据驱动研究。

**完整代码**：见 `demo_roadmap_research_pipeline.tex`

**五阶段配色**（蓝→绿→橙→紫→灰绿）：

- 问题定义：标题 `rgb(85,155,210)`，背景 `rgb(244,249,255)`

- 特征工程：标题 `rgb(75,162,125)`，背景 `rgb(242,251,244)`

- 模型构建：标题 `rgb(212,158,75)`，背景 `rgb(255,250,240)`

- 评估验证：标题 `rgb(142,115,182)`，背景 `rgb(249,244,255)`

- 结论建议：标题 `rgb(102,132,112)`，背景 `rgb(246,249,246)`

**架构要点**：

1. 每个 Stage 是一个大圆角色块（`draw=none` 无边框），内含白色卡片

2. 卡片顶部有 0.15cm 彩色装饰条

3. Stage 3 用并行三分支 + Σ 汇聚节点，展示多模型对比

4. 方法标签用圆角胶囊样式，标签间距 ≥ 2cm

5. 汇聚节点和下方卡片间距 ≥ 0.8cm

---

### 模板 5：算法流程图（带判断分支）

```latex

\begin{figure}[htbp]

\centering

\begin{tikzpicture}[

    node distance=0.8cm,

    procedure/.style={fill=blue!10, draw=blue!50, minimum width=3.5cm, minimum height=0.8cm, align=center,

        font=\small, line width=0.6pt},

    decision/.style={fill=orange!12, draw=orange!50, diamond, aspect=2.5,

        minimum width=2cm, align=center, font=\small, line width=0.6pt,

        inner sep=1pt},

    io/.style={fill=gray!8, draw=gray!50, minimum width=3cm, minimum height=0.7cm, align=center, font=\small},

    arrow/.style={-{Stealth[length=5pt]}, line width=0.7pt, color=gray!70},

    yesno/.style={font=\footnotesize, color=gray!60},

]

\node[io] (start) {输入数据 $D$};

\node[process, below=of start] (init) {初始化参数 $\theta_0$};

\node[process, below=of init] (compute) {计算目标函数 $f(\theta)$};

\node[process, below=of compute] (update) {更新参数 $\theta \leftarrow \theta - \alpha\nabla f$};

\node[decision, below=of update] (conv) {收敛?};

\node[io, below=of conv] (output) {输出最优解 $\theta^*$};

\draw[arrow] (start) -- (init);

\draw[arrow] (init) -- (compute);

\draw[arrow] (compute) -- (update);

\draw[arrow] (update) -- (conv);

\draw[arrow] (conv) -- node[yesno, right] {是} (output);

\draw[arrow] (conv.west) -- ++(-1.5,0) node[yesno, above] {否} |- (compute.west);

\end{tikzpicture}

\caption{优化算法流程图}

\label{fig:algorithm-flow}

\end{figure}

```

### 模板 6：数据处理 Pipeline（横向多阶段）

```latex

\begin{figure}[htbp]

\centering

\begin{tikzpicture}[

    node distance=0.3cm,

    stage/.style={fill=#1!12, draw=#1!50, minimum width=2.2cm, minimum height=2.2cm, align=center,

        font=\small, line width=0.6pt},

    detail/.style={font=\tiny, color=gray!40, align=center, text width=2cm},

    arrow/.style={-{Stealth[length=6pt]}, line width=1pt, color=gray!50},

]

\node[stage=blue] (raw) {\textbf{原始数据}\\[2pt]\footnotesize 多源采集};

\node[stage=blue, right=1cm of raw] (clean) {\textbf{数据清洗}\\[2pt]\footnotesize 缺失值/异常值};

\node[stage=teal, right=1cm of clean] (feat) {\textbf{特征工程}\\[2pt]\footnotesize 变量构建};

\node[stage=teal, right=1cm of feat] (model) {\textbf{模型训练}\\[2pt]\footnotesize 参数优化};

\node[stage=blue, right=1cm of model] (eval) {\textbf{评估验证}\\[2pt]\footnotesize 交叉验证};

\node[detail, below=0.3cm of raw] {CSV/API/\\数据库};

\node[detail, below=0.3cm of clean] {插值/IQR/\\标准化};

\node[detail, below=0.3cm of feat] {PCA/交互项/\\时序特征};

\node[detail, below=0.3cm of model] {XGBoost/\\DNN/SVM};

\node[detail, below=0.3cm of eval] {RMSE/AUC/\\$R^2$};

\draw[arrow] (raw) -- (clean);

\draw[arrow] (clean) -- (feat);

\draw[arrow] (feat) -- (model);

\draw[arrow] (model) -- (eval);

\draw[arrow, dashed, color=red!40] (eval.north) -- ++(0,0.8) -| (feat.north)

    node[pos=0.25, above, font=\tiny, color=red!50] {特征调优};

\end{tikzpicture}

\caption{数据处理与建模流程}

\label{fig:pipeline}

\end{figure}

```

### 模板 7：经管/统计 — 变量关系路径图（中介效应）

```latex

\begin{figure}[htbp]

\centering

\begin{tikzpicture}[

    node distance=2cm and 3cm,

    var/.style={fill=#1!12, draw=#1!50, minimum width=3cm, minimum height=1cm, align=center,

        font=\small, line width=0.7pt},

    arrow/.style={-{Stealth[length=5pt]}, line width=0.8pt},

    coef/.style={font=\footnotesize, fill=white, inner sep=2pt},

]

\node[var=blue] (x) {\textbf{自变量}\\数字化转型};

\node[var=orange, above right=1.5cm and 3.5cm of x] (m) {\textbf{中介变量}\\创新能力};

\node[var=red, below right=1.5cm and 3.5cm of x] (y) {\textbf{因变量}\\企业绩效};

\draw[arrow, color=blue!60] (x) -- node[coef, below] {$c'$ (直接效应)} (y);

\draw[arrow, color=orange!60] (x) -- node[coef, above left] {$a$ (H1)} (m);

\draw[arrow, color=red!60] (m) -- node[coef, above right] {$b$ (H2)} (y);

\node[fill=gray!8, draw=gray!40, minimum width=2.5cm, minimum height=0.7cm, align=center,

    font=\footnotesize, below=1.5cm of y] (ctrl) {控制变量\\企业规模/行业/年份};

\draw[-{Stealth[length=4pt]}, dashed, color=gray!40, line width=0.5pt] (ctrl) -- (y);

\node[font=\footnotesize\itshape, color=gray!50, below=0.3cm of x] {H3: $a \times b$ 中介效应};

\end{tikzpicture}

\caption{理论模型与研究假设}

\label{fig:theoretical-model}

\end{figure}

```

### 模板 8：竞赛 — 单问题求解流程图（带分支+判断+并行对比）

```latex

\begin{figure}[htbp]

\centering

\begin{tikzpicture}[

    node distance=0.7cm and 1.2cm,

    step/.style={fill=#1!10, draw=#1!45, minimum width=3.5cm, minimum height=0.75cm, align=center,

        font=\small, line width=0.5pt},

    substep/.style={fill=gray!6, draw=gray!35, minimum width=2.6cm, minimum height=0.6cm, align=center,

        font=\footnotesize, line width=0.4pt},

    decision/.style={fill=orange!10, draw=orange!45, diamond, aspect=2.8,

        minimum width=1.5cm, align=center, font=\small, line width=0.5pt, inner sep=1pt},

    note/.style={font=\tiny, color=gray!40, text width=3cm, align=left},

    arrow/.style={-{Stealth[length=4pt]}, line width=0.5pt, color=gray!55},

    yesno/.style={font=\tiny, color=gray!50},

    phaselabel/.style={font=\tiny\bfseries, color=#1!50, fill=#1!6, inner sep=2pt},

]

% 阶段一：数据准备

\node[phaselabel=blue] (L1) at (-3.5, 0) {数据准备};

\node[step=blue] (input) at (0, 0) {读取附件数据};

\node[step=blue, below=of input] (eda) {数据探索与可视化};

\node[decision, below=0.8cm of eda] (missing) {有缺失值?};

\node[substep, right=1.5cm of missing] (fill) {插值/删除处理};

\node[step=blue, below=0.8cm of missing] (clean) {清洗后数据集};

\draw[arrow] (input) -- (eda); \draw[arrow] (eda) -- (missing);

\draw[arrow] (missing) -- node[yesno, above] {是} (fill);

\draw[arrow] (fill.south) |- (clean);

\draw[arrow] (missing) -- node[yesno, right] {否} (clean);

% 阶段二：建模（并行两种方法）

\node[phaselabel=teal] (L2) at (-3.5, -4.5) {模型构建};

\node[step=teal, below=0.8cm of clean] (formulate) {建立数学模型};

\node[substep, below left=0.8cm and 0.8cm of formulate] (method1) {方法A：精确求解};

\node[substep, below right=0.8cm and 0.8cm of formulate] (method2) {方法B：启发式};

\draw[arrow] (clean) -- (formulate);

\draw[arrow] (formulate.south) -- ++(0,-0.3) -| (method1.north);

\draw[arrow] (formulate.south) -- ++(0,-0.3) -| (method2.north);

\node[note, right=0.3cm of formulate] {目标函数\\约束条件\\决策变量};

% 阶段三：对比选优

\node[substep, below=0.7cm of method1] (result1) {结果A};

\node[substep, below=0.7cm of method2] (result2) {结果B};

\node[step=orange, below=1.2cm of formulate] at (0, -8.5) (compare) {方法对比与选优};

\draw[arrow] (method1) -- (result1); \draw[arrow] (method2) -- (result2);

\draw[arrow] (result1.south) |- (compare.west);

\draw[arrow] (result2.south) |- (compare.east);

% 阶段四：校验

\node[step=orange, below=0.7cm of compare] (verify) {结果验证与分析};

\node[step=red, below=0.7cm of verify] (sense) {灵敏度/稳健性分析};

\node[step=red, below=0.7cm of sense] (output) {输出最终方案};

\draw[arrow] (compare) -- (verify); \draw[arrow] (verify) -- (sense); \draw[arrow] (sense) -- (output);

\end{tikzpicture}

\caption{问题一求解流程}

\label{fig:solve-flow-q1}

\end{figure}

```

### TikZ 通用样式速查

```latex

% 在 tikzpicture 外部定义（放在 preamble 或 visual 环境开头）

\usetikzlibrary{arrows.meta, positioning, shapes.geometric, calc, decorations.pathreplacing, shadows}

% 常用颜色搭配（按阶段）

% 阶段一：blue    阶段二：teal    阶段三：orange    阶段四：red

% 辅助/数据：gray  高亮/关键：purple

% 节点间距参考

% 紧凑型：node distance=0.5cm and 0.8cm

% 标准型：node distance=0.8cm and 1.2cm

% 宽松型：node distance=1.2cm and 2cm

% 箭头样式

% 主过程：-{Stealth[length=5pt]}, line width=0.7pt, color=gray!70

% 数据流：-{Stealth[length=4pt]}, line width=0.5pt, dashed, color=gray!40

% 反馈：-{Stealth[length=4pt]}, line width=0.5pt, dashed, color=red!40

```
