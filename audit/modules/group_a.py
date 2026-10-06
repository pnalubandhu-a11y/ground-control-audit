"""Group A — host / NIC / system checks for preflight.

A1 pernic_routing_tables, A2 mtu_alignment, A3 eth0_control_plane,
A4 eth1_ipv6_health, A5 kernel_driver_firmware_alignment, A6 pcie_topology,
A7 hugepages_memory_tuning, A8 irq_affinity_alignment.

Each parses a host data source provided by the Context. Where the container
cannot see a host-level view (e.g. policy routing), the module degrades to NA
rather than guessing.
"""

from __future__ import annotations

import re

from ..core.context import Context
from ..core.result import ModuleResult
from .base import Module, register, spec

_JUMBO = 9000


def _blocks(text: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    cur: dict | None = None
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("### "):
            cur = {}
            out[line[4:].strip()] = cur
        elif cur is not None and ":" in line and not line.startswith("#"):
            k, _, v = line.partition(":")
            cur[k.strip()] = v.strip()
    return out


@register
class PerNicRouting(Module):
    spec = spec("A1")

    def run(self, ctx: Context) -> ModuleResult:
        text = ctx.collect("ip_rule")
        rules = [ln for ln in text.splitlines()
                 if ":" in ln and not ln.strip().startswith("#")]
        # per-NIC source routing => rules that look up a non-default table
        custom = [r for r in rules
                  if "lookup" in r and not re.search(r"lookup (local|main|default)", r)]
        if not rules:
            return self.na("no routing rules visible (needs host netns)")
        if not custom:
            return self.warn("no per-NIC policy routing rules found")
        return self.ok(f"{len(custom)} per-NIC policy routing rule(s) present")


@register
class MtuAlignment(Module):
    spec = spec("A2")

    def run(self, ctx: Context) -> ModuleResult:
        ifaces = _blocks(ctx.collect("net_links"))
        mtus = {i: int(f.get("mtu", "0") or 0) for i, f in ifaces.items()}
        if not mtus:
            return self.na("no NICs visible")
        distinct = set(mtus.values())
        if len(distinct) > 1:
            return self.fail(
                f"MTU mismatch across NICs: {mtus}",
                evidence={"mtus": mtus},
            )
        mtu = next(iter(distinct))
        if mtu < _JUMBO:
            return self.warn(f"MTU {mtu} below jumbo ({_JUMBO})", evidence={"mtu": mtu})
        return self.ok(f"jumbo MTU {mtu} aligned on {len(mtus)} NIC(s)")


@register
class Eth0ControlPlane(Module):
    spec = spec("A3")

    def run(self, ctx: Context) -> ModuleResult:
        ifaces = _blocks(ctx.collect("net_links"))
        eth0 = ifaces.get("eth0")
        if not eth0:
            return self.na("eth0 not visible")
        if eth0.get("operstate") != "up" or eth0.get("carrier") != "1":
            return self.fail(
                f"eth0 control plane down (operstate={eth0.get('operstate')}, "
                f"carrier={eth0.get('carrier')})",
                scope="eth0",
            )
        return self.ok("eth0 control plane up (carrier ok)")


@register
class Eth1Ipv6(Module):
    spec = spec("A4")

    def run(self, ctx: Context) -> ModuleResult:
        ifaces = _blocks(ctx.collect("net_links"))
        secondary = [i for i in ifaces if re.fullmatch(r"eth[1-9]\d*", i)]
        if not secondary:
            return self.na("no secondary ethernet NIC visible")
        v6 = ctx.collect("ipv6")
        missing = [i for i in secondary if i not in v6]
        if missing:
            return self.fail(f"no IPv6 on {', '.join(missing)}", scope=missing[0])
        return self.ok(f"IPv6 present on {', '.join(secondary)}")


@register
class KernelDriverFirmware(Module):
    spec = spec("A5")

    def run(self, ctx: Context) -> ModuleResult:
        kernel = ctx.collect("kernel").strip()
        drv = re.search(r"Driver Version:\s*([\d.]+)", ctx.collect("nvidia_smi"))
        fw = re.search(r"fw_ver:\s*([\w.]+)", ctx.collect("ib_sysfs"))
        parts = {
            "kernel": kernel or None,
            "nvidia": drv.group(1) if drv else None,
            "mlx_fw": fw.group(1) if fw else None,
        }
        missing = [k for k, v in parts.items() if not v]
        if missing:
            return self.fail(f"missing version info: {', '.join(missing)}")
        return self.ok(
            f"kernel {parts['kernel']}, driver {parts['nvidia']}, fw {parts['mlx_fw']}",
            evidence=parts,
        )


@register
class PcieTopology(Module):
    spec = spec("A6")
    # NUMA-local NIC relationships (anything but SYS reaches a NIC without UPI/QPI).
    _LOCAL = {"NODE", "PIX", "PXB", "PHB"}

    def run(self, ctx: Context) -> ModuleResult:
        """Validate the PCIe topology matrix is coherent (GPU↔NIC↔self).

        NIC-affinity *correctness* (which GPU should pair with which NIC) is
        C14 gpu_nic_affinity_health; A6 only checks the tree is readable and
        reports NUMA-local NIC coverage as evidence.
        """
        lines = [ln for ln in ctx.collect("nvidia_topo").splitlines() if ln.strip()]
        if not lines:
            return self.na("no topology output")
        header = lines[0].split()
        n_gpu = len([t for t in header if re.fullmatch(r"GPU\d+", t)])
        n_nic = len([t for t in header if re.fullmatch(r"NIC\d+", t)])
        if not n_gpu or not n_nic:
            return self.na("topology matrix has no GPU/NIC columns")

        gpu_rows, local = 0, 0
        for ln in lines[1:]:
            tok = ln.split()
            if not tok or not re.fullmatch(r"GPU\d+", tok[0]):
                continue
            gpu_rows += 1
            nic_vals = tok[1:1 + n_gpu + n_nic][n_gpu:n_gpu + n_nic]
            if self._LOCAL & set(nic_vals):
                local += 1

        if gpu_rows != n_gpu:
            return self.fail(
                f"topology matrix malformed ({gpu_rows} GPU rows, header says {n_gpu})"
            )
        if local == 0:
            return self.warn(
                f"no GPU has a NUMA-local NIC ({n_gpu} GPUs, {n_nic} NICs)",
                evidence={"gpus": n_gpu, "nics": n_nic, "numa_local": 0},
            )
        return self.ok(
            f"topology coherent: {n_gpu} GPUs, {n_nic} NICs; "
            f"{local}/{n_gpu} GPUs NUMA-local to a NIC",
            evidence={"gpus": n_gpu, "nics": n_nic, "numa_local": local},
        )


@register
class Hugepages(Module):
    spec = spec("A7")

    def run(self, ctx: Context) -> ModuleResult:
        mi = _parse_meminfo(ctx.collect("meminfo"))
        if "Hugepagesize" not in mi:
            return self.na("no hugepage info")
        reserved = mi.get("HugePages_Total", 0)
        thp = mi.get("AnonHugePages", 0)
        if reserved == 0 and thp == 0:
            return self.warn("no hugepages reserved and THP inactive")
        how = f"{reserved} reserved" if reserved else f"THP active ({thp} kB)"
        return self.ok(f"hugepages ok ({how}, size {mi['Hugepagesize']} kB)")


@register
class IrqAffinity(Module):
    spec = spec("A8")

    def run(self, ctx: Context) -> ModuleResult:
        raw = ctx.collect("interrupts").strip()
        try:
            count = int(raw.split()[0]) if raw else 0
        except ValueError:
            count = 0
        if count == 0:
            return self.warn("no mlx5 NIC IRQs found")
        return self.ok(f"{count} mlx5 NIC IRQ lines present")


def _parse_meminfo(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"(\w+):\s+(\d+)", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out
