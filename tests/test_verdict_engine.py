"""Verdict correlation: the right root cause fires, on the right scope."""

from pathlib import Path

from audit.core.context import Context
from audit.core.registry import resolve_bundle
from audit.core.runner import run_modules
from audit.verdicts import evaluate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
HEALTHY = FIXTURES / "cw0bec_blackwell_healthy"
FAULTY = FIXTURES / "synth_gpu_fault"


def _run(fixture_dir):
    specs = resolve_bundle("gpu_fault")
    results = run_modules(specs, Context(mode="fixture", fixture_dir=fixture_dir))
    return results, evaluate(results)


def test_no_verdict_on_healthy():
    _, verdicts = _run(HEALTHY)
    assert verdicts == []


def test_gpu_fault_degrade_fires_on_faulty_gpu3():
    _, verdicts = _run(FAULTY)
    ids = {v.id for v in verdicts}
    assert "gpu_fault_degrade" in ids
    v = next(v for v in verdicts if v.id == "gpu_fault_degrade")
    assert v.scope == "gpu:3"
    assert v.confidence == "high"
    assert "gpu:3" in v.verdict
    assert set(v.supporting) == {"G3", "G5"}


def test_verdict_requires_same_scope():
    # G5 fault on gpu:3 but ECC clean -> condition set incomplete -> no verdict.
    from audit.core.result import ModuleResult, Status

    results = [
        ModuleResult("G5", "gpu_xid_errors", Status.FAIL, scope="gpu:3"),
        ModuleResult("G3", "gpu_ecc_errors", Status.FAIL, scope="gpu:5"),
    ]
    assert evaluate(results) == []  # different scopes must not correlate
