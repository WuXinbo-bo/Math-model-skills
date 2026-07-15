# COMPUTATION · 计算实验实现

- 实施协议：`references/stage_protocols/computational-realization/SKILL.md`
- 关键交付物：`程序/主程序.py`、`程序/code_manifest.json`、`计算结果.md`、`图表/全部结果.json`、`依赖清单.txt`
- 核验点：`approve`

## 主控职责

- 先识别已有程序和结果，避免覆盖有效证据。
- 建立逐子问题实现清单并真实运行计算。
- 汇总结构化结果到 `图表/全部结果.json`。
- 运行 `工具/build_code_appendix.py --manifest-only`，冻结当前源文件清单、入口、代码行数和 SHA-256。

## 实施角色

- `implementation-planner`：映射模型、脚本、结果文件和绘图数据。
- `solver-builder`：实现并运行求解程序，固化计算成果。
- `results-verifier`：核对问题、程序、JSON 和文字结果的一致性。

## 审计重点

- 各个子问题都应有可运行实现和独立结果证据。
- 严禁用虚构数值或未实施代码填充成果。
- 结果结构务必满足后续图形阶段的数据接口。

