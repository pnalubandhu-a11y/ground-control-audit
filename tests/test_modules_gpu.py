"""Group G modules against the recorded (healthy) and synthetic (faulty) sets."""

from pathlib import Path

import pytest

from audit.core.context import Context
from audit.core.result import Status
from audit.modules import get_impl

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
HEALTHY = FIXTURES / "cw0bec_blackwell_healthy"
FAULTY = FIXTURES / "synth_gpu_fault"


@pytest.fixture
def healthy():
    return Context(mode="fixture", fixture_dir=HEALTHY)


@pytest.fixture
def faulty():
    return Context(mode="fixture", fixture_dir=FAULTY)


def test_g1_counts_eight_gpus(healthy):
    r = get_impl("G1").run(healthy)
    assert r.status is Status.PASS
    assert r.evidence["count"] == 8


def test_g3_ecc_pass_on_healthy(healthy):
    assert get_impl("G3").run(healthy).status is Status.PASS


def test_g3_ecc_fails_on_faulty_gpu3(faulty):
    r = get_impl("G3").run(faulty)
    assert r.status is Status.FAIL
    assert r.scope == "gpu:3"


def test_g5_xid_pass_on_healthy(healthy):
    assert get_impl("G5").run(healthy).status is Status.PASS


def test_g5_xid_fails_on_faulty_gpu3(faulty):
    r = get_impl("G5").run(faulty)
    assert r.status is Status.FAIL
    assert r.scope == "gpu:3"  # dmesg PCI bus mapped back to the GPU index


def test_g6_nvlink_na_on_blackwell(healthy):
    # RTX PRO 6000 has no NVLink -> module degrades to NA, never crashes.
    assert get_impl("G6").run(healthy).status is Status.NA


def test_g7_thermal_pass_on_healthy(healthy):
    assert get_impl("G7").run(healthy).status is Status.PASS


def test_g7_thermal_fails_on_faulty_gpu3(faulty):
    r = get_impl("G7").run(faulty)
    assert r.status is Status.FAIL
    assert r.scope == "gpu:3"
