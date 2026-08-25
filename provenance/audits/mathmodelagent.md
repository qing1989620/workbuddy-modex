# MathModelAgent Provider Audit

## Date: 2026-08-25
## Auditor: OMMW automated + manual review

## Upstream
- Repository: https://github.com/jihe520/MathModelAgent
- Last observed commit date: 2026-08-17
- Total commits observed: ~98
- Activity: actively maintained

## License
- Type: **Personal, non-commercial use only.**
- Verbatim restriction: "个人免费使用，请勿商业用途，商业用途联系我（作者）"
- Implication: This is NOT a permissive license. MathModelAgent source may NOT
  be vendored into the MIT-licensed OMMW core or re-licensed.

## OMMW handling (verdict: EXTERNAL_OPTIONAL, adapter-only)
- OMMW ships `providers/mathmodelagent/{README.md, provider.toml, detect.py, adapter.py}` ONLY.
- These files contain NO upstream MathModelAgent code; only adapter contracts,
  detection logic, and provenance notes.
- Enabling is opt-in: the user clones MathModelAgent separately and accepts its
  non-commercial license.
- The OMMW core MUST remain fully functional with MathModelAgent absent (verified
  by `tests/integration/test_core_without_providers.py`).

## Security review
- `detect.py`: filesystem-only, no network, no shell.
- `adapter.py`: imports upstream lazily; raises NotImplementedError if absent.
  No code execution on import.
- No secrets, no hidden downloads, no subprocess on import.

## Findings
- P0: none
- P1: none (provider is disabled by default and adapter-only)
- P2: ensure users do not commit MathModelAgent source into OMMW forks; covered
  by .gitignore workspace/ and THIRD_PARTY_NOTICES.md.

## Conclusion
Acceptable as EXTERNAL_OPTIONAL. Re-audit if upstream license changes.
