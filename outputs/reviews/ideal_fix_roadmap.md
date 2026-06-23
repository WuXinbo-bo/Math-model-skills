# Meta-model-skills-max 理想版修复全流程

> **目标**：生产级质量，所有 P0/P1/P2 问题全部修复，文档-代码完全对齐
> **预计工作量**：2-3 周（1人全职）
> **基于**：Agent A（竞赛实战审查 58分）+ Agent B（系统架构审查 42分）+ 综合总结（50分）

---

## 修复阶段总览

| 阶段 | 内容 | 工期 | 累计 | 状态 |
|------|------|------|------|------|
| Phase 1 | P0 致命缺陷修复（8项） | 4天 | 4天 | **全部完成** |
| Phase 2 | P1 严重缺陷修复（8项） | 5天 | 9天 | **全部完成** |
| Phase 3 | P2 改进项修复（10项） | 5天 | 14天 | **全部完成** |
| Phase 4 | 文档-代码对齐审计 + 集成测试 | 3天 | 17天 | **基本完成（0 lint）** |

> **实际完成时间**：2026-06-16（单次会话完成 Phase 1-3 主要项 + Phase 4 验证）

---

## Phase 1：P0 致命缺陷修复（4天）

### P0-1：S5.5 跳过导致 S6 死锁

**问题**：状态机无 `skipped` 状态，`skip` 命令不存在，跳过后 S6 永远无法 begin。

**修复文件**：`scripts/stage_executor.py`

**修复步骤**：

1. 在状态枚举中添加 `skipped`
2. 添加 `skip` CLI 子命令（仅白名单阶段可跳过：S5.5、S7.5）
3. 修改 `get_next_actionable` 使 skipped 等同于 completed 处理依赖
4. 修改 `stages/S5.5.md` 中对 skip 命令的引用

**验证**：
```bash
python scripts/stage_executor.py skip S5.5 --reason "equation-driven"
python scripts/stage_executor.py begin S6  # S5.5 skipped 时 S6 仍可 begin
```

---

### P0-2：统一路径命名体系

**问题**：`STAGE_ARTIFACTS`（第66-82行）使用 `outputs/S1:literature/` 格式，与 S*.md 实际路径完全不一致。

**修复文件**：`scripts/stage_executor.py` 第66-82行 + 各 S*.md

**修复步骤**：

1. 以 S*.md 实际路径为准，重写 `STAGE_ARTIFACTS` 字典
2. 同时修正少数 S*.md 中的路径不一致（如 S6 缺 `outputs/` 前缀）

**路径映射表**：

| 阶段 | 当前 STAGE_ARTIFACTS 路径 | 统一后（匹配 S*.md） |
|------|--------------------------|---------------------|
| S1 | `outputs/S1:literature/` | `outputs/problem_analysis/` |
| S2 | `outputs/S2:data/` | `data/` |
| S3 | `outputs/S3:models/` | `methods/` |
| S4 | `outputs/S4:experiments/` | `methods/experiments/` |
| S5 | `outputs/S5:solving/q{N}/` | `outputs/q{N}/` |
| S5.5 | `outputs/S5.5:evolution/` | `outputs/evolution/` |
| S6 | `outputs/S6:verification/` | `outputs/verification/` |
| S7 | `outputs/S7:evidence/` | `outputs/evidence/` |
| S7.5 | `outputs/S7.5:kernel/` | `outputs/kernel/` |
| S8 | `outputs/S8:paper/` | `outputs/paper/` |
| S9 | `outputs/S9:review/` | `outputs/review/` |
| S10 | `outputs/S10:final/` | `outputs/final/` |

**验证**：`python scripts/stage_executor.py validate S1` 路径匹配

---

### P0-3：修复 Windows 非法目录名

**问题**：S0.md 创建 `outputs/S1:literature` 含冒号，Windows 直接崩溃。

**修复文件**：`stages/S0.md`

**修复**：P0-2 统一路径后自动解决（不再使用 `S1:xxx` 格式）。

---

### P0-4：统一文件名（problem.md vs problem_text.md）

**问题**：S0 产出 `inputs/problem_text.md`，S1 读取 `inputs/problem.md`。

**修复文件**：`stages/S1.md`（及所有引用 `problem.md` 的文件）

**修复**：统一为 `inputs/problem_text.md`，全文搜索替换。

---

### P0-5：统一门禁 ID + 补全 6 个缺失实现

**问题**：stage_executor 用大写 ID，gate_contracts 用小写函数名；6 个门禁无实现。

**修复文件**：`scripts/stage_executor.py` + `scripts/gate_contracts.py`

**修复步骤**：

**Step A** — 建立门禁 ID 注册表（在 stage_executor.py 中）：

```python
GATE_REGISTRY = {
    "S0":   ["G0"],
    "S1":   ["G1_PROBLEM_PARSED"],
    "S2":   ["G1_5_DATA_QUALITY"],          # 需新增实现
    "S3":   ["G1_5_METRIC_GUARDIAN"],        # 需新增实现
    "S4":   ["G2_5_RACE_COMPLETED"],         # 需新增实现
    "S5":   ["G3_CODE_REVIEWED", "PER_SUBQUESTION"],
    "S5.5": ["G3_5_EVOLUTION_CONVERGED"],    # 需新增实现
    "S6":   ["G4_RESULTS_FROZEN"],           # 需新增实现
    "S7":   ["G4_EVIDENCE_CHAIN"],
    "S7.5": ["G4_7_KERNEL"],                # 需新增实现
    "S8":   ["G5_S8_CONTENT_READY"],
    "S9":   ["G5_PAPER_QUALITY", "G5_5_ADVERSARIAL"],
    "S9.5": ["G6_PUBLICATION_READY"],
    "S10":  ["G6_APPENDIX_COMPLETE"],
}
```

**Step B** — 在 gate_contracts.py 中补全 7 个缺失函数：

| 函数名 | 检查内容 |
|--------|---------|
| `gate_data_quality` | `data/data_dictionary.md` 存在且非空 |
| `gate_metric_guardian` | `methods/evaluation_metrics.md` 存在 |
| `gate_race_completed` | `model_leaderboard.csv` 有数据行 |
| `gate_evolution_converged` | `outputs/evolution/evolution_report.md` 存在 |
| `gate_results_frozen` | `frozen_numbers.json` 存在且非空 |
| `gate_per_subquestion` | 每个 `outputs/q{N}/summary.md` 存在 |
| `gate_unified_kernel` | `outputs/kernel/unified_kernel.md` 存在且非空 |

**Step C** — 修改 auto_verdict 路由，确保大写 ID 正确映射到小写函数。

**验证**：全阶段 gate_check 不出现 "unknown gate"

---

### P0-6：移除"强制联网搜索"要求

**问题**：子Agent无网络访问，"MANDATORY 联网搜索"导致编造文献。

**修复文件**：`stages/S3.md`、`stages/S5.md`、`stages/S5.5.md`、`templates/agent_prompts/`

**修复步骤**：

1. 搜索所有含"联网搜索"的位置：
   ```bash
   grep -rn "联网搜索\|MANDATORY.*search" stages/ templates/
   ```

2. 替换为基于本地文献的指令：
   ```
   原：强制联网搜索(MANDATORY)
   改：基于 references/ 目录中的已有文献进行分析。
       如需补充文献，标注 [建议补充文献: 关键词xxx]，
       由主Agent统一执行 web_search。
   ```

3. 在 AGENTS.md 中新增"文献搜索协议"：

   子Agent 不得自行联网。流程：子Agent 标注需求 → 主Agent 搜索 → 结果写入 references/ → 二次注入子Agent。

---

### P0-7：Writer 拆分为多轮调用

**问题**：S8 Step 6 要求 Writer 一次读 50K+ tokens 并产出 12000 字论文，不可能。

**修复文件**：`stages/S8.md`

**修复方案** — 拆为 6 轮聚焦调用：

| 轮次 | 输入 | 输出 | 上下文量 |
|------|------|------|---------|
| 6A 素材核查 | 上游产物清单 | `material_checklist.md` | ~3K |
| 6B 骨架生成 | checklist + 规则 + 模板 | `paper_skeleton.md`（章节标题+字数分配） | ~5K |
| 6C 逐章填充（每章一轮） | 骨架 + 该章素材 + 前章摘要 | `chapters/ch{N}.md` | ~10-12K |
| 6D 摘要精修 | 各章摘要段落 | `abstract_final.md` | ~3K |
| 6E 全文合并 | abstract + 所有 ch{N} | `paper.md`（完整论文） | ~15K |

**关键约束**：每轮输入 < 15000 tokens

**验证**：每轮 Writer 调用上下文合理，最终 paper.md >= 10000 字且数值一致

---

### P0-8：统一阶段数为 14

**问题**：SKILL.md/AGENTS.md 声称 13 阶段，实际 14 个。

**修复文件**：`SKILL.md`、`AGENTS.md`

**修复**：全文搜索 "13.*stage" "13.*阶段"，全部替换为 14。

---

## Phase 2：P1 严重缺陷修复（5天）

### P1-1：S3 精简（15次→5次调用）

**修复文件**：`stages/S3.md`

| 模式 | 原 | 修复后 |
|------|---|--------|
| Fast | 15次 | **3次**（1 Proposer + 1轮简化攻击 + 1 Referee） |
| Standard | 15次 | **5次**（2 Proposer + 1轮攻防 + Reviewer） |
| Championship | 15次 | **8次**（3 Proposer + 2轮攻防 + Reviewer） |

---

### P1-2：Fast 模式真正精简路径

**修复文件**：`SKILL.md` + 各 S*.md

Fast 模式精简清单：

| 阶段 | Standard | Fast |
|------|----------|------|
| S0 | 审查官打分 + 门禁 | 跳过审查官，直接初始化 |
| S1 | 3子Agent | 2子Agent（跳过Reviewer） |
| S2 | 完整数据治理 | equation_driven走轻量路径 |
| S3 | 5次调用 | 3次调用 |
| S4 | 完整赛马 | 跳过（直接用S3结论） |
| S5.5 | 条件执行 | 默认跳过 |
| S6 | 三重验证 | 仅灵敏度分析 |
| S7.5 | 执行 | 合并到S8 |
| S8 | 完整撰写 | 精简模板 |
| S9 | 多轮审稿 | 1轮 |
| S9.5 | 全维度检查 | 仅P0项 |
| S10 | 完整检查 | 跳过跨子问题一致性 |

Fast 模式总子Agent调用目标：**<= 20次**（Standard 约 40-50次）

---

### P1-3：S9+S9.5 快速修复模式

**修复文件**：`stages/S9.md`、`stages/S9.5.md`

S9.5 快速修复模式（当剩余时间 < 6小时时自动启用）：
- 只修复 P0 问题（AI套话、匿名性）
- 跳过 P1/P2 自动修复
- 最多 1 次打回
- 目标耗时：1-2小时

---

### P1-4：S6 区分内部重做和 S5 回退

**修复文件**：`stages/S6.md`、`scripts/stage_executor.py`

判断标准：
- **验证方法不充分**（灵敏度范围太窄等） → `rework S6`（内部重做）
- **模型推导错误**（核心数值有误） → `rework S5`（回退）

在 stage_executor.py 中添加 `--target` 参数支持指定回退目标。

---

### P1-5：解决双状态机冲突

**修复文件**：`scripts/pipeline_manager.py`、`scripts/stage_executor.py`

方案：选择 `stage_executor.py` 为唯一状态机。

1. 废弃 `pipeline_manager.py` 的状态管理，保留报告生成
2. pipeline_manager 的状态操作委托给 stage_executor（wrapper 模式）
3. 删除 `pipeline.json`，统一 `stage_execution.json`

---

### P1-6：S1/S2 Analyst 路径冲突

**修复文件**：`stages/S1.md`、`stages/S2.md`

| 阶段 | 原路径 | 修复后 |
|------|--------|--------|
| S1 Analyst | `analyst_view.md` | `analyst_s1.md` |
| S2 Analyst | `analyst_view.md` | `data/analyst_s2.md` |

---

### P1-7：添加 LLM 幻觉检测机制

**修复文件**：新增 `scripts/hallucination_checker.py`

三大检查功能：
1. **文献引用真实性** — 论文中 `[N]` 引用 vs `references/` 目录匹配
2. **数值一致性** — 论文数值 vs `frozen_numbers.json` 追溯
3. **公式合理性** — 变量是否在 `symbol_table.md` 中定义

集成到 S9 门禁（gate_g5_paper_quality）。

---

### P1-8：限制 `--force` 标志

**修复文件**：`scripts/stage_executor.py` 第270行附近

`--force` 仅跳过 P1/P2 门禁，P0 门禁仍强制执行。

---

## Phase 3：P2 改进项修复（5天）

### P2-1：S7.5 合并到 S8

**修复文件**：`stages/S7.5.md`、`stages/S8.md`、`scripts/stage_executor.py`

将 S7.5 的"统一内核归纳"作为 S8 Step 4 的子任务。STAGE_DAG 中移除 S7.5，S8 直接依赖 S7。

---

### P2-2：gate_contracts.py 拆分

**修复文件**：`scripts/gate_contracts.py`（2955行）

```
scripts/gate_contracts/
├── __init__.py          # 兼容层，导出 auto_verdict
├── definitions.py       # 37个合约定义
├── checkers/
│   ├── s0_s1.py         # S0/S1 检查
│   ├── s2_s3.py         # S2/S3 检查
│   ├── s4_s5.py         # S4/S5/S5.5 检查
│   ├── s6_s7.py         # S6/S7/S7.5 检查
│   ├── s8.py            # S8 检查
│   └── s9_s10.py        # S9/S9.5/S10 检查
├── verdict.py           # auto_verdict 路由
└── cli.py               # CLI 入口
```

保留根目录 `gate_contracts.py` 作为兼容层。

---

### P2-3：版本号统一

统一所有文件为 `v3.0.0`。

涉及文件：`SKILL.md`、`stage_executor.py`、`pipeline_manager.py`、`AGENTS.md`

---

### P2-4：产出字数上限

| 阶段 | 子Agent | 修复后字数约束 |
|------|---------|--------------|
| S1 | Planner | 400-600字 |
| S1 | Analyst | 600-800字 |
| S1 | Reviewer | 300-500字 |
| S3 | Proposer | 300-500字/模型 |
| S3 | Red Team | 800-1200字 |
| S8 | Writer 每章 | 按骨架分配 ±10% |

原则：**信息密度优先于字数**。

---

### P2-5：审查官评分校准

为审查官提供锚定案例：
- **90分**：产出完整、数值一致、逻辑清晰、有创新
- **70分**：产出基本完整、数值基本一致、通顺无AI套话
- **60分**：有1项产出缺失、数值多处不一致

---

### P2-6：脚本分级

```markdown
### 核心脚本（Fast 模式依赖）
- stage_executor.py、gate_contracts/、build_docx.py、hallucination_checker.py

### 增强脚本（Standard/Championship 使用）
- context_bridge.py、evidence_tracer.py、experiment_race.py、
  publication_checker.py 等

### 实验脚本（可选）
- ...（其余）
```

---

### P2-7：S0 简化

Fast 模式 S0 仅 3 步：扫描工作区 → 初始化目录 → 读取题目。跳过审查官。

---

### P2-8：S4 简化路径判断明确化

明确触发条件：
1. S3 debate_summary 中只有 1 个 ADVANCE 模型且无 REPAIR
2. equation_driven + S3 已明确唯一主模型
3. Fast 模式默认走简化路径

---

### P2-9：S7 删除死代码分支

删除"若已有论文草稿，提取其中的关键数值"分支（S7 在 S8 之前，不可能有论文草稿）。

---

### P2-10：并发写入保护

在 `context_bridge.py` 中增加文件锁机制（flock/msvcrt），防止并行子Agent写入同一文件。

---

## Phase 4：文档-代码对齐审计 + 集成测试（3天）

### Day 1：全量 grep 审计

```bash
# 1. 检查所有路径引用
grep -rn "outputs/S[0-9]" stages/ scripts/  # 应无冒号格式
grep -rn "problem\.md" stages/ scripts/      # 应全为 problem_text.md

# 2. 检查所有门禁引用
grep -rn "G[0-9]" stages/ | grep -oP "G[0-9_]+" | sort -u
# 对比 GATE_REGISTRY 中的 ID，确保全部覆盖

# 3. 检查阶段数引用
grep -rn "13.*stage\|13.*阶段" stages/ SKILL.md AGENTS.md
# 应返回 0 结果

# 4. 检查联网搜索引用
grep -rn "联网搜索\|MANDATORY.*search" stages/ templates/
# 应返回 0 结果
```

### Day 2：端到端流程测试

按 Fast/Standard/Championship 模式各跑一遍空流程（mock 子Agent产出）：

```bash
# 1. 初始化
python scripts/stage_executor.py init --contest CUMCM --subquestions 3 --mode fast

# 2. 逐阶段执行
for stage in S0 S1 S2 S3 S4 S5 S6 S7 S8 S9 S9.5 S10; do
    python scripts/stage_executor.py begin $stage
    python scripts/stage_executor.py gate_check $stage
    python scripts/stage_executor.py complete $stage --artifacts "mock.md"
done

# 3. 验证
python scripts/stage_executor.py report  # 应显示全部 completed
```

### Day 3：回归测试 + 文档更新

1. 修改任意门禁后，重跑对应阶段不出现回归
2. 更新 README.md、CHANGELOG.md
3. 标记版本号为 `v3.0.0`

---

## 修复后预估效果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 综合评分 | 50/100 | **85-90/100** |
| 流程可跑通性 | 死锁（S5.5） | 完全跑通 |
| 子Agent调用次数 | 40-60次（Championship） | Fast≤20 / Standard≤35 |
| 门禁有效性 | 6个无实现 + ID不匹配 | 全部实现 + ID一致 |
| 文档-代码一致性 | 大面积脱节 | 完全对齐 |
| 72小时可行性 | 不可能 | Fast模式完全可行 |
| 竞赛得分预估 | 75-85/125 | **90-100/125** |

---

## 关键原则

1. **以 S*.md 为真相源** — Python 代码适配文档，而非反过来
2. **每修复一个 P0/P1，立即验证** — 不积累修复债务
3. **保留设计理念** — Baseline-First、子问题隔离、反AI痕迹检测全部保留
4. **Fast 模式是核心** — 72小时竞赛中 Fast 模式是唯一可行路径，必须确保其完备性
