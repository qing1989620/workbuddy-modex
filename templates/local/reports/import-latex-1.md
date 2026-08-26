# Template Import Report — latex-1

- original archive: `国赛latex模板 (1).zip`
- sha256: `6515e9cc981fb1a4…`
- source: user provided (preserved under `raw/`, never modified)
- main tex: `国赛小班课定制模板\数模通用模板.tex`
- document class: `cumcmthesis`
- required engine: **xelatex**
- bibliography: bibtex
- encoding: utf-8/gbk-safe
- packages (7): ctex, etoolbox, mdframed, natbib, subcaption, tikz, url
- fonts referenced: none detected

## Inventory
- tex=1 cls/sty=1 bib=1 figures=1 fonts=4

## Features
- abstract_env: YES
- keywords: YES
- subfigure: YES
- longtable: no
- algorithm: no
- listings: no
- tikz: YES
- hyperref: no
- header_footer: no
- cover_page: YES
- color: no

## Section architecture (top-level)
- 引言
- 问题背景
- 研究意义
- 问题重述
- 总体分析
- 模型假设
- 符号说明
- 问题一的模型的建立和求解
- 具体分析
- 模型准备
- 模型建立
- 模型求解
- 问题二的模型的建立和求解
- 具体分析
- 模型准备
- 模型建立
- 模型求解
- 问题三的模型的建立和求解
- 具体分析
- 模型准备
- 模型建立
- 模型求解
- 问题四的模型的建立和求解
- 具体分析
- 模型准备
- 模型建立
- 模型求解
- 模型的分析与检验
- 灵敏度分析
- 误差分析

## Compile smoke test
- status: **PASS**
- command: `xelatex.exe -interaction=nonstopmode -halt-on-error -output-directory _compile_test _main_compile.tex`
- warning: LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.
- warning: Package caption Warning: Unused \captionsetup[sub] on input line 12.
- warning: Package hyperref Warning: Rerun to get /PageLabels entry.
- warning: Package rerunfilecheck Warning: File `_main_compile.out' has changed.
- verified at: 2026-08-26T21:10:58

## Competition suitability
- chinese support: True
- CUMCM (国赛) fit: high
- MCM/ICM (美赛) fit: medium

## Recommended usage
use as PRIMARY LaTeX base; main=国赛小班课定制模板\数模通用模板.tex; engine=xelatex

> Honesty rule: this file is generated from the ACTUAL extraction and > compile run; statuses PASS/WARN/FAIL/BLOCKED only.