# `audit` — Ground Control

**CoreWeave GPU-Fabric Flight Director**

*Moonshot hackathon (FC26) — Team: Ground Control — Commander: Prashanth Nalubandhu*

Status: **Design** · Target v0.1 · Deadline: 2026-09-24

---

## 1. What it is

A single CLI, `audit`, that runs deep GPU-fabric and RDMA health checks on a
node (or across a cluster), correlates the raw signals into **root-cause
verdicts**, and prints an action a human can take in 30 seconds.

It is modeled on the OCI "GB300/GB200 RDMA Checker" concept but rebuilt for
CoreWeave, and — critically — designed to be run by **three different
audiences** from the same binary.

### The moon we are landing

> Today, when a training run stalls on a GB200/H100 cluster, an engineer spends
> *hours* manually correlating `ibstat`, `nvidia-smi`, `dcgmi`, NCCL logs, IMEX
> topology, and sysfs counters across many nodes to find the one bad rail,
> drifted link, or flaky GPU. The moonshot: one command that runs 40+ checks in
> parallel and returns a named root cause with a fix — collapsing a multi-hour
> war-room into a 30-second answer.

---

## 2. Design constraint: one binary, three audiences

Everything pivots on this. The same checks run for everyone; a **profile**
changes only three things — *safety*, *redaction*, and *output packaging*.

| Profile | Audience | Safety | Redaction | Output |
|---|---|---|---|---|
| `internal` *(default)* | SA / ops | Active tests allowed with `--allow-active` | None — real hostnames, IPs, serials | Terminal + JSON |
| `customer` | Customer self-serve troubleshooting | **Read-only enforced** (active tests blocked) | Internal IPs / hostnames / serials masked | Terminal + JSON, every FAIL carries plain-English remediation + "contact CoreWeave support" escalation |
| `support` | CoreWeave support team | Read-only by default | Configurable | **Support bundle** (`audit-bundle-<host>-<ts>.tar.gz`): JSON + raw evidence to attach to a ticket |

The profile is the only branch point for audience behavior. Modules and the
verdict engine are audience-agnostic.

---

## 3. Module system

Every check is a **Module** with a fixed contract so modules stay independent,
individually testable, and safe to run in parallel.

```python
class Status(Enum):
    PASS = "PASS"      # healthy
    WARN = "WARN"      # degraded but functional
    FAIL = "FAIL"      # broken / actionable
    SKIP = "SKIP"      # not selected / user-skipped
    NA   = "NA"        # not applicable on this platform (e.g. IMEX on H100)
    ERROR = "ERROR"    # the check itself failed to run

@dataclass
class ModuleResult:
    id: str            # "G5"
    name: str          # "gpu_xid_errors"
    status: Status
    severity: int      # 0..3 — drives verdict ranking
    summary: str       # one human line
    evidence: dict     # raw parsed data (nvidia-smi / ibstat / sysfs / dcgmi)
    remediation: str   # what to do; wording is profile-aware
    scope: str         # "node" | "cluster" | "gpu:3" | "mlx5_4"
    duration_ms: int

class Module:
    id: str
    name: str
    group: str                 # "A" | "B" | "C" | "G"
    requires: set[str]         # {"ib","nvswitch","dcgm","blackwell","imex",...}
    active: bool = False        # True => needs --allow-active
    def run(self, ctx: Context) -> ModuleResult: ...
```

### 3.1 Platform auto-detection

At startup the runner probes the host and builds a capability set
(`{ib, roce, nvswitch, dcgm, fabric_manager, blackwell, imex, slurm/pyxis...}`).
A module whose `requires` is not satisfied returns **`NA`** — it never crashes.

The actual demo node — CoreWeave `cw0bec` — is **8× NVIDIA RTX PRO 6000
Blackwell Server Edition** (not H100, despite earlier framing). Most modules run
natively there; the GB200/GB300-specific ones auto-degrade to `NA`:

- **A9** `imex_readiness`, **B2** `imex_state`, **C12** `imex_peer_topology_consistency`,
  **C13** `imex_rack_connectivity_health` → `NA` (IMEX requires GB200/GB300).
- **G6** `gpu_nvlink` → `NA` on these PCIe cards (no NVLink fabric).

This auto-detection is a deliberate demo beat: *"it detects the platform and
runs exactly what applies."*

### 3.2 Module catalog

IDs and names are preserved verbatim from the reference tool. The `H100` column
is the reference-design applicability target (H100 is the broad fleet platform);
the live demo node `cw0bec` is RTX PRO 6000 Blackwell, where the same NA rules
apply (IMEX + NVLink degrade to `NA`). `H100` column:
✅ runs natively · ⚠️ partial · 🚫 `NA` (Blackwell/IMEX-only) ·
🔴 active (needs `--allow-active`).

#### Group A — host / NIC / system

| ID | Name | Checks | H100 |
|----|------|--------|------|
| A1 | pernic_routing_tables | Per-NIC policy routing rules correct for multi-NIC RDMA | ✅ |
| A2 | mtu_alignment | MTU (jumbo 9000) consistent across NICs and to switch | ✅ |
| A3 | eth0_control_plane | Management / control-plane NIC health | ✅ |
| A4 | eth1_ipv6_health | Secondary NIC IPv6 health | ✅ |
| A5 | kernel_driver_firmware_alignment | Kernel / driver / firmware versions aligned to golden set | ✅ |
| A6 | pcie_topology | PCIe topology tree (GPU↔NIC↔switch) | ✅ |
| A7 | hugepages_memory_tuning | Hugepages + memory tuning present | ✅ |
| A8 | irq_affinity_alignment | NIC IRQs pinned to correct NUMA node | ✅ |
| A9 | imex_readiness | IMEX (NVLink domain) readiness | 🚫 |
| A10 | enroot_pyxis | enroot/pyxis container runtime for Slurm | ✅ |
| A11 | rttcc_rdma | RTTCC (RTT congestion control) RDMA tuning | ✅ |

#### Group B — link / RDMA physical

| ID | Name | Checks | H100 |
|----|------|--------|------|
| B1 | lldp_neighbors | LLDP neighbor discovery (verifies cabling) | ✅ |
| B2 | imex_state | IMEX daemon state | 🚫 |
| B3 | nic_error_counters | NIC error counters | ✅ |
| B4 | phy_lane_health | Per-lane PHY health (FEC / BER per lane) | ✅ |
| B5 | physical_layer_health | Physical layer (optics, signal) | ✅ |
| B6 | nic_thermal_health | NIC / transceiver temperature | ✅ |
| B7 | fw_driver_versions | Firmware / driver version check | ✅ |
| B8 | switch_signal_integrity | Switch-side signal integrity | ⚠️ |
| B9 | link_layer_sanity | Link-layer sanity | ✅ |
| B10 | rdma_link_and_auth | RDMA link + auth | ✅ |
| B11 | pfc_ecn_congestion_ident | PFC / ECN congestion identification | ✅ |
| B12 | rdma_device_health | RDMA device (ibstat) health | ✅ |
| B13 | rdma_link_state | RDMA port state (LinkUp / Active) | ✅ |
| B14 | rdma_counters | RDMA port counters (symbol errors, retransmits) | ✅ |

#### Group C — RDMA / fabric / cluster

| ID | Name | Checks | H100 |
|----|------|--------|------|
| C1 | nic_stability | Link flap / stability over a window | ✅ |
| C2 | rdma_config | RDMA config (GID, PKEY, index) | ✅ |
| C3 | rdma_authn | RDMA authentication | ✅ |
| C4 | traffic_leak | Traffic leaking onto wrong interface | 🔴 |
| C5 | reset_counters | Baseline / reset counters | ✅ |
| C6 | switch_correlation | Correlate node view against switch view | ⚠️ |
| C7 | perf_smoke_test | Quick perf smoke test | 🔴 |
| C8 | latency | RDMA latency (`ib_write_lat`) | 🔴 |
| C9 | bandwidth | RDMA bandwidth (`ib_write_bw`) | 🔴 |
| C10 | bandwidth_consistency | Bandwidth consistency across pairs | 🔴 |
| C11 | rdma_path_sanity | RDMA path / routing sanity | ✅ |
| C12 | imex_peer_topology_consistency | IMEX peer topology consistency | 🚫 |
| C13 | imex_rack_connectivity_health | IMEX rack connectivity | 🚫 |
| C14 | gpu_nic_affinity_health | GPU↔NIC affinity correctness | ✅ |
| C15 | nvswitch_path_health | NVSwitch path health | ⚠️ |
| C16 | cluster_node_discovery | Cluster node discovery | ✅ |

#### Group G — GPU

| ID | Name | Checks | H100 |
|----|------|--------|------|
| G1 | gpu_count_gseries | GPU count / expected SKU present | ✅ |
| G2 | gpu_pcie_width | GPU PCIe link width & gen | ✅ |
| G3 | gpu_ecc_errors | GPU ECC errors | ✅ |
| G4 | gpu_row_remap | GPU row-remap (memory) status | ✅ |
| G5 | gpu_xid_errors | GPU XID errors (nvidia-smi / dmesg) | ✅ |
| G6 | gpu_nvlink | NVLink link status | ✅ |
| G7 | gpu_thermal_health | GPU thermals | ✅ |
| G8 | gpu_bus_health | GPU bus health | ✅ |
| G9 | gpu_fabric_manager | NVIDIA Fabric Manager status | ✅ |
| G10 | gpu_p2p_nvlink | P2P over NVLink | ✅ |

### 3.3 Use-case bundles

Bundles are **data** (YAML), not code — adding one is a config change.
Preserved verbatim from the reference:

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

---

## 4. CLI

```
audit -l                         # list modules + bundles (the colored view)
audit -m A1,B3,C16,G7            # run explicit modules
audit -u ncc_slow               # run a use-case bundle
audit -u preflight --json       # machine-readable output
audit -u network_perf --allow-active     # unlock active perf tests
audit --profile customer -u preflight    # customer-safe, redacted
audit --profile support -u ncc_slow --bundle   # support tarball
audit -u ncc_slow --nodes gpu-[210-214]  # cluster fan-out (stretch)
```

Flags: `-l/--list`, `-m/--modules`, `-u/--usecase`, `--profile`, `--json`,
`--bundle`, `--allow-active`, `--nodes`, `--no-verdict`, `-v/--verbose`.

Exit codes: `0` all pass · `1` warnings · `2` failures — drops into CI /
preflight gates.

---

## 5. Execution engine

- **Parallel** module execution via a thread pool (checks are I/O-bound — they
  shell out to `ibstat`, `nvidia-smi`, `dcgmi`, sysfs).
- **Per-module timeout** so one hung command can't stall the run.
- **Cluster fan-out** *(stretch)*: `--nodes` runs the same audit over SSH across
  SUNK nodes and aggregates results — the headline H100 demo.
- **Safety tiers**: read-only modules always run. Active modules (C4, C7, C8,
  C9, C10) require `--allow-active` and are hard-blocked in `customer`/`support`
  profiles.

---

## 6. Verdict engine (the moonshot differentiator) 🚀

Raw check results feed a **correlation layer** that emits *named root causes*,
not counters. Rules are **YAML-authored** and extensible.

A rule matches a set of module statuses on a **shared scope** (same NIC, same
GPU, same node) and emits a verdict with confidence + action.

```yaml
# verdicts/rules.yaml
- id: bad_optic_rail
  when:
    all:
      - {module: B4, status: [WARN, FAIL]}      # phy lane degraded
      - {module: B14, status: [WARN, FAIL]}     # rising symbol errors
      - {module: C8, status: [WARN, FAIL]}      # latency spike
    same_scope: nic                              # all on the same mlx5_*
  verdict: "Bad optic/cable on {scope} — drain node, replace transceiver."
  confidence: high
  severity: 3
```

Ships with rules for the marquee failure modes:

1. **bad_optic_rail** — B4 + B14 + C8 on same NIC → bad cable/transceiver.
2. **ncc_slow_congestion** — B11 (PFC/ECN) + C11 (path) + C1 (flaps) → fabric
   congestion / misrouting slowing NCCL.
3. **gpu_fault_degrade** — G5 (XID) + G3 (ECC) / G4 (row-remap) on same GPU →
   failing GPU, cordon and RMA.
4. **fabric_manager_down** — G9 down + G6/G10 NVLink errors → Fabric Manager /
   NVSwitch path issue.

Output leads with the verdict banner, then the supporting module results.
`--no-verdict` falls back to plain per-module output (parity with the original
OCI tool).

---

## 7. Output & packaging

- **Terminal**: colored, grouped exactly like `audit -l`, with a verdict banner
  at the top of a run.
- **`--json`**: full structured result set (feeds Mission Control / pipelines).
- **Support bundle** (`--bundle`): tar of JSON + raw evidence, redaction applied
  per profile.

---

## 8. Repository layout

This is the **target** layout. Two deltas in the shipped build: platform
detection is folded into `runner.py` (a module whose `requires` aren't in the
Context capability set returns `NA`) rather than a separate `platform_detect.py`;
and `group_c.py` (the C-group fabric/cluster modules) is future work — the
shipped groups are A, B, G, plus an `N` NCCL extension. Everything else below
exists as shown.

```
hackathon/audit/
├── pyproject.toml
├── DESIGN.md                 # this document
├── README.md
├── audit/
│   ├── cli.py                # argparse entrypoint
│   ├── core/
│   │   ├── catalog.py        # the 51 reference modules (+ N extensions)
│   │   ├── registry.py       # module + bundle registry
│   │   ├── result.py         # ModuleResult, Status, Verdict
│   │   ├── runner.py         # execution + platform detection (requires→NA)
│   │   ├── context.py        # host capabilities, cached probes, fixture mode
│   │   ├── profile.py        # internal / customer / support
│   │   ├── nodes.py          # --nodes range expansion
│   │   └── redact.py         # profile-based redaction
│   ├── modules/
│   │   ├── base.py           # Module contract + impl registry
│   │   ├── group_a.py
│   │   ├── group_b.py
│   │   ├── group_g.py
│   │   └── group_n.py        # NCCL extension (group_c.py = future)
│   ├── verdicts/
│   │   ├── engine.py
│   │   └── rules.yaml
│   ├── bundles/usecases.yaml
│   └── render/
│       ├── terminal.py
│       ├── json_out.py
│       └── bundle.py
├── fixtures/                 # recorded cw0bec outputs (run + test anywhere)
└── tests/
```

---

## 9. 24-hour build plan

### MVP (must-have for the demo)
- CLI: `-l`, `-m`, `-u`, `--profile`, `--json`.
- Registry + module contract + platform auto-detect → `NA`.
- ~12 highest-impact modules **real on `cw0bec` (Blackwell)**:
  G1, G3, G5, G6, G7 (GPU) · B3, B12, B13, B14 (RDMA) · A2, A6 (host) · C16
  (discovery).
- Verdict engine + **3–4 rules** (§6).
- Bundles: `preflight`, `ncc_slow`, `gpu_fault`.
- Terminal + JSON output.
- Profiles: `internal` + `customer` (redaction).

### Stretch
- Remaining modules · `--nodes` SSH fan-out across SUNK · support bundle tar ·
  full `customer` remediation copy.

### Testing
- Every module is built against a **recorded fixture** — real
  `nvidia-smi` / `ibstat` / `dcgmi` output captured from cw0bec — so the tool is
  TDD-able and the demo works even if the cluster is flaky during judging.

---

## 10. Non-goals (YAGNI for the hackathon)
- Continuous monitoring / daemon mode (this is point-in-time).
- Web UI (JSON output feeds any existing dashboard).
- Auto-remediation (we recommend actions; we do not take them).
- Windows / non-Linux hosts.
