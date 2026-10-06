"""Registry: catalog lookups + use-case bundle resolution.

Bundles are data (bundles/usecases.yaml), not code. This module is the one
place that loads them, validates that every referenced module ID exists, and
resolves a bundle name to its ordered list of ModuleSpec.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .catalog import ALL_MODULES, MODULES_BY_ID, ModuleSpec

# audit/core/registry.py -> audit/bundles/usecases.yaml
_BUNDLES_PATH = Path(__file__).resolve().parent.parent / "bundles" / "usecases.yaml"


class RegistryError(ValueError):
    """Raised when catalog/bundle data is inconsistent."""


def get_module(module_id: str) -> ModuleSpec:
    """Return the ModuleSpec for an ID, or raise RegistryError if unknown."""
    try:
        return MODULES_BY_ID[module_id]
    except KeyError:
        raise RegistryError(f"unknown module id: {module_id!r}") from None


def modules_by_group() -> dict[str, list[ModuleSpec]]:
    """Modules grouped by their group letter, in catalog order."""
    groups: dict[str, list[ModuleSpec]] = {}
    for m in ALL_MODULES:
        groups.setdefault(m.group, []).append(m)
    return groups


@lru_cache(maxsize=1)
def _load_bundles_raw() -> dict[str, list[str]]:
    with _BUNDLES_PATH.open() as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise RegistryError(f"{_BUNDLES_PATH} must be a mapping of name -> [ids]")
    return data


def bundle_names() -> list[str]:
    """All defined bundle names, in file order."""
    return list(_load_bundles_raw().keys())


def resolve_bundle(name: str) -> list[ModuleSpec]:
    """Resolve a bundle name to its ordered list of ModuleSpec.

    Raises RegistryError if the bundle is unknown or references a missing ID.
    """
    bundles = _load_bundles_raw()
    if name not in bundles:
        raise RegistryError(f"unknown bundle: {name!r}")
    return [get_module(mid) for mid in bundles[name]]


def validate() -> None:
    """Fail loudly if any bundle references a module ID not in the catalog."""
    bundles = _load_bundles_raw()
    for name, ids in bundles.items():
        for mid in ids:
            if mid not in MODULES_BY_ID:
                raise RegistryError(
                    f"bundle {name!r} references unknown module {mid!r}"
                )
