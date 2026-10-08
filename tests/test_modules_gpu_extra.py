"""G8 gpu_bus_health + G9 gpu_fabric_manager against the real -q capture."""

from pathlib import Path

import pytest

from audit.core.context import Context
from audit.core.registry import resolve_bundle
from audit.core.result import Status
from audit.core.runner import run_modules
from audit.modules import get_impl

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
HEALTHY = FIXTURES / "cw0bec_blackwell_healthy"


@pytest.fixture
def healthy():
    return Context(mode="fixture", fixture_dir=HEALTHY)


def _ctx(**sources):
    c = Context(mode="fixture", fixture_dir=HEALTHY)
    c._cache.update(sources)
    return c


def test_g8_bus_health_pass_on_healthy(healthy):
    r = get_impl("G8").run(healthy)
    assert r.status is Status.PASS
    assert r.evidence["max_replays"] == 0


def test_g8_fails_on_high_replays():
    q = "GPU 00000000:20:00.0\n        Replays Since Reset : 4096\n"
    assert get_impl("G8").run(_ctx(nvidia_smi_q=q)).status is Status.FAIL


def test_g9_na_without_nvswitch_fabric(healthy):
    # Real Blackwell PCIe cards report Fabric State: N/A -> G9 is NA.
    assert get_impl("G9").run(healthy).status is Status.NA


def test_g9_pass_when_fabric_completed():
    q = "GPU 00000000:20:00.0\n    Fabric\n        State : Completed\n"
    assert get_impl("G9").run(_ctx(nvidia_smi_q=q)).status is Status.PASS


def test_g9_fails_when_fabric_in_progress():
    # multi-word state must not be truncated to "In" and whitelisted
    q = "GPU 00000000:20:00.0\n    Fabric\n        State : In Progress\n"
    assert get_impl("G9").run(_ctx(nvidia_smi_q=q)).status is Status.FAIL


def test_preflight_fully_implemented(healthy):
    # No module in preflight should be SKIP anymore.
    results = run_modules(resolve_bundle("preflight"), healthy)
    skipped = [r.id for r in results if r.status is Status.SKIP]
    assert skipped == [], f"still SKIP: {skipped}"
    assert not [r.id for r in results if r.status in {Status.FAIL, Status.ERROR}]
