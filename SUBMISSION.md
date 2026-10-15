# 🛰️ Ground Control — Moonshot Submission Pack

Everything needed to record and submit. Deadline: **Thu Oct 15, 12:00 PM PT**.

---

## 1. Demo video — 2 slides + full `./demo.sh` (tight ~2:58, hard cap 3:00)

**Structure:** present the **2 intro slides** (`intro-slides.pptx`, keep brief ~24s),
then a real terminal running the **full `./demo.sh`** (8 beats). Pacing is tight —
move briskly. Full presenter run-of-show (slide talk tracks + per-beat WHAT / WHY /
SAY / DO) is in [`VIDEO-SCRIPT.txt`](./VIDEO-SCRIPT.txt) and
[`DEMO-RUNOFSHOW.pdf`](./DEMO-RUNOFSHOW.pdf). Jargon explained inline.

> Setup once: `python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"`.
> **Trim levers if you run long:** drop the slides, or skip Beat 7 (JSON) and show
> only Beat 7b (the bundle).

| Time | On screen | Say (jargon explained inline) | Rubric |
|------|-----------|-----------------|--------|
| **0:00–0:12** | **Slide 1** (problem) | "A thousand-GPU run slows down — or dies. Finding out why is **hours** of hand-digging through logs across many nodes while **GPUs sit idle** — and it looks the same whether it's bad hardware or one wrong setting." | Speed + Business |
| **0:12–0:24** | **Slide 2** (solution) | "Ground Control: one command **names the root cause and the fix in 30 seconds** — for ops, customers, and support. Let me show you." | Business + Technical |
| **0:28–0:40** | `audit -l` | "51 checks across the server, network, and GPUs. It **auto-detects the hardware** — checks that don't apply show 'N-A' — and bundles the right checks per symptom." | Technical |
| **0:40–0:54** | `audit -u preflight --fixture .../cw0bec_blackwell_healthy` | "**Real data from a live CoreWeave Blackwell node** — all green, exit zero: you can gate CI and **stop a bad node before it ever gets a job**." | Technical |
| **0:54–1:10** | `audit -u gpu_fault --fixture .../synth_gpu_fault` | "First, a failing GPU. Three signs on the **same GPU** — driver errors, failing memory, 91° — collapse into **one** verdict: fence the node off and replace the card." | Technical |
| **1:10–1:42** | `audit -u nccl_slow --fixture .../nccl_tcp_fallback` | "Now the big one. GPUs sync data in training via a library called **NCCL**; normally it uses **RDMA — the fast path where network cards talk directly, skipping the CPU**. One wrong setting silently dropped it to ordinary **TCP — ~100× slower**. The **verdict names the cause and the exact fix**." | Speed + Technical |
| **1:42–1:58** | `audit -u preflight --fixture .../synth_fabric_fault` | "A dead network port — one down, one throwing errors, one congested. The verdict pins the dead **rail** and the action: check the cable, drain the node." | Technical |
| **1:58–2:14** | `audit --profile customer -u nccl_slow --fixture .../nccl_tcp_fallback` | "Same engine, **three audiences**. Customer mode is read-only, internal names **hidden**, with a plain-English fix + a 'contact support' line." | Business |
| **2:14–2:26** | `audit --profile support ... --json` | "For support and automation, the same run emits structured **JSON** — verdict, severity, scope, supporting checks." | Business |
| **2:26–2:44** | `audit --profile support ... --bundle` | "And a redacted **bundle** — result + raw evidence — to attach straight to a ticket. Self-serve into a clean handoff." | Business |
| **2:44–2:58** | Close banner | "Faster runs and less idle spend for customers; fewer escalations and higher fleet use for CoreWeave — and the foundation to **predict these failures before they strike**. Ground Control." | Business + Presentation |

**Rubric coverage:** Speed (Slide 1, 1:10) · Business impact (Slides, 1:58–2:44, close) ·
Technical execution (0:28–1:58) · Presentation & clarity (the whole Problem →
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
