"""Registry + catalog metadata consistency (data-only; no hardware needed)."""

import pytest

from audit.core import registry
from audit.core.catalog import H100, MODULES


def test_all_bundles_reference_real_modules():
    # Should not raise; every bundle ID must exist in the catalog.
    registry.validate()


def test_every_bundle_resolves_to_specs():
    assert registry.bundle_names(), "expected at least one bundle"
    for name in registry.bundle_names():
        specs = registry.resolve_bundle(name)
        assert specs, f"bundle {name} resolved to nothing"
        assert all(hasattr(s, "id") for s in specs)


def test_unknown_module_and_bundle_raise():
    with pytest.raises(registry.RegistryError):
        registry.get_module("Z99")
    with pytest.raises(registry.RegistryError):
        registry.resolve_bundle("does_not_exist")


def test_active_modules_are_exactly_the_reference_set():
    active = {m.id for m in MODULES if m.active}
    assert active == {"C4", "C7", "C8", "C9", "C10"}


def test_na_modules_are_the_imex_blackwell_set():
    na = {m.id for m in MODULES if m.h100 == H100.NA}
    assert na == {"A9", "B2", "C12", "C13"}


def test_h100_values_are_valid():
    valid = {H100.NATIVE, H100.PARTIAL, H100.NA}
    assert all(m.h100 in valid for m in MODULES)


def test_na_modules_declare_a_requirement():
    for m in MODULES:
        if m.h100 == H100.NA:
            assert m.requires, f"{m.id} is NA but declares no requires"
