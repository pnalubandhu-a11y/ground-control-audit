# 🛰️ Ground Control — Moonshot Submission Pack

Everything needed to record and submit. Deadline: **Thu Oct 15, 12:00 PM PT**.

---

## 1. Demo video — 3:00 shot-list + narration

**Format:** screen recording of a real terminal (colors + emoji render only in a
real TTY, not piped). Run the commands live or pre-stage them. The first five
beats mirror `./demo.sh`; the last beat (menu) is interactive — drive it by hand.
Keep it to **3:00 max** — judges stop at the cap.

> Tip: `pip install -e ".[dev]"` and `alias audit=./.venv/bin/audit` first, in the
> `hackathon/audit` dir. Rehearse once with `./demo.sh --auto`.

| Time | On screen | Say (narration) |
|------|-----------|-----------------|
| **0:00–0:15** | Title card or empty terminal | "When a training run stalls on a GPU cluster, an engineer burns **hours** correlating `nvidia-smi`, `ibstat`, NCCL logs, and sysfs counters across nodes to find the one bad GPU or dead rail. Ground Control does it in one command." |
| **0:15–0:35** | `audit -l` then `audit -u preflight --fixture fixtures/cw0bec_blackwell_healthy` | "51 checks in four groups, and it **auto-detects the platform**. Here's a **real CoreWeave Blackwell node** — 17 checks, all green. Exit 0, so it drops straight into a CI / preflight gate." |
| **0:35–1:15** | `audit -u nccl_slow --fixture fixtures/nccl_tcp_fallback` | "These are **real NCCL logs**. One bad env var silently dropped NCCL from RDMA to **TCP sockets** — a ~**100x bandwidth collapse** that just looks like 'the cluster is slow.' Instead of a wall of counters, the **verdict engine names the root cause and the exact fix**. This is the moonshot: correlation, not just checks." |
| **1:15–1:40** | `audit -u gpu_fault --fixture fixtures/synth_gpu_fault` | "It generalizes. Three raw signals on the **same GPU** — XID errors, uncorrectable ECC, 91C — collapse into **one** verdict: cordon the node and RMA the GPU." |
| **1:40–2:20** | `audit --profile customer --fixture fixtures/nccl_tcp_fallback`, then type `1`, then `s` | "Same engine, three audiences. A **customer** runs `audit`, picks a symptom in plain English — no flags, no bundle names — and gets the **redacted** root cause and fix. Then the payoff: **one keypress, `s`, packages that exact run into a support bundle** to hand to CoreWeave. Self-diagnose straight into a support handoff." |
| **2:20–2:45** | Verdict still on screen | "That collapses a multi-hour war-room into **30 seconds**. On clusters where idle GPU-hours cost thousands per hour, faster diagnosis is real money — and it moves tier-1 triage from the support queue to self-serve." |
| **2:45–3:00** | `demo.sh` close banner or title | "This is the **walking skeleton** of a 3-year moon: an autonomous, predictive, fleet-scale GPU-fabric flight director. Real checks on real hardware, correlated into an action in 30 seconds. **103 tests, three audiences, runs anywhere.** Everything above it is depth on the same spine." |

**Rubric coverage check:**
- *Speed / Better Ways of Working*: 0:00, 0:35, 2:20 (hours to 30s; self-serve).
- *Business Impact*: 2:20 (GPU-hours, support deflection).
- *Technical Execution*: 0:15-1:40 (auto-detect, verdict engine, real captures, 103 tests).
- *Presentation & Clarity*: the Problem-Solution-Prototype-Impact arc end-to-end.

---

## 2. Project information (paste into the submission form)

**Name:** Ground Control — GPU-Fabric Flight Director (`audit`)

**One-liner:** One command that runs 40+ GPU-fabric & RDMA health checks and
correlates the raw signals into a **named root cause with a fix** — turning a
multi-hour debugging war-room into a 30-second answer.

**Problem:** When a training run stalls on a GB200/H100 cluster, diagnosis is
manual, reactive, and expert-bound: an engineer opens ten terminals and
pattern-matches `ibstat`, `nvidia-smi`, `dcgmi`, NCCL logs, and sysfs counters
across many nodes to find the one bad rail, drifted link, or flaky GPU.

**Solution:** `audit` runs the checks in parallel and feeds results into a
YAML-authored **verdict engine** that maps failing signals **on a shared scope**
(same NIC / GPU / node) into named root causes — bad cable, fabric congestion,
failing GPU, Fabric Manager down — each with a 30-second action. One binary serves
**three audiences** via a `--profile` flag that changes only safety, redaction,
and packaging: `internal` (full detail), `customer` (read-only, redacted,
plain-English remediation + a self-serve troubleshooting menu), and `support`
(machine-readable JSON + a ticket bundle).

**What we built (prototype):** A working Python CLI — 12 live check modules across
host/RDMA/GPU groups, platform auto-detection, the verdict-correlation engine with
marquee rules, all three profiles, a customer **symptom-picker menu** with a
one-keypress **support-bundle handoff**, JSON output, and fixture-based cluster
fan-out. **103 automated tests.** Validated on a **real CoreWeave `cw0bec`
RTX PRO 6000 Blackwell** node (captures included as fixtures) plus synthetic fault
sets, so the demo runs with zero cluster access.

**Impact:** Diagnosis time for common fabric/GPU failures drops from hours to
seconds; idle-GPU cost during a stall is cut; and tier-1 triage shifts from the
support queue to customer self-serve with an automatic, redacted escalation
bundle.

**The moonshot (3 years):** an autonomous, predictive, fleet-scale flight director
that forecasts a rail/GPU failing *before* it kills a run and closes the loop
(drain / cordon / RMA) on its own. This hackathon lands Phase 0 — the vertical
slice through the whole stack; the future is depth, not a rewrite.

**Tech:** Python, YAML-authored check bundles + verdict rules, pytest (103 tests),
runs on bare-metal CoreWeave nodes; parses `ibstat`/`nvidia-smi`/NCCL/sysfs.

**How to run:**
```bash
cd hackathon/audit
python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"
./.venv/bin/audit -u nccl_slow --fixture fixtures/nccl_tcp_fallback
./.venv/bin/audit            # bare = interactive troubleshooting menu
./.venv/bin/pytest -q        # 103 passed
```

**Team:** Prashanth Nalubandhu — Solutions Architect (Mission Commander); Lalit Sahu — Solutions Engineer.

---

## 3. Rubric self-assessment (4 × 25 = 100) + special awards

Score each criterion independently; judges look for the evidence in the **video**.
Make the narration say these out loud.

| Criterion (25 pts) | Where the demo proves it | Honest self-score |
|---|---|---|
| **Speed / better ways of working** | Hours of manual `nvidia-smi`/`ibstat`/NCCL correlation → one named cause in 30s (Beats 3–4); customer self-serve menu + one-keypress support handoff (Beat 5/8). | **Strong (20)** |
| **Business impact** | Recovers idle GPU-hours on stalled runs; deflects tier-1 tickets to self-serve; catches **customer-side config faults** (NCCL-on-TCP, MTU, IRQ) that fleet automation won't flag. Ties to fleet-reliability / GPU-utilization / support-efficiency OKRs. | **Good–Strong (15–20)** |
| **Technical execution** | Module/verdict architecture, YAML-authored rules, **103 tests**, runs on a real `cw0bec` Blackwell capture, **deterministic (zero LLM inference at runtime)**. | **Strong (20)** |
| **Presentation & clarity** | Problem → Solution → Prototype → Impact arc; tight 3-min cut; the "What you're watching" frame in DEMO.md. | **Strong (20)** |

**Special awards (Yes/No — honest stances):**
- **Most efficient token usage — strong YES to claim.** The product does its core
  job — fault correlation — with **zero LLM tokens at runtime** (deterministic YAML
  rules), so it delivers the impact with *no ongoing inference cost*. Contrast with
  agentic tools that call a model per investigation. (AI was used to *build* it;
  cite build-time token metrics if available.)
- **Most OKRs — plausible YES.** Maps to GPU-fleet reliability/utilization, customer
  experience, and support efficiency. *Confirm the exact CoreWeave OKRs you'll cite.*
- **Cross-functional team — borderline; don't bank on it.** Team is **Prashanth
  Nalubandhu (Solutions Architect)** + **Lalit Sahu (Solutions Engineer)** — distinct
  roles (architecture vs. implementation/engineering) but both in the field/technical
  org, so it's a soft case for a strict judge. State both titles honestly; treat any
  Yes here as upside, not a given.

## 4. How this differs from CoreWeave Mission Control

Judges will know Mission Control — lead with the difference so this doesn't read as
redundant. Mission Control is two things: (1) **platform fleet-automation** that
auto-cordons / reboots / RMAs **CoreWeave-managed** nodes on *hardware* faults
(ECC, XID, GPU-off-bus, IB link), and (2) the **Mission Control Agent/MCP** — an AI
agent that answers GPU-health questions over telemetry.

Ground Control is **complementary, not competing** (our roadmap Phase 2 feeds *into*
Mission Control). The honest distinctions:

| | CoreWeave Mission Control | Ground Control `audit` |
|---|---|---|
| **What it does** | *Acts* on the fleet — cordon / reboot / replace a bad node | *Explains* — one named root cause **+ the fix a human applies** |
| **Fault scope** | Hardware faults CoreWeave owns | **Also customer-side config/workload faults** (NCCL-on-TCP, MTU, IRQ, env vars) that fleet automation deliberately won't touch |
| **Audience** | CoreWeave platform + internal AI agent | **Three audiences** — ops, customer (redacted, self-serve menu), support (ticket bundle) |
| **Portability** | CKS/SUNK **managed** nodes | A single portable CLI — runs on BMaaS, self-managed, non-CKS, **air-gapped** |
| **AI cost** | MCP agent = tokens per investigation | **Deterministic, zero runtime tokens** |

**One-liner for the video:** "Mission Control keeps the *fleet* healthy by pulling
bad nodes; Ground Control tells a *human* — ops, customer, or support — the named
root cause and the fix in 30 seconds, including the workload-config failures the
fleet automation isn't responsible for. It's the last-mile diagnostic that feeds
Mission Control."

## 5. Pre-submission checklist
- [ ] Record ≤3:00 video per the shot-list above
- [ ] Paste project info into the form
- [ ] Decide repo visibility — judges must be able to open the prototype link
      (make `pnalubandhu-a11y/ground-control-audit` public, grant judge read, or
      attach a zip). A private link reads as "prototype didn't work."
- [ ] Add supporting links (repo, this pack, DESIGN.md / ROADMAP.md)
