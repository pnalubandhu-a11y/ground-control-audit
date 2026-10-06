"""Group B — link / RDMA physical. Fabric counter modules for preflight.

B12 rdma_device_health, B13 rdma_link_state, B14 rdma_counters, and
B11 pfc_ecn_congestion_ident parse the IB sysfs dump; B3 nic_error_counters
parses ethernet NIC statistics. Scopes are device names (mlx5_4, eth1) so the
verdict engine can correlate on a shared rail.
"""

from __future__ import annotations

from ..core.context import Context
from ..core.result import ModuleResult
from .base import Module, register, spec

# B14 error-counter thresholds (aggregate since boot).
_HARD = {"link_downed": 0, "port_rcv_errors": 100}          # > => fail
_LANE = {"symbol_error": 1000, "link_error_recovery": 5,    # > => fail
         "local_link_integrity_errors": 5}
# B11 congestion indicators (hw_counters).
_CONGEST = {"out_of_sequence": 1000, "packet_seq_err": 1000}


def _parse_blocks(text: str) -> dict[str, dict]:
    """Parse '### name' + 'key: value' blocks into {name: {key: value}}."""
    blocks: dict[str, dict] = {}
    cur: dict | None = None
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("### "):
            cur = {}
            blocks[line[4:].strip()] = cur
        elif cur is not None and ":" in line and not line.startswith("#"):
            k, _, v = line.partition(":")
            cur[k.strip()] = v.strip()
    return blocks


def _int(d: dict, key: str) -> int:
    try:
        return int(d.get(key, "0") or "0")
    except ValueError:
        return 0


@register
class RdmaDeviceHealth(Module):
    spec = spec("B12")

    def run(self, ctx: Context) -> ModuleResult:
        devs = _parse_blocks(ctx.collect("ib_sysfs"))
        if not devs:
            return self.na("no RDMA devices found")
        missing = [d for d, f in devs.items() if not f.get("fw_ver")]
        if missing:
            return self.fail(
                f"RDMA device(s) missing firmware info: {', '.join(missing)}",
                scope=missing[0],
            )
        fw = sorted({f.get("fw_ver", "") for f in devs.values()})
        return self.ok(
            f"{len(devs)} HCAs healthy (fw {', '.join(fw)})",
            evidence={"devices": list(devs)},
        )


@register
class RdmaLinkState(Module):
    spec = spec("B13")

    def run(self, ctx: Context) -> ModuleResult:
        devs = _parse_blocks(ctx.collect("ib_sysfs"))
        if not devs:
            return self.na("no RDMA devices found")
        down = [
            d for d, f in devs.items()
            if "ACTIVE" not in f.get("state", "").upper()
            or "LINKUP" not in f.get("phys_state", "").upper().replace(" ", "")
        ]
        if down:
            return self.fail(
                f"RDMA port(s) not Active/LinkUp: {', '.join(down)}",
                scope=down[0],
                evidence={"down": down},
            )
        return self.ok(f"all {len(devs)} ports Active/LinkUp")


@register
class RdmaCounters(Module):
    spec = spec("B14")

    def run(self, ctx: Context) -> ModuleResult:
        devs = _parse_blocks(ctx.collect("ib_sysfs"))
        if not devs:
            return self.na("no RDMA devices found")
        worst: tuple[str, list[str]] | None = None
        for d, f in devs.items():
            hits = [
                f"{k}={_int(f, 'counters.' + k)}"
                for k, lim in {**_HARD, **_LANE}.items()
                if _int(f, "counters." + k) > lim
            ]
            if hits and worst is None:
                worst = (d, hits)
        if worst:
            d, hits = worst
            return self.fail(
                f"RDMA error counters rising on {d}: {', '.join(hits)}",
                scope=d,
                evidence={"counters": hits},
            )
        return self.ok("RDMA error counters nominal")


@register
class PfcEcnCongestion(Module):
    spec = spec("B11")

    def run(self, ctx: Context) -> ModuleResult:
        devs = _parse_blocks(ctx.collect("ib_sysfs"))
        if not devs:
            return self.na("no RDMA devices found")
        for d, f in devs.items():
            hits = [
                f"{k}={_int(f, 'hw_counters.' + k)}"
                for k, lim in _CONGEST.items()
                if _int(f, "hw_counters." + k) > lim
            ]
            if hits:
                return self.warn(
                    f"congestion / retransmits on {d}: {', '.join(hits)}",
                    severity=2,
                    scope=d,
                    evidence={"congestion": hits},
                )
        return self.ok("no PFC/ECN congestion signatures")


@register
class NicErrorCounters(Module):
    spec = spec("B3")

    def run(self, ctx: Context) -> ModuleResult:
        ifaces = _parse_blocks(ctx.collect("net_stats"))
        if not ifaces:
            return self.na("no NIC statistics found")
        for ifc, f in ifaces.items():
            errs = _int(f, "rx_errors") + _int(f, "tx_errors") + _int(f, "rx_crc_errors")
            if errs > 0:
                return self.fail(
                    f"NIC {ifc} error counters: rx={_int(f,'rx_errors')} "
                    f"tx={_int(f,'tx_errors')} crc={_int(f,'rx_crc_errors')}",
                    scope=ifc,
                    evidence={"iface": ifc},
                )
        return self.ok(f"{len(ifaces)} NICs error-free")
