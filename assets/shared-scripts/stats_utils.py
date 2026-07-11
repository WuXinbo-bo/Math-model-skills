#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""统计表格工具库 - 自动生成规范的三线表（LaTeX 或 Markdown）。



使用方式：

    from 工具.stats_utils import regression_table, descriptive_table



    # 输出 .tex：booktabs 三线表（PDF 模式）

    regression_table([model1, model2], ['OLS', 'Logistic'], '图表/TABLE_reg.tex')



    # 输出 .md：Markdown 三线表（Word/DOCX 模式）

    regression_table([model1, model2], ['OLS', 'Logistic'], '图表/TABLE_reg.md')



    # 强制输出两种格式（推荐：让下游写作步骤自由选择）

    regression_table(..., output='图表/TABLE_reg.tex', also_markdown=True)



⛔ Word/DOCX 工作流统一要求输出 `.md` 表格，写作环节可直接汇入 `论文/论文正文.md`。

"""

from __future__ import annotations

import os

import numpy as np





def _stars(p):

    if p is None or (isinstance(p, float) and np.isnan(p)):

        return ''

    if p < 0.01: return '***'

    if p < 0.05: return '**'

    if p < 0.1: return '*'

    return ''





def _fmt(x, d=3):

    if x is None or (isinstance(x, float) and np.isnan(x)):

        return ''

    if abs(x) >= 1000: return f'{x:,.0f}'

    return f'{x:.{d}f}'





def _write(lines, output):

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)

    with open(output, 'w', encoding='utf-8') as f:

        f.write('\n'.join(lines))

    print(f'Saved: {output}')





# ---------------------------------------------------------------------------

# Markdown 三线表辅助

# ---------------------------------------------------------------------------



def _md_table(headers: list[str], rows: list[list[str]],

              caption: str = '', label: str = '',

              note: str = '') -> list[str]:

    """生成 Markdown 三线表代码。



    格式：

        **表 X：标题**

        

        | h1 | h2 | h3 |

        |---|---|---|

        | c1 | c2 | c3 |

        

        > 注：xxx

    """

    L = []

    if caption:

        L.append(f'**{caption}**')

        L.append('')

    # 表头

    L.append('| ' + ' | '.join(str(h) for h in headers) + ' |')

    # 分隔行

    L.append('|' + '|'.join(['---'] * len(headers)) + '|')

    # 数据行

    for row in rows:

        # 单元格里的 | 转义

        cells = [str(c).replace('|', r'\|') for c in row]

        L.append('| ' + ' | '.join(cells) + ' |')

    if note:

        L.append('')

        # 去掉 LaTeX 转义（\% 等）

        note_md = note.replace('\\%', '%').replace('\\_', '_').replace('\\\\', '')

        L.append(f'> 注：{note_md}')

    if label:

        # Markdown 没有原生 label，用 HTML 注释保留供回查

        L.append('')

        L.append(f'<!-- label: {label} -->')

    return L





def _is_markdown_output(output: str) -> bool:

    """根据文件后缀判断是否输出 Markdown。"""

    return output.lower().endswith('.md') or output.lower().endswith('.markdown')





def _markdown_companion(output: str) -> str:

    """根据 .tex 输出路径推导出对应的 .md 路径（同名换后缀）。"""

    base, _ = os.path.splitext(output)

    return base + '.md'





# ---------------------------------------------------------------------------

# 回归表

# ---------------------------------------------------------------------------



def regression_table(models, col_labels=None, output='图表/TABLE_regression.tex',

                     caption='回归结果', label='tab:regression',

                     note='括号内为标准误。*、**、*** 分别表示在 10\\%、5\\%、1\\% 水平上显著。',

                     also_markdown: bool = False):

    """把 statsmodels 回归结果转成三线表（LaTeX 或 Markdown，按 output 后缀决定）。



    Args:

        models: list of statsmodels results 或 list of dict

        col_labels: 列标签

        output: 输出路径，后缀 `.tex` → LaTeX 三线表；后缀 `.md` → Markdown 三线表

        caption: 表标题

        label: 表 label（LaTeX 用 \\label；Markdown 用 HTML 注释保留）

        note: 表注

        also_markdown: 输出 .tex 时是否同时生成同名 .md（默认 False）

    """

    results = []

    for m in models:

        if isinstance(m, dict):

            results.append(m)

        else:

            results.append({

                'params': dict(m.params), 'bse': dict(m.bse), 'pvalues': dict(m.pvalues),

                'rsquared': getattr(m, 'rsquared', None),

                'rsquared_adj': getattr(m, 'rsquared_adj', None),

                'nobs': int(m.nobs),

            })

    if col_labels is None:

        col_labels = [f'({i+1})' for i in range(len(results))]

    all_vars = []

    seen = set()

    for r in results:

        for v in r['params']:

            if v not in seen and v not in ('const', 'Intercept'):

                all_vars.append(v); seen.add(v)

    for r in results:

        for v in ('const', 'Intercept'):

            if v in r['params'] and v not in seen:

                all_vars.append(v); seen.add(v)



    is_md = _is_markdown_output(output)



    if is_md:

        # ===== Markdown 三线表 =====

        headers = [''] + col_labels

        rows = []

        for var in all_vars:

            # 系数行

            cells = [str(var)]

            for r in results:

                if var in r['params']:

                    cells.append(f'{_fmt(r["params"][var])}{_stars(r["pvalues"].get(var))}')

                else:

                    cells.append('')

            rows.append(cells)

            # 标准误行（只展示括号内的 SE，第一列空）

            se_cells = ['']

            for r in results:

                if var in r.get('bse', {}):

                    se_cells.append(f'({_fmt(r["bse"][var])})')

                else:

                    se_cells.append('')

            rows.append(se_cells)

        # N 行

        rows.append(['$N$'] + [f'{int(r.get("nobs",0)):,}' for r in results])

        # R² 行

        r2 = [_fmt(r.get('rsquared'), 3) for r in results]

        if any(r2):

            rows.append(['$R^2$'] + r2)

        L = _md_table(headers, rows, caption=caption, label=label, note=note)

        _write(L, output)

        return



    # ===== LaTeX 三线表 =====

    n_cols = len(results)

    L = []

    L.append('\\begin{table}[htbp]')

    L.append('\\centering')

    L.append(f'\\caption{{{caption}}}')

    L.append(f'\\label{{{label}}}')

    L.append('\\begin{tabular}{l' + 'c' * n_cols + '}')

    L.append('\\toprule')

    L.append(' & '.join([''] + col_labels) + ' \\\\')

    L.append('\\midrule')

    for var in all_vars:

        cells = []

        for r in results:

            if var in r['params']:

                cells.append(f'{_fmt(r["params"][var])}{_stars(r["pvalues"].get(var))}')

            else:

                cells.append('')

        L.append(f'{var.replace("_", chr(92)+"_")} & ' + ' & '.join(cells) + ' \\\\')

        se_cells = []

        for r in results:

            if var in r.get('bse', {}):

                se_cells.append(f'({_fmt(r["bse"][var])})')

            else:

                se_cells.append('')

        L.append(' & ' + ' & '.join(se_cells) + ' \\\\')

    L.append('\\midrule')

    L.append('$N$ & ' + ' & '.join([f'{int(r.get("nobs",0)):,}' for r in results]) + ' \\\\')

    r2 = [_fmt(r.get('rsquared'), 3) for r in results]

    if any(r2): L.append('$R^2$ & ' + ' & '.join(r2) + ' \\\\')

    L.append('\\bottomrule')

    L.append('\\end{tabular}')

    if note:

        L.append('\\\\[0.3em]')

        L.append(f'\\parbox{{\\textwidth}}{{\\small 注：{note}}}')

    L.append('\\end{table}')

    _write(L, output)



    # 可选：同时生成 Markdown 版本（推荐 docx 模式）

    if also_markdown:

        regression_table(models, col_labels=col_labels,

                         output=_markdown_companion(output),

                         caption=caption, label=label, note=note)





# ---------------------------------------------------------------------------

# 描述性统计表

# ---------------------------------------------------------------------------



def descriptive_table(df, variables=None, output='图表/TABLE_descriptive.tex',

                      caption='描述性统计', label='tab:descriptive',

                      also_markdown: bool = False):

    """描述性统计三线表（按 output 后缀决定 LaTeX 或 Markdown）。"""

    if variables is None:

        variables = df.select_dtypes(include='number').columns.tolist()



    is_md = _is_markdown_output(output)



    if is_md:

        headers = ['变量', '观测数', '均值', '标准差', '最小值', '最大值']

        rows = []

        for var in variables:

            col = df[var].dropna()

            rows.append([

                str(var), f'{len(col):,}',

                _fmt(col.mean()), _fmt(col.std()),

                _fmt(col.min()), _fmt(col.max()),

            ])

        L = _md_table(headers, rows, caption=caption, label=label)

        _write(L, output)

        return



    L = []

    L.append('\\begin{table}[htbp]')

    L.append('\\centering')

    L.append(f'\\caption{{{caption}}}')

    L.append(f'\\label{{{label}}}')

    L.append('\\begin{tabular}{lccccc}')

    L.append('\\toprule')

    L.append('变量 & 观测数 & 均值 & 标准差 & 最小值 & 最大值 \\\\')

    L.append('\\midrule')

    for var in variables:

        col = df[var].dropna()

        dv = str(var).replace('_', '\\_')

        L.append(f'{dv} & {len(col):,} & {_fmt(col.mean())} & {_fmt(col.std())} & {_fmt(col.min())} & {_fmt(col.max())} \\\\')

    L.append('\\bottomrule')

    L.append('\\end{tabular}')

    L.append('\\end{table}')

    _write(L, output)



    if also_markdown:

        descriptive_table(df, variables=variables,

                          output=_markdown_companion(output),

                          caption=caption, label=label)





# ---------------------------------------------------------------------------

# 相关系数矩阵

# ---------------------------------------------------------------------------



def correlation_table(df, variables=None, output='图表/TABLE_correlation.tex',

                      caption='相关系数矩阵', label='tab:correlation',

                      also_markdown: bool = False):

    """相关系数矩阵三线表（下三角+显著性星号）。"""

    if variables is None:

        variables = df.select_dtypes(include='number').columns.tolist()

    sub = df[variables]

    corr = sub.corr()

    n = len(variables)

    try:

        from scipy import stats as sp

        pvals = np.zeros((n, n))

        for i in range(n):

            for j in range(n):

                if i != j:

                    _, p = sp.pearsonr(sub.iloc[:, i].dropna(), sub.iloc[:, j].dropna())

                    pvals[i, j] = p

    except ImportError:

        pvals = np.ones((n, n))



    is_md = _is_markdown_output(output)

    note = '*、**、*** 分别表示在 10%、5%、1% 水平上显著。'



    if is_md:

        short = [f'({i+1})' for i in range(n)]

        headers = [''] + short

        rows = []

        for i in range(n):

            cells = [f'({i+1}) {variables[i]}']

            for j in range(n):

                if j < i:

                    cells.append(f'{corr.iloc[i,j]:.3f}{_stars(pvals[i,j])}')

                elif j == i:

                    cells.append('1.000')

                else:

                    cells.append('')

            rows.append(cells)

        L = _md_table(headers, rows, caption=caption, label=label, note=note)

        _write(L, output)

        return



    L = []

    L.append('\\begin{table}[htbp]')

    L.append('\\centering')

    L.append(f'\\caption{{{caption}}}')

    L.append(f'\\label{{{label}}}')

    L.append('\\begin{tabular}{l' + 'c' * n + '}')

    L.append('\\toprule')

    short = [f'({i+1})' for i in range(n)]

    L.append(' & ' + ' & '.join(short) + ' \\\\')

    L.append('\\midrule')

    for i in range(n):

        dv = str(variables[i]).replace('_', '\\_')

        cells = [f'({i+1}) {dv}']

        for j in range(n):

            if j < i:

                cells.append(f'{corr.iloc[i,j]:.3f}{_stars(pvals[i,j])}')

            elif j == i:

                cells.append('1.000')

            else:

                cells.append('')

        L.append(' & '.join(cells) + ' \\\\')

    L.append('\\bottomrule')

    L.append('\\end{tabular}')

    L.append('\\\\[0.3em]')

    L.append('\\parbox{\\textwidth}{\\small 注：*、**、*** 分别表示在 10\\%、5\\%、1\\% 水平上显著。}')

    L.append('\\end{table}')

    _write(L, output)



    if also_markdown:

        correlation_table(df, variables=variables,

                          output=_markdown_companion(output),

                          caption=caption, label=label)

