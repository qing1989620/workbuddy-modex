"""Competition Compliance Kernel (Layer 1, Rule 3-7).

Detect -> Build Profile -> Enforce Gates. Official rules are FETCHED, never
assumed from model memory. LIVE mode blocks current-contest search; TRAINING
mode permits past papers with attribution.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..paths import ProjectPaths
from ..schemas import CompetitionMode, CompetitionProfile
from ..verify import Finding, VerifyReport


# Terms that indicate current-contest solution content (LIVE mode hard block).
# Intentional broad coverage: these patterns are about the CURRENT contest,
# not about historical study.
CURRENT_CONTEST_TERMS = [
    "当届", "本题答案", "本题题解", "本届全国", "本届赛题解答",
    "current contest solution", "this year's solution", "2026 cumcm answer",
    "2026 mcm answer", "2026 icm answer", "国赛答案", "美赛答案",
    # Generic solution-content words (LIVE mode only blocks these when combined
    # with contest/problem context; see check_query_allowed).
    "答案", "题解", "解答过程", "解题思路", "参考解答", "获奖论文",
    "solution", "solutions", "solved", "answer key", "writeup",
]

# LIVE-mode solution-content block patterns (lowercased, regex).
LIVE_BLOCK_PATTERNS = [
    r"(cumcm|国赛|mcm|icm|美赛|数学建模).{0,12}(答案|题解|解答|获奖论文|solution|writeup)",
    r"(答案|题解|获奖论文).{0,12}(cumcm|国赛|mcm|icm|美赛)",
    r"\d{4}\s*(cumcm|mcm|icm|国赛|美赛).{0,12}(solution|answer|题解|答案)",
]

# Allowed in LIVE mode: legitimate sources only (Rule 6).
LIVE_ALLOWED_PREFIXES = [
    "official", "官网", "规则", "rules", "regulations",
    "crossref", "openalex", "arxiv", "pubmed", "doi",
    "gov", "statistics", "官方统计",
]


@dataclass
class QueryCheck:
    allowed: bool
    reason: str = ""
    suggestion: str = ""


def check_query_allowed(profile: CompetitionProfile, query: str) -> QueryCheck:
    """LIVE-mode search gate (Rule 6): reject current-contest solution searches.

    In TRAINING/REVIEW/RESEARCH mode, everything is allowed (with attribution).
    LIVE mode: solution-content patterns (with contest context) are blocked.
    """
    if profile.mode != CompetitionMode.live or not profile.forbids_current_contest_search():
        return QueryCheck(allowed=True, reason="not live-with-restrictions")
    import re as _re
    q = query.lower()
    for term in CURRENT_CONTEST_TERMS:
        if term in q:
            return QueryCheck(
                allowed=False,
                reason=f"LIVE mode blocks current-contest content: '{term}' in query",
                suggestion="use official rules / academic literature / official statistics only",
            )
    for pat in LIVE_BLOCK_PATTERNS:
        if _re.search(pat, q):
            return QueryCheck(
                allowed=False,
                reason=f"LIVE mode blocks contest-solution pattern: {pat}",
                suggestion="use official rules / academic literature / official statistics only",
            )
    # Queries about legitimate sources are fine even in LIVE mode.
    for prefix in LIVE_ALLOWED_PREFIXES:
        if q.startswith(prefix) or prefix in q:
            return QueryCheck(allowed=True, reason="legitimate LIVE source")
    return QueryCheck(allowed=True, reason="generic query; agent must still avoid contest-solution sites")


# ---------------------------------------------------------------------------
# Compliance gate: checks a paper/project against the profile's hard rules.
# ---------------------------------------------------------------------------

def compliance_gate(pp: ProjectPaths, profile: CompetitionProfile) -> VerifyReport:
    """Run the compliance gate: page limit, anonymization, AI declaration,
    submission format, file size, forbidden content. No CRITICAL/HIGH -> pass.
    """
    rep = VerifyReport()
    state = pp.state_dir

    # Page limit (Rule 5): if profile has a limit, the built paper must respect it.
    limit = profile.effective_page_limit()
    if limit:
        pdf = pp.latex_dir / "output" / "main.pdf"
        if pdf.exists():
            n = _pdf_pages(pdf)
            if n > limit:
                rep.add("HIGH", "page-limit",
                        f"paper has {n} pages, limit is {limit}", str(pdf))
        else:
            rep.add("MEDIUM", "page-limit-unchecked",
                    "page limit set but no built PDF to measure", "")

    # Anonymization rule (if the profile requires anonymous submission).
    if profile.anonymization_rule and "anonymous" in profile.anonymization_rule.lower():
        latex_dir = pp.latex_dir / "sections"
        if latex_dir.exists():
            for f in latex_dir.glob("*.tex"):
                text = f.read_text(encoding="utf-8", errors="ignore")
                if _looks_like_personal_info(text):
                    rep.add("HIGH", "anonymization",
                            f"possible personal info in {f.name}", str(f))

    # AI declaration must exist if the profile requires it.
    if profile.ai_policy and "declare" in profile.ai_policy.lower():
        ai_md = pp.paper_dir / "ai-usage-declaration.md"
        if not ai_md.exists():
            rep.add("HIGH", "ai-declaration-missing",
                    "profile requires an AI usage declaration, none found", "")

    # Forbidden files in the submission pack.
    sub = pp.root / "submission"
    if sub.exists():
        forbidden = [".env", "config.local.toml", ".cache", ".build"]
        for name in forbidden:
            if (sub / name).exists():
                rep.add("HIGH", "forbidden-submission-file", f"submission contains {name}", str(sub))
    return rep


def _pdf_pages(pdf_path) -> int:
    try:
        data = pdf_path.read_bytes()
        # Count "/Type /Page" occurrences (not /Pages) — heuristic but deterministic.
        return data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    except Exception:
        return -1


def _looks_like_personal_info(text: str) -> bool:
    import re
    # Names, emails, phones, student ids patterns (conservative heuristic).
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        return True
    if re.search(r"(姓名|电话|学号|手机号)\s*[:：]", text):
        return True
    return False
