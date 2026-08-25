"""Citation metadata retrieval and verification.

Two-tier model (Rule 26):
  - metadata verification: the source actually exists (Crossref/OpenAlex/arXiv).
  - claim verification:     the source actually supports the cited claim.

Network is only contacted on explicit request. Offline mode marks cache misses
as UNVERIFIED_OFFLINE rather than fabricating (Rule 73).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from . import atomic
from .schemas import Source, SourceVerification


CROSSREF = "https://api.crossref.org/works/{doi}"
OPENALEX = "https://api.openalex.org/works/doi:{doi}"
ARXIV = "https://export.arxiv.org/api/query?id_list={id}"


@dataclass
class CitationCache:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def get(self, key: str) -> dict | None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data.get(key)

    def put(self, key: str, val: dict) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        val = dict(val)
        val["retrieved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        data[key] = val
        atomic.write_json(self.path, data)


def _mailto() -> str:
    return os.environ.get("CROSSREF_MAILTO", "ommw@example.com")


def fetch_doi(doi: str, cache: CitationCache, *, offline: bool = False) -> Source | None:
    """Metadata-verify a DOI via Crossref (cache-first). Returns a Source or None."""
    cached = cache.get("doi:" + doi)
    if cached:
        return Source(**{**cached, "source_id": cached.get("source_id", "S-?"),
                         "metadata_verified": True,
                         "verification": SourceVerification.metadata_verified})
    if offline:
        return None  # Rule 73: never fabricate
    try:
        r = requests.get(CROSSREF.format(doi=doi), params={"mailto": _mailto()}, timeout=15)
        if r.status_code != 200:
            return None
        msg = r.json().get("message", {})
        authors = [f"{a.get('given','')} {a.get('family','')}".strip()
                   for a in msg.get("author", [])]
        src = {
            "title": (msg.get("title") or [""])[0],
            "authors": authors,
            "year": (msg.get("published", {}).get("date-parts", [[None]])[0][0]),
            "venue": msg.get("container-title", [""])[0] if msg.get("container-title") else "",
            "doi": doi,
        }
        cache.put("doi:" + doi, src)
        src.update({"source_id": "S-?", "metadata_verified": True,
                    "verification": SourceVerification.metadata_verified})
        return Source(**src)
    except Exception:
        return None


def verify_claim_support(source: Source, claim_text: str, *, offline: bool = False) -> Source:
    """Mark a source as content_verified only when evidence is available.

    In this offline-capable core, claim verification is an explicit, recorded
    decision: we do NOT auto-assert that a found paper supports a claim. The
    agent/user must supply the corroborating excerpt; absent that, the source
    stays at METADATA_VERIFIED, never CLAIM_VERIFIED (Rule 26/70).
    """
    if not source.metadata_verified:
        return source
    if offline and not source.cache_path:
        source.verification = SourceVerification.unverified_offline
        return source
    # No automatic claim verification without an excerpt; caller sets content_verified
    # after reviewing. We only escalate if the caller already proved content_verified.
    if source.content_verified:
        source.verification = SourceVerification.claim_verified
    else:
        source.verification = SourceVerification.metadata_verified
    return source


def add_source(sources_path: Path, src: Source) -> None:
    """Append a source to the ledger (atomic per-line)."""
    atomic.append_jsonl(sources_path, src.model_dump(mode="json"))
