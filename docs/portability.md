# Portability

OMMW must run unchanged on Windows / Linux / macOS, from any drive/path,
including paths with spaces and CJK characters. It is **not** a `D:\` project —
that is only where it was first developed.

## Rules
- Core uses `pathlib.Path` only. No string concatenation of OS paths.
- No machine-specific absolute paths committed (CI portability job enforces;
  scans for `C:\Users\`, `/Users/x/`, `/home/x/`, drive roots).
- TeX Live / Pandoc / LibreOffice / WorkBuddy paths live in git-ignored
  `config.local.toml` / `.env`, auto-detected at runtime.

## Precedence
```
CLI flag > environment variable > config.local.toml > auto-detect > defaults
```

Env vars: `OMMW_HOME`, `OMMW_CONFIG`, `TEXLIVE_HOME`, `PANDOC_PATH`,
`LIBREOFFICE_PATH`, `WORKBUDDY_SKILLS_DIR`, `CROSSREF_MAILTO`.

## Tested paths
- ASCII, spaces, CJK (`测试 工作区/数学建模案例`) — covered by
  `tests/portability/test_portability.py::test_smoke_runs_in_chinese_spaces_path`.

## Fresh machine
```bash
git clone <repo> && cd <repo>
./scripts/bootstrap.sh          # Linux/macOS   (.ps1 on Windows)
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```
No dependency on parent-directory hidden files. A clean `.venv` reproduces.

## Migration
`ommw migrate` brings an older project's state schema forward (idempotent, backs
up `state/` first). Projects bind to a workflow major version (see
`COMPATIBILITY.md`).
