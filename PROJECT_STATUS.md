# PROJECT STATUS — Open Mathematical Modeling Workflow (OMMW) v0.1.0

Verification date: 2026-08-25 (Windows 11, TeX Live 2026, Python 3.13.14)
Honesty rule (spec §183): items not actually verified are marked `NOT VERIFIED`, never guessed.

## ROOT
First-time dev location on a Windows machine (path withheld for privacy; the
portable core contains no machine-specific paths — abs-path scan PASS). Git
initialized; first commit `e9e540b`, 94 tracked files, no secrets.

## PORTABLE CORE
VERIFIED. `src/ommw` Python package: config (env>local>auto), paths (pure pathlib),
atomic writes, Pydantic state schemas, doctor, verify, parity, citations, renderers,
adapters, CLI. Cross-platform; CJK + spaces path tested.

## LICENSE
VERIFIED. Core = MIT (`LICENSE`, `NOTICE`). Third parties in
`THIRD_PARTY_NOTICES.md` + `provenance/SOURCES.lock.json`. MathModelAgent kept
external (non-commercial); no restrictive source re-licensed into core.

## WORKBUDDY ADAPTER
VERIFIED. `ommw install-adapter workbuddy` installed via symlink to
`~/.workbuddy/skills/mathematical-modeling-workflow-ommw/` (thin wrapper -> repo
master skill). symlink/junction/copy fallback implemented.

## OTHER AGENT ADAPTERS
PARTIAL. Adapter framework in `adapters/`; only WorkBuddy implemented in v0.1.
Claude Code / Codex = community-supported (documented contract), NOT VERIFIED.

## MATHMODELAGENT PROVIDER
VERIFIED (as isolated external). `providers/mathmodelagent/{README,provider.toml,
detect.py,adapter.py}` — adapter only, no upstream source. Core works without it
(proven by `tests/integration/test_core_without_providers.py`). Audit in
`provenance/audits/mathmodelagent.md`.

## SCIENTIFIC SKILLS
PARTIAL. `providers/scientific-skills/` declares pinned commit `36d8f13` +
per-skill license policy; fetch-on-demand logic ready. NOT VERIFIED: no actual
network fetch performed yet (intentionally off by default).

## PYTHON ENVIRONMENT
VERIFIED. `pyproject.toml` + `.python-version` (3.13). Editable install in `.venv2`;
imports ok (ommw/typer/pydantic/python-docx/yaml/requests). `uv.lock` NOT generated
(uv not installed on this machine) — NOT VERIFIED reproducibility via `uv sync --frozen`.

## LATEX
TeX Live: 2026 (auto-detected at runtime; not hardcoded in core).
Engine: xelatex (CJK-safe via xeCJK).
Smoke build: VERIFIED — `ommw smoke-test` produced `paper/latex/output/main.pdf`
(14 KB, clean compile, zero undefined citations). `ommw init` + `ommw render` also
produces a compiling PDF.

## WORD
Pandoc: NOT INSTALLED on this machine -> Word mode DEGRADED (WARN).
python-docx: VERIFIED installed; `verify_docx` structural QA implemented + tested.
LibreOffice: NOT INSTALLED -> visual QA NOT VERIFIED (graceful degrade to
`VISUAL_QA: NOT_VERIFIED`, never falsely claimed).
Smoke build: NOT VERIFIED end-to-end (pandoc absent). `reference.docx` template
generated (36 KB). Structural QA unit-tested.

## DUAL PARITY
VERIFIED (logic). `ommw parity` compares claim/result/citation/figure/table/
equation/chapter fingerprints; writes `dist/parity-report.json`. Smoke dual mode
reports `parity: PASS`. Note: LaTeX fingerprint from compiled `.tex`, Word
fingerprint from `.md` sources (no pandoc needed for parity itself).

## CITATION SYSTEM
VERIFIED (logic). Two-tier: metadata (Crossref) vs claim verification. Offline
mode marks `UNVERIFIED_OFFLINE`. `ommw citations verify` implemented. Network to
Crossref reachable (doctor NETWORK: PASS).

## EXPERIMENT SYSTEM
VERIFIED. `experiments.jsonl` with data_hash + code_hash + metrics + seed;
staleness via dependency graph documented. Smoke records a real experiment.

## CI
PARTIAL. `.github/workflows/{ci,release}.y` defined (Windows+Ubuntu, lint+pytest+
portability+secret-scan+abs-path+fresh-machine smoke, actions pinned to versions).
NOT VERIFIED: not executed on GitHub (no remote push performed).

## PORTABILITY
Windows: VERIFIED (this machine, incl. CJK+spaces path test).
Linux: NOT VERIFIED locally (CI matrix covers it; not run here).
macOS: NOT VERIFIED (best-effort; no environment).

## EVALS
VERIFIED (anti-hallucination). `tests/hallucination` (6 tests) + smoke negative
injection: unresolved-result, unresolved-source, unverified-citation,
orphan-number, placeholder-leak — all caught. Prompt-probe discipline documented
in `references/anti-hallucination.md`.

## SECURITY AUDIT
VERIFIED (core). Skill trust levels defined; MathModelAgent audit done (P0/P1 none).
Secret-scan pattern defined in CI. Untrusted-data boundary documented. No
vendored unaudited code.

## LICENSE AUDIT
VERIFIED. `THIRD_PARTY_NOTICES.md` + `provenance/SOURCES.lock.json` record every
third party with license + trust level. No `REVIEW REQUIRED` open items in core.

## OPEN RISKS
- `uv.lock` not committed (uv absent on dev machine) -> reproducibility via
  `uv sync --frozen` NOT VERIFIED. Mitigation: `pyproject.toml` pins ranges; CI
  installs with `uv sync`.
- Word end-to-end not run (no pandoc/LibreOffice locally).
- macOS untested.
- scientific-skills not actually fetched.
- No remote GitHub repo yet (local git only).

## GITHUB READINESS
PARTIAL. Repo is git-initialized, licensed, documented, tested, CI-defined,
secret-free, abs-path-free. BLOCKED on: pushing to a remote (requires owner
action) and generating `uv.lock` + a real GitHub Actions run.

## NEW COMPUTER INSTALL COMMANDS
Windows:
```
git clone <repo> && cd <repo>
.\scripts\bootstrap.ps1
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```
Linux/macOS:
```
git clone <repo> && cd <repo>
./scripts/bootstrap.sh
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```

## HOW TO USE
After `ommw install-adapter workbuddy`, in a WorkBuddy session at your
competition workspace:
> 调用数学建模工作流完成当前题目。
> 调用数学建模工作流，LaTeX 模式，严格完成.
> 调用数学建模工作流，Dual 模式完成，并做两种格式一致性审计.

Modifiers: mode=latex|word|dual; rigor=quick|strict|competition|research; --offline.

## ACCEPTANCE CHECKLIST (§182) — honest status
- Repository exists: VERIFIED (local git)
- Core has valid license: VERIFIED
- No secrets committed: VERIFIED
- No personal absolute paths: VERIFIED (abs-path scan PASS)
- Master Skill valid: VERIFIED
- WorkBuddy adapter validated: VERIFIED
- Fresh-machine bootstrap validated: PARTIAL (fresh temp dir + clean venv; no real remote clone)
- Windows Chinese-path test passed: VERIFIED
- Python dependencies locked: NOT VERIFIED (uv.lock missing)
- MathModelAgent isolated as external provider: VERIFIED
- Scientific skills provenance recorded: VERIFIED (declared; not fetched)
- Research Core implemented: VERIFIED
- Result ledger implemented: VERIFIED
- Citation ledger implemented: VERIFIED
- Claim ledger implemented: VERIFIED
- Experiment ledger implemented: VERIFIED
- LaTeX renderer works: VERIFIED
- DOCX renderer works: NOT VERIFIED (pandoc absent; logic + structural QA tested)
- reference.docx works: VERIFIED (generated; python-docx postprocessor tested)
- LaTeX compile test passes: VERIFIED
- DOCX structural test passes: VERIFIED (unit test)
- Dual parity test passes: VERIFIED (logic)
- Anti-hallucination tests pass: VERIFIED
- Negative tests pass: VERIFIED
- GitHub CI exists: VERIFIED (defined; not run)
- README quickstart works: VERIFIED (doctor/smoke/init/render executed)
- Doctor works: VERIFIED
- No unresolved CRITICAL finding: VERIFIED

---

## v0.2 Paper Production Kernel (2026-08-26)

Honesty rule maintained: only actually-executed items are VERIFIED.

- Paper Production Kernel (contract/density/gates/scorecard): VERIFIED
  (`src/ommw/paper/`, `ommw doctor` check `PAPER:kernel` PASS)
- demo4 postmortem (audits/paper-production-postmortem.md): VERIFIED
  (empty-ledger vacuous pass root-caused; 4 CRITICAL regression reproduced)
- Upgrade baseline (upgrade-baseline.md): VERIFIED (KEEP/IMPROVE/NEW/… map)
- 10 paper-production evals (evals/paper-production/): VERIFIED (10/10 PASS,
  eval-report.json)
- Smoke test with 5 negative injections: VERIFIED (OVERALL PASS, all caught)
- pytest full suite: VERIFIED (46/46 PASS)
- CUMCM template import (cumcmthesis, CJK main file): VERIFIED
  (real xelatex compile PASS, 5-page stress demo PASS)
- MCM/ICM template import (mcmthesis): VERIFIED
  (real xelatex compile PASS, bibtex completion pass, 4-page stress demo PASS)
- Template registry + roles + comparison report: VERIFIED
  (template-registry.json, templates/local/reports/*)
- Doctor: VERIFIED (PAPER:kernel / TEMPLATES:local-registry PASS;
  PAPER:production-evals PASS after evals landed)
- Master skill routing + 6 v0.2 policy references: VERIFIED (written; symlink
  `~/.workbuddy/skills/mathematical-modeling-workflow-ommw` intact)
- DOCX renderer: still NOT VERIFIED (pandoc absent — unchanged from v0.1;
  non-blocking, Word pipeline DEGRADED)

### v0.2 open risks
- Template "verified" reflects compile only; template quality beyond
  compilability (e.g. layout aesthetics) is demo-covered, not judged.
- pandoc/LibreOffice absent => Word side not e2e-verified on this machine.
- Gate thresholds (250 words, min 2 equations, 88 score) are engineering
  defaults; calibrate against real papers over time.

