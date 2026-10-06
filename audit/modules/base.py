"""Module base class + implementation registry.

A ModuleSpec (catalog.py) is static data. A Module is the runnable check that
wraps one spec and knows how to produce a ModuleResult from a Context.

Concrete modules subclass Module, set `spec`, implement `run`, and call
`register(cls)` so the runner can find them by ID. Not every spec has an impl
yet — the runner treats a spec with no impl as SKIP.
"""

from __future__ import annotations

from ..core.catalog import MODULES_BY_ID, ModuleSpec
from ..core.context import Context
from ..core.result import ModuleResult, Status

IMPLS: dict[str, "Module"] = {}


class Module:
    """Base class for a runnable check. Subclasses set `spec` and `run`."""

    spec: ModuleSpec

    def run(self, ctx: Context) -> ModuleResult:  # pragma: no cover - abstract
        raise NotImplementedError

    # --- helpers for subclasses ---------------------------------------------
    def result(self, status, **kw) -> ModuleResult:
        return ModuleResult(id=self.spec.id, name=self.spec.name, status=status, **kw)

    def ok(self, summary, **kw):
        return self.result(Status.PASS, summary=summary, **kw)

    def warn(self, summary, severity=1, **kw):
        return self.result(Status.WARN, summary=summary, severity=severity, **kw)

    def fail(self, summary, severity=3, **kw):
        return self.result(Status.FAIL, summary=summary, severity=severity, **kw)

    def na(self, summary, **kw):
        return self.result(Status.NA, summary=summary, **kw)


def register(cls: type[Module]) -> type[Module]:
    """Class decorator: instantiate and index a module impl by its spec ID."""
    inst = cls()
    if inst.spec.id in IMPLS:
        raise ValueError(f"duplicate module impl for {inst.spec.id}")
    IMPLS[inst.spec.id] = inst
    return cls


def spec(module_id: str) -> ModuleSpec:
    return MODULES_BY_ID[module_id]


def has_impl(module_id: str) -> bool:
    return module_id in IMPLS


def get_impl(module_id: str) -> Module:
    return IMPLS[module_id]
