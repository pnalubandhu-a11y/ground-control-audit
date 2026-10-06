"""Execution context — the single boundary between modules and the host.

Modules never call subprocess directly. They ask the Context for a named data
*source* (e.g. "gpu_query"). The Context has two backends:

  - live    — runs the real command and returns its stdout
  - fixture — returns recorded output from a fixtures/<set>/ directory

This is what makes every module unit-testable off-hardware and the demo robust
if the cluster hiccups (DESIGN.md §9).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# Logical source -> (argv for live capture, fixture filename).
# Keep argv and the recorded fixture in lock-step so live and fixture modes
# observe the same bytes.
SOURCES: dict[str, tuple[list[str], str]] = {
    "nvidia_smi": (["nvidia-smi"], "nvidia-smi.txt"),
    "nvidia_smi_q": (["nvidia-smi", "-q"], "nvidia-smi_-q.txt"),
    "nvidia_smi_nvlink": (["nvidia-smi", "nvlink", "-s"], "nvidia-smi_nvlink_-s.txt"),
    "gpu_query": (
        [
            "nvidia-smi",
            "--query-gpu=index,name,pci.bus_id,temperature.gpu,"
            "ecc.errors.uncorrected.aggregate.total,"
            "ecc.errors.corrected.aggregate.total",
            "--format=csv",
        ],
        "query_gpu.csv",
    ),
    "dmesg_xid": (["sh", "-c", "dmesg | grep -i xid || true"], "dmesg_xid.txt"),
    # NCCL debug log — in live mode, point AUDIT_NCCL_LOG at the job's log file.
    "nccl_log": (["sh", "-c", 'cat "${AUDIT_NCCL_LOG:-/dev/null}"'], "nccl.log"),
}


class SourceError(RuntimeError):
    """A data source could not be collected."""


class Context:
    """Host capabilities + a cached way to collect data sources."""

    def __init__(
        self,
        *,
        mode: str = "fixture",
        fixture_dir: Path | str | None = None,
        caps: set[str] | None = None,
        timeout: int = 20,
    ):
        if mode not in ("live", "fixture"):
            raise ValueError(f"mode must be 'live' or 'fixture', got {mode!r}")
        if mode == "fixture" and fixture_dir is None:
            raise ValueError("fixture mode requires fixture_dir")
        self.mode = mode
        self.fixture_dir = Path(fixture_dir) if fixture_dir else None
        self.caps = caps if caps is not None else {"gpu"}
        self.timeout = timeout
        self._cache: dict[str, str] = {}

    def collect(self, source: str) -> str:
        """Return the stdout for a named source, cached per Context."""
        if source in self._cache:
            return self._cache[source]
        if source not in SOURCES:
            raise SourceError(f"unknown source: {source!r}")
        argv, filename = SOURCES[source]

        if self.mode == "fixture":
            path = self.fixture_dir / filename
            try:
                text = path.read_text()
            except FileNotFoundError as exc:
                raise SourceError(f"missing fixture: {path}") from exc
        else:
            try:
                proc = subprocess.run(
                    argv, capture_output=True, text=True, timeout=self.timeout
                )
            except FileNotFoundError as exc:
                raise SourceError(f"command not found: {argv[0]}") from exc
            except subprocess.TimeoutExpired as exc:
                raise SourceError(f"timed out: {' '.join(argv)}") from exc
            text = proc.stdout

        self._cache[source] = text
        return text
