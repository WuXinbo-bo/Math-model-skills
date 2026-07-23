# 环境配置说明

本文说明 Meta-model-agent 的完整运行环境。除特别说明外，命令均从仓库根目录执行。

项目包含两类运行路径：

- Codex Skill 与 Python 状态机：负责初始化、阶段推进、门禁和审稿；
- 初始化后复制到研究工作区的工具：负责建模计算、绘图、LaTeX 编译、DOCX 导出和质量检查。

仅运行状态机所需依赖很少，但完成整个数学建模与论文交付流程还需要科学计算库和对应输出路线的系统工具。

## 依赖分层

| 层级 | 依赖 | 使用场景 |
| --- | --- | --- |
| 核心 | Python 3.8+、pip | 初始化、状态管理、门禁、审稿 |
| 常用建模 | NumPy、Pandas、SciPy、scikit-learn、statsmodels、NetworkX | 数据处理、预测、评价、优化、统计分析和图论 |
| 绘图 | Matplotlib、Seaborn、SciencePlots、adjustText | 数据图、诊断图、标签避让和论文图形 |
| 表格数据 | openpyxl、xlrd | 读取 `.xlsx` 和 `.xls` 附件 |
| PDF 路线 | XeLaTeX、BibTeX、TeX 宏包、Bash、GNU 工具 | LaTeX 编译与提交质量检查 |
| DOCX 路线 | python-docx、Pillow、pypdf；页数检查需要 LibreOffice | Word 导出、图片尺寸和页数门禁 |
| 流程图 | DrawIO Desktop CLI，或 XeLaTeX/TikZ | `.drawio` 或 TikZ 技术路线图 |
| 视觉核验 | Poppler (`pdftoppm`) | 将 PDF 图形渲染为 PNG 进行检查 |

Pandoc 只用于 `references/runtime_reference/` 中的参考运行时集成，不是默认七阶段工作流的必需依赖。

## Python 环境

推荐使用独立虚拟环境。Python 3.8 是最低基线，建议使用仍受上游科学计算库支持的 Python 3.10 或 3.11。

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r scripts/requirements.txt
```

如果 PowerShell 阻止激活脚本，可以不激活环境，直接运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r scripts/requirements.txt
```

安装后验证公共 Python 环境：

```bash
python -c "import numpy, pandas, scipy, sklearn, statsmodels, networkx, matplotlib, seaborn, openpyxl, docx, PIL, pypdf; print('python dependencies: ready')"
python scripts/workspace_init.py --help
python scripts/stage_executor.py --help
```

`assets/shared-scripts/plot_utils.py` 在 SciencePlots 或 adjustText 缺失时会尝试运行 pip。使用完整 `requirements.txt` 预先安装它们，可以避免执行阶段临时联网和环境漂移。

## PDF / LaTeX 路线

PDF 路线至少要求以下命令可从 `PATH` 调用：

```text
xelatex
bibtex
kpsewhich
bash
python3
```

模板和检查脚本使用的主要 TeX 能力包括：

- `ctex`、`fontspec`、`xeCJK`；
- `amsmath`、`amssymb`、`mathtools`、`bm`；
- `graphicx`、`xcolor`、`booktabs`、`longtable`、`tabularx`、`multirow`；
- `tikz`/PGF、`algorithm2e`、`listings`；
- `geometry`、`caption`、`subcaption`、`placeins`、`needspace`；
- `hyperref`、`cleveref`、`natbib`、`lmodern`、`mdframed`。

为减少缺包导致的编译中断，推荐安装完整 TeX Live；Windows 也可以使用启用“自动安装缺失宏包”的 MiKTeX。精简 TeX Live 环境至少需要 XeTeX、中文语言包、LaTeX Extra、Science 和 BibTeX Extra 组件。

### Debian / Ubuntu 示例

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git bash curl \
  texlive-xetex texlive-lang-chinese texlive-latex-extra texlive-science \
  texlive-bibtex-extra fonts-noto-cjk fontconfig poppler-utils
```

### macOS 示例

```bash
brew install python git poppler grep gnu-sed coreutils findutils gawk
brew install --cask mactex-no-gui
```

仓库脚本使用 `grep -P` 和 GNU 风格的 `sed -i`。macOS 自带的 BSD grep/sed 可能不兼容，需要把 Homebrew 的 GNU 命令目录放到 `PATH`，例如：

```bash
export PATH="$(brew --prefix grep)/libexec/gnubin:$(brew --prefix gnu-sed)/libexec/gnubin:$(brew --prefix coreutils)/libexec/gnubin:$(brew --prefix findutils)/libexec/gnubin:$PATH"
```

安装 TeX 或修改 `PATH` 后需要重新打开终端。

### Windows

建议安装：

1. Python 3；
2. Git for Windows，并使用 Git Bash 运行仓库内的 `.sh` 检查脚本；也可以使用配置完整的 WSL；
3. TeX Live 或 MiKTeX；
4. Poppler for Windows，用于提供 `pdftoppm`；
5. 确保上述工具的 `bin` 目录位于 `PATH`。

仓库的 Shell 检查脚本使用 `python3`、`grep`、`sed`、`awk`、`find`、`wc`、`head`、`tail`、`sort`、`tr` 和 `cut`。在 Windows 中，仅有 PowerShell 不足以运行这些脚本；应在 Git Bash 或 WSL 内确认 `python3 --version` 可用。

### LaTeX 自检

```bash
xelatex --version
bibtex --version
kpsewhich ctex.sty
kpsewhich tikz.sty
kpsewhich algorithm2e.sty
kpsewhich cleveref.sty
python3 --version
```

任一 `kpsewhich` 命令没有输出，表示对应宏包尚未安装或 TeX 搜索路径未生效。

## 字体

- 绘图工具优先使用系统中文字体，并包含 `assets/shared-scripts/NotoSansSC-Regular.ttf` 作为回退；
- CUMCM 和 51MCM 模板目录包含所需的宋体/楷体文件，但仍应检查模板中的实际字体路径；
- MCM/ICM 模板使用 Latin Modern；
- Windows 通常已有 Times New Roman、宋体和微软雅黑；
- macOS/Linux 若缺少模板指定字体，应安装兼容字体或在最终人工核验后调整模板字体配置。

Linux 可以使用以下命令检查中文字体：

```bash
fc-list :lang=zh | head
```

## DOCX 路线

Python 包由 `scripts/requirements.txt` 安装。基本 DOCX 可以直接生成，但需要页数门禁的竞赛必须安装 LibreOffice，因为导出器会调用 `soffice` 或 `libreoffice` 生成 PDF 预览。

```bash
soffice --version
```

macOS 可以使用 Homebrew 安装 LibreOffice；Debian/Ubuntu 可以安装 `libreoffice` 软件包；Windows 需要将 LibreOffice 的 `program` 目录加入 `PATH`。

初始化和导出示例：

```bash
python scripts/workspace_init.py --workspace ../contest-workspace --competition cumcm --output-format docx
python "../contest-workspace/工具/docx_export.py" --workspace ../contest-workspace
```

导出完成后应同时存在：

```text
论文/数模论文.docx
论文/docx_report.json
```

## DrawIO、TikZ 与视觉核验

DrawIO 路线需要安装 DrawIO Desktop，并使以下命令之一可用：

```text
draw.io.exe   # Windows 常见名称
drawio        # Linux 常见名称
draw.io       # 部分安装方式
```

若不使用 DrawIO，可以使用 XeLaTeX/TikZ 生成结构图。需要视觉检查 PDF 时安装 Poppler，并验证：

```bash
pdftoppm -h
```

DrawIO CLI 的典型导出方式：

```bash
drawio --export --format pdf --crop --output 图表/技术路线图.pdf 图表/技术路线图.drawio
```

实际命令名称应按本机安装结果替换。

## 按题目安装的可选依赖

以下库不属于所有赛题的共同环境，不写入默认 `requirements.txt`：

| 场景 | 可选依赖 |
| --- | --- |
| 线性/整数/约束优化 | `PuLP`、`OR-Tools`、`CVXPY`、`gurobipy` |
| 遗传算法与元启发式 | `DEAP` |
| 地理空间分析 | `geopandas`、`shapely`、`pyproj`、`osmnx` |
| 梯度提升与解释 | `xgboost`、`lightgbm`、`shap` |
| 时间序列扩展 | `pmdarima` |
| 深度学习 | `torch` 或 `tensorflow`/`keras` |

按模型方案只安装实际使用的库，例如：

```bash
python -m pip install PuLP
python -m pip install geopandas
```

Gurobi 等商业求解器还需要独立许可证和本地运行时，安装 Python 包并不代表求解器已经可用。

## Git、Codex 与参考运行时

- 从 GitHub 配置全局 Skill 时需要 Git 和网络访问；
- 安装 Python 包、检索外部数据和核验 DOI/BibTeX 时需要访问 PyPI、GitHub 或对应原始数据源；
- Codex 必须能够访问目标研究工作区并执行本地命令；
- 写作规则可选使用环境变量 `SCHOLAR_SCRIPT` 指向外部 `scholar_fetch.py`；未配置时应使用原始文献页面、Crossref 或人工方式获取并核验 BibTeX；
- `references/runtime_reference/` 是参考实现，依赖外部 `config`、`services`、Agent 可执行文件，可能还需要 Pandoc；它不是本仓库默认 CLI 的直接入口；
- 默认工作流不要求 Node.js、Docker、Jupyter 或 GPU。

## 环境自检

### PowerShell

```powershell
$commands = 'git','python','bash','xelatex','bibtex','kpsewhich','pdftoppm','soffice','drawio'
foreach ($command in $commands) {
  $resolved = Get-Command $command -ErrorAction SilentlyContinue | Select-Object -First 1
  [pscustomobject]@{ Command = $command; Available = [bool]$resolved; Path = $resolved.Source }
}
```

### Bash

```bash
for command in git python3 bash xelatex bibtex kpsewhich pdftoppm soffice drawio; do
  if command -v "$command" >/dev/null 2>&1; then
    printf '%-12s %s\n' "$command" "$(command -v "$command")"
  else
    printf '%-12s %s\n' "$command" "MISSING"
  fi
done
```

并执行 Python 导入检查：

```bash
python -c "import numpy, pandas, scipy, sklearn, statsmodels, networkx, matplotlib, seaborn, openpyxl, xlrd, docx, PIL, pypdf, scienceplots, adjustText; print('python environment: ready')"
```

## 常见问题

### `python` 可用但 `python3` 不可用

Python CLI 可以继续使用 `python`，但仓库内 Bash 检查脚本调用 `python3`。请在 Git Bash/WSL/macOS/Linux 中安装或配置 `python3` 命令，避免只在 PowerShell 中创建临时别名。

### XeLaTeX 能启动但模板缺包

优先安装完整 TeX 发行版；精简安装时根据编译日志和 `kpsewhich <package>.sty` 补充宏包。不要通过删除模板中的宏包引用来绕过编译错误。

### DOCX 已生成但页数为空

确认 `soffice` 或 `libreoffice` 位于 `PATH`，并检查 `论文/docx_preview/` 是否产生 PDF。页数受限竞赛缺少预览时不能通过最终门禁。

### 中文图形出现方框

确认初始化后的工作区包含 `工具/NotoSansSC-Regular.ttf`；在 Linux 上同时检查 `fontconfig` 和 `fc-list :lang=zh` 输出。
