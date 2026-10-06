"""--nodes expansion/fan-out, --bundle tarball, --verbose evidence."""

import json
import tarfile
from pathlib import Path

import pytest

from audit.cli import main
from audit.core.nodes import expand_nodes

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


# --- node expansion ---------------------------------------------------------

@pytest.mark.parametrize("spec,expected", [
    ("gpu-[210-214]", ["gpu-210", "gpu-211", "gpu-212", "gpu-213", "gpu-214"]),
    ("gpu-[01-03]", ["gpu-01", "gpu-02", "gpu-03"]),           # zero-padding kept
    ("a,b,c", ["a", "b", "c"]),
    ("gpu-[1-2],gpu-9", ["gpu-1", "gpu-2", "gpu-9"]),
])
def test_expand_nodes(spec, expected):
    assert expand_nodes(spec) == expected


def test_expand_nodes_rejects_backwards_range():
    with pytest.raises(ValueError):
        expand_nodes("gpu-[5-1]")


# --- --nodes fan-out (fixture subdirs as node names) ------------------------

def test_nodes_fanout_aggregates_exit_code(capsys):
    # Two "nodes" = two fixture subdirs under fixtures/: one healthy, one faulty.
    rc = main(["-u", "gpu_fault", "--fixture", str(FIXTURES), "--no-verdict",
               "--nodes", "cw0bec_blackwell_healthy,synth_gpu_fault"])
    out = capsys.readouterr().out
    assert "node: cw0bec_blackwell_healthy" in out
    assert "node: synth_gpu_fault" in out
    assert "cluster rollup" in out
    assert rc == 2  # worst across nodes (the faulty one fails)


def test_nodes_requires_fixture(capsys):
    rc = main(["-u", "gpu_fault", "--nodes", "gpu-[1-2]"])
    assert rc == 2
    assert "requires --fixture" in capsys.readouterr().err


# --- --bundle ---------------------------------------------------------------

def test_bundle_writes_tarball(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = main(["-u", "gpu_fault", "--fixture", str(FIXTURES / "synth_gpu_fault"),
               "--bundle", "--json"])
    assert rc == 2
    tarballs = list(tmp_path.glob("audit-bundle-*.tar.gz"))
    assert len(tarballs) == 1
    with tarfile.open(tarballs[0]) as t:
        names = t.getnames()
        assert any(n.endswith("/result.json") for n in names)
        assert any("/evidence/" in n for n in names)
        # result.json is valid and carries the verdict
        rj = next(n for n in names if n.endswith("result.json"))
        payload = json.loads(t.extractfile(rj).read())
        assert any(v["id"] == "gpu_fault_degrade" for v in payload["verdicts"])


def test_customer_bundle_redacts_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["--profile", "customer", "-m", "N1",
          "--fixture", str(FIXTURES / "nccl_tcp_fallback"), "--bundle", "--json"])
    tb = next(tmp_path.glob("audit-bundle-*.tar.gz"))
    with tarfile.open(tb) as t:
        ev = next(n for n in t.getnames() if n.endswith("nccl_log.txt"))
        text = t.extractfile(ev).read().decode()
        assert "h100-233-129" not in text  # hostname redacted in bundled evidence


# --- --verbose --------------------------------------------------------------

def test_verbose_shows_evidence(capsys):
    main(["-u", "gpu_fault", "--fixture", str(FIXTURES / "synth_gpu_fault"), "-v"])
    out = capsys.readouterr().out
    assert "evidence:" in out
