---
name: evidence-visualization
description: "Meta-model-agent 将计算成果转换为可发表的数据图形、表格和排版引用。适用于证据图谱构建。"
---

# 证据图谱构建

## 稳定执行契约

- **执行目标**：把已冻结的计算结果转换为可核验、可复用、可直接入文的图形与表格证据。
- **调用参数**：[visual-plan-or-data-path]。
- **权威输入**：计算结果.md、图表/全部结果.json、逐问结果文件与用户图表要求。
- **允许交付**：图表/中的数据图、表格和图表引用.tex；不得改写上游数值。
- **禁止写入**：不得越权修改已冻结的上游事实、用户原始文件或本协议未授权的目录。
- **可用工具边界**：Bash(*), Read, Write, Edit, Grep, Glob, Agent。
- **最小交付**：每项核心结论至少有匹配的图或表、可追溯数据源、中文标注与论文引用入口。
- **恢复入口**：优先读取当前工作、状态记录和已有产物，从最近一次通过门禁的位置继续。
- **失败回退**：缺少结果或口径冲突时停止绘图并回退计算实现；不得臆造数据补齐视觉效果。
- **收口顺序**：先核对输入，再完成产物，再运行本环节门禁，最后登记状态；门禁未通过不得宣告完成。

Produce visuals and tables from data: **$ARGUMENTS**

## 运行参数

- **FIG_DIR = `图表/`**

- **FORMAT = `pdf`** (vector, suitable for LaTeX)

- **DPI = 300**

- **CUSTOM_REQUIREMENTS** — User-specified requirements, highest priority.

<tools_and_style>

## 工具与表达规范

`shared-scripts/plot_utils.py` 提供学术绘图的基础样式。Meta-model-agent 可按任务需要选用其中的辅助函数、仅调用 `setup_style()` 后直接使用 matplotlib，或完全采用自定义实现。

**Quality floor**: 300 DPI PDF, no in-visual title (`plt.title`), font ≥9pt, grayscale-distinguishable.

**Color palette and recipes**: read `工具/figure_style_guide.md` (color schemes) and `工具/figure_recipes_*.md` (implementation examples).

plot_utils functions: `setup_style`, `save_fig`, `heatmap`, `forest_plot`, `trend_plot`, `bar_compare`, `distribution_plot`, `scatter_plot`, `residual_diagnostic`, `multi_line_plot`, `box_plot`, `radar_plot`, `subplot_grid`

Stats tables: `stats_utils.py` supplies `regression_table`, `descriptive_table`, `correlation_table`.

</tools_and_style>

## ⛔⛔⛔ 交付契约（最高优先级）

除 `图表/图表引用.tex` 外，必须生成 `图表/figure_manifest.json`。每张图登记 `path`、`claim`、`source`、`reader_task`、`publish` 和 `placement`。只有 `publish=true` 的图必须嵌入正文；诊断图、调试图和被替代的图应登记为 `publish=false`，不得为了覆盖文件而挤入正文。

```json
{
  "version": 1,
  "figures": [
    {
      "path": "图表/fig_q1_sensitivity.pdf",
      "claim": "参数扰动不改变最优方案排序",
      "source": "图表/全部结果.json",
      "reader_task": "比较趋势与稳定区间",
      "publish": true,
      "placement": "body"
    }
  ]
}
```

**Must produce all planned visuals (per 论文规划.md or skill-specific plan)** as `图表/fig_*.png/pdf` plus `图表/图表引用.tex` (or, in docx mode, the same PNGs without 图表引用.tex requirement).

⛔ **特殊豁免**：若 论文规划.md 清晰标明写"无图形与表格"或图形与表格清单为空（纯文字综述/思辨论文），准许 图表/ 为空，但**务必**写一个空的 `图表/图表引用.tex` (`touch 图表/图表引用.tex; mkdir -p 图表`) 让下游知道这步跑过了。

⛔ **MUST run output verification prior to ending**:

```bash

PASS=true

mkdir -p 图表

FIG_PNG=$(ls 图表/fig_*.png 2>/dev/null | wc -l)

FIG_PDF=$(ls 图表/fig_*.pdf 2>/dev/null | wc -l)

TOTAL=$((FIG_PNG + FIG_PDF))

# 检查规划是否要求图表

PLAN_HAS_FIG=$(grep -E '^\s*-?\s*fig_|图表清单|图表/fig_' 论文规划.md 2>/dev/null | wc -l)

if [ "$TOTAL" -ge 1 ]; then

    echo "✅ 图表/fig_*.png/pdf ($TOTAL)"

elif [ "$PLAN_HAS_FIG" -eq 0 ]; then

    echo "✓ 规划无图表, 创建占位 图表引用.tex"

    touch 图表/图表引用.tex

else

    echo "❌ 规划要求图表但未生成"

    PASS=false

fi

MODE=$(grep -q "Word（.docx）\|docx mode" META_MODEL_AGENT.md 2>/dev/null && echo docx || echo pdf)

if [ "$MODE" = "pdf" ] && [ ! -f 图表/图表引用.tex ]; then

    touch 图表/图表引用.tex

fi

[ "$PASS" != true ] && echo "⛔ Output verification FAILED — must complete before ending"

```

## 执行流程

### 工作节点 0：恢复核验（断线重跑必读）

⛔ **当前环节可能由于断线/人工重跑被多次启动**。每一次启动前**务必**先扫描已有产物：

```bash

echo "=== 工作区扫描 ==="

HAS_PNG=$(ls 图表/fig_*.png 2>/dev/null | wc -l)

HAS_PDF=$(ls 图表/fig_*.pdf 2>/dev/null | wc -l)

HAS_TIKZ=$(ls 图表/tikz_*.pdf 2>/dev/null | wc -l)

HAS_INCLUDES=$([ -f 图表/图表引用.tex ] && wc -c < 图表/图表引用.tex || echo 0)

echo "  fig_*.png: $HAS_PNG, fig_*.pdf: $HAS_PDF, tikz_*.pdf: $HAS_TIKZ"

echo "  图表引用.tex: $HAS_INCLUDES bytes"

```

**依据扫描结果决定行动**：

| 运行状态 | 行动 |

|---|---|

| 满足 论文规划.md 中规划的图形与表格数（不少于规划） + 图表引用.tex 出现 | **跳到 Phase 9 (count verification) 校验**，校验通过即完成 |

| 已有部分图但少于规划数 | **只产出缺失的图**（已出现的图**避免重画**） |

| 图表引用.tex 缺失但图都在 | **只产出 Phase 6 的 图表引用.tex** |

| 啥都没有 | 从 Phase 1 启动 |

⛔ **铁律**：

- **已有 `图表/fig_*.png/pdf` 避免重画**（覆盖会让审稿人看到的图变了）

- **已有的 `图表/TABLE_*.md/tex` 避免重写**（数据已固化）

- 只补缺失的图 / 表

### 工作节点 1：Read manuscript structure + data discovery

1. Consult the full style guide (color schemes + visual selection decision table + anti-patterns + DrawIO/TikZ color schemes — all in one file):

```bash

cat 工具/figure_style_guide.md 2>/dev/null || cat skills/shared-scripts/figure_style_guide.md

```

2. Scan recipe file headings to know what templates are available:

```bash

echo "=== Advanced ==="

(cat 工具/figure_recipes_advanced.md 2>/dev/null || cat skills/shared-scripts/figure_recipes_advanced.md 2>/dev/null) | grep '^## '

echo "=== Basic ==="

(cat 工具/figure_recipes_basic.md 2>/dev/null || cat skills/shared-scripts/figure_recipes_basic.md 2>/dev/null) | grep '^## '

echo "=== Academic ==="

(cat 工具/figure_recipes_academic.md 2>/dev/null || cat skills/shared-scripts/figure_recipes_academic.md 2>/dev/null) | grep '^## '

echo "=== Competition ==="

(cat 工具/figure_recipes_competition.md 2>/dev/null || cat skills/shared-scripts/figure_recipes_competition.md 2>/dev/null) | grep '^## '

echo "=== Empirical ==="

(cat 工具/figure_recipes_empirical.md 2>/dev/null || cat skills/shared-scripts/figure_recipes_empirical.md 2>/dev/null) | grep '^## '

echo "=== Basic (fallback only) ==="

(cat 工具/figure_recipes_basic.md 2>/dev/null || cat skills/shared-scripts/figure_recipes_basic.md 2>/dev/null) | grep '^## '

```

3. **⛔ MANDATORY: Extract the COMPLETE visual plan from planning docs.** Read ALL planning docs and extract every planned visual/table into a numbered checklist:

```bash

echo "=== Extracting figure plan ==="

for plan in 论文规划.md 问题分析.md 选题规划.md 建模报告.md; do

    [ -f "$plan" ] || continue

    echo "--- $plan ---"

    cat "$plan"

done

```

Following reading, output a **FIGURE PLAN CHECKLIST** like this (you MUST produce this prior to proceeding):

```

FIGURE PLAN CHECKLIST (from planning docs):

[ ] 1. fig_xxx — Descriptive stats distribution (Rain Cloud) — data: results.json

[ ] 2. fig_yyy — Model comparison radar (Radar) — data: results.json

[ ] 3. fig_zzz — Regression coefficient forest plot (Forest Plot) — data: results.json

[ ] 4. TABLE_desc — Descriptive statistics table — data: results.json

[ ] 5. TABLE_reg — Regression results table — data: results.json

[ ] 6. drawio_roadmap — Technical roadmap (DrawIO)

Total planned: 6 figures + 2 tables + 1 DrawIO

```

**Every item in the plan MUST appear in this checklist. If the plan says "12 visuals", the checklist is expected to include 12 entries.**

3.5. **⛔ JSON 数据完整性核验（保证数据能支撑全部图形与表格）：**

```bash

echo "=== JSON 数据完整性检查 ==="

if [ -f 图表/全部结果.json ]; then

    python3 -c "

import json

with open('图表/全部结果.json', 'r') as f:

    data = json.load(f)

# 列出所有顶层 key

keys = list(data.keys()) if isinstance(data, dict) else [f'[{i}]' for i in range(min(len(data), 10))]

print(f'JSON 顶层 key ({len(keys)} 个): {keys}')

# 检查是否有空值

def verify_empty(obj, path=''):

    issues = []

    if isinstance(obj, dict):

        for k, v in obj.items():

            if v is None or v == '' or v == []:

                issues.append(f'{path}.{k} 为空')

            else:

                issues.extend(verify_empty(v, f'{path}.{k}'))

    elif isinstance(obj, list) and len(obj) == 0:

        issues.append(f'{path} 为空列表')

    return issues

issues = verify_empty(data)

if issues:

    print(f'⚠ 发现 {len(issues)} 个空值:')

    for i in issues[:5]:

        print(f'  - {i}')

else:

    print('✅ JSON 数据无空值')

" 2>/dev/null

else

    echo "⚠ 图表/全部结果.json 不存在，图表将缺少数据支撑"

fi

# 检查各子问题的结果文件

for f in 图表/problem_*_结果.json; do

    [ -f "$f" ] && echo "✅ $(basename $f) 存在" || true

done

```

4. Scan data files (`用户数据/` > `图表/` > root). **⛔ 避免 `cat` 或 `print()` 全部 JSON 文件——大 JSON 会撑爆上下文。** 只用以下方式扫描：

```bash

ls -la 图表/*.json 2>/dev/null

python3 -c "

import json, os

def summarize(v, depth=0):

    if isinstance(v, list):

        n = len(v)

        nulls = sum(1 for x in v if x is None)

        nums = [x for x in v if isinstance(x, (int,float)) and x is not None]

        if nums:

            return f'list[{n}] nulls={nulls} range=[{min(nums):.4g}, {max(nums):.4g}] sample={v[:3]}'

        elif v and isinstance(v[0], dict):

            return f'list[{n}] of dict, keys={list(v[0].keys())[:8]}'

        return f'list[{n}] sample={str(v[:3])[:100]}'

    elif isinstance(v, dict) and depth < 2:

        items = []

        for k2, v2 in list(v.items())[:6]:

            items.append(f'{k2}: {summarize(v2, depth+1)}')

        return 'dict{' + ', '.join(items) + '}'

    return f'{type(v).__name__}={str(v)[:60]}'

for f in sorted(os.listdir('图表')):

    if not f.endswith('.json'): continue

    sz = os.path.getsize(f'图表/{f}')

    with open(f'图表/{f}') as fh: d = json.load(fh)

    print(f'\n=== {f} ({sz//1024}KB) ===')

    if isinstance(d, dict):

        for k, v in list(d.items())[:10]:

            print(f'  {k}: {summarize(v)}')

    elif isinstance(d, list):

        print(f'  {summarize(d)}')

"

```

Every visual in the plan is expected to be generated — the actual count can exceed the plan but not fall short.

<supplement_mode>

**Supplement mode**: if `图表/` already has ≥3 PDFs + `图表引用.tex` from a previous step (e.g., experiment-bridge):

1. Compare existing PDFs against the FIGURE PLAN CHECKLIST

2. Validate quality of each existing PDF (valid chart type, uses PALETTE, valid language labels)

3. **Regenerate** any visual that fails quality validate

4. **Produce** any planned visual that doesn't exist yet

5. **Always produce** DrawIO architecture diagrams

6. **Always regenerate** `图表引用.tex` to include ALL visuals

**Normal mode** (no existing PDFs — this is the default for stats modeling since computational-realization only outputs JSON):

Produce all visuals from scratch using JSON data in `图表/*.json`.

</supplement_mode>

### 工作节点 1.5：Produce AI Image visuals (non-data visuals)

AI Image 默认关闭。仅当题目确有无法用数据图、DrawIO 或 TikZ 准确表达的物理场景，并且用户明确需要场景示意时才启用；技术路线图、流程图和模型架构图严禁使用生成式图片。

**1. AI Image 不得直接采用，必须进行内容级预核验：**

API Key 已通过配置文件 `工具/_ai_image_config.json` 注入（用户在设定页面配置，后端自动化写入）。

**直接调用即可。成功就用，失败 3 次后 DrawIO 兜底。不需检测 Python 或核验环境变量。**

```bash

# Python 路径：MH_PYTHON 由后端注入，fallback 到系统 python

PYTHON="${MH_PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)}"

GPT_IMG=1

echo "AI_IMAGE: ready (Python=$PYTHON, config=工具/_ai_image_config.json)"

```

**2. Establish language:**

```bash

# Verify paper language from planning docs（注意：comp_apmcm_zh 是中文赛项，必须先排除）

if grep -qi 'comp_apmcm_zh' META_MODEL_AGENT.md 2>/dev/null; then

    AIIMG_LANG="zh"

elif grep -qi 'MCM\|ICM\|APMCM\|comp_mcm\|comp_apmcm\|comp_certcup_en\|comp_shuwei_en' META_MODEL_AGENT.md 2>/dev/null; then

    AIIMG_LANG="en"

else

    AIIMG_LANG="zh"

fi

echo "AI Image language: $AIIMG_LANG"

```

**3. Read ALL upstream documents to understand the FINAL methods and outcomes:**

```bash

echo "=== Reading upstream docs for AI Image prompt construction ==="

cat 问题分析.md 2>/dev/null | head -500

cat 建模报告.md 2>/dev/null | head -500

cat 计算结果.md 2>/dev/null | head -200

```

**4. Consult the AI Image plan from 问题分析.md:**

```bash

grep -A 30 'AI Image' 问题分析.md 2>/dev/null

```

**5. For every planned AIIMG visual, construct a prompt and call the tool.**

**若 问题分析.md 中规划了 AIIMG 图（包含 "AIIMG-" 或 "AI Image" 字样），应先检查 `工具/ai_image.py` 是否可用。工具存在时优先尝试生成；工具未部署或连续重试失败时，记录原因并转交 systems-diagramming 使用 DrawIO 或 TikZ 替代。**

实施准则：

1. 核验规划中有几张 AIIMG 图

2. 工具存在时，对每张图调用 `python3 工具/ai_image.py`（最多重试 3 次）

3. 若 3 次重试全部失败 → 登记到 `_aiimg_failed.txt` → 由 systems-diagramming 环节自行选取最合适的替代方案（DrawIO 或 TikZ，依据图的内容自主判定）

4. 工具未部署时，记录 `tool_unavailable` 后再执行替代方案

```bash

# ⛔ 强制检查：规划中是否有 AIIMG 图

AIIMG_PLAN_COUNT=$(grep -ci 'AIIMG\|AI.Image\|场景示意图' 问题分析.md 2>/dev/null || echo 0)

echo "规划中的 AI Image 图数量: $AIIMG_PLAN_COUNT"

if [ "$AIIMG_PLAN_COUNT" -gt 0 ] && [ -f 工具/ai_image.py ]; then

    echo "⛔ 检测到 $AIIMG_PLAN_COUNT 张 AI Image 图规划 — 必须逐张尝试调用 ai_image.py"

    echo "   失败 3 次后才允许降级（DrawIO 或 TikZ，自行判断哪个更合适）"

elif [ "$AIIMG_PLAN_COUNT" -gt 0 ]; then
    echo "⚠ 工具/ai_image.py 未部署，记录 tool_unavailable 并使用 DrawIO/TikZ 替代"

fi

```

Meta-model-agent needs to construct the prompt from the final methods and results in 建模报告.md, because modeling or coding may have changed the initial plan. Write only the core scene, layout, and content description; language adaptation, style guidance, and safety constraints are supplied by the tool.

**⛔ 提示词越简洁，AI Image 发挥越好。只描述场景和元素，避免写死颜色和布局细节。**

**AI Image 只用于场景示意图（物理/工程类赛题的问题背景图）。技术路线图、求解过程图、模型架构图采用 DrawIO。**

<ai_image_prompt模板>

#### 场景示意图 (场景示意图.png)

仅适用于有具体物理/工程空间场景的赛题（光学、无人机、传感器、交通、热传导等）。

纯数据/统计类赛题不需。

Meta-model-agent 依据赛题自由构造 prompt，参考格式：

```

生成一张学术论文插图风格的{场景名}示意图。

{俯视/侧视/3D等距}视角。

画面包含：{元素1}、{元素2}、{元素3}。

用虚线箭头表示{某种关系/流向}，用不同颜色区分{不同类别}。

包含图例说明各颜色含义。

```

⛔ 约束：

- 不超过 6 个视觉元素

- 不产出真人面孔/肖像——需人物时用抽象图标

- 务必涵盖图例框解释颜色含义

- 尺寸标注用数学变量（R, H, L）不用具体数字

</ai_image_prompt模板>

**6. Execute AI Image calls (max 3 retries per visual, handled by the tool):**

```bash

AIIMG_FAILED=""

# For each planned figure, call ai_image.py

# Example (Meta-model-agent generates the actual calls based on the plan):

$PYTHON 工具/ai_image.py \

  --prompt "Generate a structured technical roadmap..." \

  --output 图表/技术路线图.png \

  --lang $AIIMG_LANG \

  --aspect-ratio 9:16 \

  --max-retries 3

if [ -f 图表/技术路线图.pdf ]; then

    echo "✅ 技术路线图 generated via AI Image 2"

else

    echo "❌ 技术路线图 FAILED after 3 retries — will use DrawIO fallback"

    AIIMG_FAILED="$AIIMG_FAILED 技术路线图"

    AIIMG_TOTAL_FAILURES=$((AIIMG_TOTAL_FAILURES + 1))

fi

# Repeat for each AIIMG figure...

# ⛔ 每张图独立重试 3 次（--max-retries 3），不要因为一张图失败就跳过后面的图

```

**7. Record failures for DrawIO fallback (persist to file for systems-diagramming step).**

```bash

# 统计结果

AIIMG_TOTAL_PLANNED=$(echo "$AIIMG_PLANNED" | wc -w)  # 计划生成的图数量

AIIMG_TOTAL_FAILURES=${AIIMG_TOTAL_FAILURES:-0}

echo "$AIIMG_FAILED" > 图表/_aiimg_failed.txt

# ⛔ 只有在 Python 不存在时才写 DISABLED

# 如果 Python 存在但 API Key 没配置或网络不通，所有图都会失败 → 写 ALL_FAILED（不是 DISABLED）

# 这样下一步 DrawIO 会为所有失败的图生成替代品

if [ "$GPT_IMG" -eq 0 ]; then

    # Python 不存在，完全跳过了 AI Image

    echo "AI_IMG_DISABLED" > 图表/_aiimg_status.txt

elif [ -z "$AIIMG_FAILED" ]; then

    # 所有图都成功了

    echo "ALL_SUCCESS" > 图表/_aiimg_status.txt

elif [ "$AIIMG_TOTAL_FAILURES" -ge "$AIIMG_TOTAL_PLANNED" ] 2>/dev/null; then

    # 所有图都失败了（可能是 API Key 没配置或网络不通）

    echo "ALL_FAILED" > 图表/_aiimg_status.txt

    echo "⚠ 所有 AI Image 图都失败了，可能是 API Key 未配置或网络问题，DrawIO 将生成所有替代图"

else

    # 部分成功部分失败

    echo "SOME_FAILED" > 图表/_aiimg_status.txt

fi

```

Status meanings:

- `ALL_SUCCESS` → all AI Image visuals generated, DrawIO only generates visuals NOT in the AI Image plan

- `SOME_FAILED` → DrawIO generates replacements ONLY for the failed visuals

- `ALL_FAILED` → all attempts failed (API Key missing / network error), DrawIO generates ALL non-data visuals

- `AI_IMG_DISABLED` → Python not found, DrawIO generates ALL non-data visuals

**8. AI Image 产出后自检：**

对每张成功产出的 AI Image 图，核验：

```bash

for img in 图表/场景示意图*.pdf 图表/AI示意图*.pdf; do

    [ -f "$img" ] || continue

    bn=$(basename "$img")

    sz=$(wc -c < "$img")

    echo "=== $bn ($sz bytes) ==="

    # 文件大小检查：AI Image 生成的 PDF 通常 > 50KB

    if [ "$sz" -lt 50000 ]; then

        echo "❌ $bn 文件过小 ($sz bytes)，可能是空白或损坏"

    else

        echo "✅ $bn 文件大小正常"

    fi

done

```

⛔ AI Image 无法做内容级自检（不可查阅图片内容），但务必保证：

- PDF 文件出现且 > 50KB

- 若产出的是 PNG，确认已自动化转换为 PDF（LaTeX 需 PDF）

- 失败的图登记到 AIIMG_FAILED，DrawIO 子阶段会自动化兜底

### 工作节点 2：Visual type decisions

Browse the recipe library (97 total across 5 files) and the `<figure_selection_guide>` decision table from the style guide. For every planned visual:

1. Identify the data characteristic (e.g., "3 methods × 4 metrics comparison")

2. Browse ALL available recipe types — don't default to the same few charts every time

3. Pick the type that best fits the data AND looks visually distinct from other visuals in this manuscript

4. Confirm visual variety: avoid apply the same chart type more than 2 times in one manuscript. Mix basic, advanced, competition, and empirical recipes

5. Consult the full implementation example from the matched recipe file

6. Select the smallest semantic color set that remains readable in grayscale

**⛔ Choose by reader task, not novelty.** Prefer familiar grouped bars, lines, scatter plots, heatmaps, or three-line tables when they communicate the claim directly. Reusing a clear chart type is correct; never switch charts merely to create variety.

Reference `工具/figure_exemplars.md` for visual distribution examples by manuscript type. Decide count and placement autonomously.

### 工作节点 2.5：Detailed visual type planning (variety validate)

For every planned visual, build a Visual Type Audit Table. The "Chosen Type" is expected to be your autonomous choice from the full recipe library — the examples below are just illustrations, not fixed recommendations:

```

| # | Data Description | Chosen Type | Why | Recipe Ref |

|---|-----------------|-------------|-----|------------|

| 1 | 4 methods × 3 metrics | (your choice from library) | (your reasoning) | (recipe #) |

| 2 | ablation results | (your choice) | | |

| 3 | feature importance | (your choice) | | |

| ... | ... | ... | ... | ... |

```

**Variety validate**: count unique chart types in the table. If < 4 unique types for a manuscript with ≥6 visuals, go back and swap some for alternatives from the recipe library. Browse recipe headings again if needed.

### 工作节点 3：Produce visual scripts

One `gen_fig_xxx.py` script per visual, executed from workspace root. Each script starts with `工具` initialization and `setup_style()` call.

Use `get_recipe.py` when a recipe matches the data and reader task. Treat recipes as implementation references, not mandatory visual decoration; remove gradient fills, rounded annotation boxes, decorative backgrounds, and extra layers unless they encode necessary data or uncertainty.

```bash

# Example: if the plan says "fig_xxx — 堆叠面积图 (basic #8)", extract recipe first:

python3 工具/get_recipe.py basic 8

# Example: if the plan says "fig_yyy — 龙卷风图 (competition #2)":

python3 工具/get_recipe.py competition 2

# Then copy the output code, adapt to actual data, save as 图表/gen_fig_xxx.py

```

**⛔ For EVERY visual script you write, the workflow is:**

1. Consult the plan entry: `fig_xxx — 图表类型 (category #N)`

2. Extract recipe: `python3 工具/get_recipe.py category N`

3. Copy the recipe implementation as starting point

4. Replace demo data with actual data from `图表/*.json`

5. Save as `图表/gen_fig_xxx.py`

Skipping a matching implementation reference may increase coding risk, but a simple custom chart is acceptable when it is clearer and passes the evidence, readability, and source-trace gates.

Matplotlib defaults should still be normalized for font and print readability. Missing gradients or annotations is not a defect; unnecessary decoration is a defect.

<script_template>

**Copy this EXACTLY as the first lines of every gen_fig_*.py script. Output extension：默认 `.pdf`（LaTeX 模式）；若 META_MODEL_AGENT.md 末尾涵盖「⛔ 交付格式：仅 PNG」（Word/docx 模式）就改成 `.png`：**

```python

import os, sys, shutil

os.makedirs('工具', exist_ok=True)

for src in ['plot_utils.py']:

    for search in ['skills/shared-scripts', '../skills/shared-scripts']:

        p = os.path.join(search, src)

        if os.path.isfile(p):

            shutil.copy2(p, f'工具/{src}')  # copies .py file, NOT .pdf

            break

sys.path.insert(0, '.')  # plain dot, NOT '.pdf'

from 工具.plot_utils import setup_style, save_fig, PALETTE

setup_style()  # defaults to Soft palette; alternatives: tableau/npg/nejm/science/colorblind

# ... figure generation code ...

# Read data from JSON/CSV, never hardcode numbers

# NEVER use cmap='RdYlGn' — use 'coolwarm' or 'YlOrRd' instead. Do NOT use 'RdBu_r' (too dark)

# No plt.title() — captions go in LaTeX only

# 默认 LaTeX 模式：save_fig(fig, '图表/fig_xxx.pdf')

# Word/docx 模式：save_fig(fig, '图表/fig_xxx.png')  # 自动 350 DPI 防中文糊

```

</script_template>

**⛔ 地图类图形与表格（中国省级热力图）环境阐明：**

- 环境已预装 `geopandas`，直接 `import geopandas as gpd` 即可

- GeoJSON 文件：`工具/china_provinces.geojson`（首次运行自动化从 `skills/shared-scripts/` 复制或从阿里云 DataV 下载）

- **⛔ 绝对避免用散点图代替地图！** 务必用 `gdf.plot()` 画省份多边形轮廓

- 若 geopandas 导入失败，用纯 matplotlib 方案：从 GeoJSON 解析坐标，用 `matplotlib.patches.Polygon` 人工画省份轮廓（参考 figure_recipes_competition.md #7 方案 B）

**⛔ figsize 硬限制（全部图形与表格务必遵守）：**

- `figsize` 的 height 不可超过 8 英寸（约 20cm）。超过会导致图占满整页，前一页只剩一句引导文字

- 数据条目多（20+ 个类别的柱状图/条形图）：只展示 Top 15-20，其余放附录表格。或用 `figsize=(7, 6)` + `fontsize=7` 缩小

- **条目超过 15 个时优先换图形与表格类别**：横向柱状图 → 棒棒糖图（lollipop，更紧凑）；排名柱状图 → 表格（LaTeX 三线表更省空间）；分类对比 → 雷达图或热力图（一张图展示全部维度）

- 横向柱状图（barh）条目超过 15 个时，务必限制 `figsize=(7, max(4, n*0.25))`，且 height 上限 8

- 热力图/混淆矩阵超过 10×10 时，用 `figsize=(8, 7)` + `fontsize=7`

- **校验**：产出后核验 PDF 文件尺寸，若高度 > 25cm 务必缩小重新产出

### 工作节点 4：Self-validate + execute

Run the self-validate script prior to execution:

```bash

bash 工具/figure_check.sh 2>/dev/null || bash skills/shared-scripts/figure_check.sh

```

<fix_patterns>

If violations found (especially CRITICAL), fix and re-validate prior to executing:

- CRITICAL missing `setup_style` → add initialization implementation from script_template above

- Hardcoded color → `PALETTE[n]`

- `plt.title()` → remove (caption in LaTeX only)

- `ax.grid()` → remove (setup_style handles grid)

- `RdYlGn` or `RdYlGn_r` colormap → use `coolwarm` (for diverging) or `YlOrRd` (for sequential). Do NOT use `RdBu_r` (too dark)

- Empty value placeholders → read from data files

- matplotlib default blue `#1f77b4` → use PALETTE

</fix_patterns>

**Execute each script ONE BY ONE (not batch). If a script fails, fix it immediately prior to moving to the next:**

```bash

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

FAILED=0

for script in 图表/gen_fig*.py; do

    [ -f "$script" ] || continue

    bn=$(basename "$script" .py)

    echo "=========================================="

    echo "Running: $script"

    echo "=========================================="

    $PYTHON "$script" 2>&1

    EXIT_CODE=$?

    # Verify if PDF was generated

    expected_pdf="图表/${bn#gen_}.pdf"

    if [ $EXIT_CODE -ne 0 ] || [ ! -f "$expected_pdf" ]; then

        # Try alternate naming

        any_new=$(find 图表/ -name "*.pdf" -newer "$script" 2>/dev/null | head -1)

        if [ -z "$any_new" ]; then

            echo "❌ FAILED: $script (exit=$EXIT_CODE) — NO PDF generated"

            echo "   → Read the error above, fix the script, and re-run it"

            FAILED=$((FAILED+1))

        else

            echo "✅ OK: $script → $any_new"

        fi

    else

        echo "✅ OK: $script → $expected_pdf"

    fi

done

[ -d "图表/figures" ] && mv 图表/图表/*.pdf 图表/ 2>/dev/null

echo ""

echo "=== Summary: $FAILED scripts failed ==="

```

**If FAILED > 0, you MUST go back and fix each failed script:**

1. Consult the error output (ImportError? FileNotFoundError? data issue?)

2. Fix the script (add missing import, fix data path, etc.)

3. Re-run ONLY the failed script: `$PYTHON 图表/gen_fig_xxx.py`

4. Validate the PDF exists: `ls -la 图表/fig_xxx.pdf`

5. Repeat until all scripts produce PDFs

**Do NOT proceed to Phase 5 until every gen_fig_*.py has generated its PDF.**

### 工作节点 5：Produce tables (LaTeX OR Markdown — pick by output mode)

**⛔ FIRST: detect output format mode**

```bash

echo "=== 检测输出格式 ==="

# META_MODEL_AGENT.md 顶部「## 参数」段会列 output_format

OUTPUT_FORMAT=$(grep -E '^- output_format:' META_MODEL_AGENT.md 2>/dev/null | sed -E 's/.*: *//' | head -1 | tr -d '[:space:]')

OUTPUT_FORMAT=${OUTPUT_FORMAT:-pdf}

echo "Output format: $OUTPUT_FORMAT"

# 学术写作四大模板始终是 docx 模式（即使 output_format 没明写）

TEMPLATE=$(grep -E '^- template:' META_MODEL_AGENT.md 2>/dev/null | sed -E 's/.*: *//' | head -1 | tr -d '[:space:]')

case "$TEMPLATE" in

    thesis_proposal|literature_review|course_paper|course_report)

        OUTPUT_FORMAT=docx

        echo "学术写作模板，强制 docx 模式"

        ;;

esac

if [ "$OUTPUT_FORMAT" = "docx" ]; then

    TABLE_EXT="md"

    echo "⛔ Word/DOCX 模式：表格输出 .md（Markdown 三线表）"

else

    TABLE_EXT="tex"

    echo "PDF 模式：表格输出 .tex（booktabs 三线表）"

fi

echo "TABLE_EXT=$TABLE_EXT (将用于 图表/TABLE_*.${TABLE_EXT})"

```

**⛔ At minimum: primary outcomes comparison table + descriptive statistics table.**

- PDF 模式 → Save as `图表/TABLE_xxx.tex`（booktabs 三线表）

- Word/DOCX 模式 → Save as `图表/TABLE_xxx.md`（Markdown 三线表）

**⛔ For Chinese papers: table captions and column headers MUST be in Chinese.** Verify 选题规划.md or 问题分析.md to determine paper language. If Chinese (stats modeling / math modeling competition), all `\caption{}` and column headers must use Chinese.

**⛔ DOCX 模式下 Markdown 三线表的标准格式（务必遵守）：**

```markdown

**表 1：模型性能对比**

| 模型 | RMSE | MAE | R² |

|---|---|---|---|

| LSTM | 0.023 | 0.018 | 0.94 |

| Transformer | 0.019 | 0.015 | 0.96 |

| XGBoost | 0.021 | 0.017 | 0.95 |

> 注：所有指标基于测试集；最优值已加粗。

<!-- label: tab:model_perf -->

```

铁律：

- 表标题：`**表 X：标题**`（不是 `\caption{}`）

- 表头独立一行 `| h1 | h2 |`，**后续务必有分隔行** `|---|---|`

- 每行 `|` 数量务必保持一致（列数对齐）

- 单元格里的 `|` 务必转义为 `\|`

- 表注：`> 注：xxx`（引用块）

- ⛔ **不要**在 .md 里写 `\begin{table}` / `\begin{tabular}` / `\toprule` / `\midrule` / `\bottomrule`

- ⛔ **避免**交付 .tex 文件（Word 模式根本不读）

**调用 stats_utils 时按后缀交付相应格式：**

```python

from 工具.stats_utils import regression_table, descriptive_table

# 自动按后缀选格式（推荐）

ext = "md" if output_format == "docx" else "tex"

regression_table(results, ['OLS', 'Logit'],

                 output=f'图表/TABLE_regression.{ext}',

                 caption='回归结果')

descriptive_table(df, output=f'图表/TABLE_descriptive.{ext}')

```

<table_sizing>

**LaTeX 模式（.tex）：**

- Narrow tables (≤4 columns): avoid use `\resizebox` — it stretches text to full width, font becomes huge

- Wide tables (≥6 columns): wrap with `\resizebox{\textwidth}{!}{...}` to prevent overflow

- Use three-line style (booktabs): `\toprule`, `\midrule`, `\bottomrule`

- **⛔ Tall tables (>30 rows or multirow causing >35 visual rows)**: use `longtable` environment or split into multiple smaller tables. A single `tabular` that exceeds one page will be silently truncated.

- **⛔ Hyperparameter/config tables**: if models have very different parameter counts (e.g., Linear Reg 2 params vs LSTM 9 params), split into separate small tables per model or use `longtable`. Avoid cram all models into one huge tabular.

**Markdown 模式（.md）：**

- 列数 ≤ 8（Word 渲染列数过多会挤压）；超过 8 列务必横向拆分

- 数据行 ≤ 25（超过 25 行的表格在 Word 里跨页效果差）；超过的拆为「正文摘要表 + 附录完整表」

- 单元格内避免换行（`<br>` Word 不一定渲染）

- 避免嵌套表格（Markdown 不支撑）

- 数值精度统一：百分比保留 2 位小数（94.72%），系数保留 3-4 位（0.0234）

</table_sizing>

### 工作节点 6：Produce LaTeX include snippets

Save to `图表/图表引用.tex`. Use `[H]` float specifier (requires `\usepackage{float}`).

**⛔ Captions needs to match manuscript language.** Validate 选题规划.md or 问题分析.md:

- Chinese papers (stats modeling / math competition): `\caption{模型性能对比雷达图}` — Chinese caption

- English papers (MCM/ICM/APMCM): `\caption{Model Performance Comparison}` — English caption

**⛔ Axis labels in gen_fig_*.py needs to also match manuscript language:**

- Chinese: `ax.set_xlabel('迭代次数')`, `ax.set_ylabel('目标函数值')`, `label='本文算法'`

- English: `ax.set_xlabel('Iterations')`, `ax.set_ylabel('Objective Value')`, `label='Ours'`

### 工作节点 8：Quality validate

<quality_checklist>

- No in-visual title (captions in LaTeX only)

- Font ≥10pt

- Grayscale-distinguishable

- Legend does not obscure data

- Axes have units

- PDF vector output

- All values populated (no empty placeholders)

- Text does not obscure data points

- Numbers consistent with manuscript body / 计算结果.md

</quality_checklist>

**⛔ MANDATORY: Visual intelligent self-review (review each visual following all are generated):**

Review each generated visual against its script implementation. Answer the items below for every. If any ❌, regenerate that visual.

```

=== Per-figure review ===

For each fig_xxx.pdf, answer:

1. [Type match] Is this chart type the best choice for this data?

   - Method comparison (≤4 methods) → Grouped bar, not lollipop

   - Single-dim ranking/count → Horizontal bar (sorted + gradient color) or Pareto. Do NOT use vertical multi-color bars (random color per bar without grouping = visual noise, looks amateurish)

   - Method ranking (≥5 methods) → Horizontal bar preferred; Lollipop OK but must have gradient bg + highlight row + reference line

   - ⛔ Lollipop: if only plain stem+dot with no decoration, visual effect is poor — must follow adv #1 recipe with gradient bg + #1 highlight + median reference line

   - Time series trend → Line chart, not bar chart

   - Distribution comparison → Rain Cloud or box plot, not bar chart

   - Correlation matrix → Heatmap, not scatter matrix

   - Composition/proportion → Stacked bar or donut chart

   - If unsure, refer to 工具/figure_style_guide.md decision table

2. [Visual quality] Does the figure look professional and clear?

   - Enough spacing between data points/bars? (not crammed together)

   - Uses PALETTE colors, not matplotlib default blue?

   - Uses restrained fills and borders whose differences encode data rather than decoration?

   - Annotation text readable? (no overlap, not too small)

   - Heatmap: text color auto-adapts to background? (white on dark cells, black on light cells)

3. [Occlusion verify] Are there any overlap/clipping issues?

   - Labels overlapping each other? → use smart_labels() or adjust offset/fontsize

   - Labels overlapping data elements (bars/lines/dots)? → move labels above/below or add white bbox background

   - Legend covering data points? → move legend to empty area (loc='upper left' if data is on the right, etc.) or place outside plot

   - Axis tick labels cut off or overlapping? → rotate labels, reduce fontsize, or increase figure margins

   - Data points clipped at plot edges? → expand xlim/ylim by 5-10%

   - Colorbar overlapping the plot area? → adjust pad/shrink parameters

   - For multi-panel figures: subplot titles overlapping adjacent subplot content? → increase hspace/wspace

3. [Recipe usage] Is each figure based on recipe code?

   - Does the script call setup_style() + PALETTE?

   - Has only the visual elements needed to support the declared claim and reader task?

   - If plain matplotlib default style (blue bars, no annotations, no fills), must rewrite using recipe

4. [Information value] Does the figure convey meaningful information?

   - Has reference lines / annotation boxes / significance markers?

   - Are data differences visible? (if all bars are nearly the same height, the figure has no information value)

   - Is there a "so what" — what conclusion can the reader draw?

5. [Diversity] Are chart types diverse across the paper?

   - Same chart type appearing ≥3 times? If so, swap one

   - Repeated reader tasks use a consistent visual grammar; chart variety is not scored

   - Lollipop: use only when ranking is clearer than a bar chart; keep stem and dot simple, with at most one semantic highlight

```

If any visual has wrong type or poor visual quality, delete and regenerate.

### 工作节点 9：Count verification (MUST match plan — checklist reconciliation)

**⛔ 先重新读规划文档，提取图形与表格清单（上下文可能已截断，务必重新读）：**

```bash

echo "=== 重新读取规划文档中的图表清单 ==="

for plan in 问题分析.md 选题规划.md 论文规划.md 建模报告.md; do

    [ -f "$plan" ] || continue

    echo "--- $plan 中的图表规划 ---"

    grep -E 'fig_|TABLE_|DrawIO|TikZ|AIIMG|数据图|图表' "$plan" | head -30

done

echo ""

echo "=== 已生成的 PDF 文件 ==="

ls -la 图表/fig_*.pdf 2>/dev/null

echo ""

echo "=== 已生成的 TABLE 文件 ==="

ls -la 图表/TABLE_*.tex 图表/TABLE_*.md 2>/dev/null

```

Go back to the FIGURE PLAN CHECKLIST from Phase 1. For every item, validate if the corresponding file exists:

```bash

echo "=== FIGURE PLAN CHECKLIST RECONCILIATION ==="

echo ""

echo "PDF figures generated:"

ls -1 图表/*.pdf 2>/dev/null

echo ""

echo "Tables generated:"

ls -1 图表/TABLE_*.tex 图表/TABLE_*.md 2>/dev/null

echo ""

echo "DrawIO diagrams:"

ls -1 图表/*.drawio 2>/dev/null && echo "YES" || echo "NO"

echo ""

echo "=== Planned figures (from planning docs) ==="

for plan in 论文规划.md 问题分析.md 选题规划.md 建模报告.md; do

    [ -f "$plan" ] && echo "--- $plan ---" && grep -i 'fig\|图\|table\|表\|chart\|plot\|heatmap\|radar\|DrawIO\|drawio\|TikZ\|tikz' "$plan" | head -30

done

```

**⛔ MANDATORY: Update the checklist with actual status:**

```

FIGURE PLAN CHECKLIST (reconciliation):

[✅] 1. fig_desc_stats — 描述性统计分布图 → 图表/fig_desc_stats.pdf (exists, 45KB)

[✅] 2. fig_radar — 模型对比雷达图 → 图表/fig_radar.pdf (exists, 38KB)

[❌] 3. fig_forest — 回归系数森林图 → MISSING — need to generate

[✅] 4. TABLE_desc — 描述性统计表 → 图表/TABLE_desc.{tex|md}（按 OUTPUT_FORMAT 决定）(exists)

[❌] 5. TABLE_reg — 回归结果表 → MISSING — need to generate

[✅] 6. drawio_roadmap — 技术路线图 → 图表/技术路线图.drawio + 图表/技术路线图.pdf (exists)

Result: 4/6 complete, 2 MISSING

```

**If ANY item is marked ❌:**

1. Go back to Phase 3 and produce scripts for the missing visuals

2. Execute them (Phase 4)

3. Re-run this Phase 9 reconciliation

4. **Repeat until ALL items are ✅**

5. **⛔ 若某张图反复失败（同一工具 3 轮都不行），启用跨工具兜底：**

   - DrawIO 失败 → 降级到 TikZ（简化版）

   - TikZ 失败 → 降级到 DrawIO（去掉公式，用文字代替）

   - AI Image 失败 → 降级到 DrawIO（已有机制）

   - Matplotlib 失败 → 简化图形与表格类别（如雷达图失败→换分组柱状图）

**Do NOT finish until every planned item exists as a file. The plan is the contract.**

### 工作节点 10：⛔ FINAL QUALITY GATE

```bash

echo "=========================================="

echo "  FIGURE GENERATION QUALITY GATE"

echo "=========================================="

GATE_FAIL=0

# 1. All gen_fig scripts generated PDFs

SCRIPTS=$(ls 图表/gen_fig*.py 2>/dev/null | wc -l)

PDFS=$(ls 图表/fig_*.pdf 2>/dev/null | wc -l)

[ "$PDFS" -ge "$SCRIPTS" ] && echo "✅ All scripts generated PDFs ($PDFS/$SCRIPTS)" || { echo "❌ $((SCRIPTS-PDFS)) scripts failed to generate PDFs"; GATE_FAIL=$((GATE_FAIL+1)); }

# 2. 图表引用.tex exists and non-empty

[ -s 图表/图表引用.tex ] && echo "✅ 图表引用.tex exists" || { echo "❌ 图表引用.tex missing or empty"; GATE_FAIL=$((GATE_FAIL+1)); }

# 3. DrawIO diagrams (if planned)

if grep -qi 'drawio\|DrawIO\|架构图\|技术路线\|roadmap\|framework\|流程图' 论文规划.md 选题规划.md 问题分析.md 2>/dev/null; then

    # DrawIO/TikZ 检查已移至 systems-diagramming 步骤，此处跳过

    DRAWIO_COUNT=$(ls 图表/*.drawio 2>/dev/null | wc -l)

    [ "$DRAWIO_COUNT" -gt 0 ] && echo "  (DrawIO: $DRAWIO_COUNT files — will be validated by systems-diagramming step)" || echo "  (no DrawIO yet — will be generated by systems-diagramming step)"

fi

# 4. Figure verify script passes

bash 工具/figure_check.sh 2>/dev/null || bash skills/shared-scripts/figure_check.sh 2>/dev/null

FC_EXIT=$?

[ "$FC_EXIT" -eq 0 ] && echo "✅ Figure verify passed" || { echo "❌ Figure verify failed (exit=$FC_EXIT) — fix color/style issues"; GATE_FAIL=$((GATE_FAIL+1)); }

# 4.1 图例/标注遮挡检查（代码层面）

echo "--- 图例遮挡风险检查 ---"

for script in 图表/gen_fig*.py; do

    [ -f "$script" ] || continue

    bn=$(basename "$script")

    # 检查是否硬编码了 loc='upper right'（收敛曲线等场景容易遮挡）

    if grep -q "loc='upper right'" "$script" 2>/dev/null; then

        echo "  ⚠ $bn: 图例硬编码 loc='upper right' — 如果数据在右上角会遮挡，建议改为 loc='best'"

    fi

    # 检查是否有 annotate 和 legend 在同一区域

    HAS_ANNOTATE=$(grep -c 'ax.annotate\|ax.text' "$script" 2>/dev/null || echo 0)

    HAS_LEGEND=$(grep -c 'ax.legend' "$script" 2>/dev/null || echo 0)

    if [ "$HAS_ANNOTATE" -gt 0 ] && [ "$HAS_LEGEND" -gt 0 ]; then

        if ! grep -q "bbox_to_anchor\|loc='best'" "$script" 2>/dev/null; then

            echo "  ⚠ $bn: 同时有标注和图例但未用 loc='best' 或 bbox_to_anchor — 可能遮挡"

        fi

    fi

    # 检查 annotate 的 xytext 是否用硬编码偏移（容易超出图表边界）

    # plot_utils._clamp_texts_to_axes 会在 savefig 时自动裁剪，但最好从源头避免

    if [ "$HAS_ANNOTATE" -gt 0 ]; then

        HARDCODED_OFFSET=$(grep -cP 'xytext=\([^)]*\+\s*\d' "$script" 2>/dev/null || echo 0)

        if [ "$HARDCODED_OFFSET" -gt 2 ]; then

            echo "  ⚠ $bn: $HARDCODED_OFFSET 处 annotate 用硬编码偏移 — 数据靠近边缘时标注会超出图表"

            echo "    建议：用 textcoords='offset points' 或确保 xytext 在 ax.get_xlim()/get_ylim() 范围内"

        fi

    fi

done

# 4.5 TikZ/DrawIO — handled by systems-diagramming step, skip here

echo "  (TikZ/DrawIO diagrams will be generated and validated by the next step: systems-diagramming)"

# 4.6 AI Image figures (if planned)

AIIMG_PLANNED=$(grep -ci 'AIIMG\|AI.Image\|场景示意' 问题分析.md 2>/dev/null || echo 0)

if [ "$AIIMG_PLANNED" -gt 0 ]; then

    AIIMG_PDF=$(ls 图表/场景示意图*.pdf 图表/AI示意图*.pdf 2>/dev/null | wc -l)

    if [ "$AIIMG_PDF" -gt 0 ]; then

        echo "✅ AI Image figures: $AIIMG_PDF PDFs"

    else

        # Verify if DrawIO fallback was used

        echo "  AI Image: no PDFs (may have used DrawIO fallback — verify AIIMG_FAILED)"

    fi

else

    echo "  (no AI Image planned)"

fi

# 5. Plan reconciliation count

PLAN_FIGS=0

for plan in 论文规划.md 选题规划.md 问题分析.md; do

    [ -f "$plan" ] || continue

    pf=$(grep -ci 'fig_\|图.*：\|figure.*:\|TABLE_' "$plan" 2>/dev/null || echo 0)

    [ "$pf" -gt "$PLAN_FIGS" ] && PLAN_FIGS=$pf

done

ACTUAL_TOTAL=$((PDFS + $(ls 图表/TABLE_*.tex 图表/TABLE_*.md 2>/dev/null | wc -l)))

if [ "$PLAN_FIGS" -gt 0 ]; then

    [ "$ACTUAL_TOTAL" -ge "$PLAN_FIGS" ] && echo "✅ Output count: $ACTUAL_TOTAL (plan: ~$PLAN_FIGS)" || { echo "❌ Only $ACTUAL_TOTAL outputs (plan: ~$PLAN_FIGS)"; GATE_FAIL=$((GATE_FAIL+1)); }

else

    echo "  Output count: $ACTUAL_TOTAL (no plan to compare)"

fi

# 6. No empty/tiny PDFs

TINY=0

HUGE=0

for pdf in 图表/fig_*.pdf; do

    [ -f "$pdf" ] || continue

    sz=$(wc -c < "$pdf")

    [ "$sz" -lt 5000 ] && { echo "  ❌ $(basename $pdf) is only $sz bytes — likely broken"; TINY=$((TINY+1)); }

done

# Verify for oversized PDFs (DrawIO/TikZ/AI Image figures that might be too tall)

for pdf in 图表/技术路线图.pdf 图表/fig_framework.pdf 图表/fig_flow_*.pdf 图表/fig_model_*.pdf 图表/fig_pipeline.pdf 图表/fig_index_*.pdf 图表/fig_network.pdf 图表/场景示意图*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    # Use Python to verify PDF page dimensions if possible

    dims=$($PYTHON -c "

try:

    from PyPDF2 import PdfReader

    r = PdfReader('$pdf')

    p = r.pages[0]

    w = float(p.mediabox.width) * 0.3528  # points to mm

    h = float(p.mediabox.height) * 0.3528

    ratio = h / w if w > 0 else 0

    print(f'{w:.0f}x{h:.0f}mm ratio={ratio:.2f}')

    if h > 250: print('TOO_TALL')

    if ratio > 1.8: print('TOO_NARROW')

except: pass

" 2>/dev/null)

    if echo "$dims" | grep -q 'TOO_TALL'; then

        echo "  ⚠ $bn 高度超过 250mm — 编译后可能占满整页，建议压缩"

        HUGE=$((HUGE+1))

    fi

    if echo "$dims" | grep -q 'TOO_NARROW'; then

        echo "  ⚠ $bn 宽高比过窄 — 用 width=0.6\\textwidth 而非 \\textwidth"

        HUGE=$((HUGE+1))

    fi

done

[ "$TINY" -eq 0 ] && echo "✅ All PDFs non-trivial" || { echo "❌ $TINY tiny/broken PDFs"; GATE_FAIL=$((GATE_FAIL+1)); }

[ "$HUGE" -eq 0 ] && echo "✅ All PDFs reasonable size" || echo "⚠ $HUGE oversized PDFs — adjust width in 图表引用.tex"

echo ""

[ "$GATE_FAIL" -eq 0 ] && echo "✅ ALL PASSED — figures ready for paper writing" || echo "❌ $GATE_FAIL FAILURES — fix and re-run"

```

**⛔ If GATE_FAIL > 0, fix every ❌ and re-run. Do NOT finish with any ❌.**

## 核心规则

- Data visuals is expected to be PDF. Avoid use pgfplots to draw from CSV (path/column/encoding issues)

- DrawIO .drawio files export to PDF via `draw.io.exe --export --format pdf --crop`

- Primary output: `图表/` directory

- Temp files: `临时文件/`

- One script per visual, independently re-runnable

- Read data from JSON/CSV, avoid hardcode values

