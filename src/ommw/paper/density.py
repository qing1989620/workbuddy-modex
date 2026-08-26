"""Paper Production Kernel -- LaTeX content density analysis (v0.2).

Static, deterministic analysis of the paper's LaTeX sources. These metrics
feed the content gates (gates.py) and the quality scorecard (scorecard.py).

Design rules (upgrade spec §66):
  - Scripts detect STRUCTURE (counts, presence, linkage); they never pretend
    to judge mathematical correctness. Meaning-level judgment stays with the
    reviewer agents.
  - All counting is comment-aware: everything after an unescaped ``%`` is
    ignored so placeholder comments do not inflate density.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# regexes (compiled once)
# ---------------------------------------------------------------------------

RE_COMMENT = re.compile(r"(?<!\\)%.*")
# Matches the WHOLE display-math construct (environment incl. its body, \\[...\\]
# and $$...$$), so the same regex both COUNTS display equations and STRIPS math
# before prose word-counting.
RE_DISPLAY_EQ = re.compile(
    r"\\begin\{(equation|align|gather|eqnarray|multline)\*?\}.*?\\end\{\1\}"
    r"|(?<!\\)\\\[.+?\\\]|\$\$.+?\$\$",
    re.DOTALL,
)
RE_INLINE_MATH = re.compile(r"(?<!\\)\$(?!\$)(.+?)\$", re.DOTALL)
RE_FIGURE = re.compile(r"\\includegraphics")
RE_TABLE_ENV = re.compile(r"\\begin\{(tabular|tabularx|longtable|longtabu|array)\*?\}")
RE_ALGORITHM = re.compile(
    r"\\begin\{(algorithm|algorithmic|algorithm2e|lstlisting|minted|verbnobox)\*?\}")
RE_TIKZ = re.compile(r"\\begin\{tikzpicture\}")
RE_CITE = re.compile(r"\\cite[tp]?\{([^}]*)\}")
RE_LABEL = re.compile(r"\\label\{([^}]*)\}")
RE_REF = re.compile(r"\\(ref|eqref|autoref|cref|Cref)\{([^}]*)\}")
RE_SECTION = re.compile(r"\\(sub)?section\*?\{([^}]*)\}")
RE_WORD = re.compile(r"[A-Za-z]+|[^\sA-Za-z]")  # CJK chars count as one word each
RE_INPUT = re.compile(r"\\(?:input|include)\{([^}]*)\}")

PLACEHOLDER_PAT = re.compile(
    r"placeholder|todo\b|fixme|\{%|<%|<!--|\bTBD\b|\bXXX\b", re.IGNORECASE)

GENERIC_MODEL_PHRASES = [
    "建立数学模型进行求解",
    "建立模型并求解",
    "建立数学模型",
]
AI_STYLE_PHRASES = [
    "综上所述", "由此可见", "具有重要意义", "显著提高", "具有较高的准确性",
    "具有一定参考价值", "不言而喻", "众所周知",
]

QUESTION_HINTS = ("question", "问题", "q1", "q2", "q3", "q4")


def strip_comments(text: str) -> str:
    """Remove unescaped % comments line by line (keeps \\%)."""
    return "\n".join(RE_COMMENT.sub("", line) for line in text.splitlines())


def count_words(text: str) -> int:
    """CJK-aware word count: each CJK char = 1 word; latin words = 1 word."""
    return len(RE_WORD.findall(text))


@dataclass
class SectionStats:
    """Density metrics for ONE section file."""
    file: str
    raw_chars: int = 0
    words: int = 0
    display_equations: int = 0
    inline_math: int = 0
    figures: int = 0
    tikz: int = 0
    tables: int = 0
    algorithms: int = 0
    citations: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    sections: int = 0
    is_placeholder: bool = False
    ai_style_hits: list[str] = field(default_factory=list)

    @property
    def effective_equations(self) -> int:
        return self.display_equations + min(self.inline_math // 5, 5)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["effective_equations"] = self.effective_equations
        return d


def analyze_text(name: str, text: str) -> SectionStats:
    """Analyze one LaTeX source string."""
    clean = strip_comments(text)
    st = SectionStats(file=name, raw_chars=len(clean))
    # WORDS = PROSE words only. Math must be stripped BEFORE counting, else a
    # dump of equations inflates "words" and the formula-inflation detector
    # (words < 200) never fires exactly when inflation is real.
    body_no_math = RE_DISPLAY_EQ.sub(" ", clean)
    body_no_math = RE_INLINE_MATH.sub(" ", body_no_math)
    st.words = count_words(body_no_math)
    st.display_equations += len(RE_DISPLAY_EQ.findall(clean))
    st.inline_math = len(RE_INLINE_MATH.findall(clean))
    st.figures = len(RE_FIGURE.findall(clean))
    st.tikz = len(RE_TIKZ.findall(clean))
    st.tables = len(RE_TABLE_ENV.findall(clean))
    st.algorithms = len(RE_ALGORITHM.findall(clean))
    for m in RE_CITE.finditer(clean):
        st.citations += [k.strip() for k in m.group(1).split(",") if k.strip()]
    st.labels = [m.group(1) for m in RE_LABEL.finditer(clean)]
    st.refs = [m.group(2) for m in RE_REF.finditer(clean)]
    st.sections = len(RE_SECTION.findall(clean))
    low = body_no_math.lower()
    st.is_placeholder = (
        PLACEHOLDER_PAT.search(clean) is not None and st.words < 40
    ) or (st.raw_chars < 120 and st.words < 25 and not st.labels)
    st.ai_style_hits = [p for p in AI_STYLE_PHRASES if p in clean or p in low]
    return st


def analyze_latex_dir(latex_dir: Path) -> dict:
    """Analyze main.tex + sections/*.tex of a LaTeX paper dir.

    Returns {"sections": [SectionStats...], "totals": {...}}.
    """
    sections_dir = latex_dir / "sections"
    files: list[Path] = []
    if sections_dir.exists():
        files = sorted(sections_dir.glob("*.tex"))
    elif latex_dir.exists():
        files = sorted(latex_dir.glob("*.tex"))
    stats = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        stats.append(analyze_text(f.name, text))
    totals = {
        "files": len(stats),
        "placeholder_files": sum(1 for s in stats if s.is_placeholder),
        "words": sum(s.words for s in stats),
        "display_equations": sum(s.display_equations for s in stats),
        "inline_math": sum(s.inline_math for s in stats),
        "figures": sum(s.figures for s in stats),
        "tikz": sum(s.tikz for s in stats),
        "tables": sum(s.tables for s in stats),
        "algorithms": sum(s.algorithms for s in stats),
        "citations": len({c for s in stats for c in s.citations}),
        "labels": len({l for s in stats for l in s.labels}),
        "refs": sum(len(s.refs) for s in stats),
        "ai_style_hits": sorted({h for s in stats for h in s.ai_style_hits}),
    }
    totals["visual_assets"] = totals["figures"] + totals["tikz"]
    return {"sections": stats, "totals": totals}


def classify_chapter(filename: str) -> str:
    """Coarse chapter role used by gates: abstract|model|experiment|support."""
    stem = Path(filename).stem.lower()
    if "abstract" in stem:
        return "abstract"
    if any(h in stem for h in QUESTION_HINTS):
        return "model"
    if any(k in stem for k in ("model", "models")):
        return "model"
    if any(k in stem for k in ("experiment", "results", "sensitivity",
                               "validation", "robustness")):
        return "experiment"
    return "support"


def words_per_equation(st: SectionStats) -> float:
    eq = st.effective_equations
    return float("inf") if eq == 0 else round(st.words / eq, 1)


def build_density_report(latex_dir: Path) -> dict:
    """Full chapter-density report (spec §34) as a JSON-serializable dict.

    Flags anomalies both ways: too little math AND formula inflation.
    """
    analysis = analyze_latex_dir(latex_dir)
    chapters = []
    for s in analysis["sections"]:
        role = classify_chapter(s.file)
        wpe = words_per_equation(s)
        anomalies = []
        if s.is_placeholder:
            anomalies.append("PLACEHOLDER_SECTION")
        if role == "model":
            if s.effective_equations <= 1 and s.words > 150:
                anomalies.append("FORMULA_DENSITY_WARNING")
            if s.words >= 800 and wpe > 800:
                anomalies.append("FORMULA_DENSITY_WARNING")
            if s.display_equations > 40 and s.words < 200:
                anomalies.append("FORMULA_INFLATION_SUSPECTED")
        if role == "experiment" and s.words > 400 and not (
                s.figures + s.tables + s.tikz):
            anomalies.append("EXPERIMENT_WITHOUT_EVIDENCE")
        if role != "abstract" and s.ai_style_hits:
            anomalies.append("AI_STYLE_PHRASES:" + "|".join(s.ai_style_hits))
        chapters.append({
            "chapter": Path(s.file).stem,
            "role": role,
            "words": s.words,
            "display_equations": s.display_equations,
            "inline_math": s.inline_math,
            "effective_equations": s.effective_equations,
            "figures": s.figures,
            "tikz": s.tikz,
            "tables": s.tables,
            "algorithms": s.algorithms,
            "citations": len(s.citations),
            "labels": len(s.labels),
            "refs": len(s.refs),
            "is_placeholder": s.is_placeholder,
            "anomalies": anomalies,
        })
    report = {
        "latex_dir": str(latex_dir),
        "totals": analysis["totals"],
        "chapters": chapters,
    }
    return report


def write_density_report(latex_dir: Path, out_path: Path) -> dict:
    rep = build_density_report(latex_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return rep
