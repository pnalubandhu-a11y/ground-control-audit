# 🛰️ Ground Control — Demo Runbook

The exact 8-beat sequence for judging. **Fixtures-first: every command below
works with zero cluster access**, so a flaky network can't break the demo.

## What you're watching

**Ground Control (`audit`)** is a GPU-fabric & RDMA health checker for CoreWeave
clusters. It runs 40+ host / network / GPU checks and — the differentiator — a
**verdict engine** correlates the raw signals on a shared scope (same NIC / GPU /
node) into a **named root cause with a 30-second fix**, instead of a wall of
PASS/FAIL lines. The same binary serves **three audiences** through one
`--profile` flag: `internal` (full detail), `customer` (read-only, redacted,
plain-English fixes + a self-serve menu), and `support` (JSON + a ticket bundle).

**The arc to watch** (what the rubric scores): **Problem** — diagnosing a stalled
run is hours of manual correlation across ten terminals → **Solution** — one
command returns one named cause with the fix → **Prototype** — real checks and the
verdict engine running right here → **Impact** — hours collapse to 30 seconds, and
customers self-diagnose straight into a support handoff.

**About the data:** every beat runs on **recorded fixtures** so it works with zero
cluster access. Some are *real captures* from a live CoreWeave `cw0bec` Blackwell
node (the healthy node, the NCCL-on-TCP logs); the fault scenarios (dead GPU, dead
rail) are *synthetic* — you can't break real hardware on cue. The code path is
identical in `live` mode (`audit` reads the node's real `nvidia-smi`, IB sysfs,
NCCL log); fixtures only swap the data source — so this is the real tool, not a
mockup.

## Setup (once, before you present)

```bash
cd hackathon/audit
python3 -m venv .venv && ./.venv/bin/pip install -q -e ".[dev]"
alias audit=./.venv/bin/audit        # or: source .venv/bin/activate
```

**Run from a real terminal** (not piped) so colors + emoji render — piped output
drops color by design.

Optional sanity check right before you go on:

```bash
./.venv/bin/pytest -q          # expect: 103 passed
```

## Fastest path: the guided script

```bash
./demo.sh            # press Enter to advance through each beat (talking points on screen)
./demo.sh --auto     # no pauses — for a rehearsal or screen recording
./demo.sh --video    # the 3-min judge cut: only the 6 beats in SUBMISSION.md §1
./demo.sh --video --timed   # hands-free one-take: auto-advances; you only type at the menu
```

**Recording the judge video?** Use `./demo.sh --video` in a **real terminal**
(colors render, and Beat 5 opens the live menu for you to drive by hand). Read the
"Say" lines from [`SUBMISSION.md`](./SUBMISSION.md) §1 and keep it under 3:00.

The script runs the non-interactive beats (1–7) below with banners + the "Say"
line for each, so you don't type anything live. The manual commands follow if
you'd rather drive by hand. Beat 8 (the menu) is interactive — run it by hand.

---

## The pitch (10 seconds)

> When a training run stalls on a GPU cluster, an engineer burns hours
> correlating `nvidia-smi`, `ibstat`, NCCL logs, and sysfs counters across nodes
> to find the one bad GPU, dead rail, or misconfig. **Ground Control runs the
> checks and returns a *named root cause with a fix* in 30 seconds** — and the
> same binary serves ops, customers, and support.

---

## Beat 1 — It knows every check and what applies here

```bash
audit -l
```

**Say:** 51 reference checks in 4 groups + an NCCL extension, plus use-case
bundles. The right column auto-detects the platform — IMEX/NVLink checks show
`NA` on this hardware, active tests are marked.

---

## Beat 2 — A healthy node: all green (real cw0bec capture)

```bash
audit -u preflight --fixture fixtures/cw0bec_blackwell_healthy
```

**Say:** This is **real data captured from a live CoreWeave `cw0bec` node** —
8× Blackwell GPUs, 9× ConnectX-7 at 100G. 17 pass, 0 fail. Note A6 even reports
the real NUMA topology (4/8 GPUs NUMA-local to a NIC). Exit code 0 → drops into
CI / preflight gates.

---

## Beat 3 — A failing GPU: correlated into ONE root cause

```bash
audit -u gpu_fault --fixture fixtures/synth_gpu_fault
```

**Say:** Three raw signals on the same GPU — XID errors, uncorrectable ECC,
91 °C — but instead of three red lines to puzzle over, the **verdict engine
correlates them on `gpu:3` into one named cause with an action**: cordon + RMA.

---

## Beat 4 — The headline: NCCL silently on TCP (435 → 3.4 GB/s)

```bash
audit -u nccl_slow --fixture fixtures/nccl_tcp_fallback
```

**Say:** These are **real NCCL logs**. One bad env var (`NCCL_IB_HCA`) made NCCL
silently fall back from RDMA to TCP sockets — a ~100× bandwidth collapse that
looks like "the cluster is just slow." Ground Control names it and tells you the
exact knob to check.

---

## Beat 5 — Fabric: a dead RDMA port, named

```bash
audit -u preflight --fixture fixtures/synth_fabric_fault
```

**Say:** Port `mlx5_5` is down, `mlx5_4` is accumulating link errors, `mlx5_6`
shows congestion — the verdict pins the dead rail and the action (check
cable/transceiver, drain).

---

## Beat 6 — SAME checks, CUSTOMER profile

```bash
audit --profile customer -u nccl_slow --fixture fixtures/nccl_tcp_fallback
```

**Say:** One binary, three audiences. The `--profile` flag is the *only* branch
point. For a customer: internal hostnames/IPs/serials are **redacted**
(`node:<host>`), active tests are **hard-blocked** (read-only), and every
failure carries **plain-English remediation + a support escalation**.

---

## Beat 7 — SUPPORT profile: machine-readable + ticket bundle

```bash
audit --profile support -u gpu_fault --fixture fixtures/synth_gpu_fault --json | head -30
audit --profile support -u gpu_fault --fixture fixtures/synth_gpu_fault --bundle
tar tzf audit-bundle-*.tar.gz | head        # result.json + evidence/
```

**Say:** For support, the same run emits structured JSON for pipelines and a
`audit-bundle-*.tar.gz` (result + raw evidence, redacted) to attach to a ticket.

---

## Beat 8 — Customer self-serve: the troubleshooting menu

```bash
audit --profile customer --fixture fixtures/nccl_tcp_fallback
#  1   training run is slow   →  read the redacted verdict
#  s   package for support    →  writes audit-bundle-*.tar.gz to attach to a ticket
#  v   show evidence   ·   Enter  back to menu   ·   q  quit
```

**Say:** Same engine, nothing to memorize. A customer just runs `audit`, picks the
symptom in plain English, and gets the same redacted root-cause verdict + fix —
read-only, no bundle names or cluster knowledge required. Then the payoff: **one
keypress (`s`) packages that exact run into a support bundle** to hand to
CoreWeave — self-diagnose straight into a support handoff, all three audiences in
one flow. On a real node, bare `audit` opens this menu live; `--fixture` makes it
reproducible offline. _Interactive — drive this beat by hand; it's not part of
`./demo.sh --auto`._

---

## Close

> We declared a 3-year moon — an autonomous, predictive, fleet-scale GPU-fabric
> flight director — and in the hackathon we landed the vertical slice that proves
> it: **real checks on real CoreWeave hardware, correlated into root-cause
> verdicts a human acts on in 30 seconds.** 103 tests, three audiences, runs
> anywhere. Everything above it is depth on the same spine.

---

## Presenter's cheat sheet — terms by beat

Plain-English definitions so you can explain anything on screen. Say the **bold**
term, then the explanation.

**Beat 1 — the catalog (`audit -l`)**
- **Check / module** — one health probe (51 total). **Groups:** **A** host/NIC/system, **B** link & RDMA physical layer, **C** RDMA/fabric/cluster, **G** GPU, **N** NCCL/collectives.
- **Bundle** — a named set of checks for a symptom (e.g. `nccl_slow`), so you don't memorize check IDs.
- **Auto-detect / `NA`** — checks that don't apply to this GPU are marked NA, not failed (e.g. IMEX/NVLink are for GB200/NVL multi-GPU systems, not RTX PRO 6000 Blackwell).
- **`active` (🔴)** — tests that generate traffic (latency/bandwidth); off unless `--allow-active`, because they perturb a live fabric.

**Beat 2 — healthy node (`preflight`)**
- **RDMA** — Remote Direct Memory Access: NIC-to-NIC transfers that bypass the CPU; how GPUs talk across nodes at full speed.
- **HCA / ConnectX-7 / InfiniBand (IB)** — the IB network card (HCA = Host Channel Adapter) and the high-speed GPU interconnect fabric it plugs into.
- **MTU 9000 / jumbo frames** — large packet size; must match end-to-end or throughput collapses.
- **NUMA-local** — the GPU and its NIC hang off the same CPU socket → lower latency.
- **ECC** — error-correcting GPU memory; *corrected* is normal, *uncorrectable* means failing silicon.
- **XID** — NVIDIA GPU hardware error codes (from the driver/dmesg); the #1 "this GPU is sick" signal.
- **Hugepages / IRQ affinity** — memory-page and interrupt-pinning tuning that RDMA needs for full performance.
- **NVLink / Fabric Manager** — GPU-to-GPU interconnect and the service that runs NVSwitch systems; `NA` here because this SKU has no NVSwitch.
- **exit 0** — all green, so it can gate CI / a pre-flight check.

**Beat 3 — failing GPU (`gpu_fault`)**
- **XID 48 / 79** — specific NVIDIA error codes (memory / fatal GPU errors).
- **Uncorrectable ECC** — memory errors the GPU couldn't fix → the chip is failing.
- **Scope correlation** — all three signals land on `gpu:3`, so they become **one** verdict, not three lines.
- **Cordon** — mark the node unschedulable so no new work lands on it. **RMA** — Return Merchandise Authorization = hardware replacement.

**Beat 4 — NCCL on TCP (`nccl_slow`, the headline)**
- **NCCL** — NVIDIA Collective Communications Library; runs the **all-reduce / all-to-all** operations that sync gradients across GPUs every training step — bandwidth-critical.
- **RDMA vs TCP sockets** — RDMA is the fast path; TCP sockets is a slow CPU-bound fallback (~100× slower).
- **busbw** — "bus bandwidth," NCCL's throughput metric in GB/s.
- **`NCCL_IB_HCA`** — the env var that tells NCCL which IB devices to use; a wrong value silently drops it to TCP.

**Beat 5 — dead RDMA port (`synth_fabric_fault`)**
- **mlx5_0..mlx5_8** — Linux driver names for the ConnectX NIC ports (9 here).
- **Active/LinkUp** — the healthy IB port state; anything else = down.
- **symbol_error / link_error_recovery / local_link_integrity_errors** — IB counters that climb with a bad cable or **transceiver** (the optic at each end).
- **rail** — one GPU's dedicated NIC→switch path (a node has several in parallel).
- **PFC / ECN**, **out_of_sequence / packet_seq_err** — congestion-control signals and the counters that reveal congestion/retransmits.
- **Drain** — evacuate workloads off the node.

**Beat 6 — customer profile**
- **Redaction** — masking hostnames/IPs/serials (shown as `node:<host>`).
- **Read-only enforced** — active (traffic-generating) tests are hard-blocked.
- **Remediation / escalation** — the plain-English fix line + the "contact CoreWeave support" line.

**Beat 7 / 7b — support profile**
- **JSON / exit_code / summary** — machine-readable output for pipelines and CI.
- **severity / scope / supporting** — the verdict's metadata: how bad, where, and which checks back it.
- **bundle (`audit-bundle-*.tar.gz`)** — `result.json` + raw evidence, redacted, to attach to a ticket.

**Beat 8 — customer menu**
- **Symptom picker** — plain-English menu over the bundles; **`s`** writes the support bundle, **`v`** shows evidence — self-diagnose straight into a support handoff.

---

## If asked / backup

- **Verbose evidence:** `audit -u gpu_fault --fixture fixtures/synth_gpu_fault -v`
- **Cluster fan-out:**
  `audit -u gpu_fault --fixture fixtures --nodes cw0bec_blackwell_healthy,synth_gpu_fault`
- **Honest caveats:** live `--nodes` remote exec is the flagged stretch (needs
  `--fixture` today); counters in the IB fixture are a 0-baseline (the container
  doesn't expose the sysfs counters subdir). Full provenance of every fixture is
  in [`docs/cluster-access-and-captures.md`](docs/cluster-access-and-captures.md).
- **Exit codes:** `0` all pass · `1` warnings · `2` failures — CI-ready.
- **"How is this different from Mission Control?"** Mission Control keeps the
  *fleet* healthy by auto-cordoning/replacing bad nodes on hardware faults.
  Ground Control tells a *human* — ops, customer, or support — the **named root
  cause + the fix in 30 seconds**, including the **customer-side config faults**
  (NCCL-on-TCP, MTU, IRQ) that fleet automation isn't responsible for. It's the
  last-mile diagnostic that *feeds* Mission Control — deterministic, portable
  (BMaaS / self-managed / air-gapped), zero runtime tokens. See `SUBMISSION.md` §4.
