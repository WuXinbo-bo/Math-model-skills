# Gate Matrix

这份矩阵把原七步 prompt 里的硬约束整理成 workflow 可实施门禁。

## DISCOVERY `problem-intelligence`

- 务必有 `问题分析.md`，且 >= 1500 bytes
- 务必写出子问题拆解
- 务必写出变量/符号或等价内容
- 务必写出建模思路、数据探索、工作计划
- 务必写出假设敏感性预检
- 务必写出题目逐句拆解/句子级五问复核
- 务必写出反向对照或经典问题升级判定
- 务必规划 `技术路线图.drawio`，且多问题赛题务必规划每问 `问题流程图_N.drawio`
- 数据图规划务必带配方编号或 `(custom)`
- 务必声明 `数据模式: supplied/collected/none`；有数据规划审计、预处理与冻结输入，无数据明确 `预处理: skipped` 及原因

## FORMULATION `model-formulation`

- 务必有 `建模报告.md`，且 >= 2000 bytes
- 子问题覆盖数不可少于分析阶段
- 务必有目标函数/公式或等价模型表达
- 务必有约束描述
- 务必写校验/检验/灵敏度有关内容
- 务必写参数化假设与替代假设
- 务必审视问题情境解构里的升级推荐，不可无声忽略
- 务必导出 `验证检查点` 和 `结构性验证输入`
- 务必带上图形与表格预规划，并写明已对照防错手册复核
- 每问务必登记论文表达卡和问题角色；`new_model/model_extension` 另登记正式名称、标准模型族、求解算法和完整结构卡，其他角色明确继承模型，算法不得冒充数学模型
- 有数据时务必定义题目专属预处理合同、泄漏边界和唯一冻结输入；无数据时明确跳过

## COMPUTATION `computational-realization`

- 务必有 `程序/主程序.py`、`计算结果.md`、`图表/全部结果.json`、`依赖清单.txt`、`程序/code_manifest.json`
- `problem*.py` 和 `problem_*_结果.json` 数量不可少于子问题数
- 不准许把 PDF 证据图谱构建职责偷跑到当前阶段
- 务必为后续 `evidence-visualization` 留下结构化 JSON 结果
- `计算结果.md` 务必逐问写明数值结果
- `程序/主程序.py` 务必有聚合入口并写出 `全部结果.json`
- `code_manifest.json` 务必登记当前源码哈希、入口和逐问程序，哈希不得陈旧
- `全部结果.json.model_identity` 务必逐问固化正式模型名称、标准模型族和求解算法，并与 `建模报告.md` 一致
- 有附件或采集数据时务必给出 `程序/data_preprocessing.py`，写入处理前后质量、哈希和泄漏控制，并保证模型只读取 `数据/processed/` 冻结输入

## EVIDENCE `evidence-visualization`

- 务必有 `图表/图表引用.tex`
- 务必有 `图表/figure_manifest.json`，正文图登记 `claim/source/reader_task/publish/placement`
- 若出现 `图表/全部结果.json`，一般情况下应产出不少于一张 `fig_*.pdf/png`
- 若 `论文规划.md` 清晰标明写无图形与表格，可用空 `图表引用.tex` 作为占位
- 产物重点是数据图，不是 DrawIO / TikZ
- 若规划文档中明示列出 `fig_xxx` 或 AIIMG 图，则务必一一产出并写进 `图表引用.tex`

## SCHEMATICS `systems-diagramming`

- 不少于一张 `.drawio` 或 `tikz_*.tex` 与相应 PDF
- 务必更新 `图表/图表引用.tex`
- 不可覆盖 EVIDENCE 里已有的数据图 include，仅可追加
- 若 `论文规划.md` 清晰标明无架构图/过程图需求，可降级为保留已有 `图表引用.tex`
- 若规划文档中明示列出 `技术路线图.drawio`、`问题流程图_N.drawio` 或 `tikz_*.tex`，务必逐一落地源码、PDF 和 include

## MANUSCRIPT `manuscript-synthesis`

- PDF 路线务必有 `论文/论文正文.tex`，且 >= 5000 bytes；DOCX 路线务必有 `论文/论文正文.md`，且 >= 5000 bytes
- 务必基于当前赛制模板，不可从零胡写
- PDF 路线务必有 `documentclass`、章节输入、参考文献、附录；DOCX 路线务必有标题、摘要、关键词、逐问模型与结果验证、结论、参考文献和复现说明
- 不准许保留模板占位符
- 务必嵌入前序图形与表格与关键结果
- 务必有摘要与结论性内容
- `figure_manifest.json` 中 `publish=true` 的 PDF/PNG 务必在论文正文中被引用；诊断图、调试图和替代版本不得强制塞入正文
- 务必有由 `build_code_appendix.py` 生成的真实代码清单；三种赛制均只展开主程序与逐问核心实现，辅助程序只列清单，显示名使用英文代码名
- 务必有关键词、正文引用、参考文献条目，并满足上标引用风格
- 摘要务必按“问题与主要模型—逐问简洁模型名或继承关系/核心方法/关键结果/检验—模型评价”组织，禁止内部合同语言和完整算法链，关键词来自标准模型族或核心算法
- 有真实数据时，“模型准备”下务必有独立数据预处理小节，并与冻结输入证据一致
- `图表引用.tex` / `TABLE_*.tex` 中的 label 若出现，务必在正文中真正落地

## ASSURANCE `delivery-assurance`

- PDF 路线务必有 `论文/数模论文.pdf`，且 >= 20000 bytes；DOCX 路线务必有 `论文/数模论文.docx`（>= 15000 bytes）和 `论文/docx_report.json`
- PDF 页数务必 > 0；有页数上限的 DOCX 赛制务必通过 LibreOffice 预览 PDF 获得页数
- PDF 不应早于 `论文/论文正文.tex`；DOCX 报告必须对应当前 `论文/论文正文.md`
- 若 `图表/全部结果.json` 更新过，PDF 不应明显陈旧
- 匿名、页数、图形与表格嵌入、模板完整性是当前阶段重点
- CUMCM 摘要按标签核验不超过 1 页，正文按 `BodyStart/BodyEnd` 核验不超过 30 页；附录不计入正文页数
- 论文源文件中严禁残留明显的队号/队员/指导老师等匿名性破坏标记
- 务必有 `论文/编译日志.log`，且不含明显的 undefined reference / citation、LaTeX 致命数学错误、Undefined control sequence
- 编译后的论文源仍应保留正文引用和参考文献条目
- 最终审计身份与结果 JSON 精确一致；摘要与论文表达卡语义一致且保持自然学术表达
- 最终数据预处理叙述、处理后文件哈希和模型代码读取路径务必一致

## Baseline vs Enhancement

- `baseline`：先满足上面全部硬门禁，不改七步结构
- `enhancement`：准许在不破坏门禁和产物契约的前提下增强子 Agent、复核链和自动化核验

## 落盘证据

每一次 `gate_check` 后，推荐在工作区留存：

- `审查/门禁/{工作名称}.json`
- `状态/工作流状态.json`
- `状态/事件日志.jsonl`

这样断点续跑时可基于磁盘证据而不是记忆判定是否放行。

