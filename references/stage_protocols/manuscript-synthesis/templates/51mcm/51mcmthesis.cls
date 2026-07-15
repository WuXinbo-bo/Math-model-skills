\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{51mcmthesis}[2025/04/26 v1.0 Standard LaTex Template for 51MCM]

% %% Inital Code
\newif\if@mcm@bwprint\@mcm@bwprintfalse
\newif\if@mcm@preface\@mcm@prefacetrue

%% Declaration of Options
\DeclareOption{colorprint}{\@mcm@bwprintfalse}
\DeclareOption{bwprint}{\@mcm@bwprinttrue}
\DeclareOption{withoutpreface}{\@mcm@prefacefalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}

%% Executing of Options
\ExecuteOptions{colorprint}
\ProcessOptions\relax

\LoadClass[a4paper,12pt]{article}

\RequirePackage{ifxetex}
\RequireXeTeX
\ifxetex\else
    \ClassError{51mcmthesis}{XeTeX is required}{}\fi

% Required packages
\RequirePackage{ctex}
% 页面布局
\RequirePackage{geometry}
% 数学宏包
\RequirePackage{amsmath}
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage{bm}
%\RequirePackage{titletoc}
% 设置颜色
\RequirePackage{xcolor}
% 插入图片
\RequirePackage{graphicx}
\RequirePackage{float}
% 表格
\RequirePackage{array}
%% 长表格
\RequirePackage{longtable}
%% booktabs 提供了\toprule 等命令.
\RequirePackage{booktabs,tabularx}
%% multirow 支持在表格中跨行
\RequirePackage{multirow}
%% 调整间隔, 让表格更好看些
\RequirePackage{bigstrut}
%% 在跨行表格中输入定界符
\RequirePackage{bigdelim}
% 保护脆落命令
\RequirePackage{cprotect}
% 设置代码环境
\RequirePackage{listings}
\RequirePackage{xcolor}
% 插入链接
\RequirePackage{url}

% 绘图的包
%\RequirePackage{tikz}
%\usetikzlibrary{snakes}

% 字图与子标题
\RequirePackage{subcaption}
\RequirePackage[titles]{tocloft}
%\renewcommand{\cftdot}{$\cdot$}
%\renewcommand{\cftsecdotsep}{1.5}
\renewcommand{\cftsecdotsep}{4.5}
\setlength{\cftbeforesecskip}{7pt}
\setlength{\cftbeforesubsecskip}{3pt}
%\setlength{\cftbeforesubsecskip}{5pt}
\renewcommand{\cftsecfont}{\bfseries\zihao{-4}\heiti}
\renewcommand{\cftsecleader}{\cftdotfill{\cftsecdotsep}}
\renewcommand{\cftsecaftersnumb}{\hskip.4em}

\RequirePackage{fontspec}

\definecolor{dkgreen}{rgb}{0,0.6,0}
\definecolor{gray}{rgb}{0.5,0.5,0.5}
\definecolor{mauve}{rgb}{0.58,0,0.82}

\lstset{
  frame=tb,
  aboveskip=3mm,
  belowskip=3mm,
  showstringspaces=false,
  columns=flexible,
  framerule=1pt,
  rulecolor=\color{gray!35},
  backgroundcolor=\color{gray!5},
  basicstyle={\small\ttfamily},
  numbers=none,
  numberstyle=\tiny\color{gray},
  keywordstyle=\color{blue},
  commentstyle=\color{dkgreen},
  stringstyle=\color{mauve},
  breaklines=true,
  breakatwhitespace=true,
  tabsize=3,
}
% 首行缩进
\RequirePackage{setspace}
% 设置浮动体的标题
\RequirePackage{caption}
% 定制列表环境
\RequirePackage{enumitem}
% 下划线
\RequirePackage{ulem}
% 尺寸计算
\RequirePackage{calc}
\RequirePackage{caption}

\RequirePackage[titletoc,title]{appendix}

%\RequirePackage[title,toc,titletoc]{appendix}

\RequirePackage{etoolbox}
\AtBeginEnvironment{thebibliography}{%
    \phantomsection
    \addcontentsline{toc}{section}{\refname}
    }

\RequirePackage{hyperref}
\RequirePackage{cleveref}

\geometry{top=25.4mm,bottom=25.4mm,left=30.8mm,right=26.8mm} % 页面布局 上:25.4mm, 下:25.4mm, 左:30.8mm, 右:26.8mm

% 4. 字号定义
\newcommand{\erhao}{\zihao{2}\selectfont}      % 二号
\newcommand{\xiaoerhao}{\zihao{-2}\selectfont}  % 小二号
\newcommand{\sanhao}{\zihao{3}\selectfont}  % 三号
\newcommand{\xiaosanhao}{\zihao{-3}\selectfont}  % 小三号
\newcommand{\sihao}{\zihao{4}\selectfont}       % 四号
\newcommand{\xiaosihao}{\zihao{-4}\selectfont}  % 小四号
\newcommand{\wuhao}{\zihao{5}\selectfont}    % 五号
\newcommand{\xiaowuhao}{\zihao{-5}\selectfont}   % 小五号
\newcommand{\liuhao}{\zihao{6}\selectfont}  % 六号
\newcommand{\qihao}{\zihao{-6}\selectfont}    % 七号


\newcommand{\wordline}[1]{%
    \setlength{\baselineskip}{#1\f@size pt}%
}


\renewcommand\normalsize{%
    \@setfontsize\normalsize{12}{12}%
    \abovedisplayskip 12\p@ \@plus3\p@ \@minus7\p@
    \abovedisplayshortskip \z@ \@plus3\p@
    \belowdisplayshortskip 6.5\p@ \@plus3.5\p@ \@minus3\p@}

% 数学环境, 定理等设置
\newtheorem{definition}{\mcm@cap@definition}
\newtheorem{theorem}{\mcm@cap@theorem}
\newtheorem{lemma}{\mcm@cap@lemma}
\newtheorem{corollary}{\mcm@cap@corollary}
\newtheorem{assumption}{\mcm@cap@assumption}
\newtheorem{conjecture}{\mcm@cap@conjecture}
\newtheorem{axiom}{\mcm@cap@axiom}
\newtheorem{principle}{\mcm@cap@principle}
\newtheorem{problem}{\mcm@cap@problem}
\newtheorem{example}{\mcm@cap@example}
\newtheorem{proof}{\mcm@cap@proof}
\newtheorem{solution}{\mcm@cap@solution}

% 浮动环境设置
% 默认情况下, \LaTeX{} 要求每页的文字至少占据 20%,否则该页就只单独放置一个浮动环境,
% 而这通常不是我们想要的, 我们将这个要求降低到 5%.
\renewcommand*{\textfraction}{0.05}
% 有时如果多个浮动环境连续放在一起, \LaTeX{}
% 会将它们分在几个不同页，即使它们可在同一页放
% 得下. 我们可以通过修改 |\topfraction| 和 |\bottomfraction| 分别设置顶端和底端的浮
% 动环境的最大比例.
\renewcommand*{\topfraction}{0.9}
\renewcommand*{\bottomfraction}{0.8}
% 有时\LaTeX{}会把一个浮动环境单独放在一页,
% 我们要求这个环境至少要占据 85% 才能单独放在一页.
% 注意:  |\floatpagefraction| 的数值必须小于 |\topfraction|.
\renewcommand*{\floatpagefraction}{0.85}

% 关于图片 graphicx
% 如果图片没有指定后缀, 依次按下列顺序搜索
\DeclareGraphicsExtensions{.pdf,.eps,.jpg,.png}
% 设置图表搜索路径, 可以给图表文件夹取如下名字
\graphicspath{{figures/}{figure/}{pictures/}%
    {picture/}{pic/}{pics/}{image/}{images/}}

% 定义存储内容的命令
\newcommand{\tihao}[1]{\def\@tihao{#1}}
\newcommand{\duihao}[1]{\def\@duihao{#1}}
\newcommand{\zubie}[1]{\def\@zubie{#1}}
\newcommand{\schoolname}[1]{\def\@schoolname{#1}}
\newcommand{\membera}[1]{\def\@membera{#1}}
\newcommand{\memberb}[1]{\def\@memberb{#1}}
\newcommand{\memberc}[1]{\def\@memberc{#1}}
\newcommand{\email}[1]{\def\@email{#1}}
\newcommand{\phone}[1]{\def\@phone{#1}}
\newcommand\mcm@tokens@keywords{}

% 设置字体
\setmainfont{Times New Roman}
%\setmonofont{Courier New}
\setsansfont{Arial}
\setCJKfamilyfont{kai}[Path=./,AutoFakeBold]{simkai.ttf}
\newcommand*{\kai}{\CJKfamily{kai}}
\setCJKfamilyfont{song}[Path=./,AutoFakeBold]{simsun.ttc}
\newcommand*{\song}{\CJKfamily{song}}
\renewcommand{\songti}{\CJKfamily{song}}
\setCJKfamilyfont{yahei}[Path=./,AutoFakeBold]{simsun.ttc}
\newcommand{\yahei}{\CJKfamily{yahei}}
\setCJKfamilyfont{heiti}[Path=./,AutoFakeBold]{simsun.ttc}
\renewcommand{\heiti}{\CJKfamily{heiti}}
\setCJKfamilyfont{fangsong}[Path=./,AutoFakeBold,AutoFakeSlant]{simsun.ttc}
\renewcommand{\fangsong}{\CJKfamily{fangsong}}

\newcommand{\stextbf}[1]{{\songti\bfseries #1}}

% 6. 文档环境
\AtBeginDocument{%
    \setlength{\parindent}{2em}% 首行缩进两字符
}

% 中文标题名称设置
\renewcommand\contentsname{\mcm@cap@contentsname}
\renewcommand\listfigurename{\mcm@cap@listfigurename}
\renewcommand\listtablename{\mcm@cap@listtablename}
\renewcommand\refname{\mcm@cap@refname}
\renewcommand\indexname{\mcm@cap@indexname}
\renewcommand\figurename{\mcm@cap@figurename}
\renewcommand\tablename{\mcm@cap@tablename}
\renewcommand\appendixname{\mcm@cap@appendixname}
\renewcommand\abstractname{\mcm@cap@abstractname}


% 中文标题格式设置
% 目录深度
\setcounter{secnumdepth}{3}
% 节标题格式, 居中, 使用\chinese命令修改计数器
\def\@seccntformat#1{\csname the#1\endcsname\ }
\renewcommand\thesection{\chinese{section}、}
\renewcommand\thesubsection{\arabic{section}\thinspace.\thinspace\arabic{subsection}}
\renewcommand\thesubsubsection{\thesubsection\thinspace.\thinspace\arabic{subsubsection}}
\renewcommand\section{\@startsection{section}{1}{\z@}%
  {-2ex \@plus -1ex \@minus -.2ex}%
  {2.3ex \@plus.2ex}%
  {\centering\sihao\bfseries\heiti}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
    {-1ex\@plus -1ex \@minus -.2ex}%
    {1.5ex \@plus .2ex}%
    {\heiti\xiaosihao}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
    {-1ex\@plus -1ex \@minus -.2ex}%
    {1.5ex \@plus .2ex}%
    {\heiti\xiaosihao}}
\renewcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
    {3.25ex \@plus1ex \@minus.2ex}%
    {-1em}%
    {\normalfont\normalsize\bfseries}}
\renewcommand\subparagraph{\@startsection{subparagraph}{5}{\parindent}%
    {3.25ex \@plus1ex \@minus .2ex}%
    {-1em}%
    {\normalfont\normalsize\bfseries}}


\setlist[enumerate]{
    topsep=0\baselineskip,    % 环境前后垂直间距
    partopsep=0\baselineskip, % 分段时额外增加的间距
    itemsep=0\baselineskip,   % 各 \item 之间的垂直间距
    parsep=0pt                  % 段落间距（通常设为 0）
}
\setlist[itemize]{
    topsep=0\baselineskip,    % 环境前后垂直间距
    partopsep=0\baselineskip, % 分段时额外增加的间距
    itemsep=0\baselineskip,   % 各 \item 之间的垂直间距
    parsep=0pt                  % 段落间距（通常设为 0）
}
\DeclareCaptionFont{song}{\songti}
\DeclareCaptionFont{minusfour}{\zihao{-4}}
\captionsetup[figure]{%
    format=hang,   % 标题从第二行开始都有缩进, 应该和 justification=raggedright 的效果一样.
    labelsep=quad, % 分隔符是一个空格
    font={song,minusfour,bf}, % 图的字体, 宋体小四
    position=bottom % position=bottom, 不代表标题放在下面, 标题仍放在你放\caption的位置.
}
\captionsetup[table]{%
    format=hang,   % 标题从第二行开始都有缩进, 应该和 justification=raggedright 的效果一样.
    labelsep=quad, % 分隔符是一个空格
    font={song,minusfour,bf}, % 表的字体, 宋体小四
    position=top % position=bottom, 不代表标题放在下面, 标题仍放在你放\caption的位置.
}

\pdfstringdefDisableCommands{%
	\def\cftdotfill{ }%
}
\lstnewenvironment{tcode}
  {
    \lstset{basicstyle = \small\ttfamily\fangsong,
        language=TeX,
        tabsize = 4,
        frame = single,
        escapechar = `,
        breaklines = true,
        breakatwhitespace = true,
        frameround = tttt,
    }
  }
  {}

%%% crefformat settings
\crefformat{figure}{#2图~#1#3}
\crefrangeformat{figure}{图~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{figure}{图~(#2#1#3)}{和~(#2#1#3)}{，(#2#1#3)}{和~(#2#1#3)}

\crefformat{table}{#2表#1#3}
\crefrangeformat{table}{表(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{table}{表~(#2#1#3)}{和~(#2#1#3)}{，(#2#1#3)}{和~(#2#1#3)}

\crefformat{equation}{#2~(#1#3)}
\crefrangeformat{equation}{~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{equation}{~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{definition}{#2\mcm@cap@definition~#1#3}
\crefrangeformat{definition}{\mcm@cap@definition~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{definition}{\mcm@cap@definition~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{theorem}{#2\mcm@cap@theorem~#1#3}
\crefrangeformat{theorem}{\mcm@cap@theorem~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{theorem}{\mcm@cap@theorem~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{lemma}{#2\mcm@cap@lemma~#1#3}
\crefrangeformat{lemma}{\mcm@cap@lemma~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{lemma}{\mcm@cap@lemma~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{corollary}{#2\mcm@cap@corollary~#1#3}
\crefrangeformat{corollary}{\mcm@cap@corollary~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{corollary}{\mcm@cap@corollary~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{assumption}{#2\mcm@cap@assumption~#1#3}
\crefrangeformat{assumption}{\mcm@cap@assumption~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{assumption}{\mcm@cap@assumption~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{conjecture}{#2\mcm@cap@conjecture~#1#3}
\crefrangeformat{conjecture}{\mcm@cap@conjecture~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{conjecture}{\mcm@cap@conjecture~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{axiom}{#2\mcm@cap@axiom~#1#3}
\crefrangeformat{axiom}{\mcm@cap@axiom~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{axiom}{\mcm@cap@axiom~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{principle}{#2\mcm@cap@principle~#1#3}
\crefrangeformat{principle}{\mcm@cap@principle~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{principle}{\mcm@cap@principle~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{problem}{#2\mcm@cap@problem~#1#3}
\crefrangeformat{problem}{\mcm@cap@problem~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{problem}{\mcm@cap@problem~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{example}{#2\mcm@cap@example~#1#3}
\crefrangeformat{example}{\mcm@cap@example~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{example}{\mcm@cap@example~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{proof}{#2\mcm@cap@proof~#1#3}
\crefrangeformat{proof}{\mcm@cap@proof~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{proof}{\mcm@cap@proof~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}

\crefformat{solution}{#2\mcm@cap@solution~#1#3}
\crefrangeformat{solution}{\mcm@cap@solution~(#3#1#4)\;\~{}\;(#5#2#6)}
\crefmultiformat{solution}{\mcm@cap@solution~(#2#1#3)}{ 和~(#2#1#3)}{，(#2#1#3)}{ 和~(#2#1#3)}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\def\@maketitle{
    \if@mcm@preface
    \thispagestyle{empty}
    {
        \begin{center}
            \yahei\xiaoerhao\noindent 五一数学建模竞赛\\
            \yahei\sanhao\noindent 承\quad 诺\quad 书 \\
        \end{center}
        \vspace*{-1em}
        \CommitmentDeclaration
        \clearpage
    }
    \setcounter{page}{1}
    {
        \begin{center}
            {\yahei\xiaoerhao\textbf{五 \! 一 \! 数 \! 学 \! 建 \! 模 \! 竞 \! 赛}}\\[8pt]
            \includegraphics[width=3.95cm,height=3.18cm]{51mcm.png} \\[3em]
            {\songti\sanhao
            \textbf{题 \! 目：}
            \underline{\makebox[18em][c]{\heiti\sanhao\bfseries \@title}}%
            }
        \end{center}
    }
    \else
    \fi
}
%% 定义摘要环境
\renewenvironment{abstract}{
    \noindent
    \if@twocolumn
        \section*{\abstractname}%
    \else
        {\xiaosihao\bfseries\songti 摘\quad 要：}%
        \quotation
    \fi
}

\RequirePackage{environ}

\NewEnviron{kwabstract}[1]{
    \noindent
    {\begin{center}\xiaosihao\bfseries\songti 摘\quad 要\end{center}}%
    \quotation
    \BODY
    \endquotation
    \keywords{#1}
    \par\medskip
}



% {\if@twocolumn\else\endquotation\newpage\null\fi}
\renewenvironment{quotation}

{\list{}{\listparindent 2em%
        \itemindent \listparindent
        \rightmargin\z@
        \leftmargin\z@
        \parsep \z@ \@plus\p@}%
    \item\relax}
{\endlist}

\newcommand\keywords[1]{%
\renewcommand{\mcm@tokens@keywords}{#1} \par

\noindent\textbf{\xiaosihao\songti 关键词：}~{\xiaosihao\songti\bfseries \mcm@tokens@keywords} \\[0.5em]
}
% 7. 承诺书命令
\newcommand{\CommitmentDeclaration}{%
    % 首行缩进
    \setlength{\parindent}{2em}% 首行缩进两字符
    % \setlength{\baselineskip}{18pt}%行距1.5倍
    \wordline{1.5}
    \songti\xiaosihao\par
    我们仔细阅读了五一数学建模竞赛的竞赛规则。\par
    我们完全明白，在竞赛开始后参赛队员不能以任何方式（包括电话、电子邮件、网上咨询等）与本队以外的任何人（包括指导教师）研究、讨论与赛题有关的问题。\par
    我们知道，抄袭别人的成果是违反竞赛规则的, 如果引用别人的成果或其它公开的资料（包括网上查到的资料），必须按照规定的参考文献的表述方式在正文引用处和参考文献中明确列出。\par
    我们郑重承诺，严格遵守竞赛规则，以保证竞赛的公正、公平性。如有违反竞赛规则的行为，我们愿意承担由此引起的一切后果。\par
    我们授权五一数学建模竞赛组委会，可将我们的论文以任何形式进行公开展示（包括进行网上公示，在书籍、期刊和其他媒体进行正式或非正式发表等）。\par
    % 正文内容
    参赛题号（从A/B/C中选择一项填写）：\underline{\makebox[12.5em][c]{\@tihao}}\par
    参赛队号：\underline{\makebox[25em][c]{\@duihao}}\par
    参赛组别（研究生、本科、专科、高中）：\underline{\makebox[11.5em][c]{\@zubie}}\par
    所属学校（学校全称）：\underline{\makebox[19.5em][c]{\@schoolname}}\par
    参赛队员：
    队员1姓名：\underline{\makebox[16.2em][c]{\@membera}}\par
    \hspace*{5em}队员2姓名：\underline{\makebox[16.2em][c]{\@memberb}}\par
    \hspace*{5em}队员3姓名：\underline{\makebox[16.2em][c]{\@memberc}}\par
    联系方式：Email：\underline{\makebox[11.48em][c]{\@email}}\quad
    联系电话：\underline{\makebox[8.75em][c]{\@phone}}\par
    \begin{flushright}
        日期：\underline{\makebox[2em][c]{\the\year}}年
        \underline{\makebox[2em][c]{\the\month}}月
        \underline{\makebox[2em][c]{\the\day}}日
    \end{flushright}


    % 页底
    \vfill
    \songti\sihao\centering\textbf{（除本页外不允许出现学校及个人信息）}
}

\renewenvironment{thebibliography}[1]
{\section*{\refname}%
    \@mkboth{\MakeUppercase\refname}{\MakeUppercase\refname}%
    \list{\@biblabel{\@arabic\c@enumiv}}%
    {\settowidth\labelwidth{\@biblabel{#1}}%
        \leftmargin\labelwidth
        \advance\leftmargin\labelsep
        \@openbib@code
        \usecounter{enumiv}%
        \let\p@enumiv\@empty
        \renewcommand\theenumiv{\@arabic\c@enumiv}}%
    \sloppy
    \clubpenalty4000
    \@clubpenalty \clubpenalty
    \widowpenalty4000%
    \sfcode`\.\@m}
{\def\@noitemerr
    {\@latex@warning{Empty `thebibliography' environment}}%
    \endlist}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%数学定理相关的常量
\newcommand*{\mcm@cap@definition}{定义}
\newcommand*{\mcm@cap@theorem}{定理}
\newcommand*{\mcm@cap@lemma}{引理}
\newcommand*{\mcm@cap@corollary}{推论}
\newcommand*{\mcm@cap@assumption}{假设}
\newcommand*{\mcm@cap@conjecture}{猜想}
\newcommand*{\mcm@cap@axiom}{公理}
\newcommand*{\mcm@cap@principle}{定律}
\newcommand*{\mcm@cap@problem}{问题}
\newcommand*{\mcm@cap@example}{例}
\newcommand*{\mcm@cap@proof}{证明}
\newcommand*{\mcm@cap@solution}{解}
%%%  中文标题名称
\newcommand*{\mcm@cap@contentsname}{目录}
\newcommand*{\mcm@cap@listfigurename}{插图清单}
\newcommand*{\mcm@cap@listtablename}{附表清单}
\newcommand*{\mcm@cap@refname}{参考文献}
\newcommand*{\mcm@cap@indexname}{索引}
\newcommand*{\mcm@cap@figurename}{图}
\newcommand*{\mcm@cap@tablename}{表}
\newcommand*{\mcm@cap@appendixname}{附录}
\newcommand*{\mcm@cap@abstractname}{摘要}
