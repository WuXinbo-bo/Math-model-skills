---
name: systems-diagramming
description: "Meta-model-agent 构建技术路线、方法关系、系统架构与流程示意资产。适用于系统逻辑制图。"
---

# 系统逻辑制图

## 稳定执行契约

- **执行目标**：构建技术路线、模型关系、系统结构与算法流程等非数据型示意资产。
- **调用参数**：[figure-plan-or-data-path]。
- **权威输入**：问题分析.md、建模报告.md、计算结果.md及既有图表计划。
- **允许交付**：图表/中的 DrawIO、TikZ 与导出图，以及图表引用.tex中的对应入口。
- **禁止写入**：不得越权修改已冻结的上游事实、用户原始文件或本协议未授权的目录。
- **可用工具边界**：Bash(*), Read, Write, Edit, Grep, Glob, Agent。
- **最小交付**：结构清晰、节点可读、关系正确、源文件可编辑、导出结果可编译。
- **恢复入口**：优先读取当前工作、状态记录和已有产物，从最近一次通过门禁的位置继续。
- **失败回退**：结构关系不明确时回退查阅建模报告；不得用装饰性连线掩盖逻辑缺口。
- **收口顺序**：先核对输入，再完成产物，再运行本环节门禁，最后登记状态；门禁未通过不得宣告完成。

Produce DrawIO architecture diagrams and TikZ visuals for: **$ARGUMENTS**

This is a **lightweight sub-step** split from evidence-visualization. It ONLY handles non-data diagrams (DrawIO + TikZ). Data visuals (matplotlib/seaborn) were already generated in the previous evidence-visualization step.

## 运行参数

- **FIG_DIR = `图表/`**

- **CUSTOM_REQUIREMENTS** — User-specified requirements, highest priority.

## ⛔⛔⛔ 交付契约（最高优先级）

**Must produce at least 1 `图表/*.drawio` or `图表/tikz_*.tex` and corresponding PDF, plus updated `图表/图表引用.tex`**.

⛔ **特殊豁免**：若 论文规划.md 清晰标明无架构图/过程图需求（纯文字论文/数据分析报告），准许跳过此 skill 的产物要求；但仍要保留已有的 `图表/图表引用.tex` 不破坏。

⛔ **MUST run output verification prior to ending**:

```bash

PASS=true

mkdir -p 图表

PDF_COUNT=$(ls 图表/*.pdf 2>/dev/null | wc -l)

DRAWIO_COUNT=$(ls 图表/*.drawio 2>/dev/null | wc -l)

TIKZ_COUNT=$(ls 图表/tikz_*.tex 2>/dev/null | wc -l)

PLAN_NEEDS_DIAGRAM=$(grep -iE 'drawio|tikz|架构图|流程图|fig_arch|fig_flow|技术路线图|fig_er' 论文规划.md 2>/dev/null | wc -l)

if [ "$PDF_COUNT" -ge 1 ] || [ "$DRAWIO_COUNT" -ge 1 ] || [ "$TIKZ_COUNT" -ge 1 ]; then

    echo "✅ diagrams: PDF=$PDF_COUNT drawio=$DRAWIO_COUNT tikz=$TIKZ_COUNT"

elif [ "$PLAN_NEEDS_DIAGRAM" -eq 0 ]; then

    echo "✓ 规划无架构图/流程图需求, 跳过"

else

    echo "❌ 规划要求架构图/流程图但未生成"

    PASS=false

fi

[ -f 图表/图表引用.tex ] || touch 图表/图表引用.tex

[ "$PASS" != true ] && echo "⛔ Output verification FAILED — must complete before ending"

```

## 执行流程

### 工作节点 0：恢复核验（断线重跑必读）

⛔ **当前环节可能由于断线/人工重跑被多次启动**。每一次启动前**务必**先扫描已有产物：

```bash

echo "=== 工作区扫描 ==="

HAS_DRAWIO=$(ls 图表/*.drawio 2>/dev/null | wc -l)

HAS_TIKZ_TEX=$(ls 图表/tikz_*.tex 2>/dev/null | wc -l)

HAS_TIKZ_PDF=$(ls 图表/tikz_*.pdf 2>/dev/null | wc -l)

HAS_FIG_PDF_FROM_DRAWIO=$(ls 图表/fig_*.pdf 2>/dev/null | wc -l)

echo "  *.drawio: $HAS_DRAWIO, tikz_*.tex: $HAS_TIKZ_TEX, tikz_*.pdf: $HAS_TIKZ_PDF"

echo "  fig_*.pdf (含 drawio 导出): $HAS_FIG_PDF_FROM_DRAWIO"

```

**依据扫描结果决定行动**：

| 运行状态 | 行动 |

|---|---|

| 规划要求的全部 drawio + tikz 都已产出（含 .drawio + 相应 .pdf） | **跳到 Phase 8 (latex_includes 核对)**，校验通过即完成 |

| 部分已产出 | **只产出缺失的**（已有的避免重画） |

| 啥都没有 | 从 Phase 1 启动 |

⛔ **铁律**：已有 `图表/*.drawio` / `图表/tikz_*.tex` / `图表/tikz_*.pdf` 避免重写。

### 工作节点 1：Read existing state + DrawIO plan

1. Validate what already exists from the previous evidence-visualization step:

```bash

echo "=== Existing figures ==="

ls -la 图表/*.pdf 2>/dev/null | head -30

echo ""

echo "=== Existing .drawio files ==="

ls -la 图表/*.drawio 2>/dev/null

echo ""

echo "=== 图表引用.tex exists? ==="

[ -f 图表/图表引用.tex ] && echo "YES" || echo "NO"

```

2. Extract the DrawIO/TikZ plan from planning docs:

```bash

# 自动选择规划文档（按存在性优先级）：

#   问题分析.md（数模竞赛/科研流程） > 研究方案.md（开题报告）

#   > 论文规划.md（论文写作/课程报告） > 文献综述.md（文献综述，跳过）

PLAN_DOC=""

for f in 问题分析.md 研究方案.md 论文规划.md; do

    if [ -f "$f" ]; then

        PLAN_DOC="$f"

        break

    fi

done

echo "=== 使用规划文档: $PLAN_DOC ==="

# 文献综述工作流不需要架构图，直接跳过

if [ -f 文献综述.md ] && [ -z "$PLAN_DOC" ]; then

    echo "✅ 文献综述工作流不需要架构图，已跳过"

    exit 0

fi

# 如果没有任何规划文档，退化为"画 1 张 技术路线图 兜底"

if [ -z "$PLAN_DOC" ]; then

    echo "⚠ 无规划文档，将只生成 技术路线图.png 兜底"

    PLAN_DOC=""

fi

echo "=== DrawIO plan from $PLAN_DOC ==="

grep -A 50 'DrawIO' "$PLAN_DOC" 2>/dev/null | grep -E 'DrawIO-[0-9]|^\- \[ \] fig_(arch|er|flow|module|roadmap|pipeline|framework|index|gantt|network)' || echo "No DrawIO plan found in $PLAN_DOC"

echo ""

echo "=== TikZ plan ==="

grep -E 'TikZ-[0-9]|模型架构|变量关系|因果路径|算法流程|几何示意' "$PLAN_DOC" 2>/dev/null || echo "No TikZ plan found"

echo ""

echo "=== AI Image failures (need DrawIO fallback) ==="

# 读取前一步 evidence-visualization 持久化的 AI Image 状态

if [ -f 图表/_aiimg_status.txt ]; then

    AIIMG_STATUS=$(cat 图表/_aiimg_status.txt)

    echo "AI Image status: $AIIMG_STATUS"

    if [ "$AIIMG_STATUS" = "ALL_SUCCESS" ]; then

        echo "All AI Image figures succeeded — only generate DrawIO for figures NOT covered by AI Image"

    elif [ "$AIIMG_STATUS" = "SOME_FAILED" ]; then

        AIIMG_FAILED=$(cat 图表/_aiimg_failed.txt 2>/dev/null)

        echo "AI Image failures: $AIIMG_FAILED — generate DrawIO for these"

    elif [ "$AIIMG_STATUS" = "ALL_FAILED" ]; then

        echo "All AI Image attempts failed (API Key missing or network error) — generate DrawIO for ALL non-data figures"

    else

        echo "AI Image disabled — generate DrawIO for ALL non-data figures"

    fi

else

    echo "No AI Image status file — generate DrawIO for ALL non-data figures (default)"

fi

echo ""

# Determine language（注意：comp_apmcm_zh 是中文赛项，必须先排除）

if grep -qi 'comp_apmcm_zh' "$PLAN_DOC" META_MODEL_AGENT.md 2>/dev/null; then

    DRAWIO_LANG="zh"

elif grep -qi 'MCM\|ICM\|APMCM\|comp_mcm\|comp_apmcm\|comp_certcup_en\|comp_shuwei_en\|语言.*English\|Language.*English' "$PLAN_DOC" META_MODEL_AGENT.md 2>/dev/null; then

    DRAWIO_LANG="en"

else

    DRAWIO_LANG="zh"

fi

echo "DrawIO language: $DRAWIO_LANG"

```

**⛔ 读完规划后，务必交付一个 DRAWIO PLAN CHECKLIST（后续环节对照用）：**

工作流类别决定数量：

- **数模竞赛 / 科研过程**（有 问题分析.md）：按 DrawIO 清单全部产出（roadmap + flow_q1/q2/pipeline 等）

- **开题报告**（有 研究方案.md）：**只产出 技术路线图**，其他 问题流程图_1/q2 避免画

- **课程论文/报告**（有 论文规划.md，无 问题分析.md）：按 论文规划.md 中 `## 架构图（drawio）规划` 段落列出的 fig_arch/fig_er/fig_flow_* 产出

- **论文写作**（有 论文规划.md，无 问题分析.md）：按 论文规划.md 列出的图产出

```

DRAWIO PLAN CHECKLIST (from $PLAN_DOC):

[ ] 1. 技术路线图 — 技术路线图 (DrawIO)

[ ] 2. 问题流程图_1 — 问题一求解流程图 (DrawIO)

[ ] 3. 问题流程图_2 — 问题二求解流程图 (DrawIO)

[ ] 4. fig_pipeline — 数据处理 Pipeline (DrawIO)

[ ] 5. tikz_architecture — 模型架构图 (TikZ, if planned)

Total: N DrawIO + M TikZ

```

**每一条都务必在后续环节中产出。规划清单就是合同。**

**⛔ DrawIO 图中全部文字务必与论文语言保持一致。**

**⛔ 数模竞赛论文务必至少产出 1 张 DrawIO 技术路线图。其他 DrawIO 图按规划清单产出。**

**⛔ 开题报告 / 文献综述 不画 问题流程图_1/q2 这些数模专用图。开题只画 技术路线图，文献综述不画。**

**⛔ 若规划清单里有 N 条 DrawIO 图，当前环节结束时务必有 N 个 .drawio 文件和 N 个相应的 .pdf。缺一不可。**

### 工作节点 2：Read DrawIO rules

**MANDATORY**: Consult the DrawIO rules prior to writing ANY .drawio XML:

```bash

cat 工具/drawio_rules.md 2>/dev/null || cat skills/shared-scripts/drawio_rules.md

```

### 工作节点 3：Produce .drawio XML files

**⛔ CRITICAL: DrawIO XML 文件很大（200-500行），务必分段写入，防止交付截断导致空工具调用。**

**无误写法（分 3 段写入）：**

```bash

# 第 1 段：写文件头 + 前半部分节点

cat << 'XMLEOF' > 图表/技术路线图.drawio

<mxfile>

  <diagram name="Page-1">

    <mxGraphModel>

      <root>

        <mxCell id="0"/>

        <mxCell id="1" parent="0"/>

        <!-- 前半部分节点（顶部标题栏 + 左栏 + 前几个阶段） -->

XMLEOF

# 第 2 段：追加中间节点

cat << 'XMLEOF' >> 图表/技术路线图.drawio

        <!-- 中间部分节点（核心阶段 + 右栏方法） -->

XMLEOF

# 第 3 段：追加剩余节点 + 连线 + 闭合标签

cat << 'XMLEOF' >> 图表/技术路线图.drawio

        <!-- 连线和底部 -->

      </root>

    </mxGraphModel>

  </diagram>

</mxfile>

XMLEOF

```

**每段不超过 150 行。** 一张技术路线图分 3 段，一张过程图分 2-3 段。

**⛔ 避免用 Write 工具写大 XML——Write 工具的 content 参数也会被截断。用 Bash heredoc 分段追加最可靠。**

按规划清单逐条产出，每张图一个 `.drawio` 文件：

**⛔ 配色与风格自由发挥原则：**

- 依据论文主题自主选取柔和高级的配色方案，避免每一次都用默认学术蓝

- 不同子问题的过程图用不同配色，形成视觉区分

- 推荐风格：低饱和度渐变色（莫兰迪色系）、柔和的暖色/冷色搭配

- 技术路线图：在三栏结构基础上优先采用黑白灰阶，通过边框粗细、虚实、留白和箭头形态建立层级；仅允许极少量低饱和强调色

- 求解过程图：鼓励采用多种节点形状（六边形=数据处理、平行四边形=输入交付、圆柱=数据源、菱形=判定），避免全用圆角矩形

- 布局可灵活：纵向、横向、L 形拐弯、泳道分区都可，依据内容选最合适的

- **关键约束不变**：三栏结构（技术路线图）、判定分支+并行+循环（过程图）、双行节点、html=1、无 shadow

| 图类别 | 文件名示例 | 内容要点 |

|--------|-----------|---------|

| 技术路线图 | `技术路线图.drawio` | ⛔ 随机选模板 A 或 B（见 drawio_rules.md），保持三栏结构。节点居中分布 |

| 子问题求解过程图 | `问题流程图_1.drawio` | ⛔ 务必涵盖：(1) 判定分支（菱形+是/否）(2) 并行分叉 (3) 循环反馈箭头 (4) 节点双行。**避免画右侧工具/方法注释栏**（技术路线图才需） |

| 数据处理 Pipeline | `fig_pipeline.drawio` | 横向多阶段、每阶段工具/方法标注 |

| 概念框架图 | `fig_framework.drawio` | 理论模块分层展示，层间大箭头 |

| 指标体系层次图 | `fig_index_hierarchy.drawio` | 目标层→准则层→指标层的树形结构 |

| 模型选取决策树 | `fig_model_decision.drawio` | 从数据特征出发的分支判定 |

| 甘特图/调度方案图 | `fig_gantt.drawio` | 横轴时间+纵轴工作项/资源 |

| 网络拓扑/路线图 | `fig_network.drawio` | 节点+边的网络结构 |

⛔ 以下图类别**避免用 DrawIO**，用 TikZ 产出：模型架构图、变量关系图、算法过程图（带公式）、几何示意图。

**⛔ 完整 XML 示例**：产出前先**随机选**一个模板参考其 XML 结构。当前有 4 个模板可选：

- `example_roadmap_stats.drawio`（B：粉色冷色，简版四阶段）

- `example_roadmap_stats_warm.drawio`（B-warm：暖橙紫色，简版四阶段）

- `example_roadmap_hex.drawio`（C：粉色冷色，完整六阶段，信息密度高）

- `example_roadmap_hex_cool.drawio`（C-cool：蓝色高对比，完整六阶段）

**⛔ 产出技术路线图前务必实施：**

```bash

echo "=== 随机选择技术路线图模板（4 选 1，确保不同论文风格有差异）==="

TEMPLATE=$(python3 -c "import random; print(random.choice(['B','B-warm','C','C-cool']))" 2>/dev/null || echo "C")

echo "本次使用模板: $TEMPLATE"

case "$TEMPLATE" in

  B)      FILE=example_roadmap_stats.drawio ;;

  B-warm) FILE=example_roadmap_stats_warm.drawio ;;

  C)      FILE=example_roadmap_hex.drawio ;;

  C-cool) FILE=example_roadmap_hex_cool.drawio ;;

esac

echo "--- 参考模板: $FILE ---"

cat 工具/$FILE 2>/dev/null | head -80

echo "... (参考完整 XML 结构和配色后再生成 技术路线图.drawio)"

```

⛔ **配色避免混搭**：选定模板后，整张图沿用该模板的配色方案，避免把不同模板的颜色混在一起。

**⛔ 产出求解过程图前务必实施：**

```bash

echo "=== 读取求解流程图示例 ==="

cat 工具/example_flow.drawio 2>/dev/null | head -50

echo "... (参考完整 XML 结构后再生成)"

```

**⛔ 每张图产出后立即校验文件出现：**

```bash

[ -f 图表/技术路线图.drawio ] && echo "✅ 技术路线图.drawio created" || echo "❌ MISSING"

```

### 工作节点 4：Export to PDF + self-validate + fix loop (⛔ 最多 3 轮)

**每张 .drawio 文件务必经过：导出 → 自检 → 修复 → 重新导出的循环，最多 3 轮。**

对每张 .drawio 文件，实施以下循环：

```

FOR each 图表/*.drawio file:

  FOR round = 1 to 3:

    1. Export: draw.io.exe --export --format pdf --crop

    2. If PDF not generated → verify XML syntax (ID duplicate, unclosed tags, escaping), fix, CONTINUE to next round

    3. Self-verify the XML (Step 5 checklist below):

       - Overlap verify (x/y/width/height collision)

       - Edge crossing verify (jumpStyle, waypoints)

       - Text overflow verify (width vs char count)

       - Spacing consistency

       - Style consistency

       - Size verify (within page bounds)

    4. If any verify fails → fix the XML, CONTINUE to next round

    5. If all checks pass → BREAK (this file is done)

  END FOR

  If still failing after 3 rounds → fallback to TikZ for this diagram

END FOR

```

**导出命令：**

```bash

draw.io.exe --export --format pdf --crop --output "图表/${bn}.pdf" "$drawio_file" 2>&1 &

DRAWIO_PID=$!

( sleep 60 && kill $DRAWIO_PID 2>/dev/null && echo "⚠ timeout" ) &

TIMER_PID=$!

wait $DRAWIO_PID 2>/dev/null

kill $TIMER_PID 2>/dev/null

```

**自检清单（每轮都过一遍）：**

```

1. [重叠检查] 同行节点：(x1 + width1 + 30) ≤ x2；上下层：(y1 + height1 + 30) ≤ y2

2. [连线遮挡] 所有连线 jumpStyle=arc;jumpSize=6;rounded=1，不穿过节点

3. [文字溢出] 中文 width ≥ 字数×16+40，英文 width ≥ 字符数×8+40，whiteSpace=wrap

4. [间距一致] 同层节点间距差异 ≤ 10px

5. [样式一致] 同类节点 fillColor/strokeColor/fontSize 一致，fontstyle=1

6. [尺寸检查] 总宽度 ≤ pageWidth，总高度 ≤ pageHeight

7. [⛔ 居中检查] 中栏子框和节点必须在虚线框内居中分布，不要左对齐留大片空白。计算：左边距 = (容器宽度 - 内容总宽度) / 2。特别检查：只有 2-3 个节点的行、最后一行（结论阶段）

```

**⛔ 发现问题务必立即调整 XML 并重新导出，不可跳过。3 轮都失败 → 降级到 TikZ 兜底。**

### 工作节点 5：Structure validation loop (⛔ MUST PASS)

对技术路线图和求解过程图运行结构自检脚本。**若不通过，务必查阅示例文件参考后重写，随后重新导出+重新自检，最多 3 轮。**

```bash

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

# 技术路线图结构检查 + 强制修复循环

if [ -f 图表/技术路线图.drawio ]; then

    for ROUND in 1 2 3; do

        echo "=== 技术路线图结构自检 (round $ROUND) ==="

        $PYTHON 工具/drawio_check.py 图表/技术路线图.drawio roadmap

        if [ $? -eq 0 ]; then

            echo "✅ 技术路线图结构合格"

            break

        fi

        if [ $ROUND -lt 3 ]; then

            echo "⛔ 不合格 — 读取示例后重写..."

            echo ">>> cat 工具/example_roadmap_stats.drawio 或 工具/example_roadmap_hex.drawio 参考结构"

            # Meta-model-agent: 你必须在这里读取一个示例模板，修改 技术路线图.drawio，然后重新导出 PDF

        else

            echo "⛔ 3 轮仍不合格 — 降级到 TikZ"

        fi

    done

fi

# 求解流程图结构检查 + 强制修复循环

for flow in 图表/fig_flow_*.drawio; do

    [ -f "$flow" ] || continue

    for ROUND in 1 2 3; do

        echo "=== 求解流程图结构自检: $(basename $flow) (round $ROUND) ==="

        $PYTHON 工具/drawio_check.py "$flow" flow

        if [ $? -eq 0 ]; then

            echo "✅ 流程图结构合格"

            break

        fi

        if [ $ROUND -lt 3 ]; then

            echo "⛔ 不合格 — 读取示例后重写..."

            echo ">>> cat 工具/example_flow.drawio 参考结构"

        else

            echo "⛔ 3 轮仍不合格 — 降级到 TikZ"

        fi

    done

done

```

**⛔ 关键：上面的 bash 脚本只是检测框架。Meta-model-agent 在看到 `⛔ 不合格` 交付后，务必：**

1. **`cat 工具/example_roadmap_stats.drawio` 或 `工具/example_roadmap_hex.drawio`** 查阅完整示例（4 个模板任选一个，与初次产出时所选模板保持一致）

2. **重写 .drawio XML**（修复结构问题）

3. **重新导出 PDF**（`draw.io.exe --export ...`）

4. **重新运行 drawio_check.py** 校验

5. **重复直到通过或 3 轮用完**

**不准许看到 CRITICAL 后跳过不修。**

### 工作节点 6：Plan reconciliation loop (⛔ 缺一不可)

**逐条对照规划清单，缺失的务必补产出。循环直到全部齐全。**

```bash

echo "=== DrawIO plan reconciliation ==="

echo "Planned:"

grep -E 'DrawIO-[0-9]' 问题分析.md 2>/dev/null

echo ""

echo "Generated:"

ls -1 图表/*.drawio 2>/dev/null

echo ""

echo "Exported PDFs:"

ls -1 图表/技术路线图.pdf 图表/fig_flow_*.pdf 图表/fig_pipeline*.pdf 图表/fig_framework*.pdf 图表/fig_index_*.pdf 图表/fig_model_*.pdf 图表/fig_network*.pdf 2>/dev/null

```

**⛔ 对照上面的交付：**

1. 规划清单中的每一条，是否都有相应的 `.drawio` 文件？

2. 各个 `.drawio` 文件是否都有相应的 `.pdf`？

3. 若有缺失 → **立即回到 Phase 3 补产出该图的 .drawio XML → 导出 PDF → 自检**

4. **重复当前环节直到全部规划项都有 .drawio + .pdf**

5. 若某张图反复失败（3 轮），启用跨工具兜底：DrawIO 失败 → TikZ，TikZ 失败 → DrawIO（简化版）

**⛔ 校验完成后，更新 DRAWIO PLAN CHECKLIST 运行状态：**

```

DRAWIO PLAN CHECKLIST (reconciliation):

[✅] 1. 技术路线图 — 图表/技术路线图.drawio + 图表/技术路线图.pdf (exists, XXX bytes)

[✅] 2. 问题流程图_1 — 图表/问题流程图_1.drawio + 图表/问题流程图_1.pdf (exists)

[❌] 3. 问题流程图_2 — MISSING — need to generate

[✅] 4. fig_pipeline — 图表/fig_pipeline.drawio + 图表/fig_pipeline.pdf (exists)

Result: 3/4 complete, 1 MISSING → go back to Step 3 for 问题流程图_2

```

### 工作节点 7：Produce TikZ diagrams (if planned)

**若规划清单中有 TikZ 类别的图，在此环节产出。**

1. Read TikZ rules:

```bash

cat 工具/tikz_rules.md 2>/dev/null || cat skills/shared-scripts/tikz_rules.md

```

2. Write TikZ implementation to `图表/结构示意图.tex`.

3. **Compile + fix loop (最多 3 轮)：**

```

FOR round = 1 to 3:

  1. Compile: xelatex -interaction=nonstopmode -output-directory=figures 图表/结构示意图.tex

  2. If compilation fails:

     - Verify: math mode paired? (\usetikzlibrary missing? align= attribute? xelatex for Chinese?)

     - Fix the .tex file

     - CONTINUE to next round

  3. Run tikz_check.sh:

     bash 工具/tikz_check.sh 图表/结构示意图.tex

  4. If CRITICAL issues found:

     - Fix the .tex file (color scheme, overlap, text width, edge crossing)

     - CONTINUE to next round

  5. If all pass → BREAK

END FOR

If still failing after 3 rounds → fallback to DrawIO (simplified version, no formulas)

```

**编译命令：**

```bash

xelatex -interaction=nonstopmode -output-directory=figures 图表/结构示意图.tex 2>&1 | tail -10

```

**tikz_check.sh 自检（编译成功后务必实施）：**

```bash

for texfile in 图表/tikz_*.tex 图表/结构示意图.tex; do

    [ -f "$texfile" ] || continue

    echo "=== TikZ 自检: $(basename $texfile) ==="

    bash 工具/tikz_check.sh "$texfile" 2>/dev/null || bash skills/shared-scripts/tikz_check.sh "$texfile"

    if [ $? -gt 0 ]; then

        echo "⛔ 有 CRITICAL 问题 — 必须修复后重新编译"

    fi

done

```

**⛔ tikz_check.sh 报告的全部 CRITICAL 务必修复后重新编译。不准许带着 CRITICAL 完成环节。**

**人工内容自检（编译成功 + tikz_verify 通过后过一遍）：**

- [ ] 全部节点文字完整可见，没有被截断

- [ ] 连线没有穿过其他节点或文字

- [ ] 箭头方向无误（因果关系/数据流向）

- [ ] 数学公式渲染无误（变量名/希腊字母/上下标）

- [ ] 配色与论文整体风格保持一致（参考 tikz_rules.md 配色方案）

- [ ] 节点间距均匀，整图居中

**若未 TikZ 图需产出 → 跳过此环节。**

### 工作节点 7.5：TikZ 视觉自检（vision LLM，自动化修复）

**对各个编译成功的 TikZ PDF，用 vision LLM 核验布局质量。最多 3 轮修复。**

**⛔ 若 vision API 不可用（exit 2），跳过此环节，不阻塞过程。**

**⛔ 实施方式：这不是一个完整的 bash 脚本。你需逐步实施：先运行 PDF→PNG + vision 核验，若返回 ISSUE，你务必用 Read 工具查阅 TikZ .tex 源码，依据 vision 反馈调整（调整坐标/间距/节点宽度/颜色），用 Write/Edit 工具写回，随后重新编译 xelatex，再重新核验。每轮都是：核验→调整→编译→随后核验。**

```bash

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

mkdir -p 临时文件

for tikz_pdf in 图表/tikz_*.pdf; do

    [ -f "$tikz_pdf" ] || continue

    bn=$(basename "$tikz_pdf" .pdf)

    tikz_tex="图表/${bn}.tex"

    [ -f "$tikz_tex" ] || tikz_tex="图表/结构示意图.tex"

    for VROUND in 1 2 3; do

        echo "=== TikZ 视觉自检: $bn (round $VROUND) ==="

        # PDF → PNG（尝试多种方式）

        PNG_OK=0

        if command -v pdftoppm >/dev/null 2>&1; then

            pdftoppm -png -r 200 -singlefile "$tikz_pdf" "临时文件/${bn}_vverify" && PNG_OK=1

        fi

        if [ "$PNG_OK" -eq 0 ] && $PYTHON -c "from pdf2image import convert_from_path" 2>/dev/null; then

            $PYTHON -c "

from pdf2image import convert_from_path

imgs = convert_from_path('$tikz_pdf', dpi=200, first_page=1, last_page=1)

imgs[0].save('临时文件/${bn}_vverify.png', 'PNG')

" && PNG_OK=1

        fi

        if [ "$PNG_OK" -eq 0 ]; then

            echo "⚠ 无法转换 PDF→PNG（缺少 pdftoppm 或 pdf2image），跳过视觉自检"

            break

        fi

        # 可选视觉检查工具未部署时，保留结构检查结果并跳过本项
        if [ ! -f 工具/tikz_vision_verify.py ]; then
            echo "⚠ tikz_vision_verify.py 未部署，跳过可选视觉检查"
            break
        fi

        VRESULT=$($PYTHON 工具/tikz_vision_verify.py "临时文件/${bn}_vverify.png" 2>&1)

        VEXIT=$?

        echo "$VRESULT"

        if [ "$VEXIT" -eq 0 ]; then

            echo "✅ $bn 视觉检查通过"

            break

        elif [ "$VEXIT" -eq 2 ]; then

            echo "⚠ Vision API 不可用，跳过视觉自检"

            break

        fi

        # 有问题 → 修复

        if [ $VROUND -lt 3 ]; then

            echo "⛔ 发现视觉问题，读取 TikZ 源码修复..."

            echo ">>> Vision 反馈: $VRESULT"

            echo ">>> ⛔ 你必须立即：1.读取 $tikz_tex 2.根据上述反馈修改节点坐标/间距/宽度/颜色 3.重新编译 xelatex"

        else

            echo "⚠ 3 轮视觉自检仍有问题，继续（不阻塞流程）"

        fi

    done

done

```

### 工作节点 8：Update 图表引用.tex

为全部 DrawIO/TikZ 导出的 PDF **追加** LaTeX include 片段到 `图表/图表引用.tex`。

**⛔ 注意：前一步 evidence-visualization 已经在 图表引用.tex 中写入了数据图的 include 片段。当前环节只追加 DrawIO/TikZ 图的片段，避免覆盖已有内容。采用 `>>` 追加而非 `>` 覆盖。**

**⛔ 图片尺寸双约束（防止占满整页）：**

| 图类别 | width | height |

|--------|-------|--------|

| 技术路线图 | `\textwidth` | `0.45\textheight` |

| Pipeline 图 | `\textwidth` | `0.3\textheight` |

| 概念框架图 | `0.9\textwidth` | `0.4\textheight` |

| 求解过程图 | `0.85\textwidth` | `0.38\textheight` |

| 决策树 | `0.85\textwidth` | `0.38\textheight` |

| 指标体系 | `0.9\textwidth` | `0.25\textheight` |

| 网络拓扑 | `0.6\textwidth` | `0.35\textheight` |

⛔ 全部图务必有 `keepaspectratio`。

**⛔ Captions needs to match manuscript language.**

```latex

% === 技术路线图 ===

\begin{figure}[H]

\centering

\includegraphics[width=\textwidth,height=0.45\textheight,keepaspectratio]{图表/技术路线图.pdf}

\caption{整体技术路线图}\label{fig:roadmap}

\end{figure}

```

**⛔⛔⛔ TikZ 图务必也写进 图表引用.tex（最常被漏！）：**

TikZ 编译产出 `图表/结构示意图.pdf`（若分多个 .tex 则是 `图表/tikz_*.pdf`，可能多页）。

**每一个 TikZ PDF 都务必像 DrawIO 一样，在 图表引用.tex 里有一个 `\includegraphics` 图块**，

反之写作环节读 图表引用.tex 时看不到 TikZ 图，论文里就会缺图。

```latex

% === TikZ 几何/算法/架构图 ===

\begin{figure}[H]

\centering

\includegraphics[width=0.85\textwidth,height=0.38\textheight,keepaspectratio]{图表/结构示意图.pdf}

\caption{弦长递推几何关系示意}\label{fig:tikz_geom}

\end{figure}

```

- 如果一个 `结构示意图.tex` 里画了多张图（多个 `\begin{tikzpicture}`），编译出的 PDF 是多页。

  务必先用 `pdfseparate 图表/结构示意图.pdf 图表/结构示意图_%d.pdf` 拆成单页，

  或在 .tex 里每张图独立 `\newpage`，随后为**每一页/每一张** TikZ 图各写一个 `\includegraphics` 块，

  caption 与规划清单里的 TikZ 条目一一相应。

- ⛔ caption 务必与论文语言保持一致（中文论文用中文 caption）。

```latex

% === 速度传递算法流程图 ===

\begin{figure}[H]

\centering

\includegraphics[width=0.85\textwidth,height=0.38\textheight,keepaspectratio]{图表/结构示意图_2.pdf}

\caption{速度传递与刚体杆约束求解流程}\label{fig:tikz_algo}

\end{figure}

```

**⛔ 追加后自检：**

```bash

echo "=== 图表引用.tex 追加验证 ==="

# 1. 检查每个 DrawIO PDF 是否都有对应的 \includegraphics

for pdf in 图表/技术路线图.pdf 图表/fig_flow_*.pdf 图表/fig_pipeline*.pdf 图表/fig_framework*.pdf 图表/fig_index_*.pdf 图表/fig_network*.pdf; do

    [ -f "$pdf" ] || continue

    bn=$(basename "$pdf")

    if grep -q "$bn" 图表/图表引用.tex 2>/dev/null; then

        echo "✅ $bn has include entry"

    else

        echo "❌ $bn MISSING from 图表引用.tex — must append"

    fi

done

# 1b. ⛔ 检查每个 TikZ PDF（含多页拆分）是否都有 \includegraphics —— 最常被漏

for tpdf in 图表/结构示意图.pdf 图表/结构示意图_*.pdf 图表/tikz_*.pdf; do

    [ -f "$tpdf" ] || continue

    tbn=$(basename "$tpdf")

    if grep -q "$tbn" 图表/图表引用.tex 2>/dev/null; then

        echo "✅ TikZ $tbn has include entry"

    else

        echo "❌ TikZ $tbn MISSING from 图表引用.tex — must append a figure block for it"

    fi

done

# 2. 检查 label 是否有重复

DUPS=$(grep -oh '\\label{[^}]*}' 图表/图表引用.tex 2>/dev/null | sort | uniq -d)

[ -z "$DUPS" ] && echo "✅ No duplicate labels" || echo "❌ Duplicate labels: $DUPS"

```

**若有 ❌，立即修复（追加缺失的 include 或修复重复 label）。TikZ 的 ❌ 尤其不可放过。**

### 工作节点 9：Concluding quality gate

```bash

echo "=========================================="

echo "  DRAWIO/TIKZ QUALITY GATE"

echo "=========================================="

GATE_FAIL=0

# DrawIO diagrams

DRAWIO_COUNT=$(ls 图表/*.drawio 2>/dev/null | wc -l)

DRAWIO_PDF=0

for df in 图表/*.drawio; do

    [ -f "$df" ] || continue

    bn=$(basename "$df" .drawio)

    [ -f "图表/${bn}.pdf" ] && DRAWIO_PDF=$((DRAWIO_PDF+1))

done

if [ "$DRAWIO_COUNT" -gt 0 ] && [ "$DRAWIO_PDF" -eq "$DRAWIO_COUNT" ]; then

    echo "✅ DrawIO: $DRAWIO_COUNT .drawio files, all exported to PDF"

elif [ "$DRAWIO_COUNT" -gt 0 ]; then

    echo "❌ DrawIO: $DRAWIO_COUNT .drawio but only $DRAWIO_PDF PDFs"; GATE_FAIL=$((GATE_FAIL+1))

else

    echo "❌ No DrawIO diagrams generated"; GATE_FAIL=$((GATE_FAIL+1))

fi

# TikZ (if planned)

if grep -qi 'tikz\|TikZ\|模型架构\|变量关系' 问题分析.md 2>/dev/null; then

    if ls 图表/tikz_*.tex 2>/dev/null > /dev/null || [ -f 图表/结构示意图.tex ]; then

        echo "✅ TikZ source files exist"

        # Run tikz_check.sh on each TikZ file

        for texfile in 图表/tikz_*.tex 图表/结构示意图.tex; do

            [ -f "$texfile" ] || continue

            bash 工具/tikz_check.sh "$texfile" 2>/dev/null

            TC_EXIT=$?

            if [ "$TC_EXIT" -gt 0 ]; then

                echo "❌ tikz_check.sh found $TC_EXIT CRITICAL issues in $(basename $texfile)"

                GATE_FAIL=$((GATE_FAIL+1))

            fi

        done

        # Verify compiled PDFs exist

        TIKZ_PDF=0

        for tf in 图表/tikz_*.tex 图表/结构示意图.tex; do

            [ -f "$tf" ] || continue

            bn=$(basename "$tf" .tex)

            [ -f "图表/${bn}.pdf" ] && TIKZ_PDF=$((TIKZ_PDF+1))

        done

        [ "$TIKZ_PDF" -gt 0 ] && echo "✅ TikZ compiled PDFs: $TIKZ_PDF" || { echo "❌ TikZ source exists but no compiled PDF"; GATE_FAIL=$((GATE_FAIL+1)); }

    else

        echo "❌ TikZ planned but no .tex files"; GATE_FAIL=$((GATE_FAIL+1))

    fi

fi

# 图表引用.tex updated with DrawIO/TikZ entries

if [ -s 图表/图表引用.tex ]; then

    echo "✅ 图表引用.tex exists"

    # 检查是否包含 DrawIO 图的 include

    DRAWIO_IN_INCLUDES=$(grep -c '技术路线图\|fig_flow\|fig_framework\|fig_pipeline\|fig_index\|fig_model\|fig_network\|fig_gantt\|tikz_' 图表/图表引用.tex 2>/dev/null || echo 0)

    if [ "$DRAWIO_IN_INCLUDES" -gt 0 ]; then

        echo "✅ 图表引用.tex contains $DRAWIO_IN_INCLUDES DrawIO/TikZ entries"

    else

        echo "❌ 图表引用.tex exists but has NO DrawIO/TikZ entries — paper will miss diagrams"

        GATE_FAIL=$((GATE_FAIL+1))

    fi

else

    echo "❌ 图表引用.tex missing"; GATE_FAIL=$((GATE_FAIL+1))

fi

# No tiny PDFs

for pdf in 图表/技术路线图.pdf 图表/fig_flow_*.pdf 图表/fig_pipeline*.pdf 图表/fig_framework*.pdf; do

    [ -f "$pdf" ] || continue

    sz=$(wc -c < "$pdf")

    [ "$sz" -lt 5000 ] && { echo "❌ $(basename $pdf) only $sz bytes — likely broken"; GATE_FAIL=$((GATE_FAIL+1)); }

done

echo ""

[ "$GATE_FAIL" -eq 0 ] && echo "✅ ALL PASSED" || echo "❌ $GATE_FAIL FAILURES — fix and re-run"

```

**⛔ If GATE_FAIL > 0:**

1. **逐个修复各个 ❌ 项**（重新产出 .drawio → 导出 → 自检，或重新编译 TikZ，或追加 latex_includes）

2. **重新运行本质量门脚本**

3. **重复直到 GATE_FAIL = 0**

4. **不准许带着任何 ❌ 结束当前环节。** 若某张图反复失败，启用跨工具兜底（DrawIO↔TikZ）

**⛔ 质量门全部通过后，交付终版 CHECKLIST 确认：**

```

DRAWIO PLAN CHECKLIST (FINAL):

[✅] 1. 技术路线图 — 图表/技术路线图.pdf (XX KB) — drawio_verify PASS

[✅] 2. 问题流程图_1 — 图表/问题流程图_1.pdf (XX KB) — drawio_verify PASS

[✅] 3. 问题流程图_2 — 图表/问题流程图_2.pdf (XX KB) — drawio_verify PASS

[✅] 4. fig_pipeline — 图表/fig_pipeline.pdf (XX KB)

[✅] 图表引用.tex — contains 4 DrawIO entries

ALL COMPLETE — systems-diagramming step finished successfully

```

## 核心规则

- DrawIO .drawio files export to PDF via `draw.io.exe --export --format pdf --crop`

- All fonts bold (`fontstyle=1`), line width 3pt

- All edges: `jumpStyle=arc;jumpSize=6;rounded=1`

- ⛔ Edges needs to NOT cross nodes or obscure text

- Component spacing 30-50px, grid alignment (`gridSize=10`)

- Default color scheme: academic blue `#dae8fc`/`#6c8ebf`

- Each mxCell id is expected to be globally unique

- Chinese text in UTF-8, XML special chars is expected to be escaped

- ⛔ No `shadow=1`, no XML comments, no `shape=callout`

- ⛔ All nodes is expected to include `html=1` (including edge labels)

- ⛔ No in-figure title — titles managed by LaTeX `\caption{}`

- ⛔ 3 rounds DrawIO fail → fallback to TikZ; 3 rounds TikZ fail → fallback to DrawIO

