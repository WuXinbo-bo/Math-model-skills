# 工作流审查报告 — 系统架构审查官视角

## 总体评价

### 一句话结论
这是一套架构雄心勃勃但工程实现存在严重断裂的工作流系统：阶段文件(S*.md)描述的流程与Python脚本的实际实现之间存在大面积不一致，依赖链有致命断点，门禁系统名不副实，72小时竞赛内完全不可执行。

### 总分：42/100

### 维度得分
| 维度 | 满分 | 得分 | 关键发现 |
|------|------|------|---------|
| 流程连贯性与依赖完整性 | 15 | 5 | S5.5跳过导致S6死锁；STAGE_ARTIFACTS路径与阶段文件路径全面不一致；S0在Windows创建非法目录名 |
| 子 Agent 可执行性 | 15 | 7 | 子Agent指令详尽但上下文窗口需求远超LLM能力；文件权限有S1/S2写入冲突 |
| 门禁与质量控制有效性 | 15 | 5 | 37个合约声明但auto_verdict仅覆盖部分；stage_executor的gate_check映射与实际函数名不匹配；6个门禁无实现 |
| 竞赛实战可行性 | 15 | 3 | 72小时内完全不可能跑完；14阶段+50+子Agent调用+多轮rework=至少200小时工作量 |
| 评分瓶颈分析 | 15 | 8 | 模型质量维度覆盖充分，但代码实际可运行性无保障；门禁形同虚设导致质量控制失效 |
| 模型不足与遗漏 | 15 | 7 | 对不同问题类型无差异化流程；计算可行性无评估；外部数据获取无容错 |
| 建议与改进方向 | 10 | 7 | 核心问题明确：需要统一路径命名、修复依赖链、精简门禁、增加skip状态 |

## P0 问题（致命缺陷 — 必须修复才能使用）
| # | 阶段 | 问题描述 | 影响 | 建议修复方案 |
|---|------|---------|------|------------|
| P0-1 | S5.5→S6 | **S5.5跳过导致S6死锁**：stage_executor.py的STAGE_DAG定义S6依赖["S5.5"]（第55行），但S5.5.md允许equation-driven问题跳过本阶段。状态机只有pending/in_progress/completed/rejected/blocked五种状态，**没有"skipped"状态**。S5.5.md中引用的`stage_executor.py skip S5.5`命令**根本不存在**于stage_executor.py的CLI中。结果：如果跳过S5.5，S6永远无法begin，流程死锁。 | 流程在equation-driven问题类型上完全无法通过S5.5→S6环节 | 1) 在stage_executor.py中添加"skipped"状态和skip命令；2) 修改STAGE_DAG使S6依赖["S5"]，S5.5作为可选分支；3) 或在get_next_actionable中特殊处理S5.5跳过 |
| P0-2 | 全局 | **STAGE_ARTIFACTS路径与阶段文件路径全面不一致**：stage_executor.py第66-82行定义的预期产出路径使用`outputs/S1:literature/`、`outputs/S2:data/`、`outputs/S3:models/`等格式，但所有S*.md阶段文件中的实际产出路径使用`outputs/problem_analysis/`、`data/`、`methods/`等完全不同的格式。例如：S1.md产出`outputs/problem_analysis/analysis.md`，但STAGE_ARTIFACTS期望`outputs/S1:literature/analysis.md`。**validate命令将永远报告所有文件缺失**。 | validate命令完全失效，无法验证任何阶段的产出完整性 | 统一路径方案：要么修改STAGE_ARTIFACTS匹配阶段文件，要么修改阶段文件匹配STAGE_ARTIFACTS。建议前者，因为阶段文件的路径更合理 |
| P0-3 | S0 | **Windows非法目录名**：S0.md Step 2创建`outputs/S1:literature`、`outputs/S2:data`等含冒号的目录。Windows文件系统禁止目录名包含冒号（`:`是保留字符）。在Windows环境下（CUMCM主要参赛环境），`os.makedirs`将直接抛出OSError。 | 在Windows上S0 Step 2直接崩溃，流程无法启动 | 将冒号改为下划线或短横线：`outputs/S1-literature/`或`outputs/S1_literature/` |
| P0-4 | S1 | **输入文件名不一致**：S1.md Step 1读取`inputs/problem.md`，但S0.md的产出清单中题目文件名为`inputs/problem_text.md`。S1将永远找不到正确的输入文件。 | S1无法读取S0的产出，依赖链在S0→S1就断裂 | 统一为`inputs/problem_text.md`或`inputs/problem.md`，两处保持一致 |
| P0-5 | 全局 | **gate_check映射与gate_contracts函数名不匹配**：stage_executor.py的cmd_gate_check（第550-566行）使用大写ID如`G1_PROBLEM_PARSED`、`G2_METHOD_VALIDATED`、`G3_CODE_REVIEWED`等调用auto_verdict，但gate_contracts.py中的实际函数名为`gate_g1_problem_parsed`、`gate_model_selection`（不是G2_METHOD_VALIDATED）、`G3_code_reviewed`（不是G3_CODE_REVIEWED）。auto_verdict的归一化逻辑（第2580行附近）能否正确映射这些不一致的ID需要验证。**很可能大部分gate_check调用都会返回"unknown gate"或异常**。 | 门禁系统形同虚设，gate_check命令无法正确执行任何检查 | 建立统一的门禁ID注册表，确保stage_executor.py、gate_contracts.py、S*.md三方使用完全相同的门禁ID |
| P0-6 | 全局 | **6个门禁合约无Python函数实现**：stage_executor.py的gate_check映射中引用了`G1_5_DATA_QUALITY`（S2）、`G1_5_METRIC_GUARDIAN`（S3）、`G2_5_RACE_COMPLETED`（S4）、`G3_5_EVOLUTION_CONVERGED`（S5.5）、`G4_RESULTS_FROZEN`（S6）、`PER_SUBQUESTION_VERIFICATION`（S6），但gate_contracts.py中**不存在**对应的检查函数。这些门禁调用将全部失败或返回默认值。 | S2/S3/S4/S5.5/S6的门禁检查完全无效 | 为每个缺失门禁实现检查函数，或从gate_check映射中移除未实现的门禁 |

## P1 问题（严重缺陷 — 强烈建议修复）
| # | 阶段 | 问题描述 | 影响 | 建议修复方案 |
|---|------|---------|------|------------|
| P1-1 | 全局 | **跨阶段rework无全局计数器**：S6/S7/S7.5/S8/S9/S10都可以rework回S5，每次增加S5的rework_count。但S5的max_rework=3（standard），来自6个不同阶段的rework可能快速耗尽S5的重做配额，而触发rework的阶段自身计数器不增加。极端情况：S6触发S5 rework（S5计数+1），S5重做完后S6仍失败，再触发S5 rework（S5计数+1），S5再完成，S7又触发S5 rework（S5计数+1=3，blocked）。此时S5被blocked但问题可能不在S5。 | S5可能被不公平地blocked，而真正有问题的阶段不受惩罚 | 增加全局rework计数器（跨阶段累计）和跨阶段rework上限（如S5被外部rework最多2次） |
| P1-2 | S1/S2 | **Analyst子Agent写入路径冲突**：S1 Step 3的Analyst写入`outputs/problem_analysis/analyst_view.md`，S2 Step 2的Analyst也写入同一路径。S2执行时会覆盖S1的Analyst产出，导致S1的评审组(Reviewer)在后续引用时读到错误内容。 | S1的Analyst数据评估被S2覆盖，审查链断裂 | S2的Analyst应写入不同路径如`outputs/problem_analysis/analyst_view_s2.md`或`data/analyst_view.md` |
| P1-3 | 全局 | **pipeline_manager.py与stage_executor.py双状态机冲突**：两个脚本各自维护独立的状态文件（pipeline.json vs stage_execution.json），各自定义阶段顺序和门禁映射，各自的CLI命令互不兼容。pipeline_manager.py从workflow.yaml加载阶段定义，stage_executor.py硬编码STAGE_DAG。两者的阶段ID格式可能不同（pipeline_manager可能使用`S1_problem_analysis`而stage_executor使用`S1`）。 | 两个状态机互相不知道对方的存在，可能导致状态不一致 | 选择一个作为唯一状态机，另一个废弃或作为wrapper |
| P1-4 | S8 | **Writer子Agent的上下文窗口不可能满足**：S8 Step 6要求Writer子Agent一次性读取experiment_review_summary.md + unified_kernel.md + 所有子问题summary.md + 所有DAC.md + paper-writing-rules.md + nature-writing-guide.md(~400行) + scoring-criteria + format-spec，然后生成≥12000字的完整论文。这些输入总计可能超过50000 tokens，远超大多数LLM的有效处理窗口。 | Writer子Agent要么截断输入导致产出不完整，要么产出质量极差 | 将论文撰写拆分为多轮：1) 骨架生成 2) 逐章节填充 3) 摘要撰写，每轮只加载相关上下文 |
| P1-5 | S3 | **S3的14步流程在单阶段内过重**：S3包含4个Proposer子Agent + Red Team + Blue Team + Referee + 可选Round2 + 可选Round3 + Reviewer终审 + 主Agent汇总 = 至少8-12次子Agent调用。每次调用需要用户手动操作（在某些平台上），仅S3一个阶段就可能需要2-4小时。 | S3单阶段耗时可能占竞赛总时间的10-15% | 将S3拆分为S3a(提案)和S3b(辩论+选择)两个阶段，或减少Proposer数量从4到2 |
| P1-6 | S0 | **S0产出目录结构与后续阶段不匹配**：S0 Step 2创建`outputs/S1:literature/`等目录（假设冒号问题修复后），但S1实际写入`outputs/problem_analysis/`，S3写入`methods/`，S5写入`outputs/q{N}/`。S0创建的目录结构完全不会被后续阶段使用，是无效操作。 | S0创建的目录是死目录，浪费执行时间且造成混淆 | S0只创建真正需要的目录：`inputs/`、`state/`、`outputs/reviews/`、`outputs/figures/`、`outputs/tables/`、`src/` |
| P1-7 | 全局 | **`--force`标志完全绕过门禁**：stage_executor.py的cmd_complete（第270行）接受`--force`标志跳过所有门禁检查。这意味着即使门禁系统完美实现，用户（或LLM）也可以用`--force`一键跳过所有质量控制。 | 门禁系统的存在意义被`--force`标志彻底否定 | 移除`--force`标志，或改为`--force`仍需通过P0级门禁 |
| P1-8 | S7.5 | **S7.5门禁无自动化实现**：stage_executor.py的gate_check映射中S7.5对应空列表`[]`（第560行），即S7.5无任何门禁检查。S7.5.md中的门禁G4.7要求主Agent手动验证4个条件，但没有Python脚本支持。 | S7.5门禁完全依赖LLM自律，无任何强制保障 | 实现`gate_unified_kernel()`检查函数并注册到gate_check映射 |

## P2 问题（一般问题 — 建议改进）
| # | 阶段 | 问题描述 | 影响 | 建议改进方案 |
|---|------|---------|------|------------|
| P2-1 | 全局 | **版本号不一致**：SKILL.md声明v2.0.0，stage_executor.py声明v2.0，pipeline_manager.py声明v1.2.0，AGENTS.md引用v11.0/v12.0/v13.0。版本号混乱暗示代码可能不是同一时期产物。 | 维护困难，难以确定哪个版本是"正确的" | 统一所有文件到同一版本号 |
| P2-2 | S6 | **S6产出路径与STAGE_ARTIFACTS不匹配**：S6.md产出`sensitivity/Qx/`和`robustness/Qx/`（无基础路径前缀），STAGE_ARTIFACTS期望`outputs/S6:verification/robustness_report.md`。S6.md中的路径缺少`outputs/`前缀。 | S6 validate永远失败 | 统一路径 |
| P2-3 | S9 | **S9产出路径混乱**：S9.md产出`outputs/paper/paper_revised.md`等，STAGE_ARTIFACTS期望`outputs/S9:review/paper_revised.md`。S9写入的是paper目录而非review目录。 | validate不匹配 | 统一路径 |
| P2-4 | 全局 | **子Agent"强制联网搜索"不可强制**：S3/S5/S5.5的Proposer和Builder子Agent指令中包含"MANDATORY — 不可跳过"的联网搜索要求，但子Agent是LLM角色扮演的，LLM无法真正执行联网搜索（除非平台支持）。这些指令会被LLM忽略或伪造搜索结果。 | 联网搜索要求形同虚设，或导致LLM编造虚假搜索结果 | 将联网搜索改为主Agent的前置步骤（主Agent可以真正搜索），然后将搜索结果作为上下文传给子Agent |
| P2-5 | S4 | **S4门禁G2.5依赖experiment_race.py**：S4.md要求运行`experiment_race.py check`，但该脚本是否能在没有实际实验数据的情况下运行存疑。如果脚本需要预先填充的JSON数据，而数据需要LLM手动生成，则门禁检查的自动化程度很低。 | 门禁检查可能因为数据格式问题而频繁失败 | 提供示例数据文件和模板 |
| P2-6 | 全局 | **gate_contracts.py过于庞大（2955行）**：单文件包含37个合约定义+22个检查函数+auto_verdict路由+CLI，维护困难，任何修改都可能引入回归bug。 | 维护成本高，测试覆盖困难 | 拆分为多个模块：contracts.py（定义）、checkers/（检查函数目录）、verdict.py（路由） |
| P2-7 | S10 | **S10 Step 4的build_docx.py路径错误**：S10.md写`python scripts/build_docx.py paper_final.md final.docx`，但实际文件路径应为`outputs/paper/paper_final.md`和`outputs/final.docx`。 | 命令执行失败 | 修正为完整路径 |
| P2-8 | 全局 | **无并发写入保护**：AGENTS.md声明"子Agent直接写入各自产出文件"，但没有任何文件锁或写入保护机制。如果两个子Agent同时写入同一文件（如S1的Analyst和S2的Analyst），可能导致数据损坏。 | 并行执行时可能数据损坏 | 在context_bridge.py中增加文件锁机制 |

## 各阶段评分
| 阶段 | 评分 | 核心优点 | 核心不足 | 建议改动 |
|------|------|---------|---------|---------|
| S0 | 4/10 | 扫描工作区思路清晰 | Windows非法目录名；产出目录与后续不匹配 | 修复目录名；只创建真正使用的目录 |
| S1 | 6/10 | 三角色(Planner+Analyst+Reviewer)协作设计合理 | 输入文件名与S0不一致；Analyst路径与S2冲突 | 统一文件名；分离Analyst输出路径 |
| S2 | 5/10 | 分支判断(equation/data/hybrid)设计合理 | 产出路径与STAGE_ARTIFACTS不匹配；门禁G1.5无实现 | 统一路径；实现门禁函数 |
| S3 | 7/10 | 4提案组+红蓝对抗+终审的辩论机制完善 | 14步流程过重；联网搜索不可强制；门禁ID不匹配 | 精简为2提案组；主Agent前置搜索 |
| S4 | 5/10 | 赛马+基线对比思路正确 | 门禁G2.5无实现；原型代码实际运行无保障 | 实现门禁；增加代码运行验证 |
| S5 | 7/10 | Baseline-First+按需图表+跨子问题合并设计完善 | 路径使用q{N}格式与STAGE_ARTIFACTS不匹配 | 统一路径格式 |
| S5.5 | 4/10 | 进化探索思路好 | skip命令不存在导致死锁；门禁无实现 | 添加skip状态；实现门禁 |
| S6 | 5/10 | 灵敏度+鲁棒性+交叉验证覆盖全面 | 产出路径混乱；门禁无实现；回退S5无全局计数 | 统一路径；实现门禁 |
| S7 | 6/10 | 证据链追溯设计合理 | 门禁依赖evidence_tracer.py的实际可用性 | 验证脚本可用性 |
| S7.5 | 4/10 | 统一内核归纳概念好 | 门禁为空（无任何检查）；完全依赖LLM自律 | 实现门禁检查函数 |
| S8 | 6/10 | M003复盘会+5步SOP+反AI痕迹设计完善 | Writer上下文窗口不可能满足；5个门禁实际可用性存疑 | 拆分撰写流程；验证门禁 |
| S9 | 7/10 | 红队+终审+修订+验证的对抗审稿设计完善 | Championship 3轮审稿在时间上不可行 | 减少为1轮（Standard）/2轮（Championship） |
| S9.5 | 6/10 | 6维度出版规范检查覆盖全面 | publication_checker.py的实际检查能力未验证 | 验证脚本功能 |
| S10 | 5/10 | 跨子问题一致性检查+逐章节检查设计合理 | build_docx路径错误；门禁依赖未实现的函数 | 修正路径；实现门禁 |

## 最关键的 3 个改进
1. **统一路径命名体系**：STAGE_ARTIFACTS、S*.md产出清单、子Agent写入路径三方必须使用完全一致的路径。建议以S*.md中的路径为准（因为它们更合理），然后更新STAGE_ARTIFACTS和所有引用。同时修复S0的Windows冒号问题。
2. **修复S5.5跳过导致的S6死锁**：在stage_executor.py中添加"skipped"状态和skip命令，修改STAGE_DAG使S6可以接受S5.5为"completed"或"skipped"。这是流程能否跑通的前提。
3. **补全缺失的门禁实现并统一门禁ID**：为6个无实现的门禁添加检查函数（或从映射中移除），统一stage_executor.py和gate_contracts.py之间的门禁ID命名。确保auto_verdict能正确路由所有门禁。

## 最被低估的 3 个优点
1. **Baseline-First建模策略（S5）**：要求先建基线再建主模型，并量化对比提升幅度。这是竞赛中非常实用且常被忽视的策略，能有效避免"复杂模型不如简单模型"的尴尬。
2. **证据链追溯机制（S7）**：将每个结论映射到具体代码输出和数据，确保论文中无数值悬空。这在CUMCM评审中是重要的加分项。
3. **反AI痕迹检测体系（S8/S9/S9.5）**：34类AI套话黑名单+结构性痕迹检测+句长/段落多样性要求。在2026年AIGC检测日益严格的背景下，这是非常有前瞻性的设计。

## 结论与建议

### 能否正式使用？
**当前状态：不能直接使用。** 存在6个P0级致命缺陷，其中最严重的是S5.5跳过死锁（P0-1）和路径全面不一致（P0-2），这两个问题会导致流程在多个阶段卡死或验证全部失败。

### 需要多少改进工作？
- **最小可用版本（MVP）**：修复6个P0问题，预计需要2-3天集中开发。核心工作量在统一路径命名（P0-2）和补全门禁实现（P0-5/P0-6）。
- **竞赛可用版本**：在MVP基础上修复8个P1问题+精简流程以适应72小时时限，预计需要1周。
- **理想版本**：全面重构双状态机冲突、拆分gate_contracts.py、实现并发保护，预计需要2-3周。

### 根本性建议
这套系统的最大问题不是某个具体bug，而是**文档与实现的脱节**。S*.md文件描述了一个非常完善的流程，但Python脚本的实际实现与文档描述之间存在大量不一致。建议在继续添加新功能之前，先做一次全面的**文档-代码对齐审计**，确保每一行文档描述都有对应的、可运行的代码实现。
