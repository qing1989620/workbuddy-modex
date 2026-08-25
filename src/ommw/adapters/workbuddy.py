"""WorkBuddy adapter (Rule 17-18).

Installs a thin SKILL.md wrapper into the WorkBuddy skills directory. The
wrapper only contains frontmatter + a pointer to the repo's master skill
(skills/mathematical-modeling-workflow/SKILL.md). Business logic stays in the
repo; no second copy drifts.

Symlink strategy with fallback (Rule 18):
  symlink -> junction (Windows) -> thin copy of the wrapper only.
The wrapper always references the repo by absolute path resolved at install
time (stored in config.local.toml, git-ignored) so the core itself stays
portable.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from ..config import Config, detect_workbuddy_skills_dir
from ..paths import core_root


WRAPPER_NAME = "mathematical-modeling-workflow-ommw"


@dataclass
class InstallResult:
    ok: bool
    skill_dir: Path | None = None
    method: str = ""  # symlink | junction | copy
    message: str = ""


class WorkbuddyAdapter:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.skills_dir = detect_workbuddy_skills_dir(cfg)
        self.core_skill = core_root() / "skills" / "mathematical-modeling-workflow"

    def detect(self) -> dict:
        return {
            "skills_dir": str(self.skills_dir) if self.skills_dir else None,
            "core_skill": str(self.core_skill),
            "core_skill_exists": self.core_skill.exists(),
            "platform": sys.platform,
        }

    def install(self) -> InstallResult:
        if not self.skills_dir:
            return InstallResult(ok=False, message="WorkBuddy skills dir not detected")
        if not self.core_skill.exists():
            return InstallResult(ok=False, message=f"master skill missing: {self.core_skill}")
        target = self.skills_dir / WRAPPER_NAME
        # Try symlink first.
        if self._try_symlink(target):
            return InstallResult(ok=True, skill_dir=target, method="symlink",
                                 message="installed via symlink")
        if os.name == "nt" and self._try_junction(target):
            return InstallResult(ok=True, skill_dir=target, method="junction",
                                 message="installed via junction")
        # Fallback: thin wrapper copy (references repo, does not duplicate logic).
        self._write_wrapper(target)
        return InstallResult(ok=True, skill_dir=target, method="copy",
                             message="installed via thin wrapper copy")

    def _try_symlink(self, target: Path) -> bool:
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                return True
            return False
        try:
            os.symlink(self.core_skill, target, target_is_directory=True)
            return True
        except (OSError, NotImplementedError):
            return False

    def _try_junction(self, target: Path) -> bool:
        if target.exists():
            return False
        try:
            subprocess_cmd = ["cmd", "/c", "mklink", "/J", str(target), str(self.core_skill)]
            import subprocess
            r = subprocess.run(subprocess_cmd, capture_output=True, text=True, timeout=15)
            return r.returncode == 0 and target.exists()
        except Exception:
            return False

    def _write_wrapper(self, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        wrapper = target / "SKILL.md"
        repo = core_root().as_posix()
        wrapper.write_text(
            "---\n"
            f"name: {WRAPPER_NAME}\n"
            "title: Open Mathematical Modeling Workflow (OMMW)\n"
            "summary: Portable, anti-hallucination competition-modeling workflow with LaTeX + Word dual output.\n"
            "---\n\n"
            "# OMMW (WorkBuddy thin wrapper)\n\n"
            "This is a thin wrapper installed by `ommw install-adapter workbuddy`. The real\n"
            "orchestrator lives in the repo and is the single source of truth.\n\n"
            f"- Repo core: `{repo}`\n"
            f"- Master skill: `{repo}/skills/mathematical-modeling-workflow/SKILL.md`\n\n"
            "Load the master skill from the repo path above. Do NOT duplicate its logic here.\n\n"
            "## Invocation\n\n"
            "> 调用数学建模工作流完成当前题目。\n\n"
            "Supported modifiers: LaTeX/Word/Dual mode, strict/quick/competition/research rigor.\n"
            "See `docs/workbuddy.md` for the full contract.\n",
            encoding="utf-8",
        )
