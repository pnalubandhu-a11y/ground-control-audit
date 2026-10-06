"""Terminal rendering for the `audit -l` view.

Colors are ANSI, auto-disabled when stdout is not a TTY (or NO_COLOR is set) so
piped/redirected output stays clean.
"""

from __future__ import annotations

import os
import sys

from ..core.catalog import H100, ModuleSpec
from ..core import registry

_GROUP_TITLES = {
    "A": "host / NIC / system",
    "B": "link / RDMA physical",
    "C": "RDMA / fabric / cluster",
    "G": "GPU",
}

# ANSI codes
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"


def _color_enabled(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


class _Paint:
    def __init__(self, enabled: bool):
        self.on = enabled

    def __call__(self, text: str, code: str) -> str:
        return f"{code}{text}{_RESET}" if self.on else text


def _marker(spec: ModuleSpec, paint: _Paint) -> str:
    """One glyph summarizing H100 applicability. Active takes precedence."""
    if spec.active:
        return paint("active 🔴", _RED)
    if spec.h100 == H100.NA:
        return paint("NA     🚫", _DIM)
    if spec.h100 == H100.PARTIAL:
        return paint("partial⚠️", _YELLOW)
    return paint("native ✅", _GREEN)


def render_list(stream=None) -> str:
    """Build the full `audit -l` view and return it (also usable for tests)."""
    stream = stream or sys.stdout
    paint = _Paint(_color_enabled(stream))
    lines: list[str] = []

    lines.append(paint("🛰️  audit — Ground Control  ·  module catalog", _BOLD))
    lines.append("")

    for group, specs in registry.modules_by_group().items():
        title = _GROUP_TITLES.get(group, group)
        lines.append(paint(f"Group {group} — {title}", _BOLD + _CYAN))
        for s in specs:
            lines.append(
                f"  {s.id:<4} {s.name:<34} {_marker(s, paint)}"
            )
        lines.append("")

    lines.append(paint("Use-case bundles", _BOLD + _CYAN))
    for name in registry.bundle_names():
        ids = ", ".join(m.id for m in registry.resolve_bundle(name))
        lines.append(f"  {name:<16} {paint(ids, _DIM)}")
    lines.append("")

    legend = "✅ native   ⚠️ partial   🚫 NA (Blackwell/IMEX)   🔴 active (--allow-active)"
    lines.append(paint(legend, _DIM))

    return "\n".join(lines)


def print_list(stream=None) -> None:
    stream = stream or sys.stdout
    print(render_list(stream), file=stream)
