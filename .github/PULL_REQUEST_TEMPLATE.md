## Summary

<!-- What does this PR change and why? -->

## Checklist

- [ ] `uv run pytest` passes (incl. portability + hallucination suites)
- [ ] No machine-specific absolute paths in core (CI portability job)
- [ ] No secrets committed (CI secret-scan job)
- [ ] If a dependency was added, `uv.lock` updated and justified
- [ ] If a third-party skill was added, provenance recorded (pinned commit + license)
- [ ] Non-permissive licenses are NOT vendored into the MIT core
- [ ] Docs updated if behavior changed

## Type

- [ ] feat
- [ ] fix
- [ ] docs
- [ ] test
- [ ] refactor
- [ ] chore
