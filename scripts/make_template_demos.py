"""Stress-test demos for locally imported LaTeX templates (spec §73).

For every registry entry whose compile status is PASS/WARN this script
generates a ``template-demo.tex`` next to the audited main tex, exercising:
abstract, keywords, display-equation groups, matrices, two figures (asset +
TikZ flowchart doubling as the algorithm diagram), a three-line table,
citations and an appendix -- then compiles it with the REAL local engine via
``ommw.templates_local.compile_smoke`` and writes a report under
``templates/local/reports/``. Registry gains ``features.stress_demo``.

Usage:  python scripts/make_template_demos.py [--templates-dir templates]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ommw.config import detect_texlive_bin, load_config  # noqa: E402
from ommw.templates_local import (  # noqa: E402
    REGISTRY_NAME, compile_smoke, find_main_tex, load_registry)

DEMO_MCM = r"""%% Stress-test demo for mcmthesis (generated; spec section 73)
\documentclass{mcmthesis}
\mcmsetup{tstyle=\color{black}\bfseries,
        tcn = 0000, problem = A,
        sheet = true, titleinsheet = true, keywordsinsheet = true,
        titlepage = false, abstract = true}
\usepackage{txfonts}
\usepackage{indentfirst}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}
\title{Stress-Test Demo: Model Integration and Sensitivity Analysis}
\author{Team 0000}
\date{\today}
\begin{document}
\begin{abstract}
This summary exercises the abstract slot of the template with a compact
narrative: we formulate an optimization--simulation pipeline, prove the
fixed-point existence of its inner solver, quantify uncertainty with 1000
Monte Carlo replications, and report a 12.4\% MAE improvement over the
baseline (R1). Results anchor on ledger experiment R1.
\begin{keywords}
stress test; sensitivity; Monte Carlo
\end{keywords}
\end{abstract}
\maketitle
\tableofcontents
\newpage

\section{Model formulation}
The objective couples a quadratic loss with an $L_1$ penalty:
\begin{equation}
\min_{\beta}\; L(\beta) = \frac{1}{2n}\sum_{i=1}^{n}\bigl(y_i-x_i^{\top}\beta\bigr)^2+\lambda\lVert\beta\rVert_1.
\label{eq:obj}
\end{equation}
For fixed $\lambda$ the inner solve is a contraction when $\rho(L)<1$:
\begin{align}
u^{(k+1)} &= (I-\alpha L)^{-1}\bigl(\alpha f + u^{(k)}\bigr), \label{eq:iter}\\
\therefore\quad \|u^{(k+1)}-u^\star\| &\le \rho^{k}\,\|u^{(0)}-u^\star\|. \label{eq:rate}
\end{align}

\subsection{Piecewise response and matrix form}
\begin{equation}
g(t)=
\begin{cases}
t^2, & t<0,\\
\sin t, & t\ge 0,
\end{cases}
\qquad
A=\begin{pmatrix} a_{11} & a_{12} \\ a_{21} & a_{22} \end{pmatrix},\;
\Sigma=\begin{bmatrix} \sigma_1^2 & 0 \\ 0 & \sigma_2^2 \end{bmatrix}.
\label{eq:piecewise}
\end{equation}

\section{Experiments}
Figure~\ref{fig:asset} shows the bundled asset render; the pipeline is
summarized by Figure~\ref{fig:flow}. Table~\ref{tab:cmp} compares accuracy.

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.55\textwidth]{example-image-a}
  \caption{Bundled asset figure rendered through the class.}
  \label{fig:asset}
\end{figure}

\begin{figure}[htbp]
  \centering
  \begin{tikzpicture}[node distance=9mm,>=Stealth]
    \node[draw, rounded corners, fill=blue!8]   (data) {data intake};
    \node[draw, below of=data, fill=green!8]    (fit)  {fit model \eqref{eq:obj}};
    \node[draw, diamond, aspect=2, below of=fit, fill=red!8] (ok) {converged?};
    \node[draw, below of=ok, fill=gray!8]       (out)  {report};
    \draw[->] (data) -- (fit);
    \draw[->] (fit) -- (ok);
    \draw[->] (ok) -- node[right]{yes} (out);
    \draw[->] (ok.east) -| node[pos=0.25,above]{no, damp $\alpha$} (fit.east);
  \end{tikzpicture}
  \caption{Algorithm flow: iterative solve with damping fallback.}
  \label{fig:flow}
\end{figure}

\begin{table}[htbp]
  \centering
  \caption{Baseline versus proposed (ledger R1).}
  \label{tab:cmp}
  \begin{tabular}{lcc}
    \hline
    model & MAE & RMSE \\
    \hline
    baseline & 0.161 & 0.204 \\
    proposed & \textbf{0.141} & \textbf{0.183} \\
    \hline
  \end{tabular}
\end{table}

As shown in Table~\ref{tab:cmp}, the gain in \eqref{eq:rate} transfers into a
12.4\% MAE reduction (experiment R1).
\cite{turing1950} discusses computability context for the iteration.

\begin{ReportAiUse}{OpenAI ChatGPT}
We used the assistant to polish wording only; all derivations and code were
authored by the team and verified against ledger results.
\end{ReportAiUse}

\appendix
\section{Additional derivation}
Substituting \eqref{eq:iter} into \eqref{eq:rate} yields the stated bound.

\begin{thebibliography}{99}
\bibitem{turing1950} Turing A M. Computing machinery and intelligence[J].
  \textit{Mind}, 1950, 59(236): 433--460.
\bibitem{box2015} Box G E P, Jenkins G M, Reinsel G C, et al. Time Series
  Analysis[M]. 5th ed. Hoboken: Wiley, 2015.
\end{thebibliography}
\end{document}
"""

DEMO_CUMCM = r"""% !TEX program = xelatex
%% 国赛 cumcmthesis 压力测试 demo（自动生成，规格 73 节）
\documentclass[withoutpreface,bwprint]{cumcmthesis}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning}
\title{基于迭代收缩的水库调度优化模型}
\author{参赛队号}
\date{}
\begin{document}
\begin{abstract}
本文针对水库调度问题建立了迭代收缩优化模型。首先将调度目标写成二次损失加正则项的形式，其次证明了内层迭代的收敛性，最后通过一千次蒙特卡洛仿真给出灵敏度分析，MAE 相对基线下降 12.4\%（实验 R1）。全部数值锚定台账实验记录。
\keywords{迭代收缩；蒙特卡洛；灵敏度分析}
\end{abstract}
\maketitle
\tableofcontents
\newpage

\section{模型建立}
目标函数由经验损失与正则项构成：
\begin{equation}
\min_{\beta}\; L(\beta)=\frac{1}{2n}\sum_{i=1}^{n}\bigl(y_i-x_i^{\top}\beta\bigr)^2+\lambda\lVert\beta\rVert_1.
\label{eq:obj}
\end{equation}
当谱半径 $\rho(L)<1$ 时，内层迭代是压缩映射：
\begin{align}
u^{(k+1)}&=(I-\alpha L)^{-1}\bigl(\alpha f+u^{(k)}\bigr),\label{eq:iter}\\
\therefore\quad \|u^{(k+1)}-u^\star\|&\le\rho^{k}\,\|u^{(0)}-u^\star\|.\label{eq:rate}
\end{align}

\subsection{分段响应与矩阵形式}
\begin{equation}
g(t)=
\begin{cases}
t^{2}, & t<0,\\
\sin t, & t\ge 0,
\end{cases}
\qquad
A=\begin{pmatrix} a_{11} & a_{12}\\ a_{21} & a_{22}\end{pmatrix},\;
\Sigma=\begin{bmatrix}\sigma_1^{2} & 0\\ 0 & \sigma_2^{2}\end{bmatrix}.
\label{eq:piecewise}
\end{equation}

\section{实验与结果}
图~\ref{fig:asset} 为模板自带素材渲染，图~\ref{fig:flow} 给出算法流程，
表~\ref{tab:cmp} 汇总精度对比。

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.5\textwidth]{figures/example}
  \caption{模板自带图片资源渲染测试。}
  \label{fig:asset}
\end{figure}

\begin{figure}[htbp]
  \centering
  \begin{tikzpicture}[node distance=9mm,>=Stealth]
    \node[draw, rounded corners, fill=blue!8]   (data) {数据接入};
    \node[draw, below of=data, fill=green!8]    (fit)  {求解式~\eqref{eq:obj}};
    \node[draw, diamond, aspect=2, below of=fit, fill=red!8] (ok) {收敛？};
    \node[draw, below of=ok, fill=gray!8]       (out)  {输出报告};
    \draw[->] (data) -- (fit);
    \draw[->] (fit) -- (ok);
    \draw[->] (ok) -- node[right]{是} (out);
    \draw[->] (ok.east) -| node[pos=0.25,above]{否，调小 $\alpha$} (fit.east);
  \end{tikzpicture}
  \caption{带阻尼回退的迭代求解算法流程图。}
  \label{fig:flow}
\end{figure}

\begin{table}[htbp]
  \centering
  \caption{基线与所提模型的精度对比（台账 R1）。}
  \label{tab:cmp}
  \begin{tabular}{lcc}
    \hline
    模型 & MAE & RMSE \\
    \hline
    基线 & 0.161 & 0.204 \\
    本文模型 & \textbf{0.141} & \textbf{0.183} \\
    \hline
  \end{tabular}
\end{table}

如表~\ref{tab:cmp} 所示，式~\eqref{eq:rate} 的收敛率优势转化为 12.4\% 的
MAE 下降（对应台账实验 R1）。\cite{turing1950}

\newpage
\appendix
\section{补充推导}
将式~\eqref{eq:iter} 代入式~\eqref{eq:rate} 即得所述上界。

\begin{thebibliography}{9}
\bibitem{turing1950} Turing A M. Computing machinery and intelligence[J].
  Mind, 1950, 59(236): 433--460.
\end{thebibliography}
\end{document}
"""


def _pages_from_log(log_text: str) -> int:
    m = re.search(r"Output written on .+?\((\d+) page", log_text)
    return int(m.group(1)) if m else 0


def stress_demo(templates_root: Path) -> int:
    cfg = load_config()
    if not detect_texlive_bin(cfg):
        print("BLOCKED: TeX Live not found")
        return 1
    reg = load_registry(templates_root)
    reports = templates_root / "local" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    failures = 0
    for tid, d in reg.items():
        if d.get("compile_status") not in ("PASS", "WARN"):
            print(f"{tid}: skip ({d.get('compile_status')})")
            continue
        staging = templates_root / "local" / "staging" / tid
        main = find_main_tex(staging)
        if not main:
            print(f"{tid}: no main tex, skip")
            continue
        cls = d.get("document_class", "")
        body = DEMO_CUMCM if "cumcm" in cls else DEMO_MCM
        demo = main.parent / "template-demo.tex"
        demo.write_text(body, encoding="utf-8")
        status, cmd, warns, pdf = compile_smoke(demo, d.get("required_engine") or "xelatex",
                                                cfg)
        pages = 0
        logp = main.parent / "_compile_test" / "template-demo.log"
        if logp.exists():
            pages = _pages_from_log(logp.read_text(encoding="utf-8", errors="ignore"))
        size_kb = round(pdf.stat().st_size / 1024, 1) if pdf and pdf.exists() else 0
        ok = status in ("PASS", "WARN") and pages > 0
        if not ok:
            failures += 1
        feat = d.setdefault("features", {})
        feat["stress_demo"] = {"status": status, "pages": pages, "kb": size_kb}
        # persist updated features back into registry
        reg[tid] = d
        lines = [
            f"# Template Demo Stress Test — {tid}", "",
            f"- generated: `{demo.name}` (spec §73 checklist)",
            "- covers: abstract, keywords, equation group, cases, pmatrix/bmatrix,",
            "  asset figure, TikZ flowchart (=algorithm diagram), three-line table,",
            "  citations, appendix",
            f"- engine: **{d.get('required_engine')}**, status: **{status}**",
            f"- output PDF: {'YES' if pdf and pdf.exists() else 'NO'} "
            f"({pages} pages, {size_kb} KB)",
            f"- command: `{cmd}`",
        ]
        lines += [f"- warning: {w}" for w in warns]
        if not ok:
            lines.append("- NOT VERIFIED: demo failed to compile.")
        out = reports / f"template-demo-{tid}.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        from ommw.templates_local import save_registry
        save_registry(reg, templates_root)
        print(f"{tid}: demo {status} ({pages} pages, {size_kb} KB)"
              + ("" if ok else "  <-- FAILED"))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates-dir", default=str(ROOT / "templates"))
    args = ap.parse_args()
    troot = Path(args.templates_dir)
    if not (troot / REGISTRY_NAME).exists():
        print(f"no registry at {troot / REGISTRY_NAME}; run template-import first")
        return 1
    return stress_demo(troot)


if __name__ == "__main__":
    raise SystemExit(main())
