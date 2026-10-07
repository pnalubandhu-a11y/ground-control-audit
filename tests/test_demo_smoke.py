"""Demo smoke test: every showcased (bundle, fixture) combo runs with no ERROR.

Guards against fixture-completeness gaps — a module ERRORing on a missing
source file would blemish the live demo. Found exactly that in a dry run.
"""

import pytest

from pathlib import Path

from audit.core.context import Context
from audit.core.registry import resolve_bundle
from audit.core.result import Status
from audit.core.runner import run_modules
from audit.verdicts import evaluate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# (bundle, fixture dir, expect a verdict?)
DEMO_COMBOS = [
    ("preflight", "cw0bec_blackwell_healthy", False),
    ("gpu_fault", "synth_gpu_fault", True),
    ("nccl_slow", "nccl_tcp_fallback", True),
    ("nccl_slow", "nccl_healthy", False),
    ("preflight", "synth_fabric_fault", True),
]


@pytest.mark.parametrize("bundle,fixture,expect_verdict", DEMO_COMBOS)
def test_demo_combo_runs_without_errors(bundle, fixture, expect_verdict):
    ctx = Context(mode="fixture", fixture_dir=FIXTURES / fixture)
    results = run_modules(resolve_bundle(bundle), ctx)
    errored = [r.id for r in results if r.status is Status.ERROR]
    assert errored == [], f"{bundle}@{fixture} ERRORed: {errored}"
    assert bool(evaluate(results)) == expect_verdict
