"""Interactive customer troubleshooting menu.

A plain-English symptom picker over the existing use-case bundles, plus a
post-verdict action menu. The caller injects a ``run_bundle`` callback
(bundle name -> RunOutcome) so this module stays decoupled from the runner
and is trivially testable.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Protocol, TextIO

# Symptom (what the customer sees) -> existing bundle name. Data only.
SYMPTOMS: list[tuple[str, str]] = [
    ("Training run is slow / stalled", "nccl_slow"),
    ("A GPU looks unhealthy (errors / heat)", "gpu_fault"),
    ("Network / RDMA problems", "rdma_debug"),
    ("Pre-flight check before a big run", "preflight"),
    ("NVLink / multi-GPU issues", "nvlink_health"),
]

_QUIT = {"q", "quit", "exit"}
_BACK = {"", "b", "back"}


class RunOutcome(Protocol):
    """What a completed run exposes to the action menu."""
    exit_code: int
    def support_bundle(self) -> str: ...   # write tarball, return its path
    def evidence(self) -> str: ...         # rendered per-module evidence


def _render(out: TextIO) -> None:
    out.write("\nWhat are you seeing? (read-only health checks)\n\n")
    for i, (label, _bundle) in enumerate(SYMPTOMS, start=1):
        out.write(f"  {i}) {label}\n")
    out.write("  q) quit\n\n")


def _action_menu(outcome: RunOutcome, input_fn: Callable[[str], str],
                 out: TextIO) -> None:
    """After a run, offer support-bundle / evidence; loop until the user goes back."""
    while True:
        out.write("\n  [s] package for support   [v] show evidence   "
                  "[Enter] back to menu\n")
        try:
            action = input_fn("action> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return

        if action in _BACK:
            return
        if action == "s":
            path = outcome.support_bundle()
            out.write(f"\n  ✓ wrote {path}\n")
        elif action == "v":
            out.write("\n" + outcome.evidence() + "\n")
        else:
            out.write(f"  '{action}' is not an option. Pick [s], [v], or Enter.\n")


def run_menu(
    run_bundle: Callable[[str], RunOutcome],
    *,
    input_fn: Callable[[str], str] = input,
    out: TextIO = sys.stdout,
) -> int:
    """Loop the symptom menu until the user quits.

    Returns the worst exit code of any bundle run this session (0 if none ran).
    """
    worst = 0
    while True:
        _render(out)
        try:
            choice = input_fn("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            out.write("\n")
            return worst

        if choice in _QUIT:
            return worst

        if choice.isdigit() and 1 <= int(choice) <= len(SYMPTOMS):
            _label, bundle = SYMPTOMS[int(choice) - 1]
            outcome = run_bundle(bundle)
            worst = max(worst, outcome.exit_code)
            _action_menu(outcome, input_fn, out)
            continue

        out.write(f"'{choice}' is not a valid choice. "
                  f"Pick 1-{len(SYMPTOMS)} or q.\n")
