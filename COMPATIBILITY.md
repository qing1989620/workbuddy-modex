# Compatibility

OMMW follows Semantic Versioning with a workflow-contract twist:

- **MAJOR** bump: the workflow contract or state schema changes in a way that
  breaks existing modeling projects. Old projects must run `ommw migrate`.
- **MINOR** bump: new backward-compatible capability. Old projects keep working.
- **PATCH** bump: bug fix.

## Project binding

Every OMMW project records `schema_version` and `workflow_version` in
`workspace/state/project.yaml`. On open, `ommw status` compares these against
the installed OMMW and refuses to silently mutate an incompatible project.

## Migration

```
migrations/
  v1_to_v2/
  v2_to_v3/
```

Run `ommw migrate` to bring an older project forward. Migrations are
idempotent and write a backup of `state/` before mutating.

## Tested matrix

Each release declares the matrix actually tested (see the release notes). The
v0.1 target matrix:

| Axis | Range |
|---|---|
| OS | Windows 10/11, Ubuntu 22.04/24.04 (macOS best-effort) |
| Python | 3.12, 3.13 |
| TeX Live | 2025, 2026 |
| Pandoc | >= 3.1 |
| LibreOffice | >= 7.5 (optional) |
| Agent runtime | WorkBuddy (validated); Claude Code / Codex (community) |

Claims of support outside the tested matrix are not made.
