# WorkBuddy Adapter

## Install

```
ommw install-adapter workbuddy
```

This installs a **thin** skill wrapper at
`~/.workbuddy/skills/mathematical-modeling-workflow-ommw/`. The wrapper only
contains frontmatter + a pointer to the repo's master skill. Business logic
lives in the repo; no second copy drifts.

Install strategy (best-effort, in order):
1. **symlink** (preferred)
2. **junction** (Windows, when symlink needs privilege)
3. **thin copy** of the wrapper only (fallback; still references the repo)

## Invocation contract

After install, in a WorkBuddy session at your competition workspace, say any of:

> 调用数学建模工作流完成当前题目。

> 调用数学建模工作流，LaTeX 模式，严格完成。

> 调用数学建模工作流，Word 模式，严格完成。

> 调用数学建模工作流，Dual 模式完成，并做两种格式一致性审计。

Modifiers:
- **mode**: latex | word | dual (default: read `project.yaml`, else ask once)
- **rigor**: quick | strict | competition | research (default: strict)
- **offline**: citation verification cache-only; misses `UNVERIFIED_OFFLINE`

## What the agent then does

1. `ommw doctor` -> write `state/capabilities.json` (honest capabilities only).
2. Drive the Problem State Machine (see `docs/workflow.md`), writing ledgers.
3. Enforce all eight anti-hallucination rules.
4. Render per mode; emit the final status block (never claiming unverified).

## Detecting the real environment

`ommw doctor` probes (no guessing from forum posts):
- user-level skills dir (`~/.workbuddy/skills`)
- project-level skills dir (`<repo>/.workbuddy/skills`)
- Python, TeX Live, Pandoc, LibreOffice, network, providers

If WorkBuddy skills dir is not auto-detected, set `WORKBUDDY_SKILLS_DIR` or
`config.local.toml [workbuddy] skills_dir`.

## Reload after edits

The reload mechanism is the host's responsibility. After editing the master
skill in the repo, re-run `ommw install-adapter workbuddy` to refresh the link.
