"""Shared result contract: Status, ModuleResult, Verdict.

These are the types every module and the verdict engine agree on. They are
defined here (not in catalog.py) so modules, the runner, renderers, and the
verdict engine all depend on one small, stable module. See DESIGN.md §3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    """Outcome of a single module run."""

    PASS = "PASS"    # healthy
    WARN = "WARN"    # degraded but functional
    FAIL = "FAIL"    # broken / actionable
    SKIP = "SKIP"    # not selected / user-skipped
    NA = "NA"        # not applicable on this platform (e.g. IMEX on H100)
    ERROR = "ERROR"  # the check itself failed to run

    def __str__(self) -> str:  # so f-strings print "FAIL", not "Status.FAIL"
        return self.value


@dataclass
class ModuleResult:
    """The result of running one module. Produced by Module.run()."""

    id: str                        # "G5"
    name: str                      # "gpu_xid_errors"
    status: Status
    severity: int = 0              # 0..3 — drives verdict ranking
    summary: str = ""              # one human line
    evidence: dict = field(default_factory=dict)  # raw parsed data
    remediation: str = ""          # what to do; wording is profile-aware
    scope: str = "node"            # "node" | "cluster" | "gpu:3" | "mlx5_4"
    duration_ms: int = 0


@dataclass
class Verdict:
    """A named root cause emitted by the correlation layer. See DESIGN.md §6."""

    id: str                        # "bad_optic_rail"
    verdict: str                   # human sentence with the action
    confidence: str = "medium"     # "low" | "medium" | "high"
    severity: int = 0              # 0..3
    scope: str = "node"            # the shared scope the rule matched on
    supporting: list[str] = field(default_factory=list)  # module IDs that fired
