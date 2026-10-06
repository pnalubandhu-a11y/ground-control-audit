"""Customer profile: read-only enforcement, redaction, remediation."""

from pathlib import Path

import pytest

from audit.core.context import Context
from audit.core.profile import get_profile
from audit.core.redact import redact_text
from audit.core.registry import resolve_bundle
from audit.core.result import ModuleResult, Status, Verdict
from audit.core.runner import run_modules
from audit.render import terminal

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
GPU_FAULT = FIXTURES / "synth_gpu_fault"
NCCL_TCP = FIXTURES / "nccl_tcp_fallback"


# --- redaction --------------------------------------------------------------

@pytest.mark.parametrize("raw,needle", [
    ("host h100-233-129 slow", "<host>"),
    ("node g08387e ready", "<host>"),
    ("ip 10.0.1.69 down", "<ip>"),
    ("GPU-096299db-e474-00e2-0f7a-6e7de89fa63f bad", "GPU-<uuid>"),
    ("Serial Number 1793825002456", "<serial>"),
    ("mac 38:a4:20:8a:92:a4 seen", "<mac>"),
])
def test_redact_masks_internal_identifiers(raw, needle):
    out = redact_text(raw)
    assert needle in out


def test_redact_keeps_device_scopes():
    # device-class scopes must survive — the customer needs them
    assert redact_text("gpu:3 mlx5_4 eth1") == "gpu:3 mlx5_4 eth1"


# --- read-only enforcement --------------------------------------------------

def test_customer_blocks_active_even_with_allow_active():
    customer = get_profile("customer")
    specs = resolve_bundle("network_perf")  # contains active C7/C8/C9/C10
    results = {r.id: r for r in run_modules(
        specs, Context(mode="fixture", fixture_dir=GPU_FAULT),
        allow_active=True, profile=customer)}
    for mid in ["C7", "C8", "C9", "C10"]:
        assert results[mid].status is Status.SKIP
        assert "read-only" in results[mid].summary


def test_internal_allows_active_with_flag():
    internal = get_profile("internal")
    specs = resolve_bundle("network_perf")
    results = {r.id: r for r in run_modules(
        specs, Context(mode="fixture", fixture_dir=GPU_FAULT),
        allow_active=True, profile=internal)}
    # active modules are no longer SKIPped for being active (they'll be SKIP for
    # "not implemented" instead — the point is the read-only gate didn't fire)
    assert "read-only" not in results["C8"].summary


# --- rendered output --------------------------------------------------------

def test_customer_output_redacts_and_escalates():
    customer = get_profile("customer")
    v = [Verdict("nccl_tcp_fallback", "NCCL fell back on node:h100-233-129",
                 confidence="high", severity=3, scope="node:h100-233-129")]
    r = [ModuleResult("N1", "nccl_transport_health", Status.FAIL,
                      summary="TCP on node:h100-233-129", scope="node:h100-233-129",
                      remediation="Check NCCL_IB_HCA.")]
    out = terminal.render_run(r, v, profile=customer, stream=_NoTty())
    assert "h100-233-129" not in out          # hostname masked
    assert "<host>" in out
    assert "Contact CoreWeave support" in out  # escalation present
    assert "Check NCCL_IB_HCA." in out         # remediation present


def test_internal_output_not_redacted():
    internal = get_profile("internal")
    r = [ModuleResult("N1", "nccl_transport_health", Status.FAIL,
                      summary="TCP on node:h100-233-129", scope="node:h100-233-129")]
    out = terminal.render_run(r, [], profile=internal, stream=_NoTty())
    assert "h100-233-129" in out               # internal keeps real identifiers
    assert "Contact CoreWeave support" not in out


class _NoTty:
    """Stand-in stream so color is disabled in assertions."""
    def isatty(self):
        return False
