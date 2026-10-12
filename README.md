# 🛰️ Ground Control — `audit`

**CoreWeave GPU-Fabric Flight Director**

A single CLI that runs deep GPU-fabric & RDMA health checks on a node (or across
a cluster), correlates the raw signals into **root-cause verdicts**, and prints
an action a human can take in 30 seconds.

> _Moonshot hackathon (FC26) · Team **Ground Control**_

---

## The moon we're landing

Today, when a training run stalls on a GB200/H100 cluster, an engineer spends
**hours** manually correlating `ibstat`, `nvidia-smi`, `dcgmi`, NCCL logs, IMEX
topology, and sysfs counters across many nodes to find the one bad rail, drifted
link, or flaky GPU.

**The moonshot:** one command that runs 40+ checks in parallel and returns a
*named root cause with a fix* — collapsing a multi-hour war-room into a 30-second
answer.

```console
$ audit -u ncc_slow

  🔴 VERDICT: Bad optic/cable on mlx5_4 (GPU-214) — drain node, replace transceiver.   [confidence: high]

  B4  phy_lane_health ........ FAIL   lane 2 FEC uncorrectable rising
  B14 rdma_counters .......... FAIL   symbol_error_counter +18k/5m on mlx5_4
  C8  latency ................ WARN   p99 12.4us (baseline 3.1us) on mlx5_4
  ...
```

---

## Why it's different

| | Original OCI checker | Ground Control |
|---|---|---|
| Output | Per-check PASS/FAIL counters | **Root-cause verdicts** + action |
| Audience | One (ops) | **Three** — internal, customer, support |
| Extensibility | Hardcoded | YAML **bundles + verdict rules** |
| Platform | GB200/GB300 | Auto-detects; runs what applies (H100 → GB300) |

### One binary, three audiences
The same checks; a `--profile` flag changes only *safety*, *redaction*, and
*packaging*:

- **`internal`** (default) — full detail, real hostnames, active tests allowed.
- **`customer`** — read-only enforced, internal identifiers redacted, plain-English remediation.
- **`support`** — produces a `audit-bundle-*.tar.gz` to attach to a ticket.

### The moonshot differentiator: the Verdict Engine 🚀
Raw check results feed a YAML-authored **correlation layer** that maps sets of
failing modules *on a shared scope* (same NIC / GPU / node) into named root
causes — bad cable, fabric congestion, failing GPU, Fabric Manager down.

---

## Usage (target)

```bash
audit -l                        # list all modules + use-case bundles
audit -m A1,B3,C16,G7           # run explicit modules
audit -u ncc_slow               # run a use-case bundle
audit -u preflight --json       # machine-readable
audit --profile customer -u preflight    # customer-safe, redacted
audit -u ncc_slow --nodes gpu-[210-214]  # cluster fan-out
```

Modules are grouped **A** (host/NIC/system), **B** (link/RDMA physical),
**C** (RDMA/fabric/cluster), **G** (GPU) — 51 checks, 12 use-case bundles.

📄 **[DESIGN.md](./DESIGN.md)** — full catalog, module contract, architecture.
🚀 **[ROADMAP.md](./ROADMAP.md)** — the 3-year moonshot, phased plan, and exact 24-hour MVP scope.
🎬 **[DEMO.md](./DEMO.md)** — the 7-beat demo runbook (exact commands + talking points).

---

## Status

| | |
|---|---|
| Design | ✅ [DESIGN.md](./DESIGN.md) |
| Verdict engine | Rules engine, marquee rules |
| Demo target | CoreWeave `cw0bec` cluster — RTX PRO 6000 Blackwell (fixtures-first) |
| Code | ✅ 91 tests passing |

---

## Crew

- **Prashanth Nalubandhu** (Mission Commander) — pnalubandhu@coreweave.com
- **L. Sahu** — lsahu@coreweave.com

---

## Development

```bash
# (once code lands)
pip install -e .
audit -l
pytest
```

Built for the CoreWeave FC26 **Moonshot** track — _Powering the Impossible._
