# EVIDENCE · 证据图谱构建

- 实施协议：`references/stage_protocols/evidence-visualization/SKILL.md`
- 关键交付物：`图表/图表引用.tex`、`图表/figure_manifest.json` 与规划中的数据图形资产
- 核验点：无

## 主控职责

- 将计算阶段的结构化结果转换为论文级图形与表格。
- 维护 `图表/图表引用.tex` 的引用完整性。
- 对无数据图形场景给出清晰标明证据，而非产出空占位。

## 实施角色

- `data-figure-builder`：制作数据驱动的出版级图形。
- `figure-inspector`：核对规划覆盖率、文件出现性和 LaTeX 引用。

## 审计重点

- 每项规划图形务必产出或给出合理豁免。
- 图形数值务必能追溯到求解结果。
- 样式、字体、单位和图例应满足正式文稿要求。
- 每张图和每个 `TABLE_*` 表必须在现有 `figure_manifest.json` 的 `figures/tables` 中登记 `question/visual_role/claim/source/result_keys/reader_task/publish/placement`；仅 `publish=true` 的图表进入正文，诊断资产和完整长表不得强制嵌入。
- 视觉角色使用 `mechanism/result/validation/decision/diagnostic`；正文优先形成机制、结果与验证的证据递进，不以图片数量评分。
- 图形质量以信息准确、最终尺寸可读、灰度可辨和风格克制为准，不以渐变、圆角框、多层叠加或图形类别数量评分。
