"""Machine-readable JSON output (DESIGN §8).

The same result set as the terminal view, structured for pipelines / Mission
Control. Redaction is applied first when the profile requires it, so customer
JSON never leaks internal identifiers either.
"""

from __future__ import annotations

import dataclasses
import json
import sys

from ..core.profile import Profile
from ..core.redact import redact_result, redact_verdict
from ..core.result import ModuleResult, Status, Verdict
from . import terminal


def build_payload(
    results: list[ModuleResult],
    verdicts: list[Verdict],
    *,
    profile: Profile | None = None,
) -> dict:
    if profile and profile.redact:
        results = [redact_result(r) for r in results]
        verdicts = [redact_verdict(v) for v in verdicts]

    counts = {s.value.lower(): 0 for s in Status}
    for r in results:
        counts[r.status.value.lower()] += 1

    return {
        "profile": profile.name if profile else "internal",
        "exit_code": terminal.exit_code(results),
        "summary": counts,
        "verdicts": [dataclasses.asdict(v) for v in verdicts],
        "modules": [dataclasses.asdict(r) for r in results],
    }


def render_json(results, verdicts, *, profile=None) -> str:
    return json.dumps(
        build_payload(results, verdicts, profile=profile), indent=2, default=str
    )


def print_json(results, verdicts, *, profile=None, stream=None) -> None:
    stream = stream or sys.stdout
    print(render_json(results, verdicts, profile=profile), file=stream)
