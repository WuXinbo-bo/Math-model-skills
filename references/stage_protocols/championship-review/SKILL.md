---
name: championship-review
description: "Meta-model-agent 冠军模式模拟质量审稿协议。仅在 quality_mode=championship 且竞赛文稿集成完成后使用，通过多轮独立审稿、修订计划、全文改写和逐项复核产出冠军版论文。"
---

# 冠军模式多轮质量审稿

## 稳定执行契约

- **执行目标**：在冠军模式下，以彼此独立的多轮视角审查并修订完整论文。
- **调用参数**：当前工作流输入。
- **权威输入**：论文/论文正文.tex、全部上游证据、审稿方法与本轮审稿任务。
- **允许交付**：审查/冠军模式/第NN轮/下的审稿、计划、修订与复核文件，以及最终冠军修订稿。
- **禁止写入**：不得越权修改已冻结的上游事实、用户原始文件或本协议未授权的目录。
- **可用工具边界**：按宿主工具权限执行。
- **最小交付**：独立审稿报告、可执行修订计划、完整修订论文、逐项复核和最终总报告。
- **恢复入口**：优先读取当前工作、状态记录和已有产物，从最近一次通过门禁的位置继续。
- **失败回退**：发现模型、程序或结果根本缺陷时立即回退对应工作流，禁止用措辞淡化上游错误。
- **收口顺序**：先核对输入，再完成产物，再运行本环节门禁，最后登记状态；门禁未通过不得宣告完成。

查阅 `references/championship-review-method.md`，严禁改变问题、模型、计算、证据和论文之间的依赖关系，仅在 `MANUSCRIPT` 与 `ASSURANCE` 之间实施本协议。

## 启动

```bash
python scripts/championship_review.py init --workspace .
python scripts/championship_review.py start-round --workspace . --round 1 --perspective mathematical
```

## 每轮实施

1. 建立全新的独立审稿角色，不向其给出上一轮结论或预设答案。
2. 审稿角色查阅 `论文/论文正文.tex`、模型报告、结果文件、图形与表格引用和本轮 `审稿任务.md`。
3. 写入 `审稿报告.md`，报告务必涵盖综合分、分维度得分及 P0/P1/P2 列表。
4. 主控角色将问题转换为 `修订计划.md`，清晰标明调整位置、证据来源和验收方式。
5. 写作角色基于计划直接产出完整 `修订论文.tex`。
6. 采用新的复核视角逐项核验调整，并写入 `修订复核.md`。
7. 登记轮次：

```bash
python scripts/championship_review.py record-round --workspace . --round 1 --score 86 --p0 0 --p1 2 --paper 审查/冠军模式/第01轮/修订论文.tex --review 审查/冠军模式/第01轮/审稿报告.md --plan 审查/冠军模式/第01轮/修订计划.md --verification 审查/冠军模式/第01轮/修订复核.md
```

后续轮次务必以上一轮 `修订论文.tex` 为审稿对象，但审稿角色保持独立。前三轮视角依次为 `mathematical`、`evidence`、`judge`。

## 根本缺陷处理

审稿若发现模型、程序或关键结果错误，停止文字润色，按知识库的回退准则调用 `stage_executor.py rework`。严禁通过弱化措辞掩盖上游错误。

## 终版闭合

完成不少于三轮且最后一轮满足 `score>=85`、`P0=0`、`P1<=2` 后运行：

```bash
python scripts/championship_review.py finalize --workspace .
```

该命令产出冠军修订稿和总审稿报告，备份并更新 `论文/论文正文.tex`。随后才准许启动 `ASSURANCE`。

