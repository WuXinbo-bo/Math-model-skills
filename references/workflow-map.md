# Meta-model-agent 研究工作流总图

本资料定义系统级导航关系。运行时先确认当前阶段，再按需载入相应协议，避免跨阶段信息干扰。

## 1. 阶段与交付物映射

| 阶段 | 实施协议 | 工作名称 | 关键交付物 | 核验点 |
| --- | --- | --- | --- | --- |
| DISCOVERY | `problem-intelligence` | 问题情境解构 | `问题分析.md` | `approve` |
| FORMULATION | `model-formulation` | 数学机制构造 | `建模报告.md` | `feedback` |
| COMPUTATION | `computational-realization` | 计算实验实现 | `程序/主程序.py`, `计算结果.md`, `图表/全部结果.json` | `approve` |
| EVIDENCE | `evidence-visualization` | 证据图谱构建 | `图表/图表引用.tex` | 无 |
| SCHEMATICS | `systems-diagramming` | 系统逻辑制图 | `图表/图表引用.tex` | 无 |
| MANUSCRIPT | `manuscript-synthesis` | 竞赛文稿集成 | `论文/论文正文.tex` | `approve` |
| ASSURANCE | `delivery-assurance` | 提交质量验收 | `论文/数模论文.pdf` | 无 |

冠军模式在 `MANUSCRIPT` 与 `ASSURANCE` 之间启用可选质量层 `championship-review`。该质量层不改变研究依赖关系，也不替代任何既定交付物；它负责多轮审稿、全文修订与终版稿回写。

## 2. 契约来源

- 机器可读阶段表：`assets/workflow_manifest.json`
- 机器门禁实现：`scripts/gate_contracts.py`
- 阶段实施协议：`references/stage_protocols/<skill-name>/SKILL.md`
- 运行编排参考：
  - `references/runtime_reference/workflow_engine.py`
  - `references/runtime_reference/agent_runner.py`
- 官方竞赛准则参考：
  - `references/cumcm-official-notes.md`
- 增强模式阐明：
  - `references/enhancement-operations.md`
- 阶段实施阐明：
  - `references/guide-discovery.md`
  - `references/guide-formulation.md`
  - `references/guide-computation.md`
  - `references/guide-evidence.md`
  - `references/guide-schematics.md`
  - `references/guide-manuscript.md`
  - `references/guide-assurance.md`
- 角色协作契约：
  - `references/subagent-architecture.md`
- 冠军审稿协议与知识库：
  - `references/stage_protocols/championship-review/SKILL.md`
  - `references/championship-review-method.md`

## 3. 运行时目录

默认在目标工作目录下建立这些目录：

- `用户数据/`
- `程序/`
- `图表/`
- `论文/`
- `状态/`
- `日志/`
- `审查/`
- `当前任务/`
- `工具/`
- `参考资料/`
- `模板/`

在此之中：

- `工具/` 来自 `assets/shared-scripts/`
- `参考资料/` 在 `begin` 时同步当前阶段所需参考资料
- `模板/` 在 `begin` 时同步当前阶段所需模板
- `当前任务/执行中/` 在 `begin` 当前工作时写入实施包（`任务包.json`、`执行协议.md`、`工作指南.md`、`协作角色.json`、`协作架构.md`、`复核闭环.md`）
- `审查/门禁/` 按中文工作名称留存每一次门禁校验的 JSON 报告

## 4. 角色职责

### 主控角色

- 决定当前阶段
- 同步当前阶段资源
- 维护 `状态/工作流状态.json`
- 实施 `validate / gate_check / complete / checkpoint / rework`
- 控制跨阶段推进和断点续跑

### 实施角色

- 当前阶段内部的细分工作
- 只在当前阶段准许的文件界限内读写
- 不擅自推进到下一阶段

实施角色配置来自 `assets/workflow_manifest.json` 各阶段的 `subagents` 字段。

## 5. 阶段推进协议

### 初始化

```bash
python scripts/workspace_init.py --workspace .
python scripts/pipeline_manager.py overview --workspace .
```

### 查阅当前阶段

```bash
python scripts/stage_executor.py current --workspace .
python scripts/pipeline_manager.py next --workspace .
```

### 启动阶段

```bash
python scripts/stage_executor.py begin DISCOVERY --workspace .
```

### 阶段闭合

```bash
python scripts/stage_executor.py validate DISCOVERY --workspace .
python scripts/stage_executor.py gate_check DISCOVERY --workspace .
python scripts/stage_executor.py complete DISCOVERY --workspace . --artifacts "问题分析.md"
```

### 处理核验点

```bash
python scripts/stage_executor.py checkpoint DISCOVERY --workspace . --action approve --note "checkpoint passed"
```

### 返工

```bash
python scripts/stage_executor.py rework DISCOVERY --workspace . --reason "artifact missing or quality gate failed"
```

阐明：

- 对某一阶段实施 `rework` 时，该阶段与其后续阶段的完成证据会被标记失效并清空 gate 报告
- 这样上游返工后，下游不会继续假装“已完成”

### 转入增强模式

只有基线工作流的全部研究活动形成有效证据后，才准许转入 `enhancement`：

```bash
python scripts/pipeline_manager.py set-phase enhancement --workspace .
```

转入 `enhancement` 后，优先查阅增强目标，再选取某一阶段做 `rework`：

```bash
python scripts/enhancement_audit.py --workspace .
```

### 启用冠军模式

```bash
python scripts/pipeline_manager.py set-mode championship --workspace .
```

`MANUSCRIPT` 完成后按提示实施：

```bash
python scripts/championship_review.py init --workspace .
```

完成不少于三轮独立审稿和全文修订并通过冠军门槛后，才能启动 `ASSURANCE`。

## 6. 断点续跑

断点信息写在：

- `状态/工作流状态.json`
- `状态/事件日志.jsonl`

续跑时优先实施：

```bash
python scripts/stage_executor.py status --workspace .
python scripts/stage_executor.py current --workspace .
```

若运行状态呈现某阶段已完成，但产物缺失或尺寸过小，应重新 `begin` 当前阶段并补做，避免直接推进。

推荐用下面的脚本做运行状态机回归校验：

```bash
python scripts/stateful_smoke.py --workspace <some-runtime-dir>
```

