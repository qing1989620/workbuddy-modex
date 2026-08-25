# LaTeX Mode

## Pipeline
- Agent writes `paper/latex/sections/*.tex` directly (not a one-shot conversion).
- Per-chapter incremental: draft -> audit -> add to LaTeX -> compile -> inspect
  log -> fix -> recompile -> chapter pass (Rule 37).
- Engine: `xelatex` default (CJK-safe via `xeCJK`). Configurable in
  `config.local.toml [latex] engine`.
- TeX Live bin is auto-detected and prepended to PATH **for the subprocess only**
  (never mutates global PATH, Rule 39).

## Compile-or-not-done
"PDF ready" requires a clean build with **zero undefined citations**. `ommw render`
parses the `.log` for fatal errors, undefined references, and undefined citations;
any of those fails the render (Rule 109).

## CJK
`xeCJK` + `SimSun`/`SimHei`/`FangSong`. The generic template
(`templates/latex/main.tex`) is CJK-safe. Competition profiles may override.

## TeX Live detection
`ommw doctor` looks for `latexmk`/`xelatex` in:
1. `config.local.toml [latex] texlive_root` (or `TEXLIVE_HOME`)
2. common install roots (`/usr/local/texlive`, `/usr`, `/opt/homebrew`, Windows defaults)
3. PATH fallback

## Troubleshooting
- `LATEX:texlive FAIL` -> set `TEXLIVE_HOME` or `[latex] texlive_root` in
  `config.local.toml`.
- Undefined citation -> the `\cite{}` key has no verified `S-xxx` source. Run
  `ommw citations verify`.
- `LATEX FAILED` but `RESEARCH VERIFIED` -> a renderer failure, not a research
  failure. Fix the `.tex`; the evidence is still valid.
