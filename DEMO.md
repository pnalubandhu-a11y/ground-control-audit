# 🛰️ Ground Control — Demo Runbook

The exact 7-beat sequence for judging. **Fixtures-first: every command below
works with zero cluster access**, so a flaky network can't break the demo.

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
./.venv/bin/pytest -q          # expect: 91 passed
```

## Fastest path: the guided script

```bash
./demo.sh            # press Enter to advance through each beat (talking points on screen)
./demo.sh --auto     # no pauses — for a rehearsal or screen recording
```

The script runs all 8 beats below with banners + the "Say" line for each, so you
don't type anything live. The manual commands follow if you'd rather drive by hand.

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

## Close

> We declared a 3-year moon — an autonomous, predictive, fleet-scale GPU-fabric
> flight director — and in the hackathon we landed the vertical slice that proves
> it: **real checks on real CoreWeave hardware, correlated into root-cause
> verdicts a human acts on in 30 seconds.** 91 tests, three audiences, runs
> anywhere. Everything above it is depth on the same spine.

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
