# adapters/workbuddy

Thin WorkBuddy skill wrapper installed by `ommw install-adapter workbuddy`.

## What it does
Creates `~/.workbuddy/skills/mathematical-modeling-workflow-ommw/` containing a
thin `SKILL.md` that points at the repo's master skill
(`skills/mathematical-modeling-workflow/SKILL.md`). Business logic stays in the
repo; no second copy drifts (Rule 17).

## Install strategy (Rule 18)
1. **symlink** (preferred, cross-platform where permitted)
2. **junction** (Windows, when symlink needs privilege)
3. **thin copy** of the wrapper only (fallback; still references the repo)

The wrapper records the repo's absolute path at install time into
`config.local.toml` (git-ignored) so the core itself stays portable.

## Detecting the real WorkBuddy environment
`ommw doctor` probes (no guessing from forum posts):
- user-level skills dir (`~/.workbuddy/skills`)
- project-level skills dir (`<repo>/.workbuddy/skills`)
- SKILL.md frontmatter presence
- the reload mechanism is the host's responsibility; reinstall after edits.

## Usage after install
> 调用数学建模工作流完成当前题目。

See `docs/workbuddy.md` for the full invocation contract.
