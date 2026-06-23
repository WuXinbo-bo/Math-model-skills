# Meta-model-skills-max v1.2.0

**日期**: 2026-06-16  
**版本**: v1.2.0  
**主题**: 版本归一 + 系统链路全量加固  

---

## 版本说明

v1.2.0 是 Meta-model-skills-max 的归一化正式版本。将此前分散的多版本号（v8.0.0/v9.0.0/v5.0.0/v6.0.0 等）统一归一到 v1.2.0，并完成系统链路全量加固。

---

## 核心能力

| 能力 | 数量 | 说明 |
|------|------|------|
| 功能角色群 | 8 个 | 规划组/分析组/提案组/构建组/审查组/评审组/写作组/总指挥 |
| 会议协议 | 4 场 | M001 题意共识会/M002 模型辩论会/M003 实验复盘会/M004 红队审稿会 |
| 阶段流水线 | 14 阶段 | S0-S10 + S5.5 + S7.5 + S9.5 |
| 质量门禁 | 35 道 | G1-G9.5 全覆盖，含并行合并/基线对比/摘要质量/出版规范门禁 |
| 工具脚本 | 50 个 | 文档处理/可视化/建模/门禁/会议/流水线管理等 |
| 深度模式 | 3 种 | Fast / Standard / Championship |
| 增强引擎 | 12 个 | 摘要质量/推导链/方法矩阵/逐题检验/对抗审稿/灵敏度分析/出版规范检查等 |

---

## 阶段流程

```
S0 问题理解 → S1 问题分析 → S2 文献综述 → S3 模型选择
→ S4 实验设计 → S5 建模求解（含 S5.5 求解小结）
→ S6 灵敏度分析 → S7 结果整合（含 S7.5 统一内核归纳）
→ S8 论文撰写 → S9 对抗审稿
→ S9.5 出版规范审查（强制门禁，不可跳过）
→ S10 最终交付
```

---

## 打回重做机制

- **门禁驱动**：Gate PASS → 推进 / Gate FAIL → rework → 修复 → 重新验证
- **Max reworks**: Fast=2 / Standard=3 / Championship=5
- **S9.5 特殊规则**: S9.5 失败 ≥2 次 → 自动打回 S9，最多打回 2 次后暂停
- **S10 前置检查**: S9.5 未完成时 `stage_executor.py begin S10` 会阻塞退出

---

## 8 层防跳过体系（S9.5）

```
第 1 层: SKILL.md 核心规则第 5 条 — publication_checker.py 列为 MANDATORY
第 2 层: SKILL.md 核心规则第 9 条 — S9.5 特殊打回规则
第 3 层: SKILL.md 核心规则第 12 条 — S9.5 强制执行声明
第 4 层: SKILL.md Auto Mode — S9.5 是强制阶段
第 5 层: stage_executor.py begin S10 — 前置检查 S9.5 已完成（代码阻塞）
第 6 层: stage_executor.py complete S9 — 输出 S9.5 MANDATORY 预警
第 7 层: stage_executor.py rework S9.5 — 失败≥2次自动打回 S9
第 8 层: S9.5.md 顶部 — 3行反跳过声明
```

---

## 文件结构

```
Meta-model-skills-max/
├── SKILL.md                    # 主 Skill 定义（v1.2.0）
├── README.md                   # 项目说明
├── AGENTS.md                   # Agent 快速参考
├── requirements.txt            # Python 依赖
├── main.py                     # 统一入口
├── config/
│   ├── workflow.yaml           # 阶段定义（14 阶段 + 35 门禁）
│   ├── rubric.yaml             # 评分标准
│   └── prompts/                # 9 个 Agent prompt
│       ├── chief_agent.md
│       ├── zhongshu.md
│       ├── hubu.md
│       ├── bingbu_a.md
│       ├── bingbu_b.md
│       ├── gongbu.md
│       ├── xingbu.md
│       ├── menxia.md
│       └── libu.md
├── stages/                     # 14 个阶段指令文件
│   ├── S0.md ~ S10.md
│   ├── S5.5.md
│   ├── S7.5.md
│   └── S9.5.md
├── scripts/                    # 50 个工具脚本
│   ├── stage_executor.py       # 阶段状态机
│   ├── pipeline_manager.py     # 流水线管理
│   ├── gate_contracts.py       # 35 道门禁合约
│   ├── meeting_protocol.py     # 会议协议引擎
│   ├── publication_checker.py  # 出版规范检查
│   ├── build_docx.py           # DOCX 生成
│   ├── ... (50 total)
│   └── tests/
├── references/                 # 参考资料库
├── docs/                       # 文档
├── examples/                   # 示例配置
└── data/                       # 数据文件
```

---

## 质量保证

- 所有 Python 脚本 0 lint 错误
- 所有阶段文件 0 语法错误
- 所有 Agent prompt 格式正确
- 门禁合约 35 个全部注册
- S9.5 8 层防跳过机制验证通过
- S10 前置检查验证通过
- S9.5 打回 S9 机制验证通过

---

**版本**: v1.2.0  
**日期**: 2026-06-16
