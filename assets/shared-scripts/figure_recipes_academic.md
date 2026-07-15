# AI/CS 学术论文 — 高级图形与表格代码范例

For: ICLR/NeurIPS/ICML/JMLR/TPAMI and CS thesis papers. Inspired by high-end Chinese academic visualization style:

gradient fills, KDE contour backgrounds, rain cloud distributions, annotation arrows, significance brackets.

All recipes assume `from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten; setup_style()`.

Recommended palettes: soft (default), science (classic), npg (Nature), colorblind (accessibility).

---

## 1. Ablation Study Bar Chart — 消融实验柱状图

**Use case**: Show incremental contribution of each module. Essential for AI experiment sections.

**Enhancements**: Waterfall connector lines between bars, green→red gradient coloring by performance, delta arrows with values.

```python

import numpy as np

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

configs = ['Full Model', '- Attention', '- Residual', '- Augment', '- Attn & Res', 'Baseline']

scores = [92.3, 89.1, 90.5, 88.7, 85.2, 82.0]

drops = [0, 3.2, 1.8, 3.6, 7.1, 10.3]

fig, ax = plt.subplots(figsize=(8, 5))

# Gradient coloring: green (high) → red (low)

cmap = plt.cm.YlOrRd

norm = plt.Normalize(min(scores) - 2, max(scores) + 2)

colors = [cmap(norm(s)) for s in scores]

bars = ax.bar(range(len(configs)), scores, color=[_lighten(c, 0.35) for c in colors],

              edgecolor=colors, linewidth=1.2, width=0.65, zorder=3)

# Waterfall connector lines between bars

for j in range(len(configs) - 1):

    ax.plot([j + 0.325, j + 0.675], [scores[j], scores[j]],

            color=COLORS['ref_line'], linewidth=0.8, linestyle='--', alpha=0.5, zorder=2)

# Value labels on top + delta arrows inside bars

for j, (bar, score, drop) in enumerate(zip(bars, scores, drops)):

    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,

            f'{score:.1f}', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

    if drop > 0:

        # Delta arrow annotation

        ax.annotate(f'↓{drop:.1f}',

                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height() - 1),

                    fontsize=8, ha='center', va='top', color='white', fontweight='bold',

                    bbox=dict(boxstyle='square,pad=0.15', facecolor=COLORS['down'],

                              alpha=0.7, edgecolor='none'))

# Highlight Full Model and Baseline

for idx in [0, len(configs) - 1]:

    bars[idx].set_edgecolor(PALETTE[0] if idx == 0 else PALETTE[3])

    bars[idx].set_linewidth(2)

ax.set_xticks(range(len(configs)))

ax.set_xticklabels(configs, rotation=18, ha='right', fontsize=9)

ax.set_ylabel('Accuracy (%)', fontsize=11)

ax.set_ylim(78, 96)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(axis='y', alpha=0.15, linestyle='--')

# Dashed line connecting Full → Baseline

ax.plot([0, len(configs) - 1], [scores[0], scores[-1]], '--',

        color=COLORS['ref_line'], linewidth=1, alpha=0.4, zorder=1)

ax.text(0.98, 0.05, f'Total drop: {scores[0] - scores[-1]:.1f}',

        transform=ax.transAxes, fontsize=8, color=COLORS['ref_line'],

        ha='right', va='bottom', style='italic',

        bbox=dict(boxstyle='square,pad=0.3', facecolor='white',

                  edgecolor=COLORS['grid'], alpha=0.9))

fig.tight_layout()

save_fig(fig, '图表/fig_ablation.pdf')

```

**★ 防遮挡技巧（Ablation Bar Chart 专用）：**

```python

# 1. Delta 箭头放在柱子外侧（右边）：不要放在柱子内部

# 2. 数值标签放在柱子顶部：va='bottom'，和 delta 箭头不在同一侧

# 3. 瀑布连接线用虚线（linestyle='--'）：不要用实线（会和柱子边框混淆）

# 4. ylim 上方留 15%：给 delta 箭头和标签留空间

```

---

## 2. Training Curves — 训练曲线（Loss + Metric 双轴）

**Use case**: Training procedure visualization showing convergence. Essential for experiment sections.

**Enhancements**: Gradient fill under loss curve, early stopping vertical line, best epoch star marker, LR schedule inset.

```python

import numpy as np

import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

np.random.seed(42)

epochs = np.arange(1, 101)

train_loss = 2.5 * np.exp(-0.04 * epochs) + 0.15 + np.random.normal(0, 0.02, 100)

val_loss = 2.5 * np.exp(-0.035 * epochs) + 0.25 + np.random.normal(0, 0.03, 100)

train_acc = (1 - train_loss / 3.0 + np.random.normal(0, 0.005, 100)) * 100

val_acc = (1 - val_loss / 3.0 + np.random.normal(0, 0.008, 100)) * 100

# LR schedule (cosine decay)

lr = 1e-3 * (0.5 * (1 + np.cos(np.pi * epochs / 100)))

fig, ax1 = plt.subplots(figsize=(8, 5))

ax2 = ax1.twinx()

# Loss curves with gradient fill

l1, = ax1.plot(epochs, train_loss, color=PALETTE[0], linewidth=1.8, label='Train Loss')

l2, = ax1.plot(epochs, val_loss, color=PALETTE[0], linewidth=1.8, linestyle='--',

               label='Val Loss', alpha=0.7)

# Gradient fill under train loss

for layer, alpha in enumerate([0.15, 0.08, 0.03]):

    ax1.fill_between(epochs, train_loss.min() - 0.1 + layer * 0.05,

                     train_loss - layer * 0.03,

                     alpha=alpha, color=PALETTE[0], linewidth=0)

# Accuracy curves

l3, = ax2.plot(epochs, train_acc, color=PALETTE[1], linewidth=1.8, label='Train Acc')

l4, = ax2.plot(epochs, val_acc, color=PALETTE[1], linewidth=1.8, linestyle='--',

               label='Val Acc', alpha=0.7)

# Best epoch (min val loss) — star marker

best_epoch = np.argmin(val_loss) + 1

ax1.scatter(best_epoch, val_loss[best_epoch - 1], marker='*', s=200, color=COLORS['down'],

            edgecolor='white', linewidth=1, zorder=6)

ax1.annotate(f'Best: epoch {best_epoch}\nloss={val_loss[best_epoch - 1]:.3f}',

             xy=(best_epoch, val_loss[best_epoch - 1]),

             xytext=(best_epoch + 15, val_loss[best_epoch - 1] + 0.3),

             fontsize=8, fontweight='bold', color=COLORS['down'],

             arrowprops=dict(arrowstyle='->', color=COLORS['down'], lw=1.2),

             bbox=dict(boxstyle='square,pad=0.3', facecolor='white',

                       edgecolor=COLORS['down'], alpha=0.9))

# Early stopping line

early_stop = best_epoch + 10

ax1.axvline(x=early_stop, color=COLORS['ref_line'], linestyle=':', linewidth=1, alpha=0.6)

ax1.text(early_stop + 1, ax1.get_ylim()[1] * 0.9, 'Early\nStopping',

         fontsize=7.5, color=COLORS['ref_line'], style='italic')

# LR schedule inset

ax_inset = inset_axes(ax1, width='30%', height='25%', loc='center right',

                      borderpad=2)

ax_inset.plot(epochs, lr * 1000, color=PALETTE[2], linewidth=1.2)

ax_inset.set_xlabel('Epoch', fontsize=6)

ax_inset.set_ylabel('LR (×10⁻³)', fontsize=6)

ax_inset.tick_params(labelsize=5)

ax_inset.set_title('LR Schedule', fontsize=7, fontweight='bold')

ax_inset.grid(alpha=0.15, linestyle='--')

for spine in ax_inset.spines.values():

    spine.set_linewidth(0.5)

ax1.set_xlabel('Epoch', fontsize=11)

ax1.set_ylabel('Loss', fontsize=11, color=PALETTE[0])

ax2.set_ylabel('Accuracy (%)', fontsize=11, color=PALETTE[1])

ax1.tick_params(axis='y', labelcolor=PALETTE[0])

ax2.tick_params(axis='y', labelcolor=PALETTE[1])

lines = [l1, l2, l3, l4]

ax1.legend(lines, [l.get_label() for l in lines], frameon=True, edgecolor=COLORS['grid'],

           fontsize=9, loc='center left')

ax1.grid(alpha=0.15, linestyle='--')

ax1.spines['top'].set_visible(False)

fig.tight_layout()

save_fig(fig, '图表/fig_training_curve.pdf')

```

**★ 防遮挡技巧（Training Curves 专用）：**

```python

# 1. Best epoch 标注用 arrowprops 连线：标注框放在曲线上方空白区

# 2. Early stopping 竖线标签放在图顶部：不要放在曲线交叉区域

# 3. LR schedule inset 放在右上角：不要和主曲线重叠

# 4. 双轴（loss + accuracy）的标签颜色和对应曲线一致

```

---

## 3. t-SNE / UMAP Visualization — 降维可视化

**Use case**: High-dimensional feature visualization showing cluster quality.

**Enhancements**: Per-class KDE contour backgrounds, 95% confidence ellipses, class center labels in white boxes.

```python

import numpy as np

import matplotlib.pyplot as plt

from scipy.stats import gaussian_kde

from matplotlib.patches import Ellipse

from 工具.plot_utils import setup_style, PALETTE, COLORS, _lighten

setup_style()

np.random.seed(42)

classes = ['Class A', 'Class B', 'Class C', 'Class D']

n_per = 150

embeddings, labels = [], []

for i, cls in enumerate(classes):

    center = np.random.randn(2) * 4

    pts = center + np.random.randn(n_per, 2) * 0.8

    embeddings.append(pts)

    labels.extend([cls] * n_per)

embeddings = np.vstack(embeddings)

fig, ax = plt.subplots(figsize=(7, 6))

for i, cls in enumerate(classes):

    mask = np.array(labels) == cls

    pts = embeddings[mask]

    # KDE contour background

    xy = pts.T

    kde = gaussian_kde(xy, bw_method=0.4)

    xg = np.linspace(pts[:, 0].min() - 2, pts[:, 0].max() + 2, 80)

    yg = np.linspace(pts[:, 1].min() - 2, pts[:, 1].max() + 2, 80)

    Xg, Yg = np.meshgrid(xg, yg)

    Z = kde(np.vstack([Xg.ravel(), Yg.ravel()])).reshape(Xg.shape)

    ax.contourf(Xg, Yg, Z, levels=5, cmap=plt.cm.Blues if i == 0 else

                plt.cm.Oranges if i == 1 else plt.cm.Greens if i == 2 else plt.cm.Purples,

                alpha=0.15)

    ax.contour(Xg, Yg, Z, levels=3, colors=PALETTE[i], alpha=0.3, linewidths=0.5)

    # 95% confidence ellipse

    cov = np.cov(pts.T)

    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    angle = np.degrees(np.arctan2(eigenvectors[1, 1], eigenvectors[0, 1]))

    width, height = 2 * np.sqrt(eigenvalues * 5.991)  # chi2 95%

    ellipse = Ellipse(xy=pts.mean(axis=0), width=width, height=height, angle=angle,

                      facecolor='none', edgecolor=PALETTE[i], linewidth=1.2,

                      linestyle='--', alpha=0.6)

    ax.add_patch(ellipse)

    # Scatter points

    ax.scatter(pts[:, 0], pts[:, 1], s=10, alpha=0.45, color=PALETTE[i],

               label=cls, edgecolor='none')

    # Class center label in white box

    cx, cy = pts.mean(axis=0)

    ax.annotate(cls, xy=(cx, cy), fontsize=9, fontweight='bold', color=PALETTE[i],

                ha='center', va='center',

                bbox=dict(boxstyle='square,pad=0.4', facecolor='white',

                          edgecolor=PALETTE[i], alpha=0.9, linewidth=1))

ax.set_xlabel('Dimension 1', fontsize=11)

ax.set_ylabel('Dimension 2', fontsize=11)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=9, markerscale=3, loc='best')

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(alpha=0.15, linestyle='--')

fig.tight_layout()

fig.savefig('图表/fig_tsne.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

**★ 防遮挡技巧（t-SNE / UMAP 专用）：**

```python

# 1. 类别中心标签用 bbox 白底 + 粗边框：确保在散点云上可读

# 2. 置信椭圆用低 alpha（0.08）：不要遮挡散点

# 3. 类别数 >6 时：只标注最大的 3-4 个簇，其余用图例

# 4. 散点用小尺寸（s=8-15）和低 alpha（0.4）：给标签让出视觉空间

```

---

## 4. Attention Heatmap — 注意力热力图

**Use case**: Transformer attention weight visualization.

**Enhancements**: Row/column dendrograms for clustering, attention entropy annotation per row, refined colorbar.

```python

import numpy as np

import matplotlib.pyplot as plt

import matplotlib.gridspec as gridspec

import seaborn as sns

from scipy.cluster.hierarchy import dendrogram, linkage

from scipy.spatial.distance import pdist

from 工具.plot_utils import setup_style, PALETTE, COLORS

setup_style()

np.random.seed(42)

tokens = ['[CLS]', 'The', 'model', 'learns', 'to', 'attend', 'key', 'features', '[SEP]']

n = len(tokens)

attn = np.random.dirichlet(np.ones(n) * 0.5, size=n)

attn += np.eye(n) * 0.3

attn[0, 5:8] += 0.2

attn[3, 6:8] += 0.15

attn = attn / attn.sum(axis=1, keepdims=True)

fig = plt.figure(figsize=(8, 7))

gs = gridspec.GridSpec(2, 2, width_ratios=[1, 6], height_ratios=[1, 6],

                       wspace=0.02, hspace=0.02)

# Top dendrogram

ax_dtop = fig.add_subplot(gs[0, 1])

Z_col = linkage(pdist(attn.T), method='ward')

dendrogram(Z_col, ax=ax_dtop, no_labels=True, color_threshold=0,

           above_threshold_color=PALETTE[0])

ax_dtop.set_xticks([])

ax_dtop.set_yticks([])

for spine in ax_dtop.spines.values():

    spine.set_visible(False)

# Left dendrogram

ax_dleft = fig.add_subplot(gs[1, 0])

Z_row = linkage(pdist(attn), method='ward')

dendrogram(Z_row, ax=ax_dleft, orientation='left', no_labels=True,

           color_threshold=0, above_threshold_color=PALETTE[0])

ax_dleft.set_xticks([])

ax_dleft.set_yticks([])

for spine in ax_dleft.spines.values():

    spine.set_visible(False)

# Main heatmap

ax_heat = fig.add_subplot(gs[1, 1])

im = ax_heat.imshow(attn, cmap='YlOrRd', aspect='auto')

ax_heat.set_xticks(range(n))

ax_heat.set_xticklabels(tokens, rotation=45, ha='right', fontsize=8)

ax_heat.set_yticks(range(n))

ax_heat.set_yticklabels(tokens, fontsize=8)

ax_heat.set_xlabel('Key', fontsize=10)

ax_heat.set_ylabel('Query', fontsize=10)

# Value annotations (only > 0.12)

for i in range(n):

    for j in range(n):

        if attn[i, j] > 0.12:

            ax_heat.text(j, i, f'{attn[i, j]:.2f}', ha='center', va='center',

                         fontsize=6.5, color='white' if attn[i, j] > 0.25 else 'black')

# Attention entropy annotation (right side)

entropy = -np.sum(attn * np.log(attn + 1e-10), axis=1)

for i, (tok, h) in enumerate(zip(tokens, entropy)):

    ax_heat.text(n + 0.3, i, f'H={h:.2f}', fontsize=6.5, va='center', color=COLORS['ref_line'])

fig.colorbar(im, ax=ax_heat, shrink=0.6, label='Attention Weight', pad=0.12)

fig.tight_layout()

fig.savefig('图表/fig_attention.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

---

## 5. Architecture Comparison Radar — 架构对比雷达图

**Use case**: Multiple methods across multiple datasets. Primary outcome visual.

**Enhancements**: Heatmap-style background coloring on bars, rank numbers on top, significance markers (bold = best).

```python

import numpy as np

import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

datasets = ['CIFAR-10', 'CIFAR-100', 'ImageNet', 'STL-10']

methods = ['Ours', 'ViT', 'ResNet', 'DeiT']

scores = np.array([[95.2, 78.3, 82.1, 93.5], [93.1, 75.8, 80.5, 91.2],

                    [91.5, 73.2, 79.8, 89.8], [92.8, 76.1, 81.2, 90.5]])

stds = np.random.uniform(0.3, 0.8, scores.shape)

fig, ax = plt.subplots(figsize=(9, 5))

x = np.arange(len(datasets))

width = 0.18

# Heatmap-style coloring: normalize scores per dataset

for j in range(len(datasets)):

    col_min, col_max = scores[:, j].min() - 2, scores[:, j].max() + 2

    cmap = plt.cm.YlGn

    norm = plt.Normalize(col_min, col_max)

    ranks = np.argsort(np.argsort(-scores[:, j])) + 1  # 1 = best

    for i, method in enumerate(methods):

        offset = (i - len(methods) / 2 + 0.5) * width

        color = cmap(norm(scores[i, j]))

        bar = ax.bar(x[j] + offset, scores[i, j], width, yerr=stds[i, j], capsize=3,

                      color=_lighten(color, 0.35), edgecolor=color, linewidth=1.0,

                      error_kw={'elinewidth': 0.8, 'capthick': 0.6})

        # Rank number on top

        rank = ranks[i]

        is_best = rank == 1

        ax.text(x[j] + offset, scores[i, j] + stds[i, j] + 0.4,

                f'{"★" if is_best else ""}{scores[i, j]:.1f}',

                ha='center', fontsize=7, fontweight='bold' if is_best else 'normal',

                color=COLORS['down'] if is_best else COLORS['text'])

# Method legend (manual)

for i, method in enumerate(methods):

    ax.bar([], [], color=_lighten(PALETTE[i], 0.4), label=method, edgecolor=PALETTE[i], linewidth=1.2)

ax.set_xticks(x)

ax.set_xticklabels(datasets, fontsize=10)

ax.set_ylabel('Accuracy (%)', fontsize=11)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=9, ncol=len(methods))

ax.set_ylim(68, 100)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(axis='y', alpha=0.15, linestyle='--')

fig.tight_layout()

save_fig(fig, '图表/fig_dataset_compare.pdf')

```

**★ 防遮挡技巧（Multi-Dataset Compare 专用）：**

```python

# 1. 排名数字放在柱子内部顶端：fontsize=7, color='white'（深色柱子）或 color=PALETTE[i]（浅色柱子）

# 2. 星号标记放在 error bar 上方：不要放在柱子顶部（会和排名数字重叠）

# 3. 数据集数 >5 时：x 轴标签 rotation=15

# 4. 图例放在图外上方：bbox_to_anchor=(0.5, 1.12), ncol=n_methods

```

---

## 6. Hyperparameter Sensitivity — 超参数灵敏度图

**Use case**: Key hyperparameter impact on performance. 2x2 subplot grid.

**Enhancements**: Gradient fill between min/max performance range, optimal region green shading, enhanced annotations.

```python

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.patches import Rectangle

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

params = {

    'Learning Rate': ([1e-4, 3e-4, 1e-3, 3e-3, 1e-2],

                      [88.2, 91.5, 92.3, 90.1, 85.4],

                      [86.0, 89.8, 90.5, 87.3, 82.1],

                      [90.1, 93.0, 94.0, 92.5, 88.2]),

    'Hidden Dim': ([64, 128, 256, 512, 1024],

                   [87.5, 90.2, 92.3, 92.1, 91.8],

                   [85.2, 88.0, 90.1, 89.8, 89.5],

                   [89.5, 92.0, 94.2, 94.0, 93.8]),

    'Num Layers': ([2, 4, 6, 8, 12],

                   [86.3, 89.8, 92.3, 91.5, 90.2],

                   [83.8, 87.5, 90.0, 89.2, 87.8],

                   [88.5, 91.8, 94.5, 93.5, 92.2]),

    'Dropout': ([0.0, 0.1, 0.2, 0.3, 0.5],

                [89.1, 91.2, 92.3, 91.8, 88.5],

                [86.8, 89.0, 90.1, 89.5, 86.0],

                [91.0, 93.2, 94.2, 93.8, 90.5]),

}

fig, axes = plt.subplots(2, 2, figsize=(10, 7))

for idx, (name, (x_vals, y_mean, y_min, y_max)) in enumerate(params.items()):

    ax = axes.flat[idx]

    x_pos = range(len(x_vals))

    # Gradient fill between min and max

    for layer, alpha in enumerate([0.20, 0.12, 0.06]):

        shrink = layer * 0.3

        ax.fill_between(x_pos,

                        np.array(y_min) + shrink,

                        np.array(y_max) - shrink,

                        alpha=alpha, color=PALETTE[idx], linewidth=0)

    # Min/max boundary lines

    ax.plot(x_pos, y_min, '--', color=PALETTE[idx], linewidth=0.8, alpha=0.4)

    ax.plot(x_pos, y_max, '--', color=PALETTE[idx], linewidth=0.8, alpha=0.4)

    # Mean line

    ax.plot(x_pos, y_mean, 'o-', color=PALETTE[idx], linewidth=2, markersize=7,

            markeredgecolor='white', markeredgewidth=1.2)

    # Optimal point highlight

    best_i = np.argmax(y_mean)

    ax.scatter(best_i, y_mean[best_i], s=150, color=PALETTE[idx], zorder=5,

               edgecolor='white', linewidth=2.5)

    # Optimal region shading (±1 of best)

    opt_left = max(0, best_i - 1)

    opt_right = min(len(x_vals) - 1, best_i + 1)

    ax.axvspan(opt_left - 0.3, opt_right + 0.3, alpha=0.08, color=COLORS['up'],

               label='Optimal region')

    ax.annotate(f'{y_mean[best_i]:.1f}', xy=(best_i, y_mean[best_i]),

                xytext=(0, 12), textcoords='offset points', fontsize=9, fontweight='bold',

                ha='center', color=PALETTE[idx],

                bbox=dict(boxstyle='square,pad=0.2', facecolor='white',

                          edgecolor=PALETTE[idx], alpha=0.9, linewidth=0.5))

    ax.set_xticks(x_pos)

    ax.set_xticklabels([str(v) for v in x_vals], fontsize=8)

    ax.set_xlabel(name, fontsize=10)

    ax.set_ylabel('Accuracy (%)', fontsize=10)

    ax.spines['top'].set_visible(False)

    ax.spines['right'].set_visible(False)

    ax.grid(alpha=0.15, linestyle='--')

    ax.set_title(f'({chr(97 + idx)})', fontsize=12, fontweight='bold', loc='left', pad=3)

fig.tight_layout(pad=0.5)

save_fig(fig, '图表/fig_hyperparam.pdf')

```

---

## 7. Confusion Matrix — 混淆矩阵

**Use case**: Distribution + box stats + raw data in one visual. Method comparison.

**Enhancements**: Gradient violin fill, significance brackets with p-values, Cohen's d effect size.

```python

import numpy as np

import matplotlib.pyplot as plt

from scipy.stats import gaussian_kde, ttest_ind

import matplotlib.colors as mcolors

from 工具.plot_utils import setup_style, PALETTE, COLORS, _lighten

setup_style()

np.random.seed(42)

groups = ['Ours', 'Method A', 'Method B']

data = [np.random.normal(92, 3, 100), np.random.normal(88, 4, 100),

        np.random.normal(85, 5, 100)]

def cohens_d(g1, g2):

    n1, n2 = len(g1), len(g2)

    pooled_std = np.sqrt(((n1 - 1) * g1.std() ** 2 + (n2 - 1) * g2.std() ** 2) / (n1 + n2 - 2))

    return (g1.mean() - g2.mean()) / pooled_std

# ★ 自适应高度

_fig_h = max(4, len(groups) * 1.0 + 1)

fig, ax = plt.subplots(figsize=(8, _fig_h))

for i, (name, d) in enumerate(zip(groups, data)):

    pos = i

    # Gradient half-violin (right side)

    kde = gaussian_kde(d, bw_method=0.3)

    yr = np.linspace(d.min() - 4, d.max() + 4, 300)

    density = kde(yr)

    density_norm = density / density.max() * 0.38

    base_rgb = mcolors.to_rgb(PALETTE[i])

    for layer in range(6):

        frac = layer / 6

        alpha = 0.35 - frac * 0.05

        ax.fill_betweenx(yr, pos + frac * 0.02, pos + density_norm * (1 - frac * 0.12),

                         alpha=alpha, color=PALETTE[i], linewidth=0)

    ax.plot(pos + density_norm, yr, color=PALETTE[i], linewidth=1.2, alpha=0.8)

    # Box plot (left, narrow)

    bp = ax.boxplot(d, positions=[pos - 0.18], widths=0.12, vert=True, patch_artist=True,

                    boxprops=dict(facecolor=_lighten(PALETTE[i], 0.4),

                                  edgecolor=PALETTE[i], linewidth=1.2),

                    medianprops=dict(color=COLORS['text'], linewidth=1.8),

                    whiskerprops=dict(linewidth=1, color=PALETTE[i]),

                    capprops=dict(linewidth=1, color=COLORS['ref_line']),

                    flierprops=dict(marker='', markersize=0))

    # Jittered strip (far left)

    jitter = np.random.uniform(-0.08, 0.08, len(d))

    ax.scatter(pos - 0.38 + jitter, d, s=6, alpha=0.2, color=PALETTE[i], edgecolor='none')

    # Mean diamond

    ax.scatter(pos - 0.18, d.mean(), marker='D', s=45, color=PALETTE[i],

               edgecolor='white', linewidth=1.2, zorder=5)

# Significance brackets with p-values and Cohen's d

def add_bracket(ax, x1, x2, y, p_val, d_val, h=1.5):

    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=COLORS['text'], linewidth=0.8)

    stars = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'n.s.'

    ax.text((x1 + x2) / 2, y + h + 0.2, f'{stars} (p={p_val:.1e})\nd={d_val:.2f}',

            ha='center', va='bottom', fontsize=7, color=COLORS['text'],

            bbox=dict(boxstyle='square,pad=0.2', facecolor=COLORS['bg_box'],

                      edgecolor=COLORS['grid'], alpha=0.9, linewidth=0.3))

y_max = max(d.max() for d in data) + 2

for idx, (g1, g2) in enumerate([(0, 1), (0, 2)]):

    _, p = ttest_ind(data[g1], data[g2])

    d_val = cohens_d(data[g1], data[g2])

    add_bracket(ax, g1, g2, y_max + idx * 7, p, d_val)

ax.set_xticks(range(len(groups)))

ax.set_xticklabels(groups, fontsize=10)

ax.set_ylabel('Accuracy (%)', fontsize=11)

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(axis='y', alpha=0.15, linestyle='--')

fig.tight_layout()

fig.savefig('图表/fig_raincloud.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

**★ 防遮挡技巧（Rain Cloud Plot 专用）：**

```python

# 1. 显著性括号从最内层开始画：最近的两组先画，跨组的画在外层

# 2. 括号 y 位置逐层递增：每层 +0.05 * y_range

# 3. Cohen's d 标注放在括号中间上方：fontsize=7.5

# 4. 组数 >5 时：只标注 p < 0.01 的显著性对比，省略不显著的

```

---

## 8. Feature Importance (SHAP-style) — 特征关键性

**Use case**: Visualize loss surface topology and optimization difficulty.

**Enhancements**: Optimization trajectory with gradient coloring (early=red, late=blue), saddle point annotations, contour projection.

```python

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.collections import LineCollection

from 工具.plot_utils import setup_style, PALETTE, COLORS, _lighten

setup_style()

x = np.linspace(-2, 2, 80)

y = np.linspace(-2, 2, 80)

X, Y = np.meshgrid(x, y)

Z = 0.5 * (X ** 2 + Y ** 2) - 0.3 * np.cos(2 * np.pi * X) * np.cos(2 * np.pi * Y) + 1

fig = plt.figure(figsize=(8, 6))

ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_surface(X, Y, Z, cmap='coolwarm', alpha=0.65, edgecolor='none',

                       antialiased=True, rstride=2, cstride=2)

# Contour projection on floor

ax.contour(X, Y, Z, zdir='z', offset=Z.min() - 0.5, cmap='coolwarm', alpha=0.3, levels=15)

# Optimization trajectory (simulated SGD path)

np.random.seed(42)

traj_x = [1.8]

traj_y = [1.5]

lr = 0.05

for step in range(60):

    gx = traj_x[-1] - 0.3 * 2 * np.pi * np.sin(2 * np.pi * traj_x[-1]) * np.cos(2 * np.pi * traj_y[-1])

    gy = traj_y[-1] - 0.3 * 2 * np.pi * np.cos(2 * np.pi * traj_x[-1]) * np.sin(2 * np.pi * traj_y[-1])

    nx = traj_x[-1] - lr * gx + np.random.normal(0, 0.02)

    ny = traj_y[-1] - lr * gy + np.random.normal(0, 0.02)

    traj_x.append(np.clip(nx, -2, 2))

    traj_y.append(np.clip(ny, -2, 2))

traj_x = np.array(traj_x)

traj_y = np.array(traj_y)

traj_z = 0.5 * (traj_x ** 2 + traj_y ** 2) - 0.3 * np.cos(2 * np.pi * traj_x) * np.cos(

    2 * np.pi * traj_y) + 1 + 0.05

# Gradient-colored trajectory (red→blue)

for k in range(len(traj_x) - 1):

    frac = k / (len(traj_x) - 1)

    color = plt.cm.coolwarm(1 - frac)  # red (early) → blue (late)

    ax.plot(traj_x[k:k + 2], traj_y[k:k + 2], traj_z[k:k + 2],

            color=color, linewidth=1.5, alpha=0.8)

# Start and end markers

ax.scatter([traj_x[0]], [traj_y[0]], [traj_z[0]], color=COLORS['down'], s=80,

           marker='^', edgecolor='white', linewidth=1, zorder=6, label='Start')

ax.scatter([traj_x[-1]], [traj_y[-1]], [traj_z[-1]], color=COLORS['up'], s=80,

           marker='*', edgecolor='white', linewidth=1, zorder=6, label='End')

# Global minimum

ax.scatter([0], [0], [Z.min()], color=COLORS['down'], s=120, marker='*',

           edgecolor='white', zorder=5, label='Global Min')

# Saddle point annotations

saddle_pts = [(-1, 0), (0, -1), (1, 0)]

for sx, sy in saddle_pts:

    sz = 0.5 * (sx ** 2 + sy ** 2) - 0.3 * np.cos(2 * np.pi * sx) * np.cos(2 * np.pi * sy) + 1

    ax.scatter([sx], [sy], [sz], color=PALETTE[2], s=40, marker='o',

               edgecolor='white', zorder=5)

    ax.text(sx, sy, sz + 0.15, 'saddle', fontsize=6, color=COLORS['ref_line'], ha='center')

ax.set_xlabel('θ₁', fontsize=10, labelpad=6)

ax.set_ylabel('θ₂', fontsize=10, labelpad=6)

ax.set_zlabel('Loss', fontsize=10, labelpad=6)

ax.view_init(elev=30, azim=135)

ax.tick_params(labelsize=8)

ax.legend(fontsize=8, loc='best')

fig.colorbar(surf, shrink=0.4, aspect=15, pad=0.12)

fig.tight_layout()

fig.savefig('图表/fig_loss_landscape.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

---

## 9. Learning Rate Schedule — 学习率调度曲线

**Use case**: Multi-method visual output comparison (generation/segmentation/detection).

**Enhancements**: SSIM/PSNR score annotations, error map row, red box highlights on key regions.

```python

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.patches import Rectangle

from 工具.plot_utils import setup_style, PALETTE, COLORS, _lighten

setup_style()

np.random.seed(42)

methods = ['Input', 'Ours', 'Method A', 'Method B', 'Ground Truth']

n_samples = 2

# Simulated metrics (PSNR/SSIM)

psnr_scores = {

    'Ours': [32.5, 31.8], 'Method A': [28.3, 27.9], 'Method B': [26.1, 25.5]

}

ssim_scores = {

    'Ours': [0.95, 0.94], 'Method A': [0.88, 0.87], 'Method B': [0.82, 0.81]

}

fig, axes = plt.subplots(n_samples * 2, len(methods), figsize=(13, 8))  # 2 rows per sample: image + error

for i in range(n_samples):

    for j, method in enumerate(methods):

        # Image row

        ax = axes[i * 2, j]

        img = np.random.rand(64, 64, 3) * 0.3

        if method == 'Ours':

            img += 0.45

        elif method == 'Ground Truth':

            img += 0.5

        elif method == 'Input':

            img += 0.15

        else:

            img += 0.3

        img = np.clip(img, 0, 1)

        ax.imshow(img)

        ax.axis('off')

        # Red box highlight on key region

        if method not in ['Input', 'Ground Truth']:

            rect = Rectangle((10, 10), 20, 20, linewidth=1.5, edgecolor=COLORS['down'],

                              facecolor='none', linestyle='-')

            ax.add_patch(rect)

        # Title with scores

        if i == 0:

            title = method

            if method in psnr_scores:

                title += f'\n{psnr_scores[method][i]:.1f}/{ssim_scores[method][i]:.2f}'

            fontw = 'bold' if method == 'Ours' else 'normal'

            color = PALETTE[0] if method == 'Ours' else 'black'

            ax.set_title(title, fontsize=8.5, fontweight=fontw, color=color)

        # Error map row

        ax_err = axes[i * 2 + 1, j]

        if method in ['Input', 'Ground Truth']:

            ax_err.axis('off')

            if method == 'Ground Truth' and i == 0:

                ax_err.text(0.5, 0.5, 'Error Map\n(|pred - GT|)', ha='center', va='center',

                            fontsize=7, color=COLORS['ref_line'], transform=ax_err.transAxes)

        else:

            error = np.random.rand(64, 64) * (0.1 if method == 'Ours' else 0.3 if method == 'Method A' else 0.5)

            ax_err.imshow(error, cmap='hot', vmin=0, vmax=0.5)

            ax_err.axis('off')

            # PSNR/SSIM annotation

            if method in psnr_scores:

                ax_err.text(0.5, -0.05, f'PSNR: {psnr_scores[method][i]:.1f} | SSIM: {ssim_scores[method][i]:.2f}',

                            ha='center', va='top', fontsize=6.5, color=COLORS['text'],

                            transform=ax_err.transAxes)

fig.tight_layout(pad=0.5, h_pad=0.3)

fig.savefig('图表/fig_qualitative.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

---

## 10. Latent Space Interpolation — 隐空间插值

**Use case**: Multi-method multi-metric comprehensive comparison.

**Enhancements**: Value labels at each vertex, threshold ring (e.g., 0.8 baseline), area ratio annotation in center.

```python

import numpy as np

import matplotlib.pyplot as plt

from 工具.plot_utils import setup_style, PALETTE, COLORS, _lighten

setup_style()

categories = ['Accuracy', 'Precision', 'Recall', 'F1', 'Speed', 'Memory']

N = len(categories)

angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist() + [0]

methods = {

    'Ours': [0.95, 0.93, 0.91, 0.92, 0.70, 0.65],

    'Transformer': [0.92, 0.90, 0.88, 0.89, 0.50, 0.40],

    'CNN': [0.88, 0.85, 0.90, 0.87, 0.85, 0.80],

}

def polygon_area(vals, angles_list):

    """Calculate polygon area for radar chart"""

    n = len(vals)

    area = 0

    for i in range(n):

        j = (i + 1) % n

        area += vals[i] * vals[j] * np.sin(angles_list[j] - angles_list[i])

    return abs(area) / 2

fig, ax = plt.subplots(figsize=(6.5, 6), subplot_kw=dict(polar=True))

# Threshold ring at 0.8

threshold = 0.8

ax.plot(angles, [threshold] * (N + 1), '--', color=COLORS['ref_line'], linewidth=1, alpha=0.4)

ax.text(0.02, 0.02, f'Baseline ({threshold})', fontsize=7, color=COLORS['ref_line'],

        transform=ax.transAxes, ha='left', va='bottom')

areas = {}

for i, (name, vals) in enumerate(methods.items()):

    vc = vals + vals[:1]

    lw = 2.5 if name == 'Ours' else 1.5

    alpha_fill = 0.18 if name == 'Ours' else 0.06

    ax.plot(angles, vc, 'o-', linewidth=lw, markersize=5, color=PALETTE[i], label=name,

            markeredgecolor='white', markeredgewidth=0.8)

    ax.fill(angles, vc, alpha=alpha_fill, color=PALETTE[i])

    # Value labels at each vertex — only label "Ours" to avoid overlap

    if name == 'Ours':

        for j, (ang, val) in enumerate(zip(angles[:-1], vals)):

            offset_r = 0.08

            ax.text(ang, val + offset_r, f'{val:.2f}', fontsize=7, ha='center', va='bottom',

                    color=PALETTE[i], fontweight='bold',

                    bbox=dict(boxstyle='square,pad=0.15', facecolor='white',

                              edgecolor=PALETTE[i], alpha=0.85, linewidth=0.4))

    areas[name] = polygon_area(vals, angles[:-1])

# Area ratio annotation in center

ours_area = areas['Ours']

ratios = [f'{name}: {ours_area / a:.2f}×' for name, a in areas.items() if name != 'Ours']

ax.text(0, 0, f'Area ratio\nvs Ours:\n' + '\n'.join(ratios),

        ha='center', va='center', fontsize=7, color=COLORS['text'],

        transform=ax.transData,

        bbox=dict(boxstyle='square,pad=0.4', facecolor='white',

                  edgecolor=COLORS['grid'], alpha=0.9))

ax.set_xticks(angles[:-1])

ax.set_xticklabels(categories, fontsize=9)

ax.set_ylim(0, 1.05)

ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])

ax.set_yticklabels(['', '0.4', '0.6', '0.8', '1.0'], fontsize=7, color=COLORS['ref_line'])

ax.legend(loc='best', bbox_to_anchor=(1.35, 1.1), frameon=True, edgecolor=COLORS['grid'], fontsize=9)

fig.tight_layout()

fig.savefig('图表/fig_radar.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

**★ 防遮挡技巧（Radar Chart 专用）：**

```python

# 1. 顶点数值标签沿辐射方向外推：r_label = v + 0.08

# 2. ha/va 根据角度自适应：上半 va='bottom'，下半 va='top'

# 3. 维度标签加 pad：ax.tick_params(axis='x', pad=18)

# 4. ylim 留余量：ax.set_ylim(0, 1.12)，给标注留空间

# 5. 图例 zorder=20：确保不被填充遮挡

```

---

## 11. Multi-Dataset Benchmark Table — 多数据集基准表

**Use case**: High-dimensional feature visualization in 3D with class separation.

**Enhancements**: Semi-transparent convex hulls per class, 2D projections on coordinate walls, class labels.

```python

import numpy as np

import matplotlib.pyplot as plt

from scipy.spatial import ConvexHull

from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from 工具.plot_utils import setup_style, PALETTE

setup_style()

np.random.seed(42)

classes = ['Class A', 'Class B', 'Class C']

n_per = 80

all_pts, all_labels = [], []

centers = [np.array([2, 2, 2]), np.array([-2, -1, 3]), np.array([0, -2, -1])]

for i, (cls, center) in enumerate(zip(classes, centers)):

    pts = center + np.random.randn(n_per, 3) * 0.7

    all_pts.append(pts)

    all_labels.extend([cls] * n_per)

all_pts_arr = np.vstack(all_pts)

fig = plt.figure(figsize=(8, 7))

ax = fig.add_subplot(111, projection='3d')

for i, (cls, pts) in enumerate(zip(classes, all_pts)):

    # Scatter points

    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=12, alpha=0.4,

               color=PALETTE[i], label=cls, edgecolor='none')

    # Semi-transparent convex hull

    try:

        hull = ConvexHull(pts)

        faces = []

        for simplex in hull.simplices:

            face = [pts[s] for s in simplex]

            faces.append(face)

        poly = Poly3DCollection(faces, alpha=0.08, facecolor=PALETTE[i],

                                edgecolor=PALETTE[i], linewidth=0.3)

        ax.add_collection3d(poly)

    except Exception:

        pass

    # 2D projections on walls

    # XY projection (on z wall)

    z_wall = ax.get_zlim()[0] if hasattr(ax, '_zlim') else all_pts_arr[:, 2].min() - 2

    ax.scatter(pts[:, 0], pts[:, 1], np.full(len(pts), all_pts_arr[:, 2].min() - 1.5),

               s=3, alpha=0.1, color=PALETTE[i], edgecolor='none')

    # XZ projection (on y wall)

    ax.scatter(pts[:, 0], np.full(len(pts), all_pts_arr[:, 1].max() + 1.5), pts[:, 2],

               s=3, alpha=0.1, color=PALETTE[i], edgecolor='none')

    # YZ projection (on x wall)

    ax.scatter(np.full(len(pts), all_pts_arr[:, 0].min() - 1.5), pts[:, 1], pts[:, 2],

               s=3, alpha=0.1, color=PALETTE[i], edgecolor='none')

    # Class center label

    cx, cy, cz = pts.mean(axis=0)

    ax.text(cx, cy, cz + 0.5, cls, fontsize=8, fontweight='bold', color=PALETTE[i],

            ha='center', va='bottom')

ax.set_xlabel('Dim 1', fontsize=10, labelpad=6)

ax.set_ylabel('Dim 2', fontsize=10, labelpad=6)

ax.set_zlabel('Dim 3', fontsize=10, labelpad=6)

ax.view_init(elev=20, azim=135)

ax.tick_params(labelsize=8)

ax.legend(fontsize=9, markerscale=3)

fig.tight_layout()

fig.savefig('图表/fig_3d_features.pdf', dpi=300, bbox_inches='tight')

plt.close(fig)

```

---

## 12. Error Analysis — 错误分析图

**Use case**: Accuracy vs FLOPs/Params trade-off. Common in CV/NLP model comparison.

**Enhancements**: Pareto frontier line, "better" direction arrow, iso-efficiency contour lines, bubble size legend.

```python

import numpy as np

import matplotlib.pyplot as plt

from scipy.interpolate import make_interp_spline

from 工具.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()

models = ['Ours', 'ViT-B', 'ViT-L', 'ResNet-50', 'ResNet-101', 'DeiT-S', 'Swin-T', 'EfficientNet']

flops = np.array([4.2, 17.6, 61.6, 4.1, 7.8, 4.6, 4.5, 0.4])

acc = np.array([92.3, 91.2, 92.0, 89.5, 90.8, 90.1, 91.5, 88.2])

params = np.array([25, 86, 307, 25, 44, 22, 28, 5])

fig, ax = plt.subplots(figsize=(8, 5.5))

# Iso-efficiency contours (acc/flops = const)

flops_grid = np.linspace(0.1, 70, 200)

for eff in [5, 10, 20, 40]:

    acc_iso = eff * np.sqrt(flops_grid)

    mask = acc_iso <= 96

    ax.plot(flops_grid[mask], acc_iso[mask], '-', color=COLORS['grid'], linewidth=0.6, alpha=0.5)

ax.text(65, 86, 'iso-efficiency\ncurves', fontsize=6.5, color=COLORS['grid'], ha='right', style='italic')

# Scatter bubbles

for i, model in enumerate(models):

    c = PALETTE[0] if model == 'Ours' else PALETTE[2]

    alpha = 1.0 if model == 'Ours' else 0.55

    s = params[i] * 3

    ax.scatter(flops[i], acc[i], s=s, color=c, alpha=alpha, edgecolor='white',

               linewidth=1, zorder=3)

    offset = (8, 8) if model not in ['ViT-L', 'EfficientNet'] else (-15, -12)

    ax.annotate(model, xy=(flops[i], acc[i]), xytext=offset, textcoords='offset points',

                fontsize=8, fontweight='bold' if model == 'Ours' else 'normal',

                color=PALETTE[0] if model == 'Ours' else 'grey')

# Ours highlight ring

ours_idx = models.index('Ours')

ax.scatter(flops[ours_idx], acc[ours_idx], s=params[ours_idx] * 3 + 120, facecolor='none',

           edgecolor=PALETTE[0], linewidth=2.5, zorder=4)

# Pareto frontier

# Find Pareto-optimal points (lower flops, higher acc)

pareto_mask = np.ones(len(models), dtype=bool)

for i in range(len(models)):

    for j in range(len(models)):

        if i != j and flops[j] <= flops[i] and acc[j] >= acc[i] and (

                flops[j] < flops[i] or acc[j] > acc[i]):

            pareto_mask[i] = False

            break

pareto_flops = flops[pareto_mask]

pareto_acc = acc[pareto_mask]

sort_idx = np.argsort(pareto_flops)

pareto_flops = pareto_flops[sort_idx]

pareto_acc = pareto_acc[sort_idx]

# Smooth Pareto line

if len(pareto_flops) >= 3:

    f_smooth = np.linspace(pareto_flops.min(), pareto_flops.max(), 100)

    try:

        spl = make_interp_spline(pareto_flops, pareto_acc, k=min(3, len(pareto_flops) - 1))

        a_smooth = spl(f_smooth)

        ax.plot(f_smooth, a_smooth, '-', color=PALETTE[0], linewidth=1.5, alpha=0.6,

                label='Pareto frontier')

    except Exception:

        ax.plot(pareto_flops, pareto_acc, '-', color=PALETTE[0], linewidth=1.5, alpha=0.6,

                label='Pareto frontier')

else:

    ax.plot(pareto_flops, pareto_acc, '-', color=PALETTE[0], linewidth=1.5, alpha=0.6,

            label='Pareto frontier')

# "Better" direction arrow

ax.annotate('', xy=(1, 94), xytext=(15, 87),

            arrowprops=dict(arrowstyle='->', color=COLORS['up'], lw=2, connectionstyle='arc3,rad=0.1'))

ax.text(5, 93.5, 'Better', fontsize=10, fontweight='bold', color=COLORS['up'],

        style='italic', rotation=15)

# Bubble size legend

for ps in [10, 50, 200]:

    ax.scatter([], [], s=ps * 3, color=COLORS['ref_line'], alpha=0.3, edgecolor='white', label=f'{ps}M params')

ax.set_xlabel('GFLOPs', fontsize=11)

ax.set_ylabel('Top-1 Accuracy (%)', fontsize=11)

ax.legend(frameon=True, edgecolor=COLORS['grid'], fontsize=8, loc='lower right', title='Model Size')

ax.spines['top'].set_visible(False)

ax.spines['right'].set_visible(False)

ax.grid(alpha=0.15, linestyle='--')

fig.tight_layout()

save_fig(fig, '图表/fig_efficiency.pdf')

```

**★ 防遮挡技巧（Efficiency Scatter 专用）：**

```python

# 1. 模型名标签必须用 smart_labels() 或 adjustText：气泡大小不同导致标签位置不规则

# 2. Pareto 前沿线用虚线：不要用实线（会和气泡边缘混淆）

# 3. 等效率曲线用极淡色（alpha=0.1）：不要遮挡气泡和标签

# 4. 气泡大小图例放在图外右侧：不要放在数据区域内

```

