"""N1 nccl_transport_health + the nccl_tcp_fallback verdict, on real logs."""

from pathlib import Path

import pytest

from audit.core.context import Context
from audit.core.registry import resolve_bundle
from audit.core.result import Status
from audit.core.runner import run_modules
from audit.modules import get_impl
from audit.verdicts import evaluate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
NCCL_OK = FIXTURES / "nccl_healthy"
NCCL_TCP = FIXTURES / "nccl_tcp_fallback"


@pytest.fixture
def healthy():
    return Context(mode="fixture", fixture_dir=NCCL_OK)


@pytest.fixture
def fallback():
    return Context(mode="fixture", fixture_dir=NCCL_TCP)


def test_n1_pass_on_rdma_log(healthy):
    r = get_impl("N1").run(healthy)
    assert r.status is Status.PASS
    assert r.evidence["transport"] == "rdma"


def test_n1_fail_on_tcp_fallback(fallback):
    r = get_impl("N1").run(fallback)
    assert r.status is Status.FAIL
    assert r.evidence["transport"] == "socket"
    assert r.scope == "node:h100-233-129"
    assert r.evidence["busbw"] == 3.4  # worst observed


def test_n1_na_without_log():
    ctx = Context(mode="fixture", fixture_dir=NCCL_OK)
    ctx._cache["nccl_log"] = ""  # simulate empty log
    assert get_impl("N1").run(ctx).status is Status.NA


def test_nccl_verdict_fires_on_fallback(fallback):
    results = run_modules(resolve_bundle("nccl_slow"), fallback)
    verdicts = evaluate(results)
    ids = {v.id for v in verdicts}
    assert "nccl_tcp_fallback" in ids
    v = next(v for v in verdicts if v.id == "nccl_tcp_fallback")
    assert v.scope == "node:h100-233-129"
    assert v.confidence == "high"


def test_nccl_verdict_silent_on_healthy(healthy):
    results = run_modules(resolve_bundle("nccl_slow"), healthy)
    assert [v for v in evaluate(results) if v.id == "nccl_tcp_fallback"] == []
