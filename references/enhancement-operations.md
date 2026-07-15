# Enhancement Operations

`enhancement` 不是新建一套替代过程，而是在保留 baseline 七步边界的前提下，对现有产物做更强的复核、返工和证据固化。

## 1. 启动条件

- `baseline` 七步已全部完成
- 已切换 phase:

```bash
python scripts/pipeline_manager.py set-phase enhancement --workspace .
```

## 2. 升级方式

升级仍采用原七步，但通过“选取阶段 -> 返工 -> 重跑 -> 重新过门禁”的方式开展：

```bash
python scripts/stage_executor.py rework COMPUTATION --workspace . --reason "enhancement tightening"
python scripts/stage_executor.py begin COMPUTATION --workspace .
python scripts/stage_executor.py validate COMPUTATION --workspace .
python scripts/stage_executor.py gate_check COMPUTATION --workspace .
python scripts/stage_executor.py complete COMPUTATION --workspace . --artifacts "程序/主程序.py,计算结果.md,图表/全部结果.json,依赖清单.txt"
python scripts/stage_executor.py checkpoint COMPUTATION --workspace . --action approve --note "enhancement pass"
```

注意：

- 对上游阶段实施 `rework` 时，当前阶段及其后续阶段的 gate 证据会被清空
- 这样可强制后续阶段基于新的上游产物重新复核，而不是复用旧通过登记

## 3. 每阶段升级重点

- `DISCOVERY`: 把赛题覆盖表、升级判定表、图形与表格清单写得更完整，减少模糊解释空间
- `FORMULATION`: 强化参数化假设、验证检查点、结构性校验输入
- `COMPUTATION`: 强化真实实施证据、数据查阅校验、结果 JSON 与文字结果一致性
- `EVIDENCE`: 强化规划图形与表格覆盖度与 `图表引用.tex` 一致性
- `SCHEMATICS`: 强化 DrawIO/TikZ 源文件、PDF、嵌入位置的相应关系
- `MANUSCRIPT`: 强化模板完整性、图形与表格全量嵌入、摘要/结论/数值一致性
- `ASSURANCE`: 强化匿名性、页数、陈旧图形与表格、编译合规核验

## 4. 不准许的事

- 不准许绕过 baseline 七步次序
- 不准许移除原有产物合同
- 不准许用“升级版新过程”替换原过程
- 不准许把 enhancement 变成只写一段阐明、不做真实返工

## 5. 推荐入口

优先查阅升级审计：

```bash
python scripts/enhancement_audit.py --workspace .
```

再选定一个阶段做 `rework` 和 `begin`。

