---
name: meta-model-agent
description: Meta-model-agent 致力于辅助研究者与参赛团队完成高质量数学建模研究和论文产出，提供从问题理解、模型构建、计算实验、证据可视化到论文写作、冠军级多轮审稿与提交验收的完整工程支持。适用于 CUMCM、51MCM、MCM/ICM 及同类数模研究任务，可用于启动或恢复项目、按证据门禁推进、修复薄弱环节并形成可复现、可验证、可提交的高质量数模论文。
---

# Meta-model-agent

Meta-model-agent 是面向数学建模研究与竞赛论文生产的工程化辅助系统。它将题意研判、数学建模、程序求解、结果验证、图形表达、论文组织和提交检查连接为一条可执行、可恢复、可审计的研究链，帮助使用者把零散的分析过程转化为证据完整、逻辑一致且能够复现的高质量数模论文。

## 项目说明

本项目的核心目标不是简单生成一篇论文文本，而是辅助完成从研究问题到最终论文的完整质量闭环：先建立可信的问题与模型契约，再通过真实计算获得结果，以图形、表格和结构图组织证据，最后形成符合竞赛规范的论文并接受多轮质量审稿。

项目优先适配 Codex，并兼容能够读取 Skill、访问工作区和运行本地命令的其他 AI 工具。Meta-model-agent 仅提供数学建模辅助；实际使用者必须核验题意、数据、模型、程序、引用、结果与最终论文，并自行承担采用或提交相关产出的风险。

项目按照研究依赖组织工作，并提供三层质量能力：

- `baseline`：保持阶段、交付物和门禁稳定，保证完整流程能够可靠运行；
- `enhancement`：针对模型、程序、证据链或论文薄弱项实施受控返工；
- `championship`：在最终验收前执行多轮独立模拟审稿和全文修订，以更高标准检验数学正确性、可复现性、逻辑一致性、表达质量与提交合规性。

Meta-model-agent 强调研究证据优先。论文中的公式、数值、图表和结论应能追溯到题面、模型、程序或结果文件；若上游证据存在根本问题，系统应回退相应阶段修复，而不是仅通过文字润色掩盖缺陷。

### 论文版面与正文密度硬约束

- 图表文件的原始画布尺寸不是论文嵌入尺寸。LaTeX 普通图默认使用 `width=0.72\linewidth,height=0.70\textheight,keepaspectratio`，再按可读性调整；宽表或宽图最高不得超过 `\linewidth`，禁止依赖 PDF 查看器裁切超出版心的内容。
- DOCX 中按页面可用宽度缩放图表：A4 常规页边距下正文图推荐宽 13.5--15.0 cm，绝不超过实际版心宽；必须锁定纵横比，禁止把像素尺寸或厘米尺寸原样放大到页面之外。
- 图表过大或导致页数超限时，优先裁除空白边缘、合并相关子图、精简重复图、缩短图注、将次要图表移至附录；不得通过把整张图缩到文字不可读来“塞进页面”。图中文字在最终 PDF/DOCX 的 100% 显示比例下必须可读。
- `MAX_PAGES` 是上限，不是正文字数目标。页数紧张时必须优先保护问题分析、模型机制、公式推导、求解过程、验证、结果解释和局限性，不能为了满足页数而删成只有结论和图表的空心论文。
- 页数合规与正文充分性必须分别验收。即使 PDF 未超页，若任一子问题缺少“机制/推导 -> 结果 -> 验证 -> 解释”，或正文有效字数明显不足，仍不得通过 MANUSCRIPT/ASSURANCE 门禁；禁止用放大字号、拉大行距、堆图或空泛文字补页。
- CUMCM 按 2026 官方规范执行：摘要原则上不超过 1 页，正文不要目录且不超过 30 页，附录单独计数且页数不限。必须通过编译后的 `AbstractStart/AbstractEnd` 与 `BodyStart/BodyEnd` 标签实测，禁止用字符估算代替最终门禁。
- 普通 LaTeX 图表使用 `[htbp]` 并在章节边界用 `\FloatBarrier` 收束，禁止全篇强制 `[H]` 造成空白页和页数膨胀。

### 图表与流程图克制表达硬约束

- 每张正文图必须登记明确论点、数据来源和读者任务；使用 `图表/figure_manifest.json` 区分正文图、附录图和诊断图，只有 `publish=true` 的图必须嵌入正文。
- 图形类别按数据结构和读者任务选择，禁止为了“高级感”或多样性强制使用渐变、阴影、圆角标注框、KDE 背景和无必要多层叠加。
- 所有 DrawIO/TikZ 流程图中的普通矩形、矩形容器和表头必须使用直角矩形；菱形、圆形、六边形、圆柱、平行四边形等其他语义形状保持不变。
- AI Image 默认关闭，禁止用于技术路线图、流程图和模型架构图；仅在用户明确需要且经过内容级核验的物理场景示意中使用。

### 代码附录硬约束

- COMPUTATION 必须生成 `程序/code_manifest.json`，登记入口、逐问程序、依赖、代码行数和源码哈希。
- MANUSCRIPT 必须运行 `工具/build_code_appendix.py`，从当前源码自动生成附录；禁止用一段复现说明或“代码见支撑材料”替代真实核心实现。
- CUMCM 附录必须完整列出全部可运行源程序及支撑材料文件；其他赛制按竞赛 Profile 嵌入主程序和逐问核心实现。源码哈希、附录标记和运行入口不一致时不得通过门禁。

## 快速启动

1. 在目标工作目录初始化运行时工作区：

```bash
python scripts/workspace_init.py --workspace . --competition cumcm --output-format pdf
```

`--competition` 支持 `cumcm`、`51mcm`、`mcm-icm`。竞赛类型会写入状态并控制模板与硬门禁；如需更换竞赛，应重新初始化工作区并重新执行论文及验收阶段。

`--output-format` 支持 `pdf`（默认）和 `docx`。DOCX 路线以 `论文/论文正文.md` 为写作源，使用 `python 工具/docx_export.py --workspace .` 生成 `论文/数模论文.docx` 与图片尺寸报告。

2. 查阅 [references/workflow-map.md](references/workflow-map.md)。

3. 查询当前阶段：

```bash
python scripts/stage_executor.py current --workspace .
```

4. 启动当前阶段，自动化同步该阶段所需的 `工具` / `参考资料` / `模板`：

```bash
python scripts/stage_executor.py begin DISCOVERY --workspace .
```

5. 仅加载当前阶段的实施协议：

- `references/stage_protocols/<skill-name>/SKILL.md`
- 如该阶段有额外 `references/` 或 `templates/`，只加载当前阶段需的文件。

6. 阶段实施完毕后，严格按下面次序收口：

```bash
python scripts/stage_executor.py validate DISCOVERY --workspace .
python scripts/stage_executor.py gate_check DISCOVERY --workspace .
python scripts/stage_executor.py complete DISCOVERY --workspace . --artifacts "问题分析.md"
```

7. 若该阶段有核验点，继续处理核验点：

```bash
python scripts/stage_executor.py checkpoint DISCOVERY --workspace . --action approve --note "checkpoint passed"
```

## 实施准则

### 冠军质量模式

需冲击最高质量时，先设定冠军模式：

```bash
python scripts/pipeline_manager.py set-mode championship --workspace .
```

冠军模式保持问题分析、模型构建、计算实验、证据整理、论文写作与提交验收之间的依赖关系不变，并在论文写作完成后强制加入多轮模拟审稿。载入 `references/stage_protocols/championship-review/SKILL.md` 和 `references/championship-review-method.md`，依次开展独立审稿、修订规划、全文重写与逐项复核。完成不少于三轮，且终版满足 P0 为 0、P1 不超过 2、综合分不低于 85 后，方可转入提交质量验收。

### 1. 严守 `baseline` 基线

- 默认运行模式为 `baseline`。
- 基线运行严禁打乱上游与下游依赖、缩减交付物目录、改变核验点类别、降低最低文件规模或取消伴随文件条件。
- 只有完整基线证据通过后，才能启动增强处理。

### 1.1 严格执行竞赛 Profile

- 初始化时将竞赛类型、语言、模板、允许/禁止身份字段、字号和页数限制写入状态。
- `MANUSCRIPT` 只能同步当前竞赛模板，不得混用其他竞赛封面或文档类。
- MCM/ICM 强制英文、至少 12pt、Summary Sheet、Control Number 且完整 PDF 不超过 25 页。
- 51MCM 强制 `51mcmthesis` 电子提交模式，并移除学校、成员、邮箱和电话字段。
- CUMCM 使用 `cumcmthesis`，提交前按当届官方通知复核匿名、编号页、页数与附件。
- 规则变化时先更新机器 Profile 和对应竞赛规则文档，再运行工作流。
- 论文章节目录允许项目统一采用 `章节/` 或模板原生采用 `sections/`；主文件引用路径必须与磁盘目录一致。
- 门禁会读取实际竞赛 `.cls`，检查纸张、页边距、基础字号、页眉或摘要页等关键合同，不能仅靠文档类名称通过。

### 2. 按阶段渐进加载

- 严禁一次载入全部研究协议。
- 先用 `stage_executor.py current` 确认活动阶段，再查阅相应实施协议。
- 对当前阶段之外的资料，只有在当前协议明确引用时才可加载。

### 3. 落实主控与工作角色分层

- 主控角色负责阶段编排、运行状态落盘、门禁收束、核验点推进和跨阶段一致性维护。
- 工作角色承担当前阶段内的原子工作项，例如题意拆解、方案质询、程序实现、图形与表格制作以及论文组装。
- 若运行环境不支撑并行工作角色，可按角色次序实施；交付路线、复核独立性和阶段边界仍须保持不变。

### 4. 保持门禁契约稳定

- 全部阶段都务必核验原产物合同。
- `computational-realization` 务必同时核验 `程序/主程序.py`、`计算结果.md` 和伴随结果文件。
- `evidence-visualization` / `systems-diagramming` 共用 `图表/图表引用.tex`，避免误删前一步产物。
- `manuscript-synthesis` 此后再转入 `delivery-assurance`，不可跳。

### 5. 依据证据恢复运行

- 续跑前先看：
  - `状态/工作流状态.json`
  - `状态/事件日志.jsonl`
  - `python scripts/stage_executor.py status --workspace .`
- 若某阶段被标记完成，但产物缺失或尺寸不达标，应重新 `begin` 并补做，而不是盲目向前推进。

## 项目组成

- `assets/workflow_manifest.json`: 研究工作流机器可读清单
- `assets/competition_profiles.json`: 三类竞赛的机器可读模板与合规硬约束
- `references/workflow-map.md`: 人类可读的过程总图和阶段映射
- `references/gate-matrix.md`: 各个阶段的机器门禁与人工复核要点
- `references/phase-control.md`: `baseline -> enhancement` 模式切换准则
- `references/subagent-architecture.md`: 主控、工作与复核角色的闭环契约
- `references/enhancement-operations.md`: 增强模式的返工与质量提升方法
- `references/cumcm-official-notes.md`: 国赛官网准则与时间节点摘录
- `references/guide-*.md`: 各项研究工作的主控与执行角色指南
- `references/stage_protocols/`: 研究工作协议及配套参考资料与模板
- `references/runtime_reference/`: `workflow_engine.py` 与 `agent_runner.py` 的运行参考实现
- `scripts/workspace_init.py`: 初始化运行时工作区
- `scripts/stage_executor.py`: 运行状态机、门禁、核验点、断点续跑入口
- `scripts/gate_contracts.py`: 研究工作流的机器门禁引擎
- `scripts/pipeline_manager.py`: 总入口、下一步提示、阶段切换
- `scripts/baseline_smoke.py`: 完整研究工作流基线冒烟校验
- `scripts/stateful_smoke.py`: 核验 checkpoint rerun、rework 传播、resume 行为
- `scripts/enhancement_audit.py`: enhancement 阶段的返工与增强推荐入口
- `scripts/championship_review.py`: 冠军模式多轮审稿、修订和终版论文回写入口
- `scripts/build_code_appendix.py`: 生成源码哈希清单，并从当前程序确定性构建 LaTeX/DOCX 代码附录
- `references/championship-review-method.md`: 冠军审稿评分、攻击策略与回退知识库
- `scripts/state_store.py`: JSON 运行状态存储
- `assets/shared-scripts/`: 原共享脚本
- `assets/templates/`: 原论文模板

## 最终交付说明

完成全部必要阶段后，项目应形成一套能够相互印证的研究成果，包括问题分析、模型报告、可运行程序、结构化结果、论文图形、完整 LaTeX 源稿和最终 PDF。冠军模式启用时，还应保留逐轮审稿报告、修订计划、修改后论文和修复验证记录。

最终论文必须满足以下原则：研究过程可解释，关键结果可复现，论文结论有证据支撑，图表与正文保持一致，格式符合目标竞赛要求，并且不存在已知的 P0 级质量问题。

