"""Execution engine: run a selected set of modules against a Context.

Serial for now (checks are cheap against fixtures). Parallelism + per-module
timeouts are a later perf concern (DESIGN.md §5). Handles platform detection
(unsatisfied `requires` -> NA), active-test gating, and never lets a single
module crash the run (exceptions -> ERROR result).
"""

from __future__ import annotations

from .catalog import ModuleSpec
from .context import Context
from .result import ModuleResult, Status
from ..modules import get_impl, has_impl


def run_modules(
    specs: list[ModuleSpec],
    ctx: Context,
    *,
    allow_active: bool = False,
) -> list[ModuleResult]:
    """Run each spec and return results in the given order."""
    results: list[ModuleResult] = []
    for s in specs:
        results.append(_run_one(s, ctx, allow_active))
    return results


def _run_one(s: ModuleSpec, ctx: Context, allow_active: bool) -> ModuleResult:
    # Platform detection: a module whose requirements aren't met is NA.
    if not s.requires <= ctx.caps:
        missing = ", ".join(sorted(s.requires - ctx.caps))
        return ModuleResult(s.id, s.name, Status.NA, summary=f"requires {missing}")

    # Active (fabric-perturbing) tests need an explicit opt-in.
    if s.active and not allow_active:
        return ModuleResult(
            s.id, s.name, Status.SKIP, summary="active test (needs --allow-active)"
        )

    if not has_impl(s.id):
        return ModuleResult(
            s.id, s.name, Status.SKIP, summary="not implemented in this build"
        )

    try:
        return get_impl(s.id).run(ctx)
    except Exception as exc:  # a broken check must not kill the run
        return ModuleResult(
            s.id, s.name, Status.ERROR, severity=1, summary=f"{type(exc).__name__}: {exc}"
        )
