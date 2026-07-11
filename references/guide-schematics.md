# SCHEMATICS · 系统逻辑制图

- 实施协议：`references/stage_protocols/systems-diagramming/SKILL.md`
- 关键交付物：DrawIO/TikZ 源文件、相应 PDF 及更新后的 `图表/图表引用.tex`
- 核验点：无

## 主控职责

- 识别既有过程图、技术路线图和架构图资产。
- 追加而非覆盖数据图形阶段已经写入的 LaTeX 引用。
- 保证每张示意图位于无误的论文章节和逻辑位置。

## 实施角色

- `diagram-builder`：制作可编辑的系统结构与过程示意图。
- `diagram-inspector`：核对源文件、PDF 和 LaTeX 引用三方相应关系。

## 审计重点

- 规划中的路线图和子问题过程图务必逐项闭合。
- 图形结构应表达真实方法关系，严禁仅作装饰。
- 严禁破坏 `图表/图表引用.tex` 中已有内容。

