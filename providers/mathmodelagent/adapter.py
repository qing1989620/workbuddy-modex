"""Thin adapter contract for MathModelAgent.

IMPORTANT: This file contains NO upstream MathModelAgent code. It only describes
how OMMW would invoke a user-installed MathModelAgent, and only after the user
has explicitly enabled the provider in config.local.toml. Importing the upstream
package is deferred to runtime so the OMMW core never depends on it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderContract:
    """Describes the call surface OMMW expects. Not a hard dependency."""

    name: str = "mathmodelagent"
    requires_enabled: bool = True
    license_noncommercial: bool = True

    def run_modeling_task(self, project_root: str, **kwargs):  # pragma: no cover
        """Invoke MathModelAgent on a project. Implemented only when enabled.

        Raises NotImplementedError if the upstream is not importable. The OMMW
        core catches this and continues with its own orchestration.
        """
        try:
            import importlib
            mod = importlib.import_module("mathmodelagent")  # type: ignore
        except Exception as e:
            raise NotImplementedError(
                "MathModelAgent not importable. Install it separately and enable "
                "in config.local.toml. OMMW core continues without it."
            ) from e
        # If importable, defer to its entrypoint. Signature intentionally generic.
        return mod.run(project_root=project_root, **kwargs)  # type: ignore[attr-defined]
