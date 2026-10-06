# 🚀 Ground Control — The 3-Year Moonshot & the 24-Hour Landing

*FC26 Moonshot track — "Powering the Impossible." Declare a moon 3+ years away,
land a working version in 24 hours.*

This document shows **the full destination**, **every capability in the reference
tool**, and **exactly what we land at the hackathon**.

---

## 1. The Moon

> **A GPU-fabric flight director that keeps a 100,000-GPU fleet healthy without a
> human in the loop** — it predicts a rail or GPU failing *before* it kills a
> training run, correlates 50+ raw signals into a single named root cause, and
> closes the loop by draining, cordoning, or scheduling an RMA on its own.

Why it's "3+ years away": today this work is manual, reactive, and expert-bound.
An engineer opens ten terminals, greps counters, and pattern-matches from memory.
The moon is to make that expertise **autonomous, predictive, and fleet-scale**.

**What we land in 24 hours:** the *walking skeleton* of that flight director —
the module framework, platform auto-detection, and the verdict-correlation engine
that every autonomous layer later plugs into. It runs live on CoreWeave `cw0bec`
(RTX PRO 6000 Blackwell) today and returns real root-cause verdicts. Same
architecture; the future is depth, not a rewrite.

---

## 2. The full destination (everything in the picture)

The reference `audit -l` exposes **51 checks in 4 groups** and **12 use-case
bundles**. This is the complete v1.0 checker — the foundation of the moonshot.

### Group A — host / NIC / system (11)
`A1 pernic_routing_tables` · `A2 mtu_alignment` · `A3 eth0_control_plane` ·
`A4 eth1_ipv6_health` · `A5 kernel_driver_firmware_alignment` ·
`A6 pcie_topology` · `A7 hugepages_memory_tuning` · `A8 irq_affinity_alignment` ·
`A9 imex_readiness` · `A10 enroot_pyxis` · `A11 rttcc_rdma`

### Group B — link / RDMA physical (14)
`B1 lldp_neighbors` · `B2 imex_state` · `B3 nic_error_counters` ·
`B4 phy_lane_health` · `B5 physical_layer_health` · `B6 nic_thermal_health` ·
`B7 fw_driver_versions` · `B8 switch_signal_integrity` · `B9 link_layer_sanity` ·
`B10 rdma_link_and_auth` · `B11 pfc_ecn_congestion_ident` ·
`B12 rdma_device_health` · `B13 rdma_link_state` · `B14 rdma_counters`

### Group C — RDMA / fabric / cluster (16)
`C1 nic_stability` · `C2 rdma_config` · `C3 rdma_authn` · `C4 traffic_leak` ·
`C5 reset_counters` · `C6 switch_correlation` · `C7 perf_smoke_test` ·
`C8 latency` · `C9 bandwidth` · `C10 bandwidth_consistency` ·
`C11 rdma_path_sanity` · `C12 imex_peer_topology_consistency` ·
`C13 imex_rack_connectivity_health` · `C14 gpu_nic_affinity_health` ·
`C15 nvswitch_path_health` · `C16 cluster_node_discovery`

### Group G — GPU (10)
`G1 gpu_count_gseries` · `G2 gpu_pcie_width` · `G3 gpu_ecc_errors` ·
`G4 gpu_row_remap` · `G5 gpu_xid_errors` · `G6 gpu_nvlink` ·
`G7 gpu_thermal_health` · `G8 gpu_bus_health` · `G9 gpu_fabric_manager` ·
`G10 gpu_p2p_nvlink`

### Use-case bundles (12)
| Bundle | Modules |
|--------|---------|
| thermal | A3, G7, G1, G6 |
| imex_fabric | A9, B2, C12, C13, C15, G6, G9 |
| cluster_drift | C6, C10, C11, C12, C13, C14, C15, C16 |
| rdma_auth | C3, B10, B13, B14 |
| preflight | A1, A2, A3, A4, A5, A6, A7, A8, A9, B3, B11, B12, B13, B14, G1, G3, G5, G6, G7, G8, G9 |
| nvlink_health | G6, G10, C15, A6 |
| ncc_slow | A1, A2, A6, B11, B12, B13, B14, C1, C2, C11, C14, G6, G10 |
| topology | A2, A6, A8, B11, C14, G2, G8 |
| gpu_fault | G1, G2, G3, G4, G5, G6, G7, G8, G9, G10, A6, A8 |
| control_plane | A3, A4, A1, C4, C6 |
| network_perf | B3, B11, B12, B13, B14, C7, C8, C9, C10 |
| rdma_debug | A1, B3, B11, B12, B13, B14, C1, C2, C3, C4, C11 |

*(Full per-module descriptions and H100 applicability in [DESIGN.md](./DESIGN.md).)*

---

## 3. The 3-year plan

Four phases. Each phase is usable on its own; each is a superset of the last.
The hackathon lands **Phase 0** — a vertical slice through the whole stack.

```
 Phase 0        Phase 1            Phase 2               Phase 3
 24 HOURS       ~Q4 2026 (3 mo)    2027 (12 mo)          2028–2029 (36 mo)
 Walking        Complete           Fleet & Continuous    Autonomous
 Skeleton       Checker            (Mission Control)      Flight Director
 ──────────►    ──────────────►    ──────────────────►   ────────────────► THE MOON
 12 modules     all 51 modules     always-on + baselines  predicts + self-heals
 3-4 verdicts   full verdict lib   drift across fleet     closed-loop remediation
 1 node live    cluster fan-out    time-series history    scheduler-gated jobs
```

### Phase 0 — Walking Skeleton *(the hackathon, 24h)*
The end-to-end path proven on real hardware:
- CLI (`-l`, `-m`, `-u`, `--profile`, `--json`), module contract, registry.
- **Platform auto-detection** → IMEX/NVLink checks degrade to `NA` on `cw0bec`.
- **12 MVP modules** running live on CoreWeave `cw0bec` (RTX PRO 6000 Blackwell) (§4).
- **Verdict engine + 3–4 correlation rules** (the moonshot differentiator).
- Bundles `preflight`, `ncc_slow`, `gpu_fault`.
- Three-audience profiles: `internal` + `customer` (redaction).
- Fixtures so the demo is bullet-proof even if the cluster hiccups.

**Deliverable:** `audit -u gpu_fault` on a live `cw0bec` node returns a named root
cause with an action.

### Phase 1 — Complete Checker *(~3 months)*
Everything in the picture, production-hardened:
- **All 51 modules**, all 12 bundles, on both H100 and GB200/GB300.
- All three profiles hardened (customer redaction, support bundle tarball).
- **Cluster fan-out** (`--nodes`) over SSH / Slurm across a rack.
- Active-test tier (C7–C10 perf/latency/bandwidth) behind `--allow-active`.
- Golden-config baselines for A5 / B7 firmware-driver alignment.
- Ship to the CoreWeave support team + customer-facing troubleshooting docs.

### Phase 2 — Fleet & Continuous *(~12 months)*
From point-in-time to always-on, wired into Mission Control:
- Daemon / DaemonSet mode; scheduled audits across the fleet.
- **Historical baselining** — counters written to ClickHouse/Prometheus; verdicts
  compare against a node's own history, not just thresholds.
- **Drift detection** at fleet scale (`cluster_drift` becomes continuous).
- Grafana dashboards + alerting from `--json` output.
- Node-health scoreboard: which nodes to drain, ranked.

### Phase 3 — Autonomous Flight Director *(~36 months — the moon)*
- **Predictive failure**: ML over counter time-series flags a rail/GPU degrading
  *before* it faults (rising FEC/symbol errors → "this optic dies in ~48h").
- **Learned correlation**: verdict rules mined from historical incidents, not
  hand-authored — the engine gets smarter as the fleet ages.
- **Closed-loop remediation**: auto-drain, cordon, reset counters, open RMA,
  reroute — with human-approval guardrails.
- **Scheduler integration**: SUNK/Slurm preflight-gates jobs so a bad node never
  gets a training run in the first place.

---

## 4. Hackathon MVP — exact scope

**12 modules**, chosen for maximum demo impact and because they run natively on
`cw0bec` (RTX PRO 6000 Blackwell — no GB200/IMEX dependency):

| # | Module | Group | Why it's in the MVP |
|---|--------|-------|---------------------|
| 1 | G1 gpu_count_gseries | GPU | Fast, always-visible sanity check |
| 2 | G3 gpu_ecc_errors | GPU | Classic silent GPU degradation |
| 3 | G5 gpu_xid_errors | GPU | #1 signal of a failing GPU |
| 4 | G6 gpu_nvlink | GPU | Feeds the Fabric Manager verdict |
| 5 | G7 gpu_thermal_health | GPU | Easy live demo (thermals move) |
| 6 | B3 nic_error_counters | RDMA phys | Feeds the bad-cable verdict |
| 7 | B12 rdma_device_health | RDMA phys | ibstat device state |
| 8 | B13 rdma_link_state | RDMA phys | Port up/active — core RDMA health |
| 9 | B14 rdma_counters | RDMA phys | Symbol errors → bad-cable verdict |
| 10 | A2 mtu_alignment | host | Common real-world misconfig |
| 11 | A6 pcie_topology | host | Ties GPU↔NIC affinity story together |
| 12 | C16 cluster_node_discovery | cluster | Sets up the fan-out narrative |

**MVP bundles:** `preflight`, `ncc_slow`, `gpu_fault`.

**MVP verdict rules (3–4):**
1. `bad_optic_rail` — B4/B14 + B3 + latency on same NIC → replace transceiver.
2. `ncc_slow_congestion` — B11 + C11 + C1 → fabric congestion slowing NCCL.
3. `gpu_fault_degrade` — G5 + G3/G4 on same GPU → cordon & RMA.
4. `fabric_manager_down` — G9 down + G6/G10 errors → Fabric Manager / NVSwitch.

**Explicitly out of scope for 24h (Phase 1+):** the other 39 modules, cluster
SSH fan-out, active perf tests (C7–C10), support-bundle tarball, continuous mode,
prediction, and remediation.

---

## 5. The pitch in one line

> We declared a moon that's **3 years out** — an autonomous, predictive,
> fleet-scale GPU-fabric flight director — and in **24 hours** we landed the
> vertical slice that proves it: real checks on real `cw0bec` Blackwell hardware, correlated
> into a root-cause verdict a human can act on in 30 seconds. Everything above it
> is depth on the same spine.
