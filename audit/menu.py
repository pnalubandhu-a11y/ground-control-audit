"""Interactive customer troubleshooting menu.

A plain-English symptom picker over the existing use-case bundles. The caller
injects a ``run_bundle`` callback (bundle name -> exit code) so this module
stays decoupled from the runner and is trivially testable.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TextIO

# Symptom (what the customer sees) -> existing bundle name. Data only.
SYMPTOMS: list[tuple[str, str]] = [
    ("Training run is slow / stalled", "nccl_slow"),
    ("A GPU looks unhealthy (errors / heat)", "gpu_fault"),
    ("Network / RDMA problems", "rdma_debug"),
    ("Pre-flight check before a big run", "preflight"),
    ("NVLink / multi-GPU issues", "nvlink_health"),
]

_QUIT = {"q", "quit", "exit"}


def _render(out: TextIO) -> None:
    out.write("\nWhat are you seeing? (read-only health checks)\n\n")
    for i, (label, _bundle) in enumerate(SYMPTOMS, start=1):
        out.write(f"  {i}) {label}\n")
    out.write("  q) quit\n\n")


def run_menu(
    run_bundle: Callable[[str], int],
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
            worst = max(worst, run_bundle(bundle))
            continue

        out.write(f"'{choice}' is not a valid choice. "
                  f"Pick 1-{len(SYMPTOMS)} or q.\n")
