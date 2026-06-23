<p align="center">
  <img src="assets/icon-large.svg" alt="Meta-model-skills-max" width="120"/>
</p>

<h1 align="center">Meta-model-skills-max</h1>

<p align="center">
  <strong>v4.0.0</strong> · 数学建模竞赛智能体工程群
</p>

<p align="center">
  <img alt="Agents" src="https://img.shields.io/badge/Agents-7%20functional%20roles-8B5CF6">
  <img alt="Stages" src="https://img.shields.io/badge/Stages-14%20stages-059669">
  <img alt="Gates" src="https://img.shields.io/badge/Gates-32%20quality%20gates-DC2626">
  <img alt="Meetings" src="https://img.shields.io/badge/Meetings-4%20protocols-F59E0B">
  <img alt="Scripts" src="https://img.shields.io/badge/Scripts-56%20tools-F59E0B">
  <img alt="Version" src="https://img.shields.io/badge/version-4.0.0-blue">
  
</p>

---

> 7 个功能角色、4 场会议协议、14 阶段流水线、32 道质量门禁、56 个工具脚本——把数学建模竞赛从"个人手工作坊"升级为"可追溯、可审计、可复现的智能体工程群"。

## 为什么需要这个？

建模竞赛真正失败的地方，往往不是"不会模型"，而是**流程漂移**：
- 题没读清楚就上复杂模型
- 论文里写的数字脚本输出找不到
- bug 修复后论文数字偷偷漂移没人察觉
- 一个人身兼数职，角色混乱导致遗漏

`Meta-model-skills-max` 用**功能角色制衡**思想，把建模流程拆成 7 个专业角色、4 场正式会议、32 道门禁——每个数字可追溯、每次修改有审计、每项声明有证据、每个决策有对抗。

## 核心能力

| 能力 | 说明 |
|---|---|
| **功能角色群** | 7 个专业角色（Planner/Analyst/Proposer/Builder/Critic/Reviewer/Writer），inline role-play 切换 |
| **4 场会议协议** | 题意共识会、模型辩论会、实验复盘会、红队审稿会——结构化决策 |
| **14 阶段流水线** | S0-S10（含 S5.5/S7.5/S9.5），workflow.yaml 驱动的 DAG 依赖管理 |
| **32 道质量门禁** | G1-G9.5 全覆盖，含并行合并门禁、基线对比门禁、摘要质量门禁、出版规范门禁 |
| **并行子问题建模** | S5 阶段按 Q1/Q2/Q3 并行 spawn，独立建模后合并 |
| **12 个增强引擎** | 摘要质量、推导链、方法矩阵、逐题检验、对抗审稿、灵敏度分析、出版规范检查等 |
| **3 种深度模式** | Fast / Standard / Championship，按赛期灵活切换 |
| **Auto Mode（全自动模式）** | 3×3 模式矩阵 × 6 决策点自动裁决 + 安全熔断 + 决策日志 |
| **Friendly Mode** | 编号选项推进，用户无需理解内部流水线 |
| **竞赛适配评分** | 100 分制自动评分 + 奖项预估（CUMCM / 51MCM / MCM-ICM） |
| **三层引用体系** | 每个阶段、每个 Agent 都有明确的 reference 文件映射 |
| **公式自动渲染** | LaTeX → OMML 原生 Word 公式（可编辑，非图片） |
| **DOCX 全链路** | 生成、修订、差异对比、完整性验证一站式完成 |

## 架构全景图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户 (人机交互)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  LLM (主Agent) │  唯一交互入口
              │  工作流编排      │  任务调度 + 门禁裁决
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
  ┌──────▼──────┐      │      ┌──────▼──────┐
  │ Auto 编排器 │      │      │ Friendly    │
  │ 3×3 自动    │      │      │ 编号选项    │
  │ 决策 + 熔断 │      │      │ 交互模式    │
  └──────┬──────┘      │      └──────┬──────┘
         │             │             │
    ┌────▼──────────────┴─────────────▼────┐
    │                  │                      │
┌───▼───────┐  ┌───────▼──────────┐  ┌────────▼────────┐
│ 功能角色  │  │   核心能力组     │  │    增强引擎     │
│           │  │                  │  │                 │
│ Planner   │  │ Analyst Builder  │  │ 摘要质量引擎    │
│ Proposer  │  │ Critic  Writer   │  │ 推导链检查器    │
│ Reviewer  │  │ Inspector        │  │ 对抗审稿系统    │
│           │  │                  │  │ 灵敏度分析器    │
└───────────┘  └──────────────────┘  │ ... 共 12 个    │
                                     └─────────────────┘
```

### 设计原则

1. **Main agent = sole LLM**: 所有推理由 LLM 自身完成，按角色视角切换（功能角色群）
2. **Python scripts = pure tooling**: 56 个脚本仅做文件 I/O、DOCX、图表、状态追踪
3. **Gate checks = main agent judgment**: 基于实际文件内容评估门禁
4. **SKILL.md = 操作手册**: 每阶段显式命令，LLM 按指令执行

## 功能角色群

| Agent | 角色 | 职责 |
|-------|------|------|
| **planner** | 规划组 | 赛题解析、建模路线规划、文献深搜、符号表 |
| **analyst** | 分析组 | 数据治理、缺失值分析、数据字典 |
| **proposer** | 提案组 | 候选模型生成（精度+稳健性视角）、公式推导、基线对比 |
| **builder** | 构建组 | Python 代码实现、实验执行、图表生成 |
| **critic** | 审查组 | 红队攻击、对抗审稿、错误搜索 |
| **reviewer** | 评审组 | 可行性审查、逻辑漏洞检测、驳回权 |
| **writer** | 写作组 | 论文撰写、格式排版、DOCX 生成 |
| **inspector** | 审查官 | 质量打分、问题识别、改进建议 |

所有角色由同一 LLM 通过 `stages/S{N}.md` 中的内联提示词切换，无独立 subagent。

### 角色调度策略

所有角色由同一 LLM 通过 `stages/S{N}.md` 中的内联提示词切换视角，不 spawn 独立进程。

**角色切换时机**:
- M001 题意共识会: planner → analyst → reviewer
- M002 模型辩论会: proposer(精度) → proposer(稳健) → critic → reviewer
- S5 建模求解: proposer(建模) → builder(编码) 交替
- M004 红队审稿: critic → reviewer → writer

**不切换**（主 LLM 直接处理）:
- 最终决策、同文件编辑、状态更新

## 四次会议协议

| 会议 | 类型 | 阶段 | 参与者 | 产出 |
|------|------|------|--------|------|
| **M001 题意共识会** | consensus | S1 | planner + analyst + reviewer | 共识文档 + 风险登记 |
| **M002 模型辩论会** | debate | S3 | proposer + critic + reviewer | 模型选择报告 |
| **M003 实验复盘会** | review | S8 | builder + proposer + critic | 复盘结论（嵌入论文） |
| **M004 红队审稿会** | adversarial | S9 | critic + reviewer + writer | 审稿报告 + 修订计划 |

## 14 阶段流水线 + 24 门禁

```
S0 输入登记 ──→ S1 题意解析(M001) ──→ S2 数据治理 ──→ S3 模型选择(M002)
     │               │ G1                  │ G1.5            │ G2, G1.5, G3假设
     │               ▼                     ▼                 ▼
     │          S4 实验赛马 ──→ S5 并行建模求解 ──→ S5.5 模型进化
     │               │ G2.5         │ G3×4              │ G3.5
     │               ▼              ▼                    ▼
     │          S6 检验与灵敏度 ──→ S7 证据链 ──→ S8 论文撰写(M003)
     │               │ G4, 逐题验证    │ G4.5         │ G5×5
     │               ▼                ▼               ▼
     │          S9 对抗审稿(M004) ──→ S10 最终构建
     │               │ G5.5, 摘要一致    │ G6×3
     │               ▼                   ▼
     └──────── 交付 DOCX + PDF ────────┘
```

## 12 个增强引擎

| # | 引擎 | 脚本 | 作用 |
|---|------|------|------|
| 1 | 摘要质量引擎 | `abstract_quality_gate.py` | 4 要素检查：模型名+量化结果+公式+标注 |
| 2 | 推导链检查器 | `derivation_chain_checker.py` | 第一性原理推导链完整性 |
| 3 | 方法选择矩阵 | `method_selection_matrix.py` | 候选方法对比 + 选择理由 |
| 4 | 逐题嵌入式检验 | `per_subquestion_verification.py` | 灵敏度+鲁棒性+误差分析 |
| 5 | 多维度讨论 | `discussion_enhancer.py` | 7 维度结果讨论框架 |
| 6 | 摘要-正文一致性 | `abstract_body_consistency.py` | 数字交叉验证 |
| 7 | 图表叙事引擎 | `figure_narrative_gate.py` | D-A-C 叙事 + 数据墨水比 |
| 8 | 学术表达增强 | `academic_expression_checker.py` | 反 AI 填充 + 口语化检测 |
| 9 | 对抗审稿系统 | `adversarial_review.py` | 三视角红队审稿 |
| 10 | 假设工程系统 | `assumption_engineer.py` | 4 类假设分类 + 质量评分 |
| 11 | 跨子问题一致性 | `cross_subquestion_consistency.py` | 变量/单位/假设一致性 |
| 12 | 竞赛适配器 | `competition_adapter.py` | CUMCM/51MCM/MCM-ICM 动态适配 |

## 支持的竞赛

| 竞赛 | 语言 | 论文格式 | 评分标准 |
|---|---|---|---|
| **CUMCM** 全国大学生数学建模竞赛（国赛） | 中文 | 三线表、宋体+黑体、A4 | 100 分制（一等奖 ≥85） |
| **51MCM** 五一数学建模竞赛 | 中文 | 三线表、宋体+黑体、A4 | 100 分制（一等奖 ≥82） |
| **MCM/ICM** 美国大学生数学建模竞赛（美赛） | 英文 | 标准学术格式 | 100 分制（一等奖 ≥82） |

## 快速开始

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd Meta-model-skills-max

# 安装依赖
pip install -r requirements.txt
```

### 环境依赖

```bash
pip install -r requirements.txt
```

核心依赖：`python-docx`, `lxml`, `latex2mathml`, `mathml2omml`, `pandas`, `numpy`, `matplotlib`, `pyyaml`, `scipy`

### 初始化

```bash
# 初始化项目（从 workflow.yaml 加载阶段定义）
python main.py init --contest CUMCM --problems 3 --mode AP

# 查看 pipeline 状态
python main.py status

# 查看 workflow.yaml 解析结果
python main.py workflow

# 列出所有门禁合约
python main.py gates
```

### 使用

在 AI 助手中说：
- "求解这道题" / "solve this" — 全流程跑
- "只做问题1" — 分段执行
- "生成论文" / "write paper" — 走 `build_docx.py`
- "修改论文" / "revise paper" — 原地编辑 DOCX
- "审阅论文" — 对抗审稿 + QA 清单

## 不知道怎么调用？直接复制这些提示词

安装完成后，在 AI 助手里明确提到 `Meta-model-skills-max`，或直接描述"数学建模竞赛 / 国赛 / 美赛 / 五一赛"，AI 助手就会读取 SKILL.md 并按流程工作。

### 最推荐的首次启动提示词

```text
请使用 Meta-model-skills-max skill 处理我上传的数学建模赛题。
竞赛类型：国赛/CUMCM
执行模式：标准模式（完整 14 阶段 + 全部门禁）
子问题数量：3

请先完成：读题、问题拆解、数据检查、建模路线选择，并告诉我下一步该做什么。
```

### 快速启动速查表

| 场景 | 中文模板 | English Template |
|------|---------|-----------------|
| 新赛题（标准） | `请使用 Meta-model-skills-max skill 处理我上传的赛题，标准模式，完整流水线。` | `Use Meta-model-skills-max skill to solve my contest problem in standard mode.` |
| 新赛题（快速） | `请使用 Meta-model-skills-max skill 处理赛题，快速模式。` | `Use Meta-model-skills-max skill in fast mode.` |
| 新赛题（冠军） | `请使用 Meta-model-skills-max skill 处理赛题，冠军模式。` | `Use Meta-model-skills-max skill in championship mode.` |
| 修订论文 | `请使用 Meta-model-skills-max skill 修订我的论文。` | `Use Meta-model-skills-max skill to revise my paper.` |
| 审计论文 | `请使用 Meta-model-skills-max skill 审计我的论文。` | `Use Meta-model-skills-max skill to audit my paper.` |
| 继续工作 | `请继续我之前的建模工作，工作目录是 [路径]。` | `Continue my modeling work from [workspace path].` |
| 新赛题（标准-全自动） | `请使用 Meta-model-skills-max skill 处理赛题，标准模式，全自动执行。` | `Use Meta-model-skills-max skill in standard-auto mode.` |
| 新赛题（快速-全自动） | `请使用 Meta-model-skills-max skill 处理赛题，快速模式，全自动。` | `Use Meta-model-skills-max skill in fast-auto mode.` |
| 新赛题（冠军-全自动） | `请使用 Meta-model-skills-max skill 处理赛题，冠军模式，全自动。` | `Use Meta-model-skills-max skill in championship-auto mode.` |

完整 11 种场景模板见 `templates/startup_prompts.md`。

## 项目结构

```
Meta-model-skills-max/
├── SKILL.md                       # Skill 入口（执行规则 + 路由表）
├── AGENTS.md                      # 多角色策略文档
├── main.py                        # 统一 CLI 入口
├── requirements.txt               # Python 依赖
│
├── config/                        # 配置层
│   ├── workflow.yaml              # 14 阶段 DAG + 24 门禁定义
│   ├── agents.yaml                # 9 角色定义
│   ├── meeting_templates.yaml     # 4 场会议模板
│   ├── rubric.yaml                # 评分标准
│   └── prompts/                   # 保留（已迁移到 stages/）
│
├── scripts/                       # 执行层（45 个纯工具脚本）
│   ├── stage_executor.py          # 单阶段执行引导器
│   ├── pipeline_manager.py        # 流水线状态机
│   ├── build_docx.py              # DOCX 生成器（LaTeX→OMML）
│   ├── formula_renderer.py        # 公式渲染引擎
│   ├── gate_contracts.py          # 门控契约（24 个）
│   ├── metric_guardian.py         # 指标守门
│   ├── experiment_race.py         # 实验赛马
│   ├── evidence_tracer.py         # 证据链追踪
│   ├── math_sandbox.py            # 数学沙箱
│   └── ... (36 more)
│
├── stages/                        # 14 个阶段指令文件
│   ├── S0.md ~ S10.md
│   ├── S5.5.md
│   └── S7.5.md
│
├── references/                    # 参考文档（450KB 知识资产）
│   ├── algorithm-library/         # 7 类算法库
│   ├── modeling-paper-archives/   # 优秀论文范例
│   ├── problem-triage.md          # 题目分类
│   └── ... (27 more)
│
├── templates/                     # 模板层
│   └── startup_prompts.md         # 11 种一键启动模板
│
├── tests/                         # 测试
│   └── test_e2e.py                # 端到端测试
│
├── assets/                        # 图标
├── docs/                          # 设计文档
├── CUMCM_Workspace/               # 竞赛工作空间（运行时生成）
└── outputs/                       # 产出层（运行时生成，Git 忽略）
```

## 脚本参考表

| 需求 | 命令 |
|------|------|
| 初始化 | `python main.py init --contest CUMCM --problems 3` |
| 查看状态 | `python main.py status` |
| 查看工作流 | `python main.py workflow` |
| 列出所有门禁 | `python main.py gates` |
| 检查门禁 | `python main.py check-gate G1_problem_parsed` |
| 冻结结果 | `python main.py freeze --subquestion Q1` |
| 沙箱执行 | `python main.py sandbox --code "..."` |
| 证据链 | `python main.py evidence --subquestion Q1` |
| G6 审计 | `python main.py audit` |
| 摘要检查 | `python main.py check-abstract paper.md` |
| 推导链检查 | `python main.py check-derivation model.md` |
| 方法矩阵 | `python main.py check-matrix selection.md` |
| 讨论检查 | `python main.py check-discussion results.md` |
| 表达检查 | `python main.py check-expression paper.md` |
| 一致性检查 | `python main.py check-consistency paper.md` |
| 灵敏度分析 | `python main.py sensitivity init/sweep/check/report -q Q1` |
| 摘要一致性 | `python main.py check-abstract-consistency -a abs.md -b body.md` |
| 逐题验证 | `python main.py check-verification -q Q1` |
| 模型进化 | `python main.py model-evolve init/evolve/status -q Q1` |
| 红队审稿 | `python main.py adversarial-review generate/check-rebuttal/report` |
| 图表叙事 | `python main.py check-figure-narrative scan/check-dac/report` |
| 闭环评分 | `python main.py review-stage score/report/check` |
| DOCX 工具 | `python main.py docx analyze/map/replace/diff/verify` |
| 运行测试 | `python main.py test` |

## 设计吸收点

本项目融合了 math-modeling-skills-main (v5.9.0) 的工业级稳健性，并在此基础上进行深度扩展。

核心升级对比：

| 维度 | math-modeling-skills-main | Meta-model-skills-max |
|------|--------------------------|----------------------|
| Agent 架构 | 三角色协作（建模/编程/论文） | 9 角色三省六部（inline role-play） |
| 决策机制 | 单人决策 | 4 场会议协议 + 对抗审稿 |
| 门控数量 | 6 个主门禁 | 24 个门禁（含子门禁） |
| 阶段数 | 线性流程 | 14 阶段 DAG + 并行子问题 |
| 增强模块 | 基础检查 | 12 个专用引擎 |
| 竞赛评分 | 无 | 100 分制 + 奖项预估 |
| 环境感知 | 无 | Startup Protocol（自动扫描工作区） |

## 论文生成（关键流程）

```bash
# 1. 写 Markdown 草稿（LaTeX 公式 + [FIGURE:] 占位符）
# 2. 一键生成 DOCX
python scripts/build_docx.py paper.md output.docx
# 3. 如果实质内容不足 12000 字 → HARD FAIL → 补充后重试
```

> **严禁**使用 Pandoc 或手动 `python-docx` 绕过此流程。

## 许可证

MIT License

---

<p align="center">
  <sub>Built for CUMCM · 51MCM · MCM/ICM — 三省六部，智能体工程群</sub>
</p>
