\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{mcmicm}[2026/07/11 Meta-model-agent COMAP MCM/ICM class]
\LoadClass[12pt,letterpaper]{article}
\RequirePackage[letterpaper,margin=1in,headheight=15pt]{geometry}
\RequirePackage[T1]{fontenc}
\RequirePackage{lmodern}
\RequirePackage{amsmath,amssymb,amsthm,mathtools}
\RequirePackage{graphicx,booktabs,longtable,tabularx,array,multirow}
\RequirePackage{float,placeins,caption,subcaption}
\RequirePackage{xcolor,enumitem,listings,algorithm2e}
\RequirePackage{fancyhdr,lastpage,hyperref,url}
\RequirePackage[numbers,sort&compress]{natbib}
\hypersetup{colorlinks=true,linkcolor=black,citecolor=blue!55!black,urlcolor=blue!60!black,pdfauthor={Anonymous MCM/ICM Team}}
\setlength{\parindent}{2em}
\setlength{\parskip}{0pt}
\linespread{1.08}
\captionsetup{font=small,labelfont=bf,labelsep=period}
\setlist{nosep,leftmargin=*}
\lstset{basicstyle=\small\ttfamily,breaklines=true,frame=single,numbers=left,numberstyle=\tiny,showstringspaces=false}
\newcommand{\MCMControlNumber}{[CONTROL NUMBER]}
\newcommand{\MCMProblem}{[A--F]}
\newcommand{\MCMPaperTitle}{[PAPER TITLE]}
\newcommand{\controlnumber}[1]{\renewcommand{\MCMControlNumber}{#1}}
\newcommand{\problemchoice}[1]{\renewcommand{\MCMProblem}{#1}}
\newcommand{\papertitle}[1]{\renewcommand{\MCMPaperTitle}{#1}}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{Team \MCMControlNumber}
\fancyhead[R]{Problem \MCMProblem}
\fancyfoot[C]{Page \thepage\ of \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\newenvironment{summarysheet}{%
  \thispagestyle{empty}\begin{center}
  {\Large\bfseries MCM/ICM Summary Sheet\par}\vspace{1em}
  {\large Control Number: \MCMControlNumber\hfill Problem: \MCMProblem\par}\vspace{1.5em}
  {\LARGE\bfseries \MCMPaperTitle\par}\vspace{1.5em}
  \end{center}\section*{Summary}
}{\clearpage}
\newcommand{\keywords}[1]{\par\medskip\noindent\textbf{Keywords:} #1\par}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{proposition}{Proposition}
\theoremstyle{definition}\newtheorem{definition}{Definition}
