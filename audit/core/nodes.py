"""Node-list expansion for cluster fan-out (`--nodes gpu-[210-214],gpu-07`)."""

from __future__ import annotations

import re

_RANGE = re.compile(r"^(.*?)\[(\d+)-(\d+)\](.*)$")


def expand_nodes(spec: str) -> list[str]:
    """Expand a comma-separated node spec into concrete node names.

    'gpu-[210-214]'      -> gpu-210 .. gpu-214
    'gpu-[01-03],gpu-99' -> gpu-01, gpu-02, gpu-03, gpu-99   (zero-padding kept)
    """
    out: list[str] = []
    for token in (t.strip() for t in spec.split(",")):
        if not token:
            continue
        m = _RANGE.match(token)
        if not m:
            out.append(token)
            continue
        prefix, lo_s, hi_s, suffix = m.groups()
        lo, hi = int(lo_s), int(hi_s)
        if hi < lo:
            raise ValueError(f"bad range in {token!r}: {hi} < {lo}")
        width = len(lo_s)
        for n in range(lo, hi + 1):
            out.append(f"{prefix}{str(n).zfill(width)}{suffix}")
    return out
