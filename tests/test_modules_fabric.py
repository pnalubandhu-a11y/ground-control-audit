"""Group B fabric modules against real-healthy + synthetic-fault IB fixtures."""

from pathlib import Path

import pytest

from audit.core.context import Context
from audit.core.registry import resolve_bundle
from audit.core.result import Status
from audit.core.runner import run_modules
from audit.modules import get_impl
from audit.verdicts import evaluate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
HEALTHY = FIXTURES / "cw0bec_blackwell_healthy"
FAULTY = FIXTURES / "synth_fabric_fault"


@pytest.fixture
def healthy():
    return Context(mode="fixture", fixture_dir=HEALTHY)


@pytest.fixture
def faulty():
    return Context(mode="fixture", fixture_dir=FAULTY)


# --- healthy: all green -----------------------------------------------------

@pytest.mark.parametrize("mid", ["B3", "B11", "B12", "B13", "B14"])
def test_all_fabric_modules_pass_on_healthy(healthy, mid):
    assert get_impl(mid).run(healthy).status is Status.PASS


def test_b12_reports_nine_hcas(healthy):
    assert len(get_impl("B12").run(healthy).evidence["devices"]) == 9


# --- faulty: each module catches its signal, on the right scope -------------

def test_b13_flags_down_port_mlx5_5(faulty):
    r = get_impl("B13").run(faulty)
    assert r.status is Status.FAIL
    assert r.scope == "mlx5_5"


def test_b14_flags_link_errors_mlx5_4(faulty):
    r = get_impl("B14").run(faulty)
    assert r.status is Status.FAIL
    assert r.scope == "mlx5_4"


def test_b11_flags_congestion_mlx5_6(faulty):
    r = get_impl("B11").run(faulty)
    assert r.status is Status.WARN
    assert r.scope == "mlx5_6"


def test_b3_flags_nic_errors_eth1(faulty):
    r = get_impl("B3").run(faulty)
    assert r.status is Status.FAIL
    assert r.scope == "eth1"


# --- verdict + preflight integration ---------------------------------------

def test_rdma_link_down_verdict_fires(faulty):
    results = run_modules(resolve_bundle("preflight"), faulty)
    verdicts = evaluate(results)
    v = next((v for v in verdicts if v.id == "rdma_link_down"), None)
    assert v is not None and v.scope == "mlx5_5" and v.confidence == "high"


def test_preflight_runs_fabric_modules_for_real(healthy):
    # In preflight, the B-group modules should now execute (not SKIP).
    results = {r.id: r for r in run_modules(resolve_bundle("preflight"), healthy)}
    for mid in ["B3", "B11", "B12", "B13", "B14"]:
        assert results[mid].status is Status.PASS
