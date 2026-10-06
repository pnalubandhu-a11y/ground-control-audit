"""Group G — GPU checks. First real implementations (G1, G3, G5, G6, G7).

All parse `nvidia-smi` outputs provided by the Context. Scope strings use
`gpu:<index>` so the verdict engine can correlate failures on the same GPU.
"""

from __future__ import annotations

import re

from ..core.context import Context
from ..core.result import ModuleResult, Status
from .base import Module, register, spec

# Thermal thresholds (°C). Blackwell/H100 throttle well above these.
_TEMP_WARN = 80
_TEMP_FAIL = 90


def _parse_gpu_query(text: str) -> list[dict]:
    """Parse the gpu_query CSV into row dicts. Tolerates '# comments' / blanks."""
    rows: list[dict] = []
    header: list[str] | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cells = [c.strip() for c in line.split(",")]
        if header is None:
            header = cells
            continue
        row = dict(zip(header, cells))
        rows.append(
            {
                "index": row.get("index", ""),
                "name": row.get("name", ""),
                "bus_id": row.get("pci.bus_id", ""),
                "temp": _to_int(row.get("temperature.gpu")),
                "ecc_uncorr": _to_int(
                    row.get("ecc.errors.uncorrected.aggregate.total")
                ),
                "ecc_corr": _to_int(row.get("ecc.errors.corrected.aggregate.total")),
            }
        )
    return rows


def _to_int(val) -> int | None:
    try:
        return int(str(val).strip())
    except (TypeError, ValueError):
        return None  # "N/A", "", etc.


def _bus_key(bus: str) -> str:
    """Normalize a PCI id to 'bus:device' so dmesg and nvidia-smi forms match.

    nvidia-smi: '00000000:46:00.0'  ->  '46:00'
    dmesg Xid : '0000:46:00'        ->  '46:00'
    """
    parts = bus.replace(".0", "").split(":")
    return ":".join(parts[-2:]) if len(parts) >= 2 else bus


@register
class GpuCount(Module):
    spec = spec("G1")

    def run(self, ctx: Context) -> ModuleResult:
        rows = _parse_gpu_query(ctx.collect("gpu_query"))
        if not rows:
            return self.fail("no GPUs detected", evidence={"count": 0})
        models = sorted({r["name"] for r in rows})
        model = models[0] if len(models) == 1 else ", ".join(models)
        return self.ok(
            f"{len(rows)}× {model}",
            evidence={"count": len(rows), "models": models},
        )


@register
class GpuEcc(Module):
    spec = spec("G3")

    def run(self, ctx: Context) -> ModuleResult:
        rows = _parse_gpu_query(ctx.collect("gpu_query"))
        uncorr = [r for r in rows if (r["ecc_uncorr"] or 0) > 0]
        corr = [r for r in rows if (r["ecc_corr"] or 0) > 0]
        if uncorr:
            g = uncorr[0]
            return self.fail(
                f"uncorrectable ECC on gpu:{g['index']} "
                f"({g['ecc_uncorr']} uncorr, {g['ecc_corr']} corr)",
                scope=f"gpu:{g['index']}",
                evidence={"uncorrectable": [r["index"] for r in uncorr]},
                remediation=("Uncorrectable memory (ECC) errors indicate failing GPU "
                             "memory. Stop scheduling work on this GPU; it should be "
                             "replaced."),
            )
        if corr:
            g = corr[0]
            return self.warn(
                f"correctable ECC on gpu:{g['index']} ({g['ecc_corr']} corr)",
                scope=f"gpu:{g['index']}",
                evidence={"correctable": [r["index"] for r in corr]},
            )
        return self.ok("no ECC errors", evidence={"gpus": len(rows)})


@register
class GpuXid(Module):
    spec = spec("G5")
    _XID_RE = re.compile(r"Xid\s*\(PCI:([0-9a-fA-F:.]+)\):\s*(\d+)")

    def run(self, ctx: Context) -> ModuleResult:
        text = ctx.collect("dmesg_xid")
        bus_to_index = {
            _bus_key(r["bus_id"]): r["index"]
            for r in _parse_gpu_query(ctx.collect("gpu_query"))
        }
        hits: list[tuple[str, str]] = []  # (gpu_index, xid)
        for m in self._XID_RE.finditer(text):
            idx = bus_to_index.get(_bus_key(m.group(1)), "?")
            hits.append((idx, m.group(2)))
        if not hits:
            return self.ok("no Xid errors")
        idx = hits[0][0]
        xids = ",".join(sorted({x for _, x in hits}))
        return self.fail(
            f"Xid {xids} on gpu:{idx}",
            scope=f"gpu:{idx}",
            evidence={"xids": hits},
            remediation=("This GPU is reporting hardware (Xid) errors. Cordon the "
                         "node so no new work lands on it; the GPU needs replacement."),
        )


@register
class GpuNvlink(Module):
    spec = spec("G6")

    def run(self, ctx: Context) -> ModuleResult:
        text = ctx.collect("nvidia_smi_nvlink").strip()
        if not text or "not supported" in text.lower() or text.startswith("("):
            return self.na("NVLink not supported on this GPU")
        if re.search(r"inactive|down", text, re.IGNORECASE):
            return self.fail("NVLink reports an inactive/down link")
        return self.ok("NVLink links active")


def _nvsmi_q_blocks(text: str) -> list[str]:
    """Split `nvidia-smi -q` into per-GPU blocks (each starts with 'GPU <bus>')."""
    blocks: list[str] = []
    cur: list[str] = []
    for line in text.splitlines():
        if re.match(r"^GPU \S", line):
            if cur:
                blocks.append("\n".join(cur))
            cur = [line]
        elif cur:
            cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


@register
class GpuBusHealth(Module):
    spec = spec("G8")
    # PCIe replay thresholds (since reset).
    _WARN, _FAIL = 100, 1000

    def run(self, ctx: Context) -> ModuleResult:
        blocks = _nvsmi_q_blocks(ctx.collect("nvidia_smi_q"))
        if not blocks:
            return self.na("no nvidia-smi -q output")
        replays: list[tuple[int, int]] = []
        for i, b in enumerate(blocks):
            m = re.search(r"Replays Since Reset\s*:\s*(\d+)", b)
            if m:
                replays.append((i, int(m.group(1))))
        if not replays:
            return self.na("no PCIe replay data")
        idx, worst = max(replays, key=lambda t: t[1])
        if worst >= self._FAIL:
            return self.fail(f"gpu:{idx} PCIe replays={worst}", scope=f"gpu:{idx}",
                             evidence={"max_replays": worst})
        if worst >= self._WARN:
            return self.warn(f"gpu:{idx} PCIe replays={worst}", scope=f"gpu:{idx}",
                             evidence={"max_replays": worst})
        return self.ok(f"PCIe replays nominal (max {worst})",
                       evidence={"max_replays": worst})


@register
class GpuFabricManager(Module):
    spec = spec("G9")

    def run(self, ctx: Context) -> ModuleResult:
        blocks = _nvsmi_q_blocks(ctx.collect("nvidia_smi_q"))
        if not blocks:
            return self.na("no nvidia-smi -q output")
        states = []
        for b in blocks:
            m = re.search(r"Fabric\b[^\n]*\n\s*State\s*:\s*(\S+)", b)
            if m:
                states.append(m.group(1))
        if not states or all(s.upper() in {"N/A", "NA"} for s in states):
            return self.na("no NVSwitch fabric (Fabric Manager not applicable)")
        bad = [s for s in states if s not in {"Completed", "In", "Completed."}]
        if bad:
            return self.fail(f"Fabric Manager not ready: {sorted(set(bad))}")
        return self.ok(f"Fabric Manager ready ({len(states)} GPUs)")


@register
class GpuThermal(Module):
    spec = spec("G7")

    def run(self, ctx: Context) -> ModuleResult:
        rows = _parse_gpu_query(ctx.collect("gpu_query"))
        temps = [(r["index"], r["temp"]) for r in rows if r["temp"] is not None]
        if not temps:
            return self.na("no temperature data")
        hottest_idx, hottest = max(temps, key=lambda t: t[1])
        if hottest >= _TEMP_FAIL:
            return self.fail(
                f"gpu:{hottest_idx} at {hottest}°C (>= {_TEMP_FAIL})",
                scope=f"gpu:{hottest_idx}",
                evidence={"max_temp": hottest},
            )
        if hottest >= _TEMP_WARN:
            return self.warn(
                f"gpu:{hottest_idx} at {hottest}°C (>= {_TEMP_WARN})",
                scope=f"gpu:{hottest_idx}",
                evidence={"max_temp": hottest},
            )
        return self.ok(f"all GPUs <= {hottest}°C", evidence={"max_temp": hottest})
