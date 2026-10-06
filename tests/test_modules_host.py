"""Group A host modules against the real cw0bec healthy fixtures.

FAIL paths are exercised by injecting source text into the Context cache, which
keeps us from committing a dozen near-duplicate fault fixtures.
"""

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
    c._cache.update(sources)  # inject/override specific sources
    return c


# --- healthy: Group A greens (PASS or NA, never FAIL) ------------------------

@pytest.mark.parametrize("mid", ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"])
def test_group_a_not_failing_on_healthy(healthy, mid):
    assert get_impl(mid).run(healthy).status in {Status.PASS, Status.NA}


def test_a2_jumbo_mtu(healthy):
    r = get_impl("A2").run(healthy)
    assert r.status is Status.PASS and "9000" in r.summary


def test_a5_reports_all_three_versions(healthy):
    ev = get_impl("A5").run(healthy).evidence
    assert ev["kernel"] and ev["nvidia"] and ev["mlx_fw"]


def test_a6_topology_coherent_reports_locality(healthy):
    # Real cw0bec: all NICs on NUMA 0, so only GPU0-3 are NUMA-local (4/8).
    r = get_impl("A6").run(healthy)
    assert r.status is Status.PASS
    assert r.evidence == {"gpus": 8, "nics": 9, "numa_local": 4}


# --- injected fault paths ---------------------------------------------------

def test_a2_fails_on_mtu_mismatch():
    nl = "### eth0\nmtu: 9000\n### ibp0\nmtu: 1500\n"
    assert get_impl("A2").run(_ctx(net_links=nl)).status is Status.FAIL


def test_a3_fails_when_eth0_down():
    nl = "### eth0\nmtu: 9000\noperstate: down\ncarrier: 0\n"
    assert get_impl("A3").run(_ctx(net_links=nl)).status is Status.FAIL


def test_a6_warns_when_no_gpu_has_local_nic():
    # One GPU, SYS to both NICs -> no NUMA-local NIC anywhere -> WARN (not FAIL).
    topo = "\tGPU0\tNIC0\tNIC1\nGPU0\t X \tSYS\tSYS\t0-31\t0\n"
    assert get_impl("A6").run(_ctx(nvidia_topo=topo)).status is Status.WARN


# --- preflight is now green on real healthy data ----------------------------

def test_preflight_has_no_failures_on_healthy(healthy):
    results = run_modules(resolve_bundle("preflight"), healthy)
    bad = [r.id for r in results if r.status in {Status.FAIL, Status.ERROR}]
    assert bad == [], f"unexpected failures: {bad}"


def test_preflight_group_a_implemented(healthy):
    results = {r.id: r for r in run_modules(resolve_bundle("preflight"), healthy)}
    for mid in ["A1", "A2", "A3", "A5", "A6", "A7", "A8"]:
        assert results[mid].status is not Status.SKIP, f"{mid} still SKIP"
