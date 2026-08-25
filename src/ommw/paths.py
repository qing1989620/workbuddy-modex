"""Path resolution. Pure pathlib, no string concatenation of OS paths.

The portable core must run unchanged on Windows / Linux / macOS, including
paths with spaces, non-ASCII (CJK) characters, and mixed separators.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


def core_root() -> Path:
    """Return the OMMW repository root (where this package's parent repo lives).

    Resolved by walking up from this file: src/ommw/paths.py -> src/ommw -> src
    -> <repo root>. Overridable via OMMW_HOME for relocated/installed copies.
    """
    env = os.environ.get("OMMW_HOME")
    if env:
        return Path(env).expanduser().resolve()
    # src/ommw/paths.py -> up three = repo root
    return Path(__file__).resolve().parents[2]


def core_dir(*parts: str) -> Path:
    """Resolve a path inside the OMMW core (skills, templates, providers, ...)."""
    return core_root().joinpath(*parts)


@dataclass(frozen=True)
class ProjectPaths:
    """Filesystem layout of a single modeling project workspace.

    A project is independent of the OMMW core: it can live anywhere, including
    paths with spaces and CJK characters. The workspace holds the Research Core
    (state) and the per-renderer paper sources.
    """

    root: Path

    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    @property
    def data_raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def data_interim(self) -> Path:
        return self.root / "data" / "interim"

    @property
    def data_processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def code_dir(self) -> Path:
        return self.root / "code"

    @property
    def figures_dir(self) -> Path:
        return self.root / "figures"

    @property
    def tables_dir(self) -> Path:
        return self.root / "tables"

    @property
    def paper_dir(self) -> Path:
        return self.root / "paper"

    @property
    def latex_dir(self) -> Path:
        return self.paper_dir / "latex"

    @property
    def word_dir(self) -> Path:
        return self.paper_dir / "word"

    @property
    def dist_dir(self) -> Path:
        return self.root / "dist"

    @property
    def build_dir(self) -> Path:
        return self.root / ".build"

    @property
    def cache_dir(self) -> Path:
        return self.root / ".cache"

    # --- state files ---
    @property
    def project_yaml(self) -> Path:
        return self.state_dir / "project.yaml"

    @property
    def progress_json(self) -> Path:
        return self.state_dir / "progress.json"

    @property
    def claims_path(self) -> Path:
        return self.state_dir / "claims.jsonl"

    @property
    def results_path(self) -> Path:
        return self.state_dir / "results.jsonl"

    @property
    def sources_path(self) -> Path:
        return self.state_dir / "sources.jsonl"

    @property
    def experiments_path(self) -> Path:
        return self.state_dir / "experiments.jsonl"

    @property
    def figures_index(self) -> Path:
        return self.state_dir / "figures.jsonl"

    @property
    def tables_index(self) -> Path:
        return self.state_dir / "tables.jsonl"

    @property
    def assumptions_path(self) -> Path:
        return self.state_dir / "assumptions.yaml"

    @property
    def notation_path(self) -> Path:
        return self.state_dir / "notation.yaml"

    @property
    def capabilities_path(self) -> Path:
        return self.state_dir / "capabilities.json"

    def ensure_dirs(self) -> None:
        """Create the canonical project directory tree (idempotent)."""
        for p in (
            self.state_dir,
            self.data_raw,
            self.data_interim,
            self.data_processed,
            self.code_dir,
            self.figures_dir,
            self.tables_dir,
            self.paper_dir,
            self.latex_dir,
            self.latex_dir / "sections",
            self.latex_dir / "figures",
            self.latex_dir / "tables",
            self.latex_dir / "bibliography",
            self.latex_dir / "output",
            self.word_dir,
            self.word_dir / "sections",
            self.dist_dir,
            self.build_dir,
            self.cache_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)


def is_portable_path(p: Path) -> bool:
    """Heuristic: True if a path string contains no machine-specific absolute root.

    Used by the portability test to reject hardcoded paths like D:\\ or
    /Users/<someone> committed into the core. Handles both POSIX and Windows
    string forms (a Path may stringify with either separator depending on OS).
    """
    s = str(p).replace("\\", "/").lower()
    # Windows drive roots and POSIX home roots are non-portable.
    if len(s) >= 2 and s[1] == ":" and s[0].isalpha():
        return False
    if s.startswith("/users/") or s.startswith("/home/") or s.startswith("/c/users"):
        return False
    return True


def native(path: Path) -> str:
    """Return a path as a native OS string (for subprocess invocation)."""
    return str(path)


def quote_for_subprocess(path: Path) -> str:
    """Quote a path for the current OS shell."""
    s = str(path)
    if sys.platform.startswith("win"):
        # Wrap in double quotes if it contains spaces; escape embedded quotes.
        if " " in s or "\t" in s:
            return '"' + s.replace('"', '\\"') + '"'
        return s
    # POSIX: use shlex
    import shlex

    return shlex.quote(s)
