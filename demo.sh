#!/usr/bin/env bash
# 🛰️ Ground Control — guided demo. Press Enter to advance through each beat.
# Talking points mirror DEMO.md. Runs entirely on recorded fixtures (no cluster).
#
#   ./demo.sh            # interactive: pause before each beat
#   ./demo.sh --auto     # no pauses (for a rehearsal / recording)

set -u
cd "$(dirname "$0")"

AUDIT="./.venv/bin/audit"
[ -x "$AUDIT" ] || AUDIT="audit"   # fall back to an activated venv

AUTO=0
[ "${1:-}" = "--auto" ] && AUTO=1

BOLD=$'\033[1m'; CYAN=$'\033[1;36m'; DIM=$'\033[2m'; RESET=$'\033[0m'

beat() {  # beat "<title>" "<talking point>" "<command...>"
  printf '\n%s━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n' "$CYAN" "$RESET"
  printf '%s%s%s\n' "$CYAN$BOLD" "$1" "$RESET"
  printf '%s%s%s\n' "$DIM" "$2" "$RESET"
  printf '%s$ %s%s\n' "$BOLD" "$3" "$RESET"
  if [ "$AUTO" -eq 0 ]; then printf '%s[Enter to run]%s' "$DIM" "$RESET"; read -r _; fi
  eval "$3"
  echo
}

clear
printf '%s🛰️  Ground Control — GPU-fabric flight director%s\n' "$BOLD" "$RESET"
printf '%sWhen a training run stalls, an engineer burns hours correlating nvidia-smi,\n' "$DIM"
printf 'ibstat, NCCL logs, and sysfs counters to find the one bad GPU or rail.\n'
printf 'Ground Control returns a NAMED ROOT CAUSE WITH A FIX in 30 seconds.%s\n' "$RESET"
[ "$AUTO" -eq 0 ] && { printf '\n%s[Enter to begin]%s' "$DIM" "$RESET"; read -r _; }

beat "BEAT 1 — it knows every check and what applies here" \
  "51 reference checks in 4 groups + an NCCL extension, plus use-case bundles. The right column auto-detects the platform." \
  "$AUDIT -l"

beat "BEAT 2 — a healthy node: all green (REAL cw0bec capture)" \
  "Real data from a live CoreWeave cw0bec node: 8x Blackwell GPUs, 9x ConnectX-7. 17 pass, 0 fail, exit 0 -> CI-ready." \
  "$AUDIT -u preflight --fixture fixtures/cw0bec_blackwell_healthy"

beat "BEAT 3 — a failing GPU, correlated into ONE root cause" \
  "Three raw signals on the same GPU (XID + ECC + 91C) become one named cause with an action: cordon + RMA." \
  "$AUDIT -u gpu_fault --fixture fixtures/synth_gpu_fault"

beat "BEAT 4 — THE HEADLINE: NCCL silently on TCP (435 -> 3.4 GB/s)" \
  "Real NCCL logs. One bad env var made NCCL fall back from RDMA to TCP sockets — a ~100x collapse that looks like 'the cluster is just slow.'" \
  "$AUDIT -u nccl_slow --fixture fixtures/nccl_tcp_fallback"

beat "BEAT 5 — fabric: a dead RDMA port, named" \
  "Port mlx5_5 is down, mlx5_4 accumulating link errors, mlx5_6 congested — the verdict pins the dead rail and the action." \
  "$AUDIT -u preflight --fixture fixtures/synth_fabric_fault"

beat "BEAT 6 — SAME checks, CUSTOMER profile" \
  "One binary, three audiences. --profile is the only branch point: hostnames/IPs redacted, active tests blocked, plain-English fix + escalation." \
  "$AUDIT --profile customer -u nccl_slow --fixture fixtures/nccl_tcp_fallback"

beat "BEAT 7 — SUPPORT profile: machine-readable + ticket bundle" \
  "Same run emits structured JSON for pipelines and a redacted tarball to attach to a ticket." \
  "$AUDIT --profile support -u gpu_fault --fixture fixtures/synth_gpu_fault --json | head -20"

beat "BEAT 7b — the support bundle" \
  "result.json + raw evidence, redaction applied." \
  "$AUDIT --profile support -u gpu_fault --fixture fixtures/synth_gpu_fault --bundle && tar tzf audit-bundle-*.tar.gz | head && rm -f audit-bundle-*.tar.gz"

printf '\n%s━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n' "$CYAN" "$RESET"
printf '%sWe declared a 3-year moon and landed the vertical slice that proves it:\n' "$BOLD"
printf 'real checks on real CoreWeave hardware, correlated into root-cause verdicts\n'
printf 'a human acts on in 30 seconds. 91 tests, three audiences, runs anywhere.%s\n\n' "$RESET"
