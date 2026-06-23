# Nature-Figure Making Guide for Math Modeling Papers

Integrated from `nature-figure` skill, adapted for CUMCM/MCM contest papers.
Produces publication-quality figures with Nature journal semantic palette,
correct CJK font handling, and built-in data integrity checks.

## Quick Start

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# MANDATORY: SimHei first for CJK, Arial fallback for Latin (FIXED from original nature-figure)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'DejaVu Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['axes.unicode_minus'] = False

# Nature style
plt.rcParams.update({
    'axes.spines.right': False,
    'axes.spines.top': False,
    'legend.frameon': False,
    'axes.linewidth': 0.8,
})
```

## Figure Contract (Establish Before Plotting)

Every figure must satisfy the following contract before being accepted into the paper:

### Mandatory Checklist
- [ ] Resolution >= 300 DPI
- [ ] Font size >= 7pt (after paper scaling, min readable = 7pt)
- [ ] Axis labels present with units in brackets
- [ ] Legend present if multiple series
- [ ] Colorblind-safe palette (use preset: CB_color_cycle or Tol color set)
- [ ] No title inside plot area (title goes in caption)
- [ ] No grid lines (Nature style: clean background)
- [ ] No excessive decimal places (max 3 significant digits on axes)
- [ ] File saved as PNG (not JPG) for lossless compression

## Color Palettes

### Nature Journal Semantic Palette (Universal)
```python
Nature = {
    'blue': '#3B4992',
    'red': '#EE0000',
    'green': '#008B45',
    'purple': '#631879',
    'orange': '#BB0021',
    'light_blue': '#5B8BD0',
    'light_red': '#FB8072',
    'yellow': '#F1A340',
    'sky_blue': '#80B1D3',
    'pink': '#FCCDE5',
}
```

### Colorblind-Safe Cycle (8 colors)
```python
CB_color_cycle = [
    '#0072B2', '#D55E00', '#009E73', '#CC79A7',
    '#56B4E9', '#F0E442', '#000000', '#E69F00',
]
```

### Tol Color Set (12 colors, high contrast)
```python
Tol = [
    '#332288', '#88CCEE', '#44AA99', '#117733',
    '#999933', '#DDCC77', '#CC6677', '#882255',
    '#AA4499', '#661100', '#6699CC', '#AA4466',
]
```

## Figure Type Templates

### (A) Comparison Bar Chart

```python
def bar_chart_comparison(categories, values_a, values_b, labels, ylabel, filename):
    """Grouped bar chart for comparing two models across categories"""
    x = np.arange(len(categories))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(6, 4))
    bars1 = ax.bar(x - width/2, values_a, width, label=labels[0], color=Nature['blue'])
    bars2 = ax.bar(x + width/2, values_b, width, label=labels[1], color=Nature['red'])
    
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
```

### (B) Sensitivity Line Chart

```python
def sensitivity_line(perturbations, results_dict, xlabel, ylabel, filename):
    """Multi-line chart for parameter sensitivity analysis"""
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = [Nature['blue'], Nature['red'], Nature['green'], Nature['purple']]
    
    for i, (param_name, values) in enumerate(results_dict.items()):
        ax.plot(perturbations, values, 'o-', color=colors[i % len(colors)],
                label=param_name, linewidth=1.5, markersize=4)
    
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
```

### (C) Scatter + Diagonal (for prediction vs actual)

```python
def scatter_with_diagonal(y_true, y_pred, xlabel, ylabel, filename, metric_text=None):
    """Scatter plot with y=x diagonal for prediction vs actual"""
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(y_true, y_pred, s=20, alpha=0.6, color=Nature['blue'], edgecolors='none')
    
    lims = [min(min(y_true), min(y_pred)), max(max(y_true), max(y_pred))]
    ax.plot(lims, lims, 'k--', linewidth=0.8, alpha=0.7)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_aspect('equal')
    
    if metric_text:
        ax.text(0.05, 0.95, metric_text, transform=ax.transAxes,
                fontsize=9, verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
```

### (D) Heatmap (for correlation / confusion matrix)

```python
def heatmap(data, row_labels, col_labels, title, filename, cmap='RdBu_r'):
    """Heatmap with annotations"""
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(data, cmap=cmap, aspect='auto')
    
    ax.set_xticks(range(len(col_labels)))
    ax.set_yticks(range(len(row_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha='right')
    ax.set_yticklabels(row_labels)
    
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            ax.text(j, i, f'{data[i, j]:.2f}', ha='center', va='center', fontsize=8)
    
    plt.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
```

### (E) Convergence Curve

```python
def convergence_curve(iterations, values, xlabel, ylabel, filename):
    """Single or multi-line convergence plot"""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(iterations, values, color=Nature['blue'], linewidth=1.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
```

## Pre-Submission Figure Audit

Before adding figures to the paper, check:

- [ ] Resolution >= 300 DPI
- [ ] Font size: axis labels >= 10pt, tick labels >= 8pt, legend >= 8pt
- [ ] Axis labels include units in brackets
- [ ] All text readable when printed at full page width
- [ ] Color palette is colorblind-safe
- [ ] No grid lines, no unnecessary borders
- [ ] File saved as PNG (no JPG)
- [ ] Figure title is conclusive (see nature-writing-guide Fig/Table title standards)
- [ ] Corresponding `*_DAC.md` file exists and is filled
- [ ] Figure is referenced in the body text with D-A-C interpretation
