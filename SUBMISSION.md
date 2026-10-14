# 🛰️ Ground Control — Moonshot Submission Pack

Everything needed to record and submit. Deadline: **Thu Oct 15, 12:00 PM PT**.

---

## 1. Demo video — ~2:50 script (hard cap 3:00)

**Record the 6-beat cut:** `./demo.sh --video` (real terminal + mic, big font).
Rehearse silently with `./demo.sh --video --auto`; hands-free one-take with
`./demo.sh --video --timed`. The full narration teleprompter is
[`VIDEO-SCRIPT.txt`](./VIDEO-SCRIPT.txt) — scroll it while you record. The table
below is the same script in brief; each row is tagged with the rubric criterion it
serves.

> Setup once: `python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"`.
> Do **not** run bare `./demo.sh` for the video — that's the full 8-beat version
> and runs long. Use `--video`.

| Time | On screen | Say (narration) | Rubric |
|------|-----------|-----------------|--------|
| **0:00–0:20** | Title / empty terminal | "Picture a thousand-GPU training run that suddenly slows to a crawl — or dies. Finding the cause means an engineer hand-correlating `nvidia-smi`, `ibstat`, and NCCL logs across dozens of nodes — **hours** of your most expensive people, while **thousands of dollars of GPUs sit idle**. Ground Control turns that into one command." | Speed + Business |
| **0:20–0:38** | `audit -l` | "51 checks across host, network, and GPU, plus an NCCL extension. It **auto-detects the hardware** — checks that don't apply show NA instead of firing false alarms — and groups them into bundles so you run the right ones for the symptom." | Technical |
| **0:38–0:58** | `audit -u preflight --fixture fixtures/cw0bec_blackwell_healthy` | "**Real data from a live CoreWeave Blackwell node** — 8 GPUs, 9 ConnectX-7 NICs. 17 checks, all green, exit 0 — so it drops straight into CI or a pre-flight gate and **stops a bad node before it ever gets a job**." | Technical |
| **0:58–1:35** | `audit -u nccl_slow --fixture fixtures/nccl_tcp_fallback` | "A real failure — **real NCCL logs**. One wrong env var silently pushed NCCL off RDMA onto TCP sockets: a ~**100× collapse** that just looks like 'the cluster feels slow,' and teams burn days on it. Ground Control's **verdict engine correlates the signals into the named root cause and the exact fix**. That's the moonshot: an answer, not another dashboard." | Speed + Technical |
| **1:35–1:55** | `audit -u gpu_fault --fixture fixtures/synth_gpu_fault` | "It generalizes. Three signals on the **same GPU** — XID, uncorrectable ECC, 91° — collapse into **one** verdict with an action: cordon the node and open an RMA." | Technical |
| **1:55–2:35** | `audit --profile customer --fixture fixtures/nccl_tcp_fallback` → type `1`, then `s` | "One binary, **three audiences**. A **customer** picks a symptom in plain English — no flags, no expertise — and gets the root cause with internal IDs **redacted**. Then the payoff: **one keypress packages that exact run into a support bundle**. The customer self-diagnoses; if they still need us, **CoreWeave support gets structured evidence** instead of 'it's slow.'" | Business |
| **2:35–2:50** | Close banner | "Concrete value: for customers, **faster runs, less idle GPU spend, less waiting on support**; for CoreWeave, **fewer escalations, faster triage, higher fleet utilization** — on the failures that hurt most." | Business |
| **2:50–3:00** | Close banner | "And this is the **walking skeleton** of a bigger moon — an autonomous, fleet-scale flight director that predicts failures before they strike. 103 tests, three audiences, real hardware. Ground Control." | Presentation |

**Rubric coverage:** Speed (0:00, 0:58) · Business impact (0:00, 1:55, 2:35) ·
Technical execution (0:20–1:55) · Presentation & clarity (the whole Problem →
Solution → Prototype → Impact arc).

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
