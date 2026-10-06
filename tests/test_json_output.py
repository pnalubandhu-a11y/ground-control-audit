"""--json output: valid JSON, full result set, redaction honored."""

import json
from pathlib import Path

from audit.core.context import Context
from audit.core.profile import get_profile
from audit.core.registry import resolve_bundle
from audit.core.runner import run_modules
from audit.render import json_out
from audit.verdicts import evaluate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GPU_FAULT = FIXTURES / "synth_gpu_fault"


def _run(fixture, profile_name="internal"):
    profile = get_profile(profile_name)
    results = run_modules(resolve_bundle("gpu_fault"),
                          Context(mode="fixture", fixture_dir=fixture),
                          profile=profile)
    return results, evaluate(results), profile


def test_json_is_valid_and_structured():
    results, verdicts, profile = _run(GPU_FAULT)
    payload = json.loads(json_out.render_json(results, verdicts, profile=profile))
    assert payload["profile"] == "internal"
    assert payload["exit_code"] == 2
    assert payload["summary"]["fail"] >= 2
    assert len(payload["modules"]) == len(results)
    assert any(v["id"] == "gpu_fault_degrade" for v in payload["verdicts"])


def test_json_module_has_all_contract_fields():
    results, verdicts, profile = _run(GPU_FAULT)
    payload = json.loads(json_out.render_json(results, verdicts, profile=profile))
    g5 = next(m for m in payload["modules"] if m["id"] == "G5")
    for key in ("id", "name", "status", "severity", "summary", "evidence",
                "remediation", "scope", "duration_ms"):
        assert key in g5
    assert g5["status"] == "FAIL"
    assert g5["scope"] == "gpu:3"


def test_json_status_serialized_as_string():
    results, verdicts, profile = _run(GPU_FAULT)
    raw = json_out.render_json(results, verdicts, profile=profile)
    assert '"status": "PASS"' in raw  # enum rendered as its value, not Status.PASS


def test_customer_json_is_redacted():
    from audit.core.result import ModuleResult, Status, Verdict

    customer = get_profile("customer")
    results = [ModuleResult("N1", "nccl_transport_health", Status.FAIL,
                            summary="TCP on node:h100-233-129",
                            scope="node:h100-233-129")]
    verdicts = [Verdict("nccl_tcp_fallback", "fell back on node:h100-233-129",
                        scope="node:h100-233-129")]
    raw = json_out.render_json(results, verdicts, profile=customer)
    assert "h100-233-129" not in raw
    assert "<host>" in raw
