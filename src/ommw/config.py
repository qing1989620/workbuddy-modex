"""Configuration loading with strict precedence:

    CLI flag > environment variable > config.local.toml > auto-detect > defaults

No machine-specific paths are hardcoded. Empty values mean "auto-detect".
"""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from .paths import core_root


@dataclass
class LatexConfig:
    texlive_root: str = ""
    engine: str = "xelatex"


@dataclass
class WordConfig:
    pandoc_path: str = ""
    libreoffice_path: str = ""


@dataclass
class WorkbuddyConfig:
    skills_dir: str = ""


@dataclass
class ProviderConfig:
    enabled: bool = False
    path: str = ""
    commit: str = ""


@dataclass
class OutputConfig:
    default_mode: str = "latex"  # latex | word | dual
    default_rigor: str = "strict"  # quick | strict | competition | research


@dataclass
class Config:
    latex: LatexConfig = field(default_factory=LatexConfig)
    word: WordConfig = field(default_factory=WordConfig)
    workbuddy: WorkbuddyConfig = field(default_factory=WorkbuddyConfig)
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    output: OutputConfig = field(default_factory=OutputConfig)
    source: str = "defaults"  # where the loaded config came from

    def provider(self, name: str) -> ProviderConfig:
        return self.providers.get(name, ProviderConfig())


def _config_path() -> Path | None:
    """Resolve the local config path: OMMW_CONFIG env, else config.local.toml in core root."""
    env = os.environ.get("OMMW_CONFIG")
    if env:
        return Path(env).expanduser()
    candidate = core_root() / "config.local.toml"
    return candidate if candidate.exists() else None


def load_config() -> Config:
    """Load configuration honoring the documented precedence."""
    cfg = Config(source="defaults")

    # 1. local config file (lowest non-default layer)
    path = _config_path()
    if path and path.exists():
        with path.open("rb") as f:
            data = tomllib.load(f)
        cfg.source = str(path)
        if "latex" in data:
            cfg.latex = LatexConfig(**data["latex"])
        if "word" in data:
            cfg.word = WordConfig(**data["word"])
        if "workbuddy" in data:
            cfg.workbuddy = WorkbuddyConfig(**data["workbuddy"])
        if "output" in data:
            cfg.output = OutputConfig(**data["output"])
        for pname, pdata in data.get("providers", {}).items():
            cfg.providers[pname] = ProviderConfig(**pdata)

    # 2. environment variables override file values
    if v := os.environ.get("TEXLIVE_HOME"):
        cfg.latex.texlive_root = v
    if v := os.environ.get("PANDOC_PATH"):
        cfg.word.pandoc_path = v
    if v := os.environ.get("LIBREOFFICE_PATH"):
        cfg.word.libreoffice_path = v
    if v := os.environ.get("WORKBUDDY_SKILLS_DIR"):
        cfg.workbuddy.skills_dir = v

    return cfg


# ---------------------------------------------------------------------------
# Auto-detection helpers (used by doctor). Empty config values fall through
# to these. They never mutate global state.
# ---------------------------------------------------------------------------


def which(name: str) -> str | None:
    """shutil.which wrapper returning a native string or None."""
    found = shutil.which(name)
    return found if found else None


def detect_texlive_bin(cfg: Config) -> Path | None:
    """Locate a TeX Live bin directory containing latexmk/xelatex."""
    candidates: list[Path] = []
    if cfg.latex.texlive_root:
        root = Path(cfg.latex.texlive_root)
        candidates.extend(_texlive_bin_subdirs(root))
    # Common install locations (auto-detect only; never hardcoded into core logic).
    if sys.platform.startswith("win"):
        candidates += [
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "TeX Live",
        ]
        # `tlmgr --version` location
    else:
        candidates += [Path("/usr/local/texlive"), Path("/usr"), Path("/opt/homebrew")]

    for c in candidates:
        for b in _texlive_bin_subdirs(c):
            if (b / "latexmk").exists() or (b / "latexmk.exe").exists():
                return b
    # Fallback: PATH lookup
    for tool in ("latexmk", "xelatex"):
        found = which(tool)
        if found:
            return Path(found).resolve().parent
    return None


def _texlive_bin_subdirs(root: Path) -> list[Path]:
    """Given a TeX Live root, return candidate bin dirs (year/bin/<arch>)."""
    out: list[Path] = []
    if not root.exists():
        return out
    if (root / "bin").is_dir():
        # Layout: <root>/bin/windows, <root>/bin/x86_64-linux ...
        for sub in (root / "bin").iterdir():
            if sub.is_dir():
                out.append(sub)
    else:
        # Layout: <root>/2026/bin/windows
        for year in sorted(root.iterdir(), reverse=True):
            if year.is_dir() and (year / "bin").is_dir():
                for sub in (year / "bin").iterdir():
                    if sub.is_dir():
                        out.append(sub)
    return out


def detect_pandoc(cfg: Config) -> str | None:
    if cfg.word.pandoc_path:
        p = Path(cfg.word.pandoc_path)
        return str(p) if p.exists() else None
    return which("pandoc")


def detect_libreoffice(cfg: Config) -> str | None:
    if cfg.word.libreoffice_path:
        p = Path(cfg.word.libreoffice_path)
        return str(p) if p.exists() else None
    for n in ("soffice", "libreoffice"):
        found = which(n)
        if found:
            return found
    if sys.platform.startswith("win"):
        for base in (Path(os.environ.get("ProgramFiles", "C:/Program Files")),
                     Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))):
            cand = base / "LibreOffice" / "program" / "soffice.exe"
            if cand.exists():
                return str(cand)
    return None


def detect_workbuddy_skills_dir(cfg: Config) -> Path | None:
    if cfg.workbuddy.skills_dir:
        p = Path(cfg.workbuddy.skills_dir)
        return p if p.exists() else None
    # Auto-detect user-level then project-level.
    home = Path(os.path.expanduser("~")) / ".workbuddy" / "skills"
    if home.exists():
        return home
    proj = core_root() / ".workbuddy" / "skills"
    return proj if proj.exists() else None
