"""Template Intake Pipeline (v0.2 upgrade, spec §4-§9).

Discovers user-provided LaTeX template archives, preserves them untouched
under ``templates/local/raw/``, extracts to ``staging/``, audits dependencies
/ fonts / engine, runs a REAL compile smoke test with the local TeX Live,
normalizes into ``normalized/<template_id>/``, writes a per-template report
plus a machine-readable registry at ``templates/template-registry.json``.

Iron rules honored:
  - originals are copied read-only; never modified;
  - no machine paths hardcoded -- engine discovery goes through
    ``config.detect_texlive_bin`` (env > local toml > PATH);
  - "Template verified" is ONLY written after an actual successful compile.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config, detect_texlive_bin

ARCHIVE_EXTS = {".zip", ".7z", ".rar"}
TEX_EXTS = {".tex", ".cls", ".sty", ".bib", ".def", ".cfg", ".clo"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".pdf", ".eps", ".svg", ".gif", ".bmp"}
FONT_EXTS = {".ttf", ".otf", ".ttc", ".pfb", ".pfm"}

ENGINE_HINT_XELATEX = re.compile(
    r"ctex|xeCJK|fontspec|zhnumber|\xe5\xae\x8b|simsun|SimSun|Fandol", re.IGNORECASE)
BIBLATEX = re.compile(r"\\usepackage.*\{biblatex\}|\\addbibresource")
RE_DOCCLASS = re.compile(r"^\s*\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}", re.MULTILINE)
RE_USEPKG = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}")
RE_INPUT = re.compile(r"\\(?:input|include)\{([^}]*)\}")
RE_BIB = re.compile(r"\\bibliography\{([^}]*)\}|\\addbibresource\{([^}]*)\}")
# Machine-specific absolute paths embedded in the TEMPLATE's own files
# (example scripts, hardcoded data paths). Reported as audit findings --
# they are third-party content, not OMMW core, so we surface but never fix.
HARDCODED_PATH_RE = re.compile(
    r"[A-Za-z]:\\(?:Users|Program Files|Windows|ProgramData)\\" 
    r"|(?:/(?:Users|home)/[A-Za-z0-9._-]+/)")


@dataclass
class TemplateRecord:
    """One audited template as stored in template-registry.json."""
    template_id: str
    original_archive: str = ""
    sha256: str = ""
    source: str = "user_provided"
    main_tex: str = ""
    document_class: str = ""
    required_engine: str = ""
    required_packages: list[str] = field(default_factory=list)
    required_fonts: list[str] = field(default_factory=list)
    encoding: str = "utf-8"
    bibliography_system: str = ""
    counts: dict = field(default_factory=dict)
    section_architecture: list[str] = field(default_factory=list)
    abstract_support: bool = False
    keywords_support: bool = False
    features: dict = field(default_factory=dict)
    compile_command: str = ""
    compile_status: str = "NOT_RUN"          # PASS | WARN | FAIL | NOT_RUN | BLOCKED
    compile_warnings: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    competition_fit: dict = field(default_factory=dict)
    role: str = ""                           # PRIMARY | SECONDARY | SPECIAL_PURPOSE | UNSUITABLE
    recommended_usage: str = ""
    verified_at: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


# ---------------------------------------------------------------------------
# discovery + extraction
# ---------------------------------------------------------------------------

def discover_archives(root: Path) -> list[Path]:
    hits = []
    for ext in ARCHIVE_EXTS:
        hits.extend(root.glob(f"*{ext}"))
    return sorted(set(hits))


def _fix_zip_name(info: zipfile.ZipInfo) -> str:
    """Chinese Windows zips store names GBK-encoded but flag them cp437."""
    name = info.filename
    if info.flag_bits & 0x800:      # UTF-8 flag
        return name
    try:
        return name.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def extract_archive(archive: Path, dest: Path) -> list[str]:
    """Extract to dest; returns list of extracted relative paths.

    zip: stdlib with GBK name repair. 7z/rar: requires external tool on PATH.
    """
    dest.mkdir(parents=True, exist_ok=True)
    ext = archive.suffix.lower()
    extracted: list[str] = []
    if ext == ".zip":
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                target_name = _fix_zip_name(info)
                target = dest / target_name
                # zip-slip guard
                if not str(target.resolve()).startswith(str(dest.resolve())):
                    continue
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
                extracted.append(target_name)
        return extracted
    tool = shutil.which("7z") if ext == ".7z" else (
        shutil.which("unrar") or shutil.which("rar"))
    if not tool:
        raise RuntimeError(f"no extractor available for {ext} archives "
                           f"(install 7-Zip/UnRAR or provide a .zip)")
    r = subprocess.run([tool, "x", "-y", str(archive), f"-o{dest}"],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"{Path(tool).name} failed: {r.stderr[:200]}")
    extracted = [str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()]
    return extracted


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# inventory / audit
# ---------------------------------------------------------------------------

def _is_work_file(p: Path, root: Path) -> bool:
    """True if p belongs to the template proper (not our _compile_test dirs)."""
    try:
        rel = p.relative_to(root)
    except ValueError:
        return False
    return not any(part.startswith("_") for part in rel.parts)


def find_main_tex(root: Path) -> Path | None:
    """The .tex that has \\documentclass AND \\begin{document}; prefer shallow."""
    candidates = [p for p in sorted(root.rglob("*.tex"), key=lambda p: len(p.parts))
                  if _is_work_file(p, root)]
    best = None
    for p in candidates:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "\\documentclass" in t and "\\begin{document}" in t:
            if "\\title" in t or "\\maketitle" in t or best is None:
                best = p
                if "\\maketitle" in t:
                    break
    return best


def inventory(root: Path, main_tex: Path | None) -> dict:
    files = [p for p in root.rglob("*") if p.is_file() and _is_work_file(p, root)]
    counts = {
        "files_total": len(files),
        "tex": sum(1 for p in files if p.suffix.lower() == ".tex"),
        "cls_sty": sum(1 for p in files if p.suffix.lower() in (".cls", ".sty")),
        "bib": sum(1 for p in files if p.suffix.lower() == ".bib"),
        "figures": sum(1 for p in files if p.suffix.lower() in IMAGE_EXTS),
        "fonts": sum(1 for p in files if p.suffix.lower() in FONT_EXTS),
        "scripts_readme": sum(1 for p in files if p.suffix.lower() in (".bat", ".ps1", ".sh", ".md")),
    }
    # third-party content audit: machine paths embedded in template files
    hardcoded: list[str] = []
    for p in files:
        if p.suffix.lower() not in (".py", ".m", ".r", ".cpp", ".c", ".bat", ".ps1", ".sh", ".tex"):
            continue
        if p.stat().st_size > 400_000:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in t.splitlines():
            if HARDCODED_PATH_RE.search(line) and not line.strip().startswith(("#", "//", "%", "--")):
                hardcoded.append(f"{p.name}: {line.strip()[:110]}")
                break
    text = ""
    packages: set[str] = set()
    docclass = ""
    if main_tex:
        text = main_tex.read_text(encoding="utf-8", errors="ignore")
        m = RE_DOCCLASS.search(text)
        docclass = m.group(1) if m else ""
        # follow one level of \\input for package discovery
        corpus = [text]
        for im in RE_INPUT.finditer(text):
            inc = main_tex.parent / (im.group(1) if im.group(1).endswith(".tex")
                                     else im.group(1) + ".tex")
            if inc.exists():
                corpus.append(inc.read_text(encoding="utf-8", errors="ignore"))
        for c in corpus:
            for um in RE_USEPKG.finditer(c):
                for pkg in um.group(1).split(","):
                    packages.add(pkg.strip())
    fonts_needed = sorted({f for f in ("SimSun", "SimHei", "FandolSong", "Times New Roman",
                                       "Arial", "Courier New", "FangSong", "KaiTi")
                           if re.search(re.escape(f), text, re.IGNORECASE)})
    engine = "pdflatex"
    full_corpus = text
    for p in files:
        if p.suffix in (".cls", ".sty") and p.stat().st_size < 400_000:
            try:
                full_corpus += p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                pass
    if ENGINE_HINT_XELATEX.search(full_corpus) or any(
            pkg in ("ctex", "xeCJK", "fontspec") for pkg in packages):
        engine = "xelatex"
    bib = "bibtex"
    if BIBLATEX.search(text):
        bib = "biber"
    sections = [s.group(2) for s in re.finditer(
        r"\\((?:sub)*section)\*?\{([^}]*)\}", text)]
    features = {
        "abstract_env": bool(re.search(r"\\begin\{abstract\}|摘要", text)),
        "keywords": bool(re.search(r"关键词|[Kk]eywords", text)),
        "subfigure": any(p in packages for p in ("subfigure", "subcaption", "subfig")),
        "longtable": "longtable" in packages,
        "algorithm": any(p in packages for p in ("algorithm", "algorithm2e", "algorithmicx")),
        "listings": "listings" in packages,
        "tikz": "tikz" in packages or "pgfplots" in packages,
        "hyperref": "hyperref" in packages,
        "header_footer": any(p in packages for p in ("fancyhdr", "titlesec", "hdrset")) or "fancyhdr" in full_corpus,
        "cover_page": bool(re.search(r"\bcover\b|封面|\\\\makecover", text, re.IGNORECASE)),
        "color": any(p in packages for p in ("xcolor", "color")),
    }
    return {"counts": counts, "document_class": docclass, "packages": sorted(packages),
            "engine": engine, "bibliography_system": bib, "sections": sections,
            "fonts_needed": fonts_needed, "features": features,
            "hardcoded_paths": hardcoded}


# ---------------------------------------------------------------------------
# REAL compile smoke test (no compile => never "verified")
# ---------------------------------------------------------------------------

def compile_smoke(main_tex: Path, engine: str, cfg: Config,
                  timeout: int = 240) -> tuple[str, str, list[str], Path | None]:
    """Compile in place next to the main tex. Returns (status, command,
    warnings, pdf_path_or_None).

    status: PASS (pdf produced, no fatal), WARN (pdf produced but errors
    recovered / unresolved warnings), FAIL (no pdf).

    Path-safety rules (both verified against real failures):
      1. TeX engines fail to even start when given non-ASCII paths as
         arguments -> run with cwd=<main tex dir>, RELATIVE args only.
      2. A non-ASCII MAIN FILE NAME itself is also fatal -> clone the entry
         file as ``_main_compile.tex`` (underscore prefix keeps it out of
         inventory) when needed.
      The scratch build dir ``_compile_test`` is anchored NEXT TO the main
      tex so the -output-directory argument stays pure-ASCII relative.
      If the run leaves undefined citations and the tree ships a .bib, one
      bibtex pass plus two engine reruns are executed before judging.
    """
    texbin = detect_texlive_bin(cfg)
    if not texbin:
        return "BLOCKED", "", ["TeX Live bin dir not found (run `ommw doctor`)"], None
    exe = texbin / (engine + (".exe" if os.name == "nt" else ""))
    if not exe.exists():
        exe = texbin / ("pdflatex" + (".exe" if os.name == "nt" else ""))
    work = main_tex.parent
    src_name = main_tex.name
    if not src_name.isascii():
        shutil.copy2(main_tex, work / "_main_compile.tex")
        src_name = "_main_compile.tex"
    jobname = Path(src_name).stem
    build_dir = work / "_compile_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(exe), "-interaction=nonstopmode", "-halt-on-error",
           "-output-directory", "_compile_test", src_name]
    display_cmd = (
        f"{exe.name} -interaction=nonstopmode -halt-on-error "
        f"-output-directory _compile_test {src_name}")
    log_tail = ""
    ok_any = False

    def _engine_run() -> tuple[int, str]:
        r = subprocess.run(cmd, cwd=str(work), capture_output=True,
                           text=True, timeout=timeout, errors="replace")
        lp = build_dir / (jobname + ".log")
        tail = lp.read_text(encoding="utf-8", errors="ignore") if lp.exists() else ""
        return r.returncode, tail

    try:
        for i in range(4):   # cross-refs usually converge by pass 3
            rc, log_tail = _engine_run()
            if (build_dir / (jobname + ".pdf")).exists():
                ok_any = True
            converged = not re.search(
                r"Rerun to get|Label\(s\) may have changed", log_tail)
            if rc == 0 and ok_any and converged:
                break
    except subprocess.TimeoutExpired:
        return "FAIL", display_cmd, [f"compile timeout after {timeout}s"], None

    # bibliography completion pass (undefined citations + a shipped .bib)
    bib_ran = False
    if ok_any and re.search(r"Citation .* undefined|There were undefined citations",
                            log_tail):
        bibs = [p for p in sorted(work.rglob("*.bib")) if _is_work_file(p, work)]
        bibtex = texbin / ("bibtex" + (".exe" if os.name == "nt" else ""))
        if bibs and bibtex.exists():
            env = os.environ.copy()
            env["BIBINPUTS"] = str(work) + os.pathsep + env.get("BIBINPUTS", "")
            env["BSTINPUTS"] = str(work) + os.pathsep + env.get("BSTINPUTS", "")
            try:
                subprocess.run([str(bibtex), jobname], cwd=str(build_dir), env=env,
                               capture_output=True, text=True, timeout=60,
                               errors="replace")
                bib_ran = True
                for i in range(2):
                    rc, log_tail = _engine_run()
                ok_any = (build_dir / (jobname + ".pdf")).exists()
            except subprocess.TimeoutExpired:
                pass

    warnings = sorted({w.strip()[:160] for w in re.findall(
        r"(LaTeX Warning: [^\n]+|Package \S+ Warning: [^\n]+)", log_tail)})[:15]
    missing_char = len(re.findall(r"Missing character", log_tail))
    overfull = len(re.findall(r"Overfull \\hbox \((\d+)", log_tail))
    if missing_char:
        warnings.append(f"missing-glyph events: {missing_char} (check font setup)")
    if overfull > 20:
        warnings.append(f"many overfull boxes: {overfull} (layout quality risk)")
    if not ok_any:
        err = re.search(r"^! (.+)$", log_tail, re.MULTILINE)
        notes = warnings + ([f"fatal: {err.group(1)}"] if err else [])
        if not log_tail:
            notes.append("engine produced no log (failed to start; check engine/path)")
        return "FAIL", display_cmd, notes, None
    fatal_in_log = re.search(r"^! ", log_tail, re.MULTILINE)
    if fatal_in_log:
        return ("WARN", display_cmd,
                warnings + ["pdf produced despite errors (nonstopmode recovered)"],
                build_dir / (jobname + ".pdf"))
    if re.search(r"Citation .* undefined|There were undefined citations", log_tail):
        note = "citations still undefined after bibtex rerun" if bib_ran \
            else "undefined citations (no .bib shipped to rerun bibtex)"
        return ("WARN", display_cmd, warnings + [note],
                build_dir / (jobname + ".pdf"))
    return "PASS", display_cmd, warnings, build_dir / (jobname + ".pdf")


# ---------------------------------------------------------------------------
# full import pipeline
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return s or "template"


def guess_template_id(staging_dir: Path) -> str:
    """A stable id from docclass/name, e.g. cumcm-cumcmthesis / mcm-2025."""
    main = find_main_tex(staging_dir)
    cls = ""
    if main:
        m = RE_DOCCLASS.search(main.read_text(encoding="utf-8", errors="ignore"))
        cls = m.group(1) if m else ""
    base = slugify(cls or staging_dir.name)[:32]
    return base


def import_archive(archive: Path, templates_root: Path, cfg: Config,
                   *, role_hint: str = "") -> tuple[TemplateRecord, Path]:
    """Run Discover->Archive->Extract->Inventory->Audit->Compile->Normalize.

    Returns (record, report_path). Raises nothing; failures land in record.
    """
    troot = templates_root
    raw_dir = troot / "local" / "raw"
    staging_base = troot / "local" / "staging"
    norm_dir = troot / "local" / "normalized"
    reports_dir = troot / "local" / "reports"
    for d in (raw_dir, staging_base, norm_dir, reports_dir):
        d.mkdir(parents=True, exist_ok=True)

    rec = TemplateRecord(template_id=slugify(archive.stem))
    rec.original_archive = archive.name
    rec.sha256 = sha256_of(archive)

    # raw: preserve pristine copy (original stays where the user put it too)
    raw_copy = raw_dir / archive.name
    if not raw_copy.exists():
        shutil.copy2(archive, raw_copy)

    staging = staging_base / rec.template_id
    # Idempotent, delete-free re-import: if this exact archive (sha) was
    # already extracted here, reuse the tree; otherwise extract in OVERWRITE
    # mode. We never rmtree the staging tree (sandbox-safe and idempotent).
    marker = staging / ".import-sha"
    same_sha = marker.exists() and marker.read_text(encoding="utf-8").strip() == rec.sha256
    if not staging.exists():
        staging.mkdir(parents=True)
    if not same_sha:
        try:
            extract_archive(archive, staging)
            marker.write_text(rec.sha256, encoding="utf-8")
        except Exception as e:  # noqa: BLE001 -- honest failure capture
            rec.compile_status = "BLOCKED"
            rec.known_issues.append(f"extraction failed: {e}")
            rp = write_template_report(rec, reports_dir)
            register(rec, troot)
            return rec, rp

    main = find_main_tex(staging)
    inv = inventory(staging, main)
    rec.main_tex = str(main.relative_to(staging)) if main else ""
    rec.document_class = inv["document_class"]
    rec.required_engine = inv["engine"]
    rec.required_packages = inv["packages"]
    rec.required_fonts = inv["fonts_needed"]
    rec.bibliography_system = inv["bibliography_system"]
    rec.counts = inv["counts"]
    rec.section_architecture = inv["sections"][:40]
    rec.features = inv["features"]
    rec.abstract_support = inv["features"]["abstract_env"]
    rec.keywords_support = inv["features"]["keywords"]
    rec.encoding = "utf-8/gbk-safe"
    if inv["hardcoded_paths"]:
        rec.known_issues.append(
            "template ships hardcoded machine paths in its own scripts: "
            + "; ".join(inv["hardcoded_paths"][:4])
            + ("; …" if len(inv["hardcoded_paths"]) > 4 else "")
            + " (third-party content; audit-only, not modified)")

    # competition fit heuristics. Chinese support = the template ACTUALLY
    # typesets Chinese: ctex/xeCJK class/package usage OR CJK characters in
    # the demo body. Engine choice alone is NOT evidence (xelatex-only
    # English templates exist).
    corpus = ""
    if main:
        corpus += main.read_text(encoding="utf-8", errors="ignore")
        cls_sty = list(staging.glob("*.cls")) + list(staging.glob("*.sty"))
        for p in cls_sty[:5]:
            try:
                corpus += p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                pass
    has_cjk_text = bool(re.search(r"[\u4e00-\u9fff]", re.sub(r"%.*", "", corpus)))
    zh_pkg = bool(re.search(r"^\\(?:RequiresPackage|usepackage).*(?:ctex|xeCJK)", corpus, re.MULTILINE))
    zh_class = rec.document_class.startswith(("ctex", "ctexbook", "ctexart"))
    zh = (has_cjk_text or zh_class) and (zh_pkg or zh_class or has_cjk_text)
    rec.competition_fit = {
        "chinese_support": zh,
        "math_packages": sorted({"amsmath", "amssymb", "amsthm", "mathtools"} &
                                 set(rec.required_packages)),
        "cumcm_suitability": "high" if zh else "low",
        "mcm_icm_suitability": "medium" if zh else ("high" if rec.compile_status != "FAIL" else "unknown"),
    }

    # REAL compile test
    if main:
        status, cmd, warns, pdf_path = compile_smoke(main, rec.required_engine, cfg)
        rec.compile_status = status
        rec.compile_command = cmd.replace(str(staging), "<staging>")
        rec.compile_warnings = warns
        if status in ("PASS", "WARN") and pdf_path is not None and pdf_path.exists():
            rec.verified_at = time.strftime("%Y-%m-%dT%H:%M:%S")
            # normalized copy WITHOUT build junk. Overwrite-in-place (never
            # rmtree): stale extra files are harmless in the working copy.
            target = norm_dir / rec.template_id
            shutil.copytree(staging, target, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(
                                "_compile_test", "_manual_test", "_main_compile*"))
            rec.recommended_usage = (
                f"use as {'PRIMARY' if role_hint == 'PRIMARY' else 'available'} LaTeX base; "
                f"main={rec.main_tex}; engine={rec.required_engine}")
        elif status == "BLOCKED":
            rec.known_issues.extend(warns)
        else:
            rec.known_issues.extend(warns[:3])
    else:
        rec.compile_status = "FAIL"
        rec.known_issues.append("no compilable main .tex found (needs \\documentclass)")

    rp = write_template_report(rec, reports_dir)
    register(rec, troot)
    return rec, rp


def write_template_report(rec: TemplateRecord, reports_dir: Path) -> Path:
    lines = [
        f"# Template Import Report — {rec.template_id}",
        "",
        f"- original archive: `{rec.original_archive}`",
        f"- sha256: `{rec.sha256[:16]}…`",
        f"- source: user provided (preserved under `raw/`, never modified)",
        f"- main tex: `{rec.main_tex or 'NOT FOUND'}`",
        f"- document class: `{rec.document_class}`",
        f"- required engine: **{rec.required_engine}**",
        f"- bibliography: {rec.bibliography_system}",
        f"- encoding: {rec.encoding}",
        f"- packages ({len(rec.required_packages)}): {', '.join(rec.required_packages[:25]) or '-'}",
        f"- fonts referenced: {', '.join(rec.required_fonts) or 'none detected'}",
        "",
        "## Inventory",
        f"- tex={rec.counts.get('tex')} cls/sty={rec.counts.get('cls_sty')} "
        f"bib={rec.counts.get('bib')} figures={rec.counts.get('figures')} "
        f"fonts={rec.counts.get('fonts')}",
        "",
        "## Features",
    ]
    for k, v in rec.features.items():
        lines.append(f"- {k}: {'YES' if v else 'no'}")
    lines += [
        "",
        "## Section architecture (top-level)",
    ]
    lines += [f"- {s}" for s in rec.section_architecture[:30]] or ["- (none parsed)"]
    lines += [
        "",
        "## Compile smoke test",
        f"- status: **{rec.compile_status}**",
        f"- command: `{rec.compile_command}`",
    ]
    for w in rec.compile_warnings:
        lines.append(f"- warning: {w}")
    for issue in rec.known_issues:
        lines.append(f"- issue: {issue}")
    if rec.compile_status in ("PASS", "WARN"):
        lines.append(f"- verified at: {rec.verified_at}")
    else:
        lines.append("- NOT verified: no real successful compile was performed.")
    lines += [
        "",
        "## Competition suitability",
        f"- chinese support: {rec.competition_fit.get('chinese_support')}",
        f"- CUMCM (国赛) fit: {rec.competition_fit.get('cumcm_suitability')}",
        f"- MCM/ICM (美赛) fit: {rec.competition_fit.get('mcm_icm_suitability')}",
        "",
        "## Recommended usage",
        rec.recommended_usage or "(not recommended until compile passes)",
        "",
        "> Honesty rule: this file is generated from the ACTUAL extraction and "
        "> compile run; statuses PASS/WARN/FAIL/BLOCKED only.",
    ]
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"import-{rec.template_id}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


REGISTRY_NAME = "template-registry.json"


def registry_path(templates_root: Path) -> Path:
    return templates_root / REGISTRY_NAME


def register(rec: TemplateRecord, templates_root: Path) -> Path:
    reg = load_registry(templates_root)
    reg[rec.template_id] = rec.to_dict()
    return save_registry(reg, templates_root)


def load_registry(templates_root: Path) -> dict:
    p = registry_path(templates_root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_registry(reg: dict, templates_root: Path) -> Path:
    p = registry_path(templates_root)
    p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def select_template(templates_root: Path, *, competition: str = "",
                    language: str = "", page_limit: int = 0) -> TemplateRecord | None:
    """Registry-driven selection (spec §9). Never hardcode template paths."""
    reg = load_registry(templates_root)
    comp = (competition or "").lower()
    want_zh = language == "zh" or comp in ("cumcm", "国赛", "cums")
    scored: list[tuple[int, str]] = []
    for tid, d in reg.items():
        if d.get("compile_status") not in ("PASS", "WARN"):
            continue
        fit = d.get("competition_fit", {})
        score = 0
        if want_zh and fit.get("chinese_support"):
            score += 3
        if not want_zh and not fit.get("chinese_support"):
            score += 3
        if comp in ("cumcm",) :
            score += {"high": 3, "medium": 1}.get(fit.get("cumcm_suitability", ""), 0)
        if comp in ("mcm_icm", "mcm", "icm"):
            score += {"high": 3, "medium": 1}.get(fit.get("mcm_icm_suitability", ""), 0)
        if d.get("role") == "PRIMARY":
            score += 2
        score += min(d.get("counts", {}).get("cls_sty", 0), 3)
        scored.append((-score, tid))
    if not scored:
        return None
    scored.sort()
    d = reg[scored[0][1]]
    return TemplateRecord(**d)
