"""Group N — NCCL / collectives (CoreWeave extension beyond the reference 51).

N1 nccl_transport_health parses an NCCL debug log (NCCL_DEBUG=INFO) and decides
whether collectives are running over RDMA or have silently fallen back to TCP
sockets — the classic "my training run is 100× slower" root cause.
"""

from __future__ import annotations

import re

from ..core.context import Context
from ..core.result import ModuleResult
from .base import Module, register, spec

_RDMA_RE = re.compile(r"NET/IB|IBext|GDRDMA", re.IGNORECASE)
_SOCKET_RE = re.compile(r"NET/Socket", re.IGNORECASE)
_BUSBW_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*GB/s")
_HOST_RE = re.compile(r"^([A-Za-z0-9][\w.-]*):\d+\s+NCCL", re.MULTILINE)


def _busbw(text: str) -> float | None:
    vals = [float(m.group(1)) for m in _BUSBW_RE.finditer(text)]
    return min(vals) if vals else None  # worst (lowest) observed


def _host(text: str) -> str:
    m = _HOST_RE.search(text)
    return m.group(1) if m else "node"


@register
class NcclTransport(Module):
    spec = spec("N1")

    def run(self, ctx: Context) -> ModuleResult:
        text = ctx.collect("nccl_log")
        if not text.strip():
            return self.na("no NCCL log provided (set AUDIT_NCCL_LOG or --fixture)")

        rdma = bool(_RDMA_RE.search(text))
        socket = bool(_SOCKET_RE.search(text))
        bw = _busbw(text)
        scope = f"node:{_host(text)}"
        bw_note = f", busbw {bw} GB/s" if bw is not None else ""

        # Inter-node traffic on sockets with no RDMA in sight => TCP fallback.
        if socket and not rdma:
            return self.fail(
                f"NCCL inter-node transport is TCP sockets, not RDMA{bw_note}",
                scope=scope,
                evidence={"transport": "socket", "rdma": False, "busbw": bw},
                remediation=(
                    "NCCL is not using RDMA — verify NCCL_IB_HCA matches the "
                    "node's IB devices (e.g. ibp0..ibp7) and that the IB "
                    "interfaces are up."
                ),
            )
        if rdma:
            return self.ok(
                f"NCCL using RDMA (IB/GDRDMA){bw_note}",
                scope=scope,
                evidence={"transport": "rdma", "rdma": True, "busbw": bw},
            )
        return self.warn(
            "could not determine NCCL transport from log",
            scope=scope,
            evidence={"transport": "unknown"},
        )
