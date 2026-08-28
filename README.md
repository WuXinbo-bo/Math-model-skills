<p align="center">
  <img src="assets/branding/logo.svg" alt="Meta-model-agent" width="200">
</p>

<h1 align="center">Meta-model-agent</h1>

<p align="center">
  面向数学建模研究与竞赛论文的可执行、可恢复、可审计工作流
</p>

<p align="center">
  <img alt="Workflow" src="https://img.shields.io/badge/Workflow-7%20Stages-0E7490">
  <img alt="Targets" src="https://img.shields.io/badge/Targets-CUMCM%20%7C%2051MCM%20%7C%20MCM%2FICM-2563A8">
  <img alt="Outputs" src="https://img.shields.io/badge/Outputs-PDF%20%7C%20DOCX-6D4CC3">
  <img alt="Platform" src="https://img.shields.io/badge/Primary-Codex-111827">
  <img alt="Version" src="https://img.shields.io/badge/Version-v1.2-16A34A">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-16A34A"></a>
</p>

Meta-model-agent 将题意分析、模型构建、真实计算、结果验证、证据可视化、论文写作和提交验收连接为一条工程化研究链。它优先作为 Codex Skill 使用，也可以由能够读取 Markdown 指令、访问工作区并执行本地命令的其他 AI 工具调用。

项目适用于 CUMCM、51MCM、MCM/ICM 及结构相近的数学建模任务。它强调结果可复现和证据一致性，不以单纯生成一篇完整论文文本为目标。

> Meta-model-agent 只提供研究辅助。题意、数据、模型、程序、引用、结果、竞赛规则与最终提交材料必须由使用者核验；项目内部评分和门禁不代表竞赛结果承诺。

## 核心能力

- 从真实题面、附件和数据建立问题底稿，并按 `supplied/collected/none` 声明数据模式；
- 有数据时执行题目驱动的数据审计、预处理、质量复核和输入冻结，无数据时明确跳过；
- 将自然语言任务转化为可计算、可验证的数学模型，严格区分模型名称、定制机制与求解算法；
- 先建立可解释基线，再通过对照、消融和稳健性分析验证改进；
- 运行逐问程序并保存结构化结果，使论文数值能够追溯到计算输出；
- 生成数据图、结果表、DrawIO/TikZ 流程图和稳定的论文引用；
- 按目标竞赛模板组织 LaTeX 或 DOCX 论文，控制摘要结构、正文密度、图表尺寸与页数；
- 从当前源码生成仅包含主程序和逐问核心实现的代码附录，并使用英文程序显示名；
- 通过阶段门禁、返工传播、断点恢复和多轮审稿控制研究质量。

## v1.2 重点升级

本版本保持原有七阶段工作流和主要交付物数量不变，重点完善论文内容与证据合同：

- **摘要表达**：中文摘要按“总述—逐问—评价”组织，逐问说明模型或继承关系、核心方法、关键结果与检验，避免内部审计字段和算法流水账进入论文；MCM/ICM Summary Sheet 使用对应英文表达。
- **数学模型名称**：新增审计身份与论文表达分层，要求正式名称体现题目机制和标准模型族，禁止用求解器、算法或“优化模型”等泛化名称冒充数学模型；比较、验证和应用类问题允许继承已有模型。
- **条件数据预处理**：数据准备作为七阶段内的条件子流程执行。处理方法由题目字段、数据质量、时间或空间结构及模型需求决定，处理后输入通过哈希固化并与模型代码读取路径一致。
- **论文排版与正文密度**：分别验收页数合规和内容充分性，限制 LaTeX/DOCX 图表嵌入尺寸，保护模型机制、公式推导、结果验证、解释和局限性，避免以堆图、放大字号或空泛文字补页。
- **核心代码附录**：三种赛制均从当前源码确定性生成附录，只展开主程序和逐问核心实现；数据处理、绘图、校验与公共工具进入支撑材料清单，不再全文铺入论文。

对应规则已进入 [`SKILL.md`](SKILL.md)、[门禁矩阵](references/gate-matrix.md)、分阶段协议、论文模板与自动化回归检查，不依赖 README 文本单独生效。

## 工作流

正式工作流由 [机器清单](assets/workflow_manifest.json) 定义，当前包含 7 个阶段：

| 阶段 | 目标 |
| --- | --- |
| `DISCOVERY` | 读取题面、附件与数据，拆解问题并声明数据模式 |
| `FORMULATION` | 建立数学机制、模型身份、预处理合同与验证方案 |
| `COMPUTATION` | 按需预处理数据，编写程序并开展真实计算 |
| `EVIDENCE` | 将结果转化为论文图表与数据证据 |
| `SCHEMATICS` | 绘制技术路线和系统逻辑图 |
| `MANUSCRIPT` | 集成模型、实验、图表、引用与核心代码附录 |
| `ASSURANCE` | 编译并检查内容、版式、身份与最终材料 |

详细的阶段依赖、核验点和产物映射见 [工作流总图](references/workflow-map.md) 与 [门禁矩阵](references/gate-matrix.md)。

## 阶段与质量模式

项目将研究阶段和质量模式作为两个独立维度：

| 维度 | 可选值 | 说明 |
| --- | --- | --- |
| 研究阶段 `phase` | `baseline`、`enhancement` | 默认先完成稳定基线，再对薄弱环节实施受控增强 |
| 质量模式 `mode` | `standard`、`championship` | 默认使用标准模式；冠军模式在论文完成后增加多轮独立审稿 |

切换命令：

```bash
python scripts/pipeline_manager.py set-phase enhancement --workspace ../contest-workspace
python scripts/pipeline_manager.py set-mode championship --workspace ../contest-workspace
```

`enhancement` 不能绕过基线证据。`championship` 至少执行三轮审稿，并应用项目内部的 P0/P1 和综合评分门槛。详细规则见 [阶段控制](references/phase-control.md)、[增强操作](references/enhancement-operations.md) 和 [冠军审稿方法](references/championship-review-method.md)。

## 运行要求

- Python 3.8 或更高版本，建议使用 Python 3.10 或 3.11；
- PDF 路线需要 Bash、XeLaTeX、BibTeX 和相应 TeX 宏包；
- DOCX 页数门禁需要 LibreOffice；DrawIO 和 PDF 视觉核验需要对应系统工具；
- 完整的分平台安装、可选建模依赖和自检命令见 [环境配置说明](ENVIRONMENT.md)。

安装 Python 依赖：

```bash
python -m pip install -r scripts/requirements.txt
```

## 快速开始

### 方式一：在 Codex 中配置并直接使用（推荐）

先向 Codex 发送下面的提示词，将项目配置为全局 Skill：

```text
将 https://github.com/WuXinbo-bo/Math-model-skills 这个 Skill 直接配置到 Codex 全局 Skill 中。
```

配置完成后，上传赛题、附件和数据，再发送：

```text
开始处理我上传的数学建模赛题。
竞赛类型：CUMCM
模式：冠军模式
论文撰写方式：LaTeX
```

可以按实际任务将竞赛类型改为 `CUMCM`、`51MCM` 或 `MCM/ICM`，将模式改为标准模式或冠军模式，将论文撰写方式改为 `LaTeX` 或 `DOCX`。根目录的 [`SKILL.md`](SKILL.md) 是 Skill 执行入口；运行时应按当前阶段渐进加载协议，而不是一次读取全部参考文件。

### 方式二：使用命令行运行

以下命令均从本仓库根目录执行，`../contest-workspace` 表示独立的目标研究工作区。不要把仓库根目录和研究工作区视为同一目录。

#### 1. 初始化工作区

```bash
python scripts/workspace_init.py --workspace ../contest-workspace --competition cumcm --output-format pdf
```

`--competition` 支持 `cumcm`、`51mcm` 和 `mcm-icm`；`--output-format` 支持 `pdf` 和 `docx`。竞赛类型会控制模板、语言、匿名字段、字号和页数门禁。

#### 2. 查看状态

```bash
python scripts/pipeline_manager.py overview --workspace ../contest-workspace
python scripts/stage_executor.py current --workspace ../contest-workspace
```

#### 3. 开始当前阶段

```bash
python scripts/stage_executor.py begin DISCOVERY --workspace ../contest-workspace
```

阶段开始后，系统会把当前阶段需要的工具、参考资料和模板同步到目标工作区。完成实际研究工作后，按顺序执行：

```bash
python scripts/stage_executor.py validate DISCOVERY --workspace ../contest-workspace
python scripts/stage_executor.py gate_check DISCOVERY --workspace ../contest-workspace
python scripts/stage_executor.py complete DISCOVERY --workspace ../contest-workspace --artifacts "问题分析.md"
python scripts/stage_executor.py checkpoint DISCOVERY --workspace ../contest-workspace --action approve --note "reviewed"
```

使用以下命令获取下一步建议：

```bash
python scripts/pipeline_manager.py next --workspace ../contest-workspace
```

#### DOCX 路线

初始化时选择 `--output-format docx`。论文源稿完成后，使用初始化过程中复制到目标工作区的导出工具：

```bash
python "../contest-workspace/工具/docx_export.py" --workspace ../contest-workspace
```

## 文档导航

| 主题 | 文档 |
| --- | --- |
| 环境安装与依赖自检 | [ENVIRONMENT.md](ENVIRONMENT.md) |
| 总流程与阶段映射 | [workflow-map.md](references/workflow-map.md) |
| 阶段门禁与人工核验 | [gate-matrix.md](references/gate-matrix.md) |
| Baseline 与 Enhancement | [phase-control.md](references/phase-control.md) |
| 增强模式操作 | [enhancement-operations.md](references/enhancement-operations.md) |
| 冠军模式审稿与评分 | [championship-review-method.md](references/championship-review-method.md) |
| 主控、工作与复核角色 | [subagent-architecture.md](references/subagent-architecture.md) |
| CUMCM 官方规则摘录 | [cumcm-official-notes.md](references/cumcm-official-notes.md) |
| 竞赛机器配置 | [competition_profiles.json](assets/competition_profiles.json) |
| 分阶段实施协议 | [`references/stage_protocols/`](references/stage_protocols/) |

目标竞赛的当期正式规则始终高于仓库中的模板、摘录和机器门禁。

## 项目结构

```text
Meta-model-agent/
├── SKILL.md                  # Skill 入口与总执行规则
├── ENVIRONMENT.md            # 环境安装、依赖分层与自检
├── agents/                   # Skill 界面配置
├── assets/                   # 工作流清单、竞赛配置、模板和共享工具
├── references/               # 工作流指南、知识库和阶段协议
└── scripts/                  # 初始化、状态机、门禁、审稿和回归脚本
```

初始化后的研究工作区通常包含：

```text
用户数据/  程序/  图表/  论文/  审查/
状态/      日志/  工具/  参考资料/  模板/
```

## 质量边界

- 自动门禁只能检查已编码的合同，不能证明题意、模型、数据或结论一定正确；
- 外部资料、参考文献、数据集和竞赛规则必须回到原始来源核验；
- 使用者应重新运行程序，检查随机种子、参数、输入、关键数值和图表一致性；
- `championship` 是内部质量模式名称，不代表获奖、录用或任何第三方评价；
- 最终提交前必须完成人工通读、匿名检查、格式检查和提交确认。

出现中断或上游错误时，先运行 `stage_executor.py status` 和 `pipeline_manager.py next`；需要返工时从对应阶段执行 `rework`，不要只修改最终论文掩盖模型或数据问题。

## 许可与致谢

本项目采用 [MIT License](LICENSE)，允许在保留版权和许可声明的前提下使用、复制、修改、合并、发布、分发、再许可和销售软件副本。

工作流设计参考了 [xuec699-sudo/math-modeling-skills](https://github.com/xuec699-sudo/math-modeling-skills)，并从 **Modex-MH-Agent** 的工作流组织方式中获得部分灵感。本项目为独立设计与实现，与上述项目不存在官方隶属或质量背书关系。

## 赞助支持

<table>
  <tr>
    <td align="center" width="28%">
      <a href="https://88.scxai.top/">
        <img src="assets/branding/sponsor-chuangshi-xinyuan.jpg" alt="创世の鑫元" width="150">
      </a><br>
      <strong>创世の鑫元</strong><br>
      <a href="https://88.scxai.top/">访问官方网站</a>
    </td>
    <td>
      感谢 <strong>创世の鑫元</strong> 对本项目的赞助与支持。其网站提供 AI 相关服务与工具信息；具体服务内容、价格、可用性及使用条款请以官方网站的最新说明为准。
    </td>
  </tr>
</table>
