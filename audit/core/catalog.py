"""The module catalog — the 51 checks, verbatim from the reference `audit -l`.

Data only (no check logic). Each entry carries enough metadata to drive the
`audit -l` view and, later, platform auto-detection and the runner.

Fields per DESIGN.md §3:
  id        — "G5"
  name      — "gpu_xid_errors" (preserved verbatim from the reference tool)
  group     — "A" host/NIC/system | "B" link/RDMA phys | "C" fabric/cluster | "G" GPU
  requires  — capability tags that must be satisfied or the module returns NA
  active    — True => needs --allow-active (perturbs the fabric), blocked for customer
  h100      — applicability on the H100 demo node (cw0bec): see H100 below

Only the IMEX/Blackwell modules carry an explicit `requires` today — those are
the ones DESIGN.md justifies as NA on H100. Platform auto-detection (requires ->
NA at run time) lands with the runner; `h100` drives the static `-l` display.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class H100:
    """Static applicability of a module on the H100 demo node (for `-l`)."""

    NATIVE = "native"    # ✅ runs natively on cw0bec
    PARTIAL = "partial"  # ⚠️ partially applicable
    NA = "na"            # 🚫 not applicable (Blackwell/IMEX-only)


@dataclass(frozen=True)
class ModuleSpec:
    """Static description of a check. The runnable Module wraps one of these."""

    id: str
    name: str
    group: str
    requires: frozenset[str] = field(default_factory=frozenset)
    active: bool = False
    h100: str = H100.NATIVE


def _m(id, name, group, *, requires=(), active=False, h100=H100.NATIVE):
    return ModuleSpec(id, name, group, frozenset(requires), active, h100)


# Group A — host / NIC / system (11)
_GROUP_A = [
    _m("A1", "pernic_routing_tables", "A"),
    _m("A2", "mtu_alignment", "A"),
    _m("A3", "eth0_control_plane", "A"),
    _m("A4", "eth1_ipv6_health", "A"),
    _m("A5", "kernel_driver_firmware_alignment", "A"),
    _m("A6", "pcie_topology", "A"),
    _m("A7", "hugepages_memory_tuning", "A"),
    _m("A8", "irq_affinity_alignment", "A"),
    _m("A9", "imex_readiness", "A", requires={"imex"}, h100=H100.NA),
    _m("A10", "enroot_pyxis", "A"),
    _m("A11", "rttcc_rdma", "A"),
]

# Group B — link / RDMA physical (14)
_GROUP_B = [
    _m("B1", "lldp_neighbors", "B"),
    _m("B2", "imex_state", "B", requires={"imex"}, h100=H100.NA),
    _m("B3", "nic_error_counters", "B"),
    _m("B4", "phy_lane_health", "B"),
    _m("B5", "physical_layer_health", "B"),
    _m("B6", "nic_thermal_health", "B"),
    _m("B7", "fw_driver_versions", "B"),
    _m("B8", "switch_signal_integrity", "B", h100=H100.PARTIAL),
    _m("B9", "link_layer_sanity", "B"),
    _m("B10", "rdma_link_and_auth", "B"),
    _m("B11", "pfc_ecn_congestion_ident", "B"),
    _m("B12", "rdma_device_health", "B"),
    _m("B13", "rdma_link_state", "B"),
    _m("B14", "rdma_counters", "B"),
]

# Group C — RDMA / fabric / cluster (16)
_GROUP_C = [
    _m("C1", "nic_stability", "C"),
    _m("C2", "rdma_config", "C"),
    _m("C3", "rdma_authn", "C"),
    _m("C4", "traffic_leak", "C", active=True),
    _m("C5", "reset_counters", "C"),
    _m("C6", "switch_correlation", "C", h100=H100.PARTIAL),
    _m("C7", "perf_smoke_test", "C", active=True),
    _m("C8", "latency", "C", active=True),
    _m("C9", "bandwidth", "C", active=True),
    _m("C10", "bandwidth_consistency", "C", active=True),
    _m("C11", "rdma_path_sanity", "C"),
    _m("C12", "imex_peer_topology_consistency", "C", requires={"imex"}, h100=H100.NA),
    _m("C13", "imex_rack_connectivity_health", "C", requires={"imex"}, h100=H100.NA),
    _m("C14", "gpu_nic_affinity_health", "C"),
    _m("C15", "nvswitch_path_health", "C", h100=H100.PARTIAL),
    _m("C16", "cluster_node_discovery", "C"),
]

# Group G — GPU (10)
_GROUP_G = [
    _m("G1", "gpu_count_gseries", "G"),
    _m("G2", "gpu_pcie_width", "G"),
    _m("G3", "gpu_ecc_errors", "G"),
    _m("G4", "gpu_row_remap", "G"),
    _m("G5", "gpu_xid_errors", "G"),
    _m("G6", "gpu_nvlink", "G"),
    _m("G7", "gpu_thermal_health", "G"),
    _m("G8", "gpu_bus_health", "G"),
    _m("G9", "gpu_fabric_manager", "G"),
    _m("G10", "gpu_p2p_nvlink", "G"),
]

MODULES: list[ModuleSpec] = [*_GROUP_A, *_GROUP_B, *_GROUP_C, *_GROUP_G]

# Extension modules — CoreWeave additions beyond the reference tool's 51 checks.
# Kept separate so the reference catalog (and its test) stays verbatim at 51.
# Group "N" = NCCL / collectives.
EXTENSION_MODULES: list[ModuleSpec] = [
    _m("N1", "nccl_transport_health", "N"),
]

# Everything the runner/registry can resolve (reference + extensions).
ALL_MODULES: list[ModuleSpec] = [*MODULES, *EXTENSION_MODULES]

# Convenience index by id, built once (covers extensions too).
MODULES_BY_ID: dict[str, ModuleSpec] = {m.id: m for m in ALL_MODULES}
